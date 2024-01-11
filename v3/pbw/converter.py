"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from typing import Optional

import requests
from decouple import config
from validataclass.exceptions import ValidationError
from validataclass.validators import DataclassValidator

from common.base_converter import PullConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from util import SourceInfo
from v3.pbw.mapper import PbwMapper
from v3.pbw.validation import PbwCityInput, PbwParkingSiteDetailInput, PbwParkingSiteInput, PbwRealtimeInput


class PbwPullConverter(PullConverter):
    _base_url = 'https://www.mypbw.de/api/'

    mapper = PbwMapper()

    @property
    def api_key(self) -> str:
        # TODO: find better method then that
        return config('PARK_API_PBW_API_KEY')

    city_validator = DataclassValidator(PbwCityInput)
    parking_site_detail_validator = DataclassValidator(PbwParkingSiteDetailInput)
    parking_site_validator = DataclassValidator(PbwParkingSiteInput)
    realtime_validator = DataclassValidator(PbwRealtimeInput)

    source_info = SourceInfo(
        id='pbw',
        name='PBW',
        public_url='https://www.pbw.de',
    )

    def get_static_parking_sites(self) -> ImportSourceResult:
        city_dicts = self._get_remote_data('catalog-city')
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        for city_dict in city_dicts:
            try:
                city_input: PbwCityInput = self.city_validator.validate(city_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=city_dict.get('id'),
                        message=f'validation error: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_detail_dicts = self._get_remote_data('object-by-city', city_input.id)

            for parking_site_detail_dict in parking_site_detail_dicts:
                try:
                    parking_site_detail_input: PbwParkingSiteDetailInput = self.parking_site_detail_validator.validate(
                        parking_site_detail_dict
                    )
                except ValidationError as e:
                    import_source_result.static_parking_site_errors.append(
                        ImportParkingSiteException(
                            uid=str(city_input.id),
                            message=f'validation error: {e.to_dict()}',
                        ),
                    )
                    continue

                import_source_result.static_parking_site_inputs.append(
                    self.mapper.map_static_parking_site(parking_site_detail_input),
                )

        return import_source_result

    def get_realtime_parking_sites(self) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            realtime_parking_site_inputs=[],
            realtime_parking_site_errors=[],
        )

        parking_site_dicts = self._get_remote_data('catalog-object')
        for parking_site_dict in parking_site_dicts:
            parking_site_input: PbwParkingSiteInput = self.parking_site_validator.validate(parking_site_dict)

            realtime_dicts = self._get_remote_data('object-dynamic-by-id', parking_site_input.id)

            for realtime_dict in realtime_dicts:
                realtime_input: PbwRealtimeInput = self.realtime_validator.validate(realtime_dict)
                import_source_result.realtime_parking_site_inputs.append(self.mapper.map_realtime_parking_site(realtime_input))

        return import_source_result

    def _get_remote_data(self, data_type: str, data_id: Optional[int] = None) -> list[dict]:
        parameters = {
            'format': 'json',
            'key': self.api_key,
            'type': data_type,
        }
        if data_id is not None:
            parameters['id'] = data_id

        result: dict = requests.get(self._base_url, params=parameters, timeout=60).json()

        items: list[dict] = []
        for key, item in result.items():
            item['id'] = key
            items.append(item)

        return items
