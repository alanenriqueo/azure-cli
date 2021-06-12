# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pytest
from azure_devtools.scenario_tests import AllowLargeResponse
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
from .test_rdbms_flexible_commands_local_context import (
    FlexibleServerLocalContextScenarioTest
)
from .test_rdbms_flexible_commands import (
    ServerPreparer
)
from .conftest import test_location

if test_location is None:
    test_location = 'eastus2euap'


# Local context test is separated out from the rest of the test due to daily pipeline run issue
class MySqlFlexibleServerLocalContextScenarioTest(FlexibleServerLocalContextScenarioTest):

    test_location = test_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=test_location)
    def test_mysql_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('mysql', resource_group)
