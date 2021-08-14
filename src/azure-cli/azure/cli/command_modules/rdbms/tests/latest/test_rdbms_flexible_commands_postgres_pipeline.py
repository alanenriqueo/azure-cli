# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pytest
import os
import time
import unittest
from datetime import datetime, timedelta, tzinfo
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ScenarioTest,
    StringContainCheck,
    ResourceGroupPreparer,
    VirtualNetworkPreparer,
    LocalContextScenarioTest,
    live_only)
from .test_rdbms_flexible_commands_pipeline import (
    ServerPreparer,
    FlexibleServerRegularMgmtScenarioTest,
    FlexibleServerIopsMgmtScenarioTest,
    FlexibleServerHighAvailabilityMgmt,
    FlexibleServerVnetServerMgmtScenarioTest,
    FlexibleServerProxyResourceMgmtScenarioTest,
    FlexibleServerValidatorScenarioTest,
    FlexibleServerReplicationMgmtScenarioTest,
    FlexibleServerVnetProvisionScenarioTest,
    FlexibleServerPublicAccessMgmtScenarioTest,
    write_failed_result,
    write_succeeded_result
)
from .conftest import resource_random_name, test_location, SINGLE_AVAILABILITY_FILE, REGULAR_SERVER_FILE, VNET_SERVER_FILE, VNET_HA_SERVER_FILE, HA_SERVER_FILE, PROXY_SERVER_FILE
from ..._flexible_server_util import get_postgres_list_skus_info

SERVER_NAME_PREFIX = 'clitest-'
RG_NAME_PREFIX = 'clitest.rg'
SERVER_NAME_MAX_LENGTH = 50
RG_NAME_MAX_LENGTH = 50
SOURCE_RG = 'clitest-do-not-delete'
SOURCE_SERVER_PREFIX = 'clitest-server-postgres-'
SOURCE_HA_SERVER_PREFIX = 'clitest-server-ha-postgres-'
SOURCE_VNET_SERVER_PREFIX = 'clitest-server-vnet-postgres-'
SOURCE_VNET_HA_SERVER_PREFIX = 'clitest-server-vnet-ha-postgres-'

if test_location is None:
    test_location = 'eastus2euap'


