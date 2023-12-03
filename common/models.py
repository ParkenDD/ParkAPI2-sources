"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from common.exceptions import ImportParkingSiteException
from common.validators import StaticParkingSiteInput


class SourceStatus(Enum):
    DISABLED = 'DISABLED'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'
    PROVISIONED = 'PROVISIONED'


@dataclass
class ImportSourceResult:
    uid: str
    name: str
    status: SourceStatus

    public_url: Optional[str] = None

    attribution_license: Optional[str] = None
    attribution_contributor: Optional[str] = None
    attribution_url: Optional[str] = None

    static_parking_site_inputs: Optional[list[StaticParkingSiteInput]] = None
    realtime_parking_site_inputs: Optional[list[StaticParkingSiteInput]] = None

    static_parking_site_errors: Optional[list[ImportParkingSiteException]] = None
    realtime_parking_site_errors: Optional[list[ImportParkingSiteException]] = None

    @property
    def static_parking_site_error_count(self) -> Optional[int]:
        if self.static_parking_site_errors is None:
            return None
        return len(self.static_parking_site_errors)

    @property
    def realtime_parking_site_error_count(self) -> Optional[int]:
        if self.realtime_parking_site_errors is None:
            return None
        return len(self.realtime_parking_site_errors)
