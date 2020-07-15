# Copyright 2020 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CSCC test"""

import pytest
from google.cloud import securitycenter
from sqlalchemy.sql import text


class TestNotifierCloudSecurityCommandCenter:
    """CSCC test

    Run notifier and assert findings are created.
    """
    @staticmethod
    def get_violations(cloudsql_connection, scanner_id):
        query = text('SELECT '
                     'violation_hash '
                     'FROM forseti_security.violations '
                     'WHERE '
                     'scanner_index_id = :scanner_id '
                     'ORDER BY violation_hash')
        violations = (
            cloudsql_connection.execute(query,
                                        scanner_id=scanner_id).fetchall())
        return set([v[0][:32] for v in violations])

    @pytest.mark.e2e
    @pytest.mark.notifier
    @pytest.mark.server
    def test_cscc_findings_match_violations(self, cscc_source_id,
                                            forseti_notifier_readonly,
                                            forseti_scan_readonly):
        """CSCC findings test

        Args:
            cscc_source_id (str): CSCC Source Id.
            forseti_notifier_readonly (object): Notifier run process result.
            forseti_scan_readonly (object): Scanner run process result.
        """
        # Arrange
        _ = forseti_notifier_readonly
        scanner_id, _ = forseti_scan_readonly
        violations = (
            TestNotifierCloudSecurityCommandCenter.get_violations(scanner_id))

        # Act
        client = securitycenter.SecurityCenterClient()
        finding_result_iterator = client.list_findings(cscc_source_id,
                                                       filter_='state="ACTIVE"')

        # Assert
        for _, finding_result in enumerate(finding_result_iterator):
            finding_id = finding_result.finding.name.rsplit('/', 1)
            if finding_id and len(finding_id) > 1:
                violations.discard(finding_id[1])
        assert len(violations) == 0
