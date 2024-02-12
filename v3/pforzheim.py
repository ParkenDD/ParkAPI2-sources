"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone
from decimal import Decimal

from validataclass.dataclasses import validataclass
from validataclass.exceptions import ValidationError
from validataclass.validators import DataclassValidator, DecimalValidator, IntegerValidator, StringValidator

from common.base_converter import CsvConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from common.validators.base_validators import ParkingSiteTypeInput
from common.validators.fields.boolean_validators import ExtendedBooleanValidator
from common.validators.fields.noneable import ExcelNoneable
from util import SourceInfo

import csv
import json
from io import StringIO
from typing import Optional

@validataclass
class PforzheimRowInput:
    uid: str = StringValidator(max_length=255)
    name: str = StringValidator(max_length=255)
    lat: Decimal = DecimalValidator(min_value=40, max_value=60)
    lon: Decimal = DecimalValidator(min_value=7, max_value=10)
    operator_name: str = StringValidator(max_length=255)
    address: str = StringValidator(max_length=255, multiline=True)
    description: str = StringValidator(max_length=512, multiline=True)
    type: str = StringValidator(max_length=255)
    #capacity: Optional[any] = ExcelNoneable(default=1) #int = IntegerValidator(allow_strings=True)
    #capacity_woman: Optional[any] = ExcelNoneable(default=0) #int = IntegerValidator(allow_strings=True) #
    #capacity_disabled: Optional[any] = ExcelNoneable(default=0) #int = IntegerValidator(allow_strings=True) #
    is_supervised: str = StringValidator(max_length=255)
    fee_description: str = StringValidator(multiline=True)
    opening_hours_is_24_7: str = StringValidator(max_length=255)
    opening_hours: str = StringValidator(max_length=255, multiline=True)
    

class PforzheimConverter(CsvConverter):
    pforzheim_row_validator = DataclassValidator(PforzheimRowInput)

    source_info = SourceInfo(
        id='pforzheim',
        name='Stadt Pforzheim',
        public_url='',
    )

    header_mapping: dict[str, str] = {
        'Id': 'uid',
        'name': 'name',
        'locations': 'location',
        'operatorID': 'operator_name',
        'address': 'address',
        'description': 'description',
        'type': 'type',
        'quantitySpacesReservedForWomen': 'capacity_woman',
        'quantitySpacesReservedForMobilityImpededPerson': 'capacity_disabled',
        'securityInformation': 'is_supervised',
        'feeInformation': 'fee_description',
        'capacity': 'capacity',
        'hasOpeningHours24h': 'opening_hours_is_24_7',
        'openingHours': 'opening_hours'
    }

    type_mapping: dict[str, ParkingSiteTypeInput] = {
        'Parkplatz': ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        'onStreet': ParkingSiteTypeInput.ON_STREET,
        'Parkhaus': ParkingSiteTypeInput.CAR_PARK,
        'Tiefgarage': ParkingSiteTypeInput.UNDERGROUND,
    }

    def handle_csv_string(self, data: StringIO) -> ImportSourceResult:
        return self.handle_csv(list(csv.reader(data, delimiter=',')))

    def handle_csv(self, data: list[list]) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        print(data[0])
        mapping: dict[str, int] = self.get_mapping_by_header(self.header_mapping, data[0])
        print(mapping)

        # We start at row 2, as the first one is our header
        for row in data[1:]:
            input_dict: dict[str, str] = {}
            for field in self.header_mapping.values():
                input_dict[field] = row[mapping[field]]

            input_dict['lat'] = str(json.loads(input_dict['location']).get('coordinates')[1])
            input_dict['lon'] = str(json.loads(input_dict['location']).get('coordinates')[0])

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
                uid=input_data.uid,
                name=input_data.name,
                type= self.type_mapping.get("onStreet") if "onStreet" in input_data.type else self.type_mapping.get(input_data.type),
                lat=input_data.lat,
                lon=input_data.lon,
                address=input_data.address.replace('\n', ' '),
                description=input_data.description,
                #capacity=input_data.capacity, #int(input_data.capacity) if input_data.capacity is not None and input_data.capacity != '' else 1,
                #capacity_woman=int(input_data.capacity_woman) if input_data.capacity_woman is not None and input_data.capacity_woman != '' else 0,
                #capacity_disabled=int(input_data.capacity_disabled) if input_data.capacity_disabled is not None and input_data.capacity_disabled != '' else 0,
                has_fee=True if input_data.fee_description is not None and input_data.fee_description != '' else False,
                fee_description=input_data.fee_description,
                opening_hours='24/7' if input_data.opening_hours == 'durchgehend geöffnet' else None,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
