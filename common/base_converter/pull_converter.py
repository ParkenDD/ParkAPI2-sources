"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import abstractmethod

from common.base_converter import BaseConverter
from common.models import ImportSourceResult


class PullConverter(BaseConverter):
    @abstractmethod
    def get_static_parking_sites(self) -> ImportSourceResult:
        pass

    @abstractmethod
    def get_realtime_parking_sites(self) -> ImportSourceResult:
        pass
