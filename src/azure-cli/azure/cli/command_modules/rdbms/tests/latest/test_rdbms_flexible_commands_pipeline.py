# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from datetime import datetime, timedelta, tzinfo
from time import sleep
from dateutil.tz import tzutc
import pytest
import random
from azure_devtools.scenario_tests import AllowLargeResponse
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.local_context import AzCLILocalContext, ALL, LOCAL_CONTEXT_FILE
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StringContainCheck,
    VirtualNetworkPreparer,
    LocalContextScenarioTest,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from .conftest import resource_random_name
from azure.cli.command_modules.rdbms._flexible_server_util import get_id_components

# Constants
SERVER_NAME_PREFIX = 'clitest-'
RG_NAME_PREFIX = 'clitest.rg'
SERVER_NAME_MAX_LENGTH = 50
EXISTING_RG = 'clitest-do-not-delete'
RESTORE_BUFFER = 90

def write_failed_result(filename):
    with open(filename, "w") as f:
        f.write("FAIL")

def write_succeeded_result(filename):
    with open(filename, "w") as f:
        f.write("SUCCESS")


class RdbmsScenarioTest(ScenarioTest):

    def create_random_name(self, prefix, length, description=None):
        self.test_resources_count += 1
        moniker = '{}{:06}'.format(prefix, self.test_resources_count)

        class_name = type(self).__name__
        if 'MySql' in class_name:
            class_name = class_name.replace('MySqlFlexibleServer', '')
        else:
            class_name = class_name.replace('PostgresFlexibleserver', '')
        class_name = class_name.replace('ScenarioTest', '')

        if self.in_recording:
            name = prefix + class_name.lower()
            if description is not None:
                name += '-' + description
            name += '-' + resource_random_name
            name = name[:50].lower()
            self.name_replacer.register_name_pair(name, moniker)
            return name

        return moniker


class ServerPreparer(AbstractPreparer, SingleValueReplacer):

    def __init__(self, engine_type, location, engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server',
                 resource_group_parameter_name='resource_group'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.engine_type = engine_type
        self.engine_prameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} flexible-server create -l {} -g {} -n {} --public-access none'
        execute(self.cli_ctx, template.format(self.engine_type,
                                              self.location,
                                              group, name))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    # def remove_resource(self, name, **kwargs):
    #     group = self._get_resource_group(**kwargs)
    #     execute(self.cli_ctx, 'az {} flexible-server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)


