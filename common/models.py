"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

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

    static_parking_site_inputs: List[StaticParkingSiteInput] = field(default_factory=list)
    realtime_parking_site_inputs: List[StaticParkingSiteInput] = field(default_factory=list)

    static_parking_site_error_count: int = 0
    realtime_parking_site_error_count: int = 0
