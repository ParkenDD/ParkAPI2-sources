"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import csv
import re
from datetime import datetime, timezone
from enum import Enum
from io import StringIO
from typing import Any

from validataclass.dataclasses import validataclass
from validataclass.exceptions import ValidationError
from validataclass.validators import (
    DataclassValidator,
    DecimalValidator,
    EnumValidator,
    IntegerValidator,
    ListValidator,
    StringValidator,
)

from common.base_converter import CsvConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from common.validators.base_validators import ParkingSiteTypeInput
from common.validators.fields.noneable import ExcelNoneable
from util import SourceInfo


class ReutlingenParkingSiteType(Enum):
    PARKHAUS = 'parkhaus'
    TIEFGARAGE = 'tiefgarage'
    PARKFLAECHE = 'parkfläche'
    P_R = 'p+r'

    def to_parking_site_type_input(self) -> ParkingSiteTypeInput:
        return {
            self.PARKHAUS: ParkingSiteTypeInput.CAR_PARK,
            self.TIEFGARAGE: ParkingSiteTypeInput.UNDERGROUND,
            self.PARKFLAECHE: ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        }.get(self, ParkingSiteTypeInput.OTHER)


class PointCoordinateTupleValidator(ListValidator):
    PATTERN = r'POINT \(([-+]?\d+\.\d+) ([-+]?\d+\.\d+)\)'

    def validate(self, input_data: Any, **kwargs) -> list:
        self._ensure_type(input_data, str)
        input_match = re.match(self.PATTERN, input_data)

        if input_match is None:
            raise ValidationError(code='invalid_tuple_input', reason='invalid point coordinate tuple input')
        input_data = [input_match.group(1), input_match.group(2)]

        return super().validate(input_data, **kwargs)


@validataclass
class ReutlingenRowInput:
    uid: int = IntegerValidator(allow_strings=True)
    type: ReutlingenParkingSiteType = EnumValidator(ReutlingenParkingSiteType)
    coordinates: list = PointCoordinateTupleValidator(DecimalValidator())
    capacity: str = ExcelNoneable(IntegerValidator(allow_strings=True))
    name: str = StringValidator(max_length=255)


class ReutlingenConverter(CsvConverter):
    reutlingen_row_validator = DataclassValidator(ReutlingenRowInput)

    source_info = SourceInfo(
        id='reutlingen',
        name='Stadt Reutlingen',
        public_url='https://www.reutlingen.de',
    )

    header_mapping: dict[str, str] = {'id': 'uid', 'ort': 'name', 'Kapazität': 'capacity', 'GEOM': 'coordinates', 'type': 'type'}

    def handle_csv_string(self, data: StringIO) -> ImportSourceResult:
        return self.handle_csv(list(csv.reader(data, dialect='unix', delimiter=',')))

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
                input_data: ReutlingenRowInput = self.reutlingen_row_validator.validate(input_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_dict.get('uid'),
                        message=f'validation error for {input_dict}: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_input = StaticParkingSiteInput(
                uid=input_data.uid,
                name=input_data.name,
                address=f'{input_data.name}, Reutlingen',
                lat=input_data.coordinates[1],
                lon=input_data.coordinates[0],
                type=input_data.type.to_parking_site_type_input(),
                capacity=input_data.capacity,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