class FlexibleServerRegularMgmtScenarioTest(RdbmsScenarioTest):

    def _test_flexible_server_create(self, database_engine, resource_group, server):
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D2s_v3'
            version = '12'
            storage_size = 128
        elif database_engine == 'mysql':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
            storage_size = 32
            version = '5.7'
        storage_size_mb = storage_size * 1024
        backup_retention = 7

        self.cmd('{} flexible-server create -l {} -g {} -n {} --public-access none'
                 .format(database_engine, self.location, resource_group, server), checks=None)
        
        list_checks = [JMESPathCheck('name', server),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=list_checks)

        if database_engine == 'mysql':
            self.cmd('{} flexible-server db show -g {} -s {} -d flexibleserverdb'
                     .format(database_engine, resource_group, server), checks=[JMESPathCheck('name', 'flexibleserverdb')])

    def _test_flexible_server_create_non_default_tiers(self, database_engine, resource_group, server1, server2):

        if database_engine == 'postgres':
            self.cmd('postgres flexible-server create -g {} -l {} -n {} --tier Burstable --sku-name Standard_B1ms --public-access none'
                     .format(resource_group, self.location, server1))

            self.cmd('postgres flexible-server show -g {} -n {}'
                     .format(resource_group, server1),
                     checks=[JMESPathCheck('sku.tier', 'Burstable'),
                             JMESPathCheck('sku.name', 'Standard_B1ms')])

            self.cmd('postgres flexible-server create -g {} -l {} -n {} --tier MemoryOptimized --sku-name Standard_E2s_v3 --public-access none'
                     .format(resource_group, self.location, server2))

            self.cmd('postgres flexible-server show -g {} -n {}'
                     .format(resource_group, server2),
                     checks=[JMESPathCheck('sku.tier', 'MemoryOptimized'),
                             JMESPathCheck('sku.name', 'Standard_E2s_v3')])

        elif database_engine == 'mysql':
            self.cmd('mysql flexible-server create -g {} -l {} -n {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --public-access none'
                     .format(resource_group, self.location, server1))

            self.cmd('mysql flexible-server show -g {} -n {}'
                     .format(resource_group, server1),
                     checks=[JMESPathCheck('sku.tier', 'GeneralPurpose'),
                             JMESPathCheck('sku.name', 'Standard_D2s_v3')])

            self.cmd('mysql flexible-server create -g {} -l {} -n {} --tier MemoryOptimized --sku-name Standard_E2s_v3 --public-access none'
                     .format(resource_group, self.location, server2))

            self.cmd('mysql flexible-server show -g {} -n {}'
                     .format(resource_group, server2),
                     checks=[JMESPathCheck('sku.tier', 'MemoryOptimized'),
                             JMESPathCheck('sku.name', 'Standard_E2s_v3')])

    def _test_flexible_server_create_different_version(self, database_engine, resource_group, server):

        if database_engine == 'postgres':
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --version 11 --public-access none'
                     .format(resource_group, server, self.location))

            self.cmd('postgres flexible-server show -g {} -n {}'
                     .format(resource_group, server),
                     checks=[JMESPathCheck('version', 11)])

    def _test_flexible_server_create_select_zone(self, database_engine, resource_group, server):

        if database_engine == 'postgres':
            self.cmd('postgres flexible-server create -g {} -l {} -n {} --zone 1 --public-access none'
                     .format(resource_group, self.location, server))

            self.cmd('postgres flexible-server show -g {} -n {}'
                     .format(resource_group, server),
                     checks=[JMESPathCheck('availabilityZone', 1)])

    def _test_flexible_server_update_password(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server update -g {} -n {} -p randompw321##@!'
                 .format(database_engine, resource_group, server))

    def _test_flexible_server_update_storage(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server update -g {} -n {} --storage-size 256'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('storageProfile.storageMb', 256 * 1024)])

    def _test_flexible_server_update_backup_retention(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'
                 .format(database_engine, resource_group, server, 17),
                 checks=[JMESPathCheck('storageProfile.backupRetentionDays', 17)])

    def _test_flexible_server_update_scale_up(self, database_engine, resource_group, server):

        # Scale up
        if database_engine == 'postgres':
            tier = 'MemoryOptimized'
            sku_name = 'Standard_E16s_v3'
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D16s_v3'

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

    def _test_flexible_server_update_scale_down(self, database_engine, resource_group, server):
        # Scale down
        if database_engine == 'postgres':
            tier = 'MemoryOptimized'
            sku_name = 'Standard_E2s_v3'
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D2s_v3'

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

    def _test_flexible_server_update_mmw(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server update -g {} -n {} --maintenance-window Mon:1:30'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('maintenanceWindow.dayOfWeek', 1),
                         JMESPathCheck('maintenanceWindow.startHour', 1),
                         JMESPathCheck('maintenanceWindow.startMinute', 30)])

    def _test_flexible_server_update_tag(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server update -g {} -n {} --tags key=3'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('tags.key', '3')])

    def _test_flexible_server_restore(self, database_engine, resource_group, server, restore_server):

        try:
            self.cmd('{} flexible-server show -g {} --name {}'.format(database_engine, resource_group, server))
        except:
            pytest.skip("source server not provisioned")

        restore_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --restore-time {}'
                .format(database_engine, resource_group, restore_server, server, restore_time),
                checks=[JMESPathCheck('name', restore_server),
                        JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('{} flexible-server delete -g {} --name {} --yes'.format(database_engine, resource_group, restore_server))

    def _test_flexible_server_restart(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server restart -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_stop(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server stop -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_start(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server start -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_list(self, database_engine, resource_group):
        self.cmd('{} flexible-server list -g {}'.format(database_engine, resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])

    def _test_flexible_server_connection_string(self, database_engine, server):
        connection_string = self.cmd('{} flexible-server show-connection-string -s {}'
                                     .format(database_engine, server)).get_output_in_json()

        self.assertIn('jdbc', connection_string['connectionStrings'])
        self.assertIn('node.js', connection_string['connectionStrings'])
        self.assertIn('php', connection_string['connectionStrings'])
        self.assertIn('python', connection_string['connectionStrings'])
        self.assertIn('ado.net', connection_string['connectionStrings'])

    def _test_flexible_server_list_skus(self, database_engine, location):
        self.cmd('{} flexible-server list-skus -l {}'.format(database_engine, location),
                 checks=[JMESPathCheck('type(@)', 'array')])


class FlexibleServerIopsMgmtScenarioTest(RdbmsScenarioTest):

    def _test_flexible_server_iops_create(self, database_engine, resource_group, server):
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        # IOPS passed is beyond limit of max allowed by SKU and free storage
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 350 --storage-size 200 --tier Burstable --sku-name Standard_B1ms'
                 .format(database_engine, resource_group, server, self.location))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('storageProfile.storageIops', 640)])

    def _test_flexible_server_iops_scale_up(self, database_engine, resource_group, server):

        # SKU upgraded and IOPS value set smaller than free iops, max iops for the sku
        self.cmd('{} flexible-server update -g {} -n {} --tier GeneralPurpose --sku-name Standard_D8s_v3 --iops 400'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('storageProfile.storageIops', 900)])

    def _test_flexible_server_iops_scale_down(self, database_engine, resource_group, server):

        # SKU downgraded and free iops is bigger than free iops
        self.cmd('{} flexible-server update -g {} -n {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --storage-size 300'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('storageProfile.storageIops', 1200)])


