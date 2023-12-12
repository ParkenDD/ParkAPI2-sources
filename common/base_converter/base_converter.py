"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import ABC, abstractmethod
from typing import Optional

from validataclass.validators import DataclassValidator

from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult, SourceStatus
from common.validators import RealtimeParkingSiteInput, StaticParkingSiteInput
from util import SourceInfo


class BaseConverter(ABC):
    static_parking_site_validator = DataclassValidator(StaticParkingSiteInput)
    realtime_parking_site_validator = DataclassValidator(RealtimeParkingSiteInput)

    @property
    @abstractmethod
    def source_info(self) -> SourceInfo:
        pass

    def generate_import_source_result(
        self,
        static_parking_site_inputs: Optional[list[StaticParkingSiteInput]] = None,
        realtime_parking_site_inputs: Optional[list[RealtimeParkingSiteInput]] = None,
        static_parking_site_errors: Optional[list[ImportParkingSiteException]] = None,
        realtime_parking_site_errors: Optional[list[ImportParkingSiteException]] = None,
    ) -> ImportSourceResult:
        return ImportSourceResult(
            uid=self.source_info.id,
            name=self.source_info.name,
            public_url=self.source_info.public_url,
            status=SourceStatus.ACTIVE,
            static_parking_site_inputs=static_parking_site_inputs,
            realtime_parking_site_inputs=realtime_parking_site_inputs,
            static_parking_site_errors=static_parking_site_errors,
            realtime_parking_site_errors=realtime_parking_site_errors,
        )
