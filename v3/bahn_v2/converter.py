"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""
import json

import requests
from decouple import config
from validataclass.exceptions import ValidationError
from validataclass.validators import DataclassValidator

from common.base_converter import PullConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from util import SourceInfo

from .mapper import BahnMapper
from .validators import BahnParkingSiteInput


class BahnV2PullConverter(PullConverter):
    _base_url = 'https://apis.deutschebahn.com/db-api-marketplace/apis/parking-information/db-bahnpark/v2'

    mapper = BahnMapper()
    bahn_parking_site_validator = DataclassValidator(BahnParkingSiteInput)

    @property
    def api_client_id(self) -> str:
        # TODO: find better method then that
        return config('PARK_API_BAHN_API_CLIENT_ID')

    @property
    def api_client_secret(self) -> str:
        # TODO: find better method then that
        return config('PARK_API_BAHN_API_CLIENT_SECRET')

    source_info = SourceInfo(
        id='bahn_v2',
        name='Deutsche Bahn Parkplätze',
        public_url='https://www.dbbahnpark.de',
    )

    def get_static_parking_sites(self) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )
        parking_site_dicts = self.get_data()

        for parking_site_dict in parking_site_dicts.get('_embedded', []):
            try:
                parking_site_input: BahnParkingSiteInput = self.bahn_parking_site_validator.validate(parking_site_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=parking_site_dict.get('id'),
                        message=f'validation error: {e.to_dict()}',
                    ),
                )
                continue

            import_source_result.static_parking_site_inputs.append(
                self.mapper.map_static_parking_site(parking_site_input),
            )
        return import_source_result

    def get_realtime_parking_sites(self) -> ImportSourceResult:
        return self.generate_import_source_result()

    def get_data(self) -> dict:
        headers: dict[str, str] = {
            'DB-Client-Id': self.api_client_id,
            'DB-Api-Key': self.api_client_secret,
            'Accept': 'application/vnd.parkinginformation.db-bahnpark.v1+json',
            'accept': 'application/json',
        }

        response = requests.get(f'{self._base_url}/parking-facilities', headers=headers, timeout=60)
        return response.json()
