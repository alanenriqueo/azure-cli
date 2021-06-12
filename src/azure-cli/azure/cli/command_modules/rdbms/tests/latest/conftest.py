# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pytest

test_location = None
resource_random_name = None


def pytest_addoption(parser):
    parser.addoption("--mysql-location", action="store", default="eastus2euap")
    parser.addoption("--postgres-location", action="store", default="eastus2euap")
    parser.addoption("--resource-random-name", action="store", default="clirecording")


def pytest_configure(config):
    global test_location, resource_random_name  # pylint:disable=global-statement
    test_location = config.getoption('--test-location')
    resource_random_name = config.getoption('--resource-random-name')


REGULAR_SERVER_FILE = './regular_server_cache.txt'
VNET_SERVER_FILE = './vnet_server_cache.txt'
VNET_HA_SERVER_FILE = './vnet_ha_server_cache.txt'
HA_SERVER_FILE = './ha_server_cache.txt'
PROXY_SERVER_FILE = './proxy_server_cache.txt'
IOPS_SERVER_FILE = './iops_server_cache.txt'
REPLICA_SERVER_FILE = './replica_server_cache.txt'

def skip_if_test_failed(filename):
    with open(filename, "r") as f:
        result = f.readline()

    if result == 'FAIL':
        pytest.skip("skipping the test due to dependent resource provision failure")

@pytest.fixture()
def regular_server_provision_check():
    skip_if_test_failed(REGULAR_SERVER_FILE)

@pytest.fixture()
def vnet_server_provision_check():
    skip_if_test_failed(VNET_SERVER_FILE)

@pytest.fixture()
def vnet_ha_server_provision_check():
    skip_if_test_failed(VNET_HA_SERVER_FILE)

@pytest.fixture()
def ha_server_provision_check():
    skip_if_test_failed(HA_SERVER_FILE)

@pytest.fixture()
def proxy_server_provision_check():
    skip_if_test_failed(PROXY_SERVER_FILE)

@pytest.fixture()
def iops_server_provision_check():
    skip_if_test_failed(IOPS_SERVER_FILE)

@pytest.fixture()
def replica_server_provision_check():
    skip_if_test_failed(REPLICA_SERVER_FILE)
