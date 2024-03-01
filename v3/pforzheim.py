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
from validataclass.validators import DataclassValidator, IntegerValidator, NumericValidator, StringValidator

from common.base_converter import JsonConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from common.validators.base_validators import ParkingSiteTypeInput
from common.validators.fields.noneable import Noneable
from util import SourceInfo


@validataclass
class PforzheimInput:
    Id: str = StringValidator(max_length=255)
    name: str = StringValidator(max_length=255)
    operatorID: str = StringValidator(max_length=255)
    address: str = StringValidator(max_length=255, multiline=True)
    description: str = StringValidator(max_length=512, multiline=True)
    type: str = StringValidator(max_length=255)
    lat: Decimal = NumericValidator(min_value=40, max_value=60)
    lon: Decimal = NumericValidator(min_value=7, max_value=10)
    capacity: int = IntegerValidator()
    quantitySpacesReservedForWomen: Optional[int] = Noneable(IntegerValidator())
    quantitySpacesReservedForMobilityImpededPerson: Optional[int] = Noneable(IntegerValidator())
    securityInformation: str = StringValidator(multiline=True)
    feeInformation: str = StringValidator(multiline=True)
    openingHours: str = StringValidator(multiline=True)


class PforzheimConverter(JsonConverter):
    pforzheim_validator = DataclassValidator(PforzheimInput)

    source_info = SourceInfo(
        id='pforzheim',
        name='Stadt Pforzheim',
        public_url='https://www.pforzheim.de',
    )

    type_mapping: dict[str, ParkingSiteTypeInput] = {
        'onStreet': ParkingSiteTypeInput.ON_STREET,
        'carPark': ParkingSiteTypeInput.CAR_PARK,
        'undergroundCarPark': ParkingSiteTypeInput.UNDERGROUND,
    }

    def handle_json(self, data: dict | list) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        for input_dict in data:
            try:
                input_data: PforzheimInput = self.pforzheim_validator.validate(input_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_dict.get('uid'),
                        message=f'validation error for {input_dict}: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_input = StaticParkingSiteInput(
                uid=input_data.Id,
                name=input_data.name,
                type=self.type_mapping.get(input_data.type),
                lat=input_data.lat,
                lon=input_data.lon,
                address=input_data.address.replace('\n', ', '),
                description=input_data.description.replace('\n', ', '),
                capacity=input_data.capacity,
                capacity_woman=input_data.quantitySpacesReservedForWomen,
                capacity_disabled=input_data.quantitySpacesReservedForMobilityImpededPerson,
                fee_description=input_data.feeInformation.replace('\n', ', '),
                is_supervised=input_data.securityInformation,
                hasOpeningHours24h=True if input_data.openingHours == 'durchgehend geöffnet' else False,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