class FlexibleServerHighAvailabilityMgmt(RdbmsScenarioTest):

    def _test_flexible_server_high_availability_create(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server create -g {} -l {} -n {} --high-availability Enabled --tier GeneralPurpose --sku-name Standard_D4s_v3 --public-access none'
                 .format(database_engine, resource_group, self.location, server))

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('haEnabled', 'Enabled')])

    def _test_flexible_server_high_availability_disable(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server update -g {} -n {} --high-availability Disabled'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('haEnabled', 'Disabled')])

        time.sleep(5 * 60)

    def _test_flexible_server_high_availability_enable(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server update -g {} -n {} --high-availability Enabled'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('haEnabled', 'Enabled')])

    def _test_flexible_server_high_availability_update_scale_up(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server update -g {} -n {} --tier GeneralPurpose --sku-name Standard_D8s_v3'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('sku.name', 'Standard_D8s_v3'),
                         JMESPathCheck('sku.tier', 'GeneralPurpose')])

    def _test_flexible_server_high_availability_update_parameter(self, database_engine, resource_group, server):
        if database_engine == 'mysql':
            parameter_name = 'wait_timeout'
            value = '30000'
        elif database_engine == 'postgres':
            parameter_name = 'lock_timeout'
            value = '2000'

        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])

    def _test_flexible_server_high_availability_restart(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server restart -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_high_availability_stop(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server stop -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_high_availability_start(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server start -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_flexible_server_high_availability_restore(self, database_engine, resource_group, server, restore_server):

        try:
            self.cmd('{} flexible-server show -g {} --name {}'.format(database_engine, resource_group, server))
        except:
            pytest.skip("source server not provisioned")
        restore_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        if database_engine == 'postgres':
            self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --zone 2 --restore-time {}'
                     .format(database_engine, resource_group, restore_server, server, restore_time),
                     checks=[JMESPathCheck('name', restore_server),
                             JMESPathCheck('resourceGroup', resource_group),
                             JMESPathCheck('availabilityZone', 2)])
        else:
            self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --restore-time {}'
                     .format(database_engine, resource_group, restore_server, server, restore_time),
                     checks=[JMESPathCheck('name', restore_server),
                             JMESPathCheck('resourceGroup', resource_group)])
        
        self.cmd('{} flexible-server delete -g {} --name {} --yes'.format(database_engine, resource_group, restore_server))

    def _test_flexible_server_high_availability_delete(self, database_engine, resource_group, server):
        self.cmd('{} flexible-server delete -g {} --name {} --yes'.format(database_engine, resource_group, server))


class FlexibleServerVnetServerMgmtScenarioTest(RdbmsScenarioTest):

    def _test_flexible_server_vnet_server_create(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server create -g {} -n {} -l {}'.format(database_engine, resource_group, server, self.location))

        show_result = self.cmd('{} flexible-server show -g {} -n {}'
                               .format(database_engine, resource_group, server)).get_output_in_json()

        self.assertEqual(show_result['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, 'Vnet' + server[6:], 'Subnet' + server[6:]))

    def _test_flexible_server_vnet_ha_server_create(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --high-availability Enabled '
                 .format(database_engine, resource_group, server, self.location))
        
        show_result = self.cmd('{} flexible-server show -g {} -n {}'
                               .format(database_engine, resource_group, server),
                               checks=[JMESPathCheck('haEnabled', 'Enabled')]).get_output_in_json()

        self.assertEqual(show_result['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, 'Vnet' + server[6:], 'Subnet' + server[6:]))

    def _test_flexible_server_vnet_server_update_scale_up(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server update -g {} -n {} --tier GeneralPurpose --sku-name Standard_D8s_v3'
                 .format(database_engine, resource_group, server))

    def _test_flexible_server_vnet_server_restore(self, database_engine, resource_group, server, restore_server):

        try:
            self.cmd('{} flexible-server show -g {} --name {}'.format(database_engine, resource_group, server))
        except:
            pytest.skip("source server not provisioned")
        restore_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()

        self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --restore-time {}'
                    .format(database_engine, resource_group, restore_server, server, restore_time),
                    checks=[JMESPathCheck('name', restore_server),
                            JMESPathCheck('resourceGroup', resource_group)])
        
        self.cmd('{} flexible-server delete -g {} --name {} --yes'.format(database_engine, resource_group, restore_server))

    def _test_flexible_server_vnet_server_delete(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server delete -g {} --name {} --yes'.format(database_engine, resource_group, server))


class FlexibleServerProxyResourceMgmtScenarioTest(RdbmsScenarioTest):

    def _test_firewall_rule_mgmt(self, database_engine, resource_group, server):

        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]

        self.cmd('{} flexible-server firewall-rule create -g {} --name {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule show -g {} --name {} --rule-name {} '
                 .format(database_engine, resource_group, server, firewall_rule_name),
                 checks=firewall_rule_checks)

        new_start_ip_address = '9.9.9.9'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --start-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_start_ip_address),
                 checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])

        new_end_ip_address = '13.13.13.13'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --end-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_end_ip_address))

        new_firewall_rule_name = 'firewall_test_rule2'
        firewall_rule_checks = [JMESPathCheck('name', new_firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        self.cmd('{} flexible-server firewall-rule create -g {} -n {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, new_firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} flexible-server firewall-rule delete --rule-name {} -g {} --name {} --yes'
                 .format(database_engine, firewall_rule_name, resource_group, server), checks=NoneCheck())

        self.cmd('{} flexible-server firewall-rule list -g {} --name {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 1)])

        self.cmd('{} flexible-server firewall-rule delete -g {} -n {} --rule-name {} --yes'
                 .format(database_engine, resource_group, server, new_firewall_rule_name))

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_parameter_mgmt(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server parameter list -g {} -s {}'.format(database_engine, resource_group, server), checks=[JMESPathCheck('type(@)', 'array')])

        if database_engine == 'mysql':
            parameter_name = 'wait_timeout'
            default_value = '28800'
            value = '30000'
        elif database_engine == 'postgres':
            parameter_name = 'lock_timeout'
            default_value = '0'
            value = '2000'

        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {} -g {} -s {}'.format(database_engine, parameter_name, resource_group, server),
                 checks=[JMESPathCheck('defaultValue', default_value),
                         JMESPathCheck('source', source)])

        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])

    def _test_database_mgmt(self, database_engine, resource_group, server):

        database_name = 'flexibleserverdbtest'

        self.cmd('{} flexible-server db create -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
                 checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('{} flexible-server db list -g {} -s {} '.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('{} flexible-server db delete -g {} -s {} -d {} --yes'.format(database_engine, resource_group, server, database_name),
                 checks=NoneCheck())

    def _test_flexible_server_proxy_resource_mgmt_delete(self, resource_group):
        self.cmd('az group delete --name {} --yes --no-wait'.format(resource_group), checks=NoneCheck())


class FlexibleServerValidatorScenarioTest(ScenarioTest):

    def _test_mgmt_validator(self, database_engine, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 30
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 1

        # Create
        self.cmd('{} flexible-server create -g {} -l {} --tier {} --public-access none'.format(database_engine, resource_group, location, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --version {} --public-access none'.format(database_engine, resource_group, location, invalid_version), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --tier {} --sku-name {} --public-access none'.format(database_engine, resource_group, location, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --backup-retention {} --public-access none'.format(database_engine, resource_group, location, invalid_backup_retention), expect_failure=True)

        if database_engine == 'postgres':
            invalid_storage_size = 60
        elif database_engine == 'mysql':
            invalid_storage_size = 999999
        self.cmd('{} flexible-server create -g {} -l {} --storage-size {} --public-access none'.format(database_engine, resource_group, location, invalid_storage_size), expect_failure=True)

        server = self.create_random_name(SERVER_NAME_PREFIX, RANDOM_VARIABLE_MAX_LENGTH)
        if database_engine == 'postgres':
            tier = 'MemoryOptimized'
            version = 12
            sku_name = 'Standard_E2s_v3'
            storage_size = 64
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            version = 5.7
            if location == 'eastus2euap':
                sku_name = 'Standard_D2s_v3'
            else:
                sku_name = 'Standard_D2ds_v4'
            storage_size = 32
        storage_size_mb = storage_size * 1024
        backup_retention = 10

        list_checks = [JMESPathCheck('name', server),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --version {} --sku-name {} --storage-size {} --backup-retention {} --public-access none'
                 .format(database_engine, resource_group, server, location, tier, version, sku_name, storage_size, backup_retention))
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server), checks=list_checks)

        # Update
        invalid_storage_size_small = storage_size - 1
        self.cmd('{} flexible-server update -g {} -n {} --tier {}'.format(database_engine, resource_group, server, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'.format(database_engine, resource_group, server, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --storage-size {}'.format(database_engine, resource_group, server, invalid_storage_size_small), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'.format(database_engine, resource_group, server, invalid_backup_retention), expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server), checks=NoneCheck())


class FlexibleServerReplicationMgmtScenarioTest(RdbmsScenarioTest):  # pylint: disable=too-few-public-methods

    def _test_flexible_server_replica_create(self, database_engine, resource_group, master_server, replicas):

        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'None')]).get_output_in_json()

        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replicas[0], master_server),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        time.sleep(20 * 60)

    def _test_flexible_server_replica_list(self, database_engine, resource_group, master_server):

        self.cmd('{} flexible-server replica list -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

    def _test_flexible_server_replica_stop(self, database_engine, resource_group, master_server, replicas):

        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'Source')]).get_output_in_json()

        self.cmd('{} flexible-server replica stop-replication -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

    def _test_flexible_server_replica_delete_source(self, database_engine, resource_group, master_server, replicas):

        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'None')]).get_output_in_json()

        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replicas[1], master_server),
                 checks=[
                     JMESPathCheck('name', replicas[1]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, master_server), checks=NoneCheck())

        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, replicas[1]),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

    def _test_flexible_server_replica_delete(self, database_engine, resource_group, replicas):

        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())

        self.cmd('az group delete --name {} --yes --no-wait'.format(resource_group), checks=NoneCheck())


