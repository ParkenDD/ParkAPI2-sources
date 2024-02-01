"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from validataclass.dataclasses import validataclass
from validataclass.exceptions import ValidationError
from validataclass.validators import DataclassValidator, DecimalValidator, IntegerValidator, StringValidator

from common.base_converter import CsvConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from common.validators.base_validators import ParkingSiteTypeInput
from common.validators.fields.boolean_validators import ExtendedBooleanValidator
from util import SourceInfo


@validataclass
class NeckarsulmRowInput:
    uid: int = IntegerValidator(allow_strings=True)
    name: str = StringValidator(max_length=255)
    type: str = StringValidator(max_length=255)
    lat: Decimal = DecimalValidator(min_value=40, max_value=60)
    lon: Decimal = DecimalValidator(min_value=7, max_value=10)
    street: str = StringValidator(max_length=255)
    postcode: str = StringValidator(max_length=255)
    city: str = StringValidator(max_length=255)
    max_stay: str = StringValidator(max_length=255)
    capacity: int = IntegerValidator(allow_strings=True)
    capacity_carsharing: int = IntegerValidator(allow_strings=True)
    capacity_charging: int = IntegerValidator(allow_strings=True)
    capacity_woman: int = IntegerValidator(allow_strings=True)
    capacity_disabled: int = IntegerValidator(allow_strings=True)
    has_fee: str = StringValidator(max_length=255)
    opening_hours: str = StringValidator(max_length=255)


class NeckarsulmConverter(CsvConverter):
    neckarsulm_row_validator = DataclassValidator(NeckarsulmRowInput)

    source_info = SourceInfo(
        id='neckarsulm',
        name='Stadt Neckarsulm',
        public_url='https://www.neckarsulm.de',
    )

    header_mapping: dict[str, str] = {
        'id': 'uid',
        'name': 'name',
        'kategorie': 'type',
        'y-koord': 'lat',
        'x-koord': 'lon',
        'strasse': 'street',
        'plz': 'postcode',
        'stadt': 'city',
        'maxparken_1': 'max_stay',
        'anz_plaetze': 'capacity',
        'anzcarsharing': 'capacity_carsharing',
        'anzeladestation': 'capacity_charging',
        'anzfrauenpark': 'capacity_woman',
        'anzbehinderte': 'capacity_disabled',
        'gebuehren': 'has_fee',
        'open_time': 'opening_hours',
    }

    # If there are more tables with our defined format, it would make sense to move type_mapping to XlsxConverter
    type_mapping: dict[str, ParkingSiteTypeInput] = {
        'Parkplatz': 'OFF_STREET_PARKING_GROUND',
        'Wanderparkplatz': 'OFF_STREET_PARKING_GROUND',
        'Parkhaus': 'CAR_PARK',
        'Tiefgarage': 'UNDERGROUND',
        'p+r': 'PARK_AND_RIDE',
    }

    def handle_csv(self, data: list[list]) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        # Second approach: create header position mapping
        mapping = self.get_mapping_by_header(self.header_mapping, data[0])

        # We start at row 2, as the first one is our header
        for row in data[1:]:
            # Mapping table and the header
            input_data: dict[str, str] = {}
            for position, field in enumerate(mapping):
                input_data[field] = row[position]

            try:
                input_data: NeckarsulmRowInput = self.neckarsulm_row_validator.validate(input_data)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_data.get('id'),
                        message=f'validation error: {e.to_dict()}',
                    ),
                )
                continue

            extended_boolean_validator = ExtendedBooleanValidator()
            parking_site_input = StaticParkingSiteInput(
                uid=input_data.uid,
                name=input_data.name,
                type=self.type_mapping.get(input_data.type),
                lat=input_data.lat,
                lon=input_data.lon,
                address=f'{input_data.street}, {input_data.postcode} {input_data.city}',
                max_stay=input_data.max_stay,
                capacity=input_data.capacity,
                capacity_carsharing=input_data.capacity_carsharing,
                capacity_charging=input_data.capacity_charging,
                capacity_woman=input_data.capacity_woman,
                capacity_disabled=input_data.capacity_disabled,
                has_fee=extended_boolean_validator.validate(input_data.has_fee),
                opening_hours=input_data.opening_hours,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