class PostgresFlexibleServerRegularMgmtScenarioTest(FlexibleServerRegularMgmtScenarioTest):

    def __init__(self, method_name):
        super(PostgresFlexibleServerRegularMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'regular')
        self.server2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'diff-tier1')
        self.server3 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'diff-tier2')
        self.server4 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'diff-ver')
        self.server5 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'zone')
        self.restore_server = 'restore-' + self.server[:55]
        self.location = test_location
        _, single_az = get_postgres_list_skus_info(self, test_location)
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")

    @pytest.mark.order(1)
    def test_postgres_flexible_server_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_create(self):
        try:
            self._test_flexible_server_create('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_password(self):
        try:
            self._test_flexible_server_update_password('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_storage(self):
        try:
            self._test_flexible_server_update_storage('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_backup_retention(self):
        try:
            self._test_flexible_server_update_backup_retention('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_scale_up(self):
        try:
            self._test_flexible_server_update_scale_up('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_scale_down(self):
        try:
            self._test_flexible_server_update_scale_down('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_mmw(self):
        try:
            self._test_flexible_server_update_mmw('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_update_tag(self):
        try:
            self._test_flexible_server_update_tag('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False
    
    @AllowLargeResponse()
    @pytest.mark.order(10)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_restart(self):
        try:
            self._test_flexible_server_restart('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(11)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_stop(self):
        try:
            self._test_flexible_server_stop('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(12)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_start(self):
        try:
            self._test_flexible_server_start('postgres', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(13)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_list(self):
        self._test_flexible_server_list('postgres', self.resource_group)
        self._test_flexible_server_connection_string('postgres', self.server)

    @AllowLargeResponse()
    @pytest.mark.order(14)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_postgres_flexible_server_list_skus(self):
        self._test_flexible_server_list_skus('postgres', self.location)

    @AllowLargeResponse()
    @pytest.mark.order(15)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_create_non_default_tiers(self):
        self._test_flexible_server_create_non_default_tiers('postgres', self.resource_group, self.server2, self.server3)

    @AllowLargeResponse()
    @pytest.mark.order(16)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_create_select_zone(self):
        self._test_flexible_server_create_select_zone('postgres', self.resource_group, self.server4)

    @AllowLargeResponse()
    @pytest.mark.order(17)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_create_different_version(self):
        self._test_flexible_server_create_different_version('postgres', self.resource_group, self.server5)

    @AllowLargeResponse()
    @pytest.mark.order(18)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_restore(self):
        self._test_flexible_server_restore('postgres', SOURCE_RG, SOURCE_SERVER_PREFIX + self.location, self.restore_server)


class PostgresFlexibleServerHighAvailabilityMgmt(FlexibleServerHighAvailabilityMgmt):

    def __init__(self, method_name):
        super(PostgresFlexibleServerHighAvailabilityMgmt, self).__init__(method_name)
        self.current_time = datetime.utcnow()
        self.location = test_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'ha')
        self.restore_server = 'restore-' + self.server[:55]
        _, single_az = get_postgres_list_skus_info(self, test_location)
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")

    @pytest.mark.order(1)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_create(self):
        with open(SINGLE_AVAILABILITY_FILE, "r") as f:
            result = f.readline()

            if result == "TRUE":
                write_failed_result(HA_SERVER_FILE)
                pytest.skip("skipping the test due to non supported feature in single availability zone")

        try:
            self._test_flexible_server_high_availability_create('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_disable(self):
        try:
            self._test_flexible_server_high_availability_disable('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_enable(self):
        try:
            self._test_flexible_server_high_availability_enable('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_update_parameter(self):
        try:
            self._test_flexible_server_high_availability_update_parameter('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_restart(self):
        try:
            self._test_flexible_server_high_availability_restart('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_stop(self):
        try:
            self._test_flexible_server_high_availability_stop('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_start(self):
        try:
            self._test_flexible_server_high_availability_start('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_update_scale_up(self):
        try:
            self._test_flexible_server_high_availability_update_scale_up('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_failover(self):
        try:
            self._test_flexible_server_high_availability_failover('postgres', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_succeeded_result(HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(11)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_delete(self):
        self._test_flexible_server_high_availability_delete('postgres', self.resource_group, self.server)
    
    @AllowLargeResponse()
    @pytest.mark.order(12)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_high_availability_restore(self):
        self._test_flexible_server_high_availability_restore('postgres', SOURCE_RG, SOURCE_HA_SERVER_PREFIX + self.location, self.restore_server)


class PostgresFlexibleServerVnetServerMgmtScenarioTest(FlexibleServerVnetServerMgmtScenarioTest):

    def __init__(self, method_name):
        super(PostgresFlexibleServerVnetServerMgmtScenarioTest, self).__init__(method_name)
        self.location = test_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'vnet')
        self.server2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'vnet-ha')
        self.restore_server = 'restore-' + self.server[:55]
        self.restore_server2 = 'restore-' + self.server2[:55]
        _, single_az = get_postgres_list_skus_info(self, test_location)
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")


    @pytest.mark.order(1)
    def test_postgres_flexible_server_vnet_server_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_vnet_server_create(self):
        try:
            self._test_flexible_server_vnet_server_create('postgres', self.resource_group, self.server)
            write_succeeded_result(VNET_SERVER_FILE)
        except:
            write_failed_result(VNET_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_vnet_ha_server_create(self):
        with open(SINGLE_AVAILABILITY_FILE, "r") as f:
            result = f.readline()

            if result == "TRUE":
                write_failed_result(VNET_HA_SERVER_FILE)
                pytest.skip("skipping the test due to non supported feature in single availability zone")

        try:
            self._test_flexible_server_vnet_ha_server_create('postgres', self.resource_group, self.server2)
            write_succeeded_result(VNET_HA_SERVER_FILE)
        except:
            write_succeeded_result(VNET_HA_SERVER_FILE)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("vnet_server_provision_check")
    def test_postgres_flexible_server_vnet_server_update_scale_up(self):
        self._test_flexible_server_vnet_server_update_scale_up('postgres', self.resource_group, self.server)
    
    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(3600)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("vnet_ha_server_provision_check")
    def test_postgres_flexible_server_vnet_ha_server_update_scale_up(self):
        self._test_flexible_server_vnet_server_update_scale_up('postgres', self.resource_group, self.server2)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.usefixtures("vnet_server_provision_check")
    def test_postgres_flexible_server_vnet_server_delete(self):
        self._test_flexible_server_vnet_server_delete('postgres', self.resource_group, self.server)
    
    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("vnet_ha_server_provision_check")
    def test_postgres_flexible_server_vnet_ha_server_delete(self):
        self._test_flexible_server_vnet_server_delete('postgres', self.resource_group, self.server2)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(5400)
    def test_postgres_flexible_server_vnet_server_restore(self):
        self._test_flexible_server_vnet_server_restore('postgres', SOURCE_RG, SOURCE_VNET_SERVER_PREFIX + self.location, self.restore_server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_postgres_flexible_server_vnet_ha_server_restore(self):
        self._test_flexible_server_vnet_server_restore('postgres', SOURCE_RG, SOURCE_VNET_HA_SERVER_PREFIX +  self.location, self.restore_server2)


class PostgresFlexibleServerProxyResourceMgmtScenarioTest(FlexibleServerProxyResourceMgmtScenarioTest):

    test_location = test_location

    def __init__(self, method_name):
        super(PostgresFlexibleServerProxyResourceMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'proxy-resource')

    @AllowLargeResponse()
    @pytest.mark.order(1)
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_proxy_resource_mgmt_prepare(self):
        try:
            self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))
            self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('postgres', test_location, self.resource_group, self.server))
            write_succeeded_result(PROXY_SERVER_FILE)
        except:
            write_failed_result(PROXY_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_postgres_flexible_server_firewall_rule_mgmt(self):
        self._test_firewall_rule_mgmt('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_postgres_flexible_server_parameter_mgmt(self):
        self._test_parameter_mgmt('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_postgres_flexible_server_database_mgmt(self):
        self._test_database_mgmt('postgres', self.resource_group, self.server)


class PostgresFlexibleServerValidatorScenarioTest(FlexibleServerValidatorScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=test_location)
    def test_postgres_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('postgres', resource_group)


class PostgresFlexibleServerVnetProvisionScenarioTest(FlexibleServerVnetProvisionScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @live_only()
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_vnet_provision_supplied_subnetid(self):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_provision_existing_supplied_subnetid('postgres')

    @AllowLargeResponse()
    @live_only()
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_vnet_provision_supplied_subnet_id_in_different_rg(self):
        self._test_flexible_server_vnet_provision_supplied_subnet_id_in_different_rg('postgres')

    @AllowLargeResponse()
    @live_only()
    @pytest.mark.execution_timeout(3600)
    def test_postgres_flexible_server_vnet_provision_private_dns_zone_without_private(self):
        self._test_flexible_server_vnet_provision_private_dns_zone_without_private('postgres')


class PostgresFlexibleServerPublicAccessMgmtScenarioTest(FlexibleServerPublicAccessMgmtScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=test_location)
    @live_only()
    @pytest.mark.execution_timeout(5000)
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)