class FlexibleServerVnetProvisionScenarioTest(ScenarioTest):

    def _test_flexible_server_vnet_provision_existing_supplied_subnetid(self, database_engine):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        server = 'clitest-vnetprovision-supplied-subnetid-' + resource_random_name
        resource_group = 'clitest.vnetprovision-supplied-subnetid-' + resource_random_name + '-rg'
        self.cmd('group create -n {} -l {}'.format(resource_group, location))

        # Scenario : Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        vnet_name = 'clitestvnet'
        subnet_name = 'clitestsubnet'
        address_prefix = '172.0.0.0/16'
        subnet_prefix = '172.0.0.0/24'

        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group, location, address_prefix, subnet_name,
                    subnet_prefix)).get_output_in_json()

        subnet_id = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(resource_group, subnet_name, vnet_name)).get_output_in_json()['id']

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {}'
                .format(database_engine, resource_group, server, subnet_id, location))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'], subnet_id)

        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server),
                 checks=NoneCheck())


    def _test_flexible_server_vnet_provision_supplied_subnet_id_in_different_rg(self, database_engine):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        vnet_name = 'clitestvnet7'
        subnet_name = 'clitestsubnet7'
        address_prefix = '172.0.0.0/16'
        subnet_prefix_1 = '172.0.0.0/24'

        # flexible-servers
        server = 'clitest-vnetprovision-diff-rg-subnetid-' + resource_random_name
        resource_group_1 = 'clitest.vnetprovision-diff-rg-subnetid-' + resource_random_name + '-rg1'
        resource_group_2 = 'clitest.vnetprovision-diff-rg-subnetid-' + resource_random_name + '-rg2'
        self.cmd('group create -n {} -l {}'.format(resource_group_1, location))
        self.cmd('group create -n {} -l {}'.format(resource_group_2, location))

        # Case 1 : Provision a server with supplied subnetid that exists in a different RG

        # create vnet and subnet.
        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group_1, location, address_prefix, subnet_name,
                    subnet_prefix_1)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {}'
                .format(database_engine, resource_group_2, server, vnet_result['newVNet']['subnets'][0]['id'], location))

        
        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group_2, server)).get_output_in_json()


        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_1, vnet_name, subnet_name))


        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, server),
                 checks=NoneCheck())


    def _test_flexible_server_vnet_provision_create_without_parameters(self, database_engine):
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        result = self.cmd('{} flexible-server create -l {}'.format(database_engine, location)).get_output_in_json()
        _, rg, server_name, _ = get_id_components(result['id'])
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, rg, server_name))
        time.sleep(60*20)
        self.cmd('az group delete --name {} --yes --no-wait'.format(rg))
    
    def _test_flexible_server_vnet_provision_private_dns_zone_without_private(self, database_engine):
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location
        

        server = 'clitest-vnetprovision-dns-no-private-' + resource_random_name
        dns_zone = 'testdnsname.postgres.database.azure.com'
        resource_group = 'clitest.vnetprovision-dns-no-private-' + resource_random_name + '-rg'
        self.cmd('group create -n {} -l {}'.format(resource_group, location))

        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {}'
                 .format(database_engine, resource_group, server, location, dns_zone))
        
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server),
                checks=[JMESPathCheck('privateDnsZoneArguments.privateDnsZoneArmResourceId', '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, dns_zone))])
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server))


class FlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):

    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            sku_name = 'Standard_D2s_v3'
            location = self.postgres_location
        elif database_engine == 'mysql':
            sku_name = 'Standard_B1ms'
            location = self.mysql_location

        # flexible-servers
        servers = ['clitest-publicaccess-server1' + resource_random_name,
                   'clitest-publicaccess-server2' + resource_random_name]

        # Case 1 : Provision a server with public access all
        # create server
        self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                 .format(database_engine, resource_group, servers[0], 'all', location),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAll_')])

        # Case 2 : Provision a server with public access allowing all azure services
        self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                 .format(database_engine, resource_group, servers[1], '0.0.0.0', location),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAllAzureServicesAndResourcesWithinAzureIps_')])

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())
