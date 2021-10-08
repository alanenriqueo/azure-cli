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
    RdbmsScenarioTest,
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
from .conftest import test_location, SINGLE_AVAILABILITY_FILE, REGULAR_SERVER_FILE, VNET_SERVER_FILE, VNET_HA_SERVER_FILE, HA_SERVER_FILE, PROXY_SERVER_FILE, IOPS_SERVER_FILE, REPLICA_SERVER_FILE
from ..._flexible_server_util import get_mysql_list_skus_info

SERVER_NAME_PREFIX = 'clitest-'
RG_NAME_PREFIX = 'clitest.rg'
SERVER_NAME_MAX_LENGTH = 50
RG_NAME_MAX_LENGTH = 50
SOURCE_RG = 'clitest-do-not-delete'
SOURCE_SERVER_GEORESTORE_PREFIX = 'clitest-server-georestore-mysql-'
SOURCE_SERVER_PREFIX = 'clitest-server-mysql-'
SOURCE_HA_SERVER_PREFIX = 'clitest-server-ha-mysql-'
SOURCE_VNET_SERVER_PREFIX = 'clitest-server-vnet-mysql-'
SOURCE_VNET_HA_SERVER_PREFIX = 'clitest-server-vnet-ha-mysql-'

if test_location is None:
    test_location = 'eastus2euap'


