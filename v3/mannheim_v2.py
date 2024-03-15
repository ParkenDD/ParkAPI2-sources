"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from validataclass.dataclasses import validataclass
from validataclass.exceptions import ValidationError
from validataclass.validators import AnythingValidator, DataclassValidator, ListValidator

from common.base_converter import JsonConverter
from common.exceptions import ImportParkingSiteException, ImportSourceException
from common.models import ImportSourceResult
from common.validators import RealtimeParkingSiteInput, StaticParkingSiteInput
from util import SourceInfo


@validataclass
class ParkingSiteItemsInput:
    items: list[dict] = ListValidator(AnythingValidator(allowed_types=[dict]))


class MannheimV2Converter(JsonConverter):
    parking_site_items_validator = DataclassValidator(ParkingSiteItemsInput)

    source_info = SourceInfo(
        id='mannheim_v2',
        name='Mannheim',
        public_url='https://www.parken-mannheim.de/',
        source_url=None,
        timezone='Europe/Berlin',
        attribution_contributor='Mannheimer Parkhausbetriebe GmbH',
        attribution_license=None,
        attribution_url='https://www.parken-mannheim.de/impressum',
    )

    def handle_json(self, data: dict | list) -> ImportSourceResult:
        static_parking_site_inputs: list[StaticParkingSiteInput] = []
        static_parking_site_errors: list[ImportParkingSiteException] = []
        realtime_parking_site_inputs: list[RealtimeParkingSiteInput] = []
        realtime_parking_site_errors: list[ImportParkingSiteException] = []

        try:
            parking_site_item_inputs = self.parking_site_items_validator.validate(data)
        except ValidationError as e:
            raise ImportSourceException(uid=self.source_info.id, message=f'Invalid data {e.to_dict()}') from e

        for parking_site_dict in parking_site_item_inputs.items:
            try:
                static_parking_site_input = self.static_parking_site_validator.validate(parking_site_dict)
                static_parking_site_inputs.append(static_parking_site_input)
            except ValidationError as e:
                static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=parking_site_dict.get('uid'),
                        message=f'validation error for {parking_site_dict}: {e.to_dict()}',
                    ),
                )
                continue
            if not static_parking_site_input.has_realtime_data:
                continue
            try:
                realtime_parking_site_inputs.append(self.realtime_parking_site_validator.validate(parking_site_dict))
            except ValidationError as e:
                realtime_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=parking_site_dict.get('uid'),
                        message=f'validation error for {parking_site_dict}: {e.to_dict()}',
                    ),
                )

        return self.generate_import_source_result(
            static_parking_site_inputs=static_parking_site_inputs,
            static_parking_site_errors=static_parking_site_errors,
            realtime_parking_site_inputs=realtime_parking_site_inputs,
            realtime_parking_site_errors=realtime_parking_site_errors,
        )
