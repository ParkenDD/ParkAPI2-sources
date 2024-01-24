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
from util import SourceInfo


@validataclass
class NeckarsulmRowInput:
    id: int = IntegerValidator(allow_strings=True)
    name: str = StringValidator(max_length=255)
    lat: Decimal = DecimalValidator(min_value=40, max_value=60)
    lon: Decimal = DecimalValidator()


class NeckarsulmConverter(CsvConverter):
    neckarsulm_row_validator = DataclassValidator(NeckarsulmRowInput)

    source_info = SourceInfo(
        id='neckarsulm',
        name='Stadt Neckarsulm',
        public_url='https://www.neckarsulm.de',
    )

    header_row: list[str] = [
        'id',
        'name',
        'lat',
        'lon',
    ]
    header_mapping: dict[str, str] = {
        'id': 'id',
        'name': 'name',
        'x-koord': 'lat',
        'y-koord': 'lon',
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
            # First approach: defined list
            input_dict: dict[str, Any] = dict(zip(self.header_row, row))

            # Second approach: by mapping table and the header
            input_data: dict[str, str] = {}
            for position, field in enumerate(mapping):
                input_data[field] = row[position]

            try:
                input_data: NeckarsulmRowInput = self.neckarsulm_row_validator.validate(input_dict)
            except ValidationError as e:
                import_source_result.static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=input_dict.get('id'),
                        message=f'validation error: {e.to_dict()}',
                    ),
                )
                continue

            parking_site_input = StaticParkingSiteInput(
                uid=str(input_data.id),
                name=input_data.name,
                lat=input_data.lat,
                lon=input_data.lon,
                static_data_updated_at=datetime.now(tz=timezone.utc),
            )
            import_source_result.static_parking_site_inputs.append(parking_site_input)

        return import_source_result
