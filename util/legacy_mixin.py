"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from typing import Callable

from util import LotDataList, LotInfoList


class LegacyMixin:
    get_realtime_parking_sites: Callable
    get_static_parking_sites: Callable

    def get_lot_data(self) -> LotDataList:
        import_source_result = self.get_realtime_parking_sites()
        return LotDataList(
            [item.to_lot_data() for item in import_source_result.realtime_parking_site_inputs],
            errors=[item.message for item in import_source_result.realtime_parking_site_errors],
        )

    def get_lot_infos(self) -> LotInfoList:
        import_source_result = self.get_static_parking_sites()
        return LotInfoList(
            [item.to_lot_info() for item in import_source_result.static_parking_site_inputs],
            errors=[item.message for item in import_source_result.static_parking_site_errors],
        )