class MySqlFlexibleServerRegularMgmtScenarioTest(FlexibleServerRegularMgmtScenarioTest):

    def __init__(self, method_name):
        super(MySqlFlexibleServerRegularMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'regular')
        self.server2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'diff-tier1')
        self.server3 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'diff-tier2')
        self.restore_server = 'restore-' + self.server[:55]
        self.georestore_server = 'georestore-' + self.server[:55]
        self.location = test_location
        location_metadata = get_mysql_list_skus_info(self, test_location)
        single_az = location_metadata['single_az']
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")


    @pytest.mark.order(1)
    def test_mysql_flexible_server_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_create(self):
        try:
            self._test_flexible_server_create('mysql', self.resource_group, self.server)
            write_succeeded_result(REGULAR_SERVER_FILE)
        except:
            write_failed_result(REGULAR_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_password(self):
        self._test_flexible_server_update_password('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_storage(self):
        self._test_flexible_server_update_storage('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_backup_retention(self):
        self._test_flexible_server_update_backup_retention('mysql', self.resource_group, self.server)
    
    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_scale_up(self):
        self._test_flexible_server_update_scale_up('mysql', self.resource_group, self.server)\

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_scale_down(self):
        self._test_flexible_server_update_scale_down('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_mmw(self):
        self._test_flexible_server_update_mmw('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_update_tag(self):
        self._test_flexible_server_update_tag('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_restart(self):
        self._test_flexible_server_restart('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(11)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_stop(self):
        self._test_flexible_server_stop('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(12)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_start(self):
        self._test_flexible_server_start('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(13)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_list(self):
        self._test_flexible_server_list('mysql', self.resource_group)
        self._test_flexible_server_connection_string('mysql', self.server)

    @AllowLargeResponse()
    @pytest.mark.order(14)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("regular_server_provision_check")
    def test_mysql_flexible_server_list_skus(self):
        self._test_flexible_server_list_skus('mysql', self.location)

    @AllowLargeResponse()
    @pytest.mark.order(15)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_create_non_default_tiers(self):
        self._test_flexible_server_create_non_default_tiers('mysql', self.resource_group, self.server2, self.server3)
    
    @AllowLargeResponse()
    @pytest.mark.order(17)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_restore(self):
        self._test_flexible_server_restore('mysql', SOURCE_RG, SOURCE_SERVER_PREFIX + self.location, self.restore_server)
    

    @AllowLargeResponse()
    @pytest.mark.order(18)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_restore(self):
        self._test_flexible_server_georestore('mysql', SOURCE_RG, SOURCE_SERVER_GEORESTORE_PREFIX + self.location, self.georestore_server)


class MySqlFlexibleServerIopsMgmtScenarioTest(FlexibleServerIopsMgmtScenarioTest):

    def __init__(self, method_name):
        super(MySqlFlexibleServerIopsMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'iops')
        self.location = test_location

    @AllowLargeResponse()
    @pytest.mark.order(1)
    def test_mysql_flexible_server_iops_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_iops_create(self):
        try:
            self._test_flexible_server_iops_create('mysql', self.resource_group, self.server)
            write_succeeded_result(IOPS_SERVER_FILE)
        except:
            write_failed_result(IOPS_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("iops_server_provision_check")
    def test_mysql_flexible_server_iops_scale_up(self):
        self._test_flexible_server_iops_scale_up('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("iops_server_provision_check")
    def test_mysql_flexible_server_iops_scale_down(self):
        self._test_flexible_server_iops_scale_down('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    def test_mysql_flexible_server_iops_delete(self):
        self.cmd('az group delete --name {} --yes --no-wait'.format(self.resource_group))


class MySqlFlexibleServerVnetServerMgmtScenarioTest(FlexibleServerVnetServerMgmtScenarioTest):

    def __init__(self, method_name):
        super(MySqlFlexibleServerVnetServerMgmtScenarioTest, self).__init__(method_name)
        self.location = test_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'vnet')
        self.server2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'vnet-ha')
        self.restore_server = 'restore-' + self.server[:55]
        self.restore_server2 = 'restore-' + self.server2[:55]
        self.current_time = datetime.utcnow()
        location_metadata = get_mysql_list_skus_info(self, test_location)
        single_az = location_metadata['single_az']
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")

    @pytest.mark.order(1)
    def test_mysql_flexible_server_vnet_server_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_vnet_server_create(self):
        try:
            self._test_flexible_server_vnet_server_create('mysql', self.resource_group, self.server)
            write_succeeded_result(VNET_SERVER_FILE)
        except:
            write_failed_result(VNET_SERVER_FILE)
            assert False
    
    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_vnet_ha_server_create(self):
        with open(SINGLE_AVAILABILITY_FILE, "r") as f:
            result = f.readline()

            if result == "TRUE":
                write_failed_result(VNET_HA_SERVER_FILE)
                pytest.skip("skipping the test due to non supported feature in single availability zone")

        try:
            self._test_flexible_server_vnet_ha_server_create('mysql', self.resource_group, self.server2)
            write_succeeded_result(VNET_HA_SERVER_FILE)
        except:
            write_failed_result(VNET_HA_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("vnet_server_provision_check")
    def test_mysql_flexible_server_vnet_server_update_scale_up(self):
        self._test_flexible_server_vnet_server_update_scale_up('mysql', self.resource_group, self.server)
    
    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("vnet_ha_server_provision_check")
    def test_mysql_flexible_server_vnet_ha_server_delete(self):
        self._test_flexible_server_vnet_server_delete('mysql', self.resource_group, self.server2)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.usefixtures("vnet_server_provision_check")
    def test_mysql_flexible_server_vnet_server_delete(self):
        self._test_flexible_server_vnet_server_delete('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.execution_timeout(5400)
    def test_mysql_flexible_server_vnet_server_restore(self):
        self._test_flexible_server_vnet_server_restore('mysql', SOURCE_RG, SOURCE_VNET_SERVER_PREFIX + self.location, self.restore_server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_mysql_flexible_server_vnet_ha_server_restore(self):
        self._test_flexible_server_vnet_server_restore('mysql', SOURCE_RG, SOURCE_VNET_HA_SERVER_PREFIX + self.location, self.restore_server2)


class MySqlFlexibleServerProxyResourceMgmtScenarioTest(FlexibleServerProxyResourceMgmtScenarioTest):

    test_location = test_location

    def __init__(self, method_name):
        super(MySqlFlexibleServerProxyResourceMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'proxy-resource')

    @AllowLargeResponse()
    @pytest.mark.order(1)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_proxy_resource_mgmt_prepare(self):
        try:
            self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))
            self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('mysql', test_location, self.resource_group, self.server))
            write_succeeded_result(PROXY_SERVER_FILE)
        except:
            write_failed_result(PROXY_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_mysql_flexible_server_firewall_rule_mgmt(self):
        self._test_firewall_rule_mgmt('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_mysql_flexible_server_parameter_mgmt(self):
        self._test_parameter_mgmt('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("proxy_server_provision_check")
    def test_mysql_flexible_server_database_mgmt(self):
        self._test_database_mgmt('mysql', self.resource_group, self.server)


class MySqlFlexibleServerHighAvailabilityMgmt(FlexibleServerHighAvailabilityMgmt):

    def __init__(self, method_name):
        super(MySqlFlexibleServerHighAvailabilityMgmt, self).__init__(method_name)
        self.current_time = datetime.utcnow()
        self.location = test_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'ha')
        self.restore_server = 'restore-' + self.server[:55]
        location_metadata = get_mysql_list_skus_info(self, test_location)
        single_az = location_metadata['single_az']
        with open(SINGLE_AVAILABILITY_FILE, "w") as f:
            if single_az:
                f.write("TRUE")
            else:
                f.write("FALSE")

    @pytest.mark.order(1)
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_mysql_flexible_server_high_availability_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_high_availability_create(self):
        with open(SINGLE_AVAILABILITY_FILE, "r") as f:
            result = f.readline()

            if result == "TRUE":
                write_failed_result(HA_SERVER_FILE)
                pytest.skip("skipping the test due to non supported feature in single availability zone")

        try:
            self._test_flexible_server_high_availability_create('mysql', self.resource_group, self.server)
            write_succeeded_result(HA_SERVER_FILE)
        except:
            write_failed_result(HA_SERVER_FILE)
            assert False
    
    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("ha_server_provision_check")
    def test_mysql_flexible_server_high_availability_update_parameter(self):
        self._test_flexible_server_high_availability_update_parameter('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("ha_server_provision_check")
    def test_mysql_flexible_server_high_availability_restart(self):
        self._test_flexible_server_high_availability_restart('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("ha_server_provision_check")
    def test_mysql_flexible_server_high_availability_stop(self):
        self._test_flexible_server_high_availability_stop('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("ha_server_provision_check")
    def test_mysql_flexible_server_high_availability_start(self):
        self._test_flexible_server_high_availability_start('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.execution_timeout(7200)
    @pytest.mark.usefixtures("ha_server_provision_check")
    @pytest.mark.usefixtures("single_availability_zone_check")
    def test_mysql_flexible_server_high_availability_failover(self):
        self._test_flexible_server_high_availability_failover('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.usefixtures("ha_server_provision_check")
    def test_mysql_flexible_server_high_availability_delete(self):
        self._test_flexible_server_high_availability_delete('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.usefixtures("single_availability_zone_check")
    @pytest.mark.execution_timeout(5400)
    def test_mysql_flexible_server_high_availability_restore(self):
        self._test_flexible_server_high_availability_restore('mysql', SOURCE_RG, SOURCE_HA_SERVER_PREFIX + self.location, self.restore_server)


class MySqlFlexibleServerValidatorScenarioTest(FlexibleServerValidatorScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=test_location)
    def test_mysql_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('mysql', resource_group)


class MySqlFlexibleServerReplicationMgmtScenarioTest(FlexibleServerReplicationMgmtScenarioTest):  # pylint: disable=too-few-public-methods

    test_location = test_location

    def __init__(self, method_name):
        super(MySqlFlexibleServerReplicationMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.master_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'replica-source')
        self.replicas = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'replica1'),
                         self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, 'replica2')]
        self.location = test_location
        self.result = None

    @AllowLargeResponse()
    @pytest.mark.order(1)
    @pytest.mark.execution_timeout(5400)
    def test_mysql_flexible_server_replica_prepare(self):
        try:
            self.cmd('az group create --location {} --name {}'.format(test_location, self.resource_group))
            self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none --tier GeneralPurpose --sku-name Standard_D2s_v3'
                    .format('mysql', self.resource_group, self.master_server, test_location, 256))
            write_succeeded_result(REPLICA_SERVER_FILE)
        except:
            write_failed_result(REPLICA_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("replica_server_provision_check")
    def test_mysql_flexible_server_replica_create(self):
        try:
            self._test_flexible_server_replica_create('mysql', self.resource_group, self.master_server, self.replicas)
            write_succeeded_result(REPLICA_SERVER_FILE)
        except:
            write_failed_result(REPLICA_SERVER_FILE)
            assert False

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("replica_server_provision_check")
    def test_mysql_flexible_server_replica_list(self):
        self._test_flexible_server_replica_list('mysql', self.resource_group, self.master_server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("replica_server_provision_check")
    def test_mysql_flexible_server_replica_stop(self):
        self._test_flexible_server_replica_stop('mysql', self.resource_group, self.master_server, self.replicas)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.execution_timeout(5400)
    @pytest.mark.usefixtures("replica_server_provision_check")
    def test_mysql_flexible_server_replica_delete_source(self):
        self._test_flexible_server_replica_delete_source('mysql', self.resource_group, self.master_server, self.replicas)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.usefixtures("replica_server_provision_check")
    def test_mysql_flexible_server_replica_delete(self):
        self._test_flexible_server_replica_delete('mysql', self.resource_group, self.replicas)


class MySqlFlexibleServerVnetProvisionScenarioTest(FlexibleServerVnetProvisionScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_vnet_provision_supplied_subnetid(self):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_provision_existing_supplied_subnetid('mysql')

    @AllowLargeResponse()
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_vnet_provision_supplied_subnet_id_in_different_rg(self):
        self._test_flexible_server_vnet_provision_supplied_subnet_id_in_different_rg('mysql')


class MySqlFlexibleServerPublicAccessMgmtScenarioTest(FlexibleServerPublicAccessMgmtScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=test_location)
    @live_only()
    @pytest.mark.execution_timeout(7200)
    def test_mysql_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)
