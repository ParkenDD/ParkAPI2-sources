"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import csv
import json
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from typing import Optional

from validataclass.dataclasses import validataclass
from validataclass.exceptions import ValidationError
from validataclass.validators import DataclassValidator, DecimalValidator, IntegerValidator, StringValidator, UrlValidator

from common.base_converter import JsonConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from common.validators.base_validators import ParkingSiteTypeInput
from common.validators.fields.noneable import ExcelNoneable
from util import SourceInfo, name_to_id


@validataclass
class PforzheimRowInput:
    uid: str = StringValidator(max_length=255)
    name: str = StringValidator(max_length=255)
    operator_name: str = StringValidator(max_length=255)
    address: str = StringValidator(max_length=255, multiline=True)
    description: str = StringValidator(max_length=512, multiline=True)
    type: str = StringValidator(max_length=255)
    lat: Decimal = DecimalValidator(min_value=40, max_value=60)
    lon: Decimal = DecimalValidator(min_value=7, max_value=10)
    capacity: Optional[int] = ExcelNoneable(IntegerValidator(allow_strings=True), default=1)
    capacity_woman: Optional[int] = ExcelNoneable(IntegerValidator(allow_strings=True), default=0)
    capacity_disabled: Optional[int] = ExcelNoneable(IntegerValidator(allow_strings=True), default=0)
    is_supervised: str = StringValidator(max_length=255)
    fee_description: str = StringValidator(multiline=True)
    public_url: str = UrlValidator()
    opening_hours: str = StringValidator(max_length=255, multiline=True)


class PforzheimConverter(JsonConverter):
    pforzheim_row_validator = DataclassValidator(PforzheimRowInput)

    source_info = SourceInfo(
        id='pforzheim',
        name='Stadt Pforzheim',
        public_url='https://www.pforzheim.de',
    )

    type_mapping: dict[str, ParkingSiteTypeInput] = {
        'Parkplatz': ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        'onStreet': ParkingSiteTypeInput.ON_STREET,
        'Parkhaus': ParkingSiteTypeInput.CAR_PARK,
        'undergroundCarPark': ParkingSiteTypeInput.UNDERGROUND,
    }

    def handle_json(self, data: dict | list) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        # We start at row 2, as the first one is our header
        for item in data:
            input_dict = {
                'uid': item.get('Id'),
                'name': item.get('name'),
                'lat': str(item.get('lat')),
                'lon': str(item.get('lon')),
                'operator_name': item.get('operatorID'),
                'address': item.get('address'),
                'description': item.get('description'),
                'public_url': f"https://{item.get('description')}" if item.get('description').startswith('www.') else self.source_info.public_url,
                'type': item.get('type'),
                'capacity_woman': item.get('quantitySpacesReservedForWomen'),
                'capacity_disabled': item.get('quantitySpacesReservedForMobilityImpededPerson'),
                'is_supervised': item.get('securityInformation'),
                'fee_description': item.get('feeInformation'),
                'capacity': item.get('capacity'),
                'opening_hours': item.get('openingHours'),
            }

            try:
                input_data: PforzheimRowInput = self.pforzheim_row_validator.validate(input_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_dict.get('id'),
                        message=f'validation error for {input_dict}: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_input = StaticParkingSiteInput(
                uid=name_to_id(self.source_info.id, input_data.name) if input_data.uid == '' else input_data.uid,
                name=input_data.name,
                type=self.type_mapping.get('onStreet') if 'onStreet' in input_data.type else self.type_mapping.get(input_data.type),
                lat=input_data.lat,
                lon=input_data.lon,
                address=input_data.address.replace('\n', ' '),
                description=input_data.description,
                public_url=input_data.public_url,
                capacity=input_data.capacity,
                capacity_woman=input_data.capacity_woman,
                capacity_disabled=input_data.capacity_disabled,
                has_fee=True if input_data.fee_description is not None and input_data.fee_description != '' else False,
                fee_description=input_data.fee_description,
                opening_hours='24/7' if input_data.opening_hours == 'durchgehend geöffnet' else None,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
