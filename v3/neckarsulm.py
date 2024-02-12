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
    # max_stay exists in the table as maxparken_1, but has no parsable data format
    capacity: int = IntegerValidator(allow_strings=True)
    capacity_carsharing: int = IntegerValidator(allow_strings=True)
    capacity_charging: int = IntegerValidator(allow_strings=True)
    capacity_woman: int = IntegerValidator(allow_strings=True)
    capacity_disabled: int = IntegerValidator(allow_strings=True)
    has_fee: bool = ExtendedBooleanValidator()
    opening_hours: str = StringValidator(max_length=255)
    max_height: Decimal = DecimalValidator()


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
        'anz_plaetze': 'capacity',
        'anzcarsharing': 'capacity_carsharing',
        'anzeladestation': 'capacity_charging',
        'anzfrauenpark': 'capacity_woman',
        'anzbehinderte': 'capacity_disabled',
        'gebuehren': 'has_fee',
        'open_time': 'opening_hours',
        'maxhoehe': 'max_height',
    }

    type_mapping: dict[str, ParkingSiteTypeInput] = {
        'Parkplatz': ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        'Wanderparkplatz': ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        'Parkhaus': ParkingSiteTypeInput.CAR_PARK,
        'Tiefgarage': ParkingSiteTypeInput.UNDERGROUND,
        # there is the value 'p+r', but as this is not a parking type, but an usecase, we just map this to off street parking ground
        'p+r': ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
    }

    def handle_csv(self, data: list[list]) -> ImportSourceResult:
        import_source_result = self.generate_import_source_result(
            static_parking_site_inputs=[],
            static_parking_site_errors=[],
        )

        mapping: dict[str, int] = self.get_mapping_by_header(self.header_mapping, data[0])

        # We start at row 2, as the first one is our header
        for row in data[1:]:
            input_dict: dict[str, str] = {}
            for field in self.header_mapping.values():
                input_dict[field] = row[mapping[field]]

            try:
                input_data: NeckarsulmRowInput = self.neckarsulm_row_validator.validate(input_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_dict.get('id'),
                        message=f'validation error for {input_dict}: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_input = StaticParkingSiteInput(
                uid=str(input_data.uid),
                name=input_data.name,
                type=self.type_mapping.get(input_data.type),
                lat=input_data.lat,
                lon=input_data.lon,
                address=f'{input_data.street}, {input_data.postcode} {input_data.city}',
                capacity=input_data.capacity,
                capacity_carsharing=input_data.capacity_carsharing,
                capacity_charging=input_data.capacity_charging,
                capacity_woman=input_data.capacity_woman,
                capacity_disabled=input_data.capacity_disabled,
                has_fee=input_data.has_fee,
                opening_hours='24/7' if input_data.opening_hours == '00:00-24:00' else None,
                static_data_updated_at=datetime.now(tz=timezone.utc),
                max_height=int(input_data.max_height * 100) if input_data.max_height else None,
                # TODO: we could use the P+R type as park_and_ride_type, but for now p+r in data source is rather broken
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
