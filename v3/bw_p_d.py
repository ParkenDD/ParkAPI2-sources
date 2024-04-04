"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import ABC
from datetime import datetime, timezone
from typing import Any

from openpyxl.cell import Cell
from openpyxl.workbook.workbook import Workbook
from validataclass.exceptions import ValidationError
from util.strings import name_to_id

from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput
from util import SourceInfo

from common.base_converter.xlsx_converter import XlsxConverter

class BWParkAndDriveConverter(XlsxConverter):

    source_info = SourceInfo(
        id='bw-p-d',
        name='Baden-Württemberg: Park und Mitfahren',
        public_url='https://mobidata-bw.de/dataset/p-m-parkplatze-baden-wurttemberg',
    )

    # If there are more tables with our defined format, it would make sense to move header_row to XlsxConverter
    header_row: dict[str, str] = {
        'AS-Nummer': 'uid',
        'Bezeichnung Parkplatz': 'name',
        'Straße': 'street',
        'Längengrad': 'lat',
        'Breitengrad': 'lon',
        'Zufahrt': 'description',
        'Anzahl Plätze': 'capacity'
    }

    def handle_xlsx(self, workbook: Workbook) -> ImportSourceResult:
        worksheet = workbook.active
        mapping: dict[str, int] = self.get_mapping_by_header(next(worksheet.rows))

        static_parking_site_errors: list[ImportParkingSiteException] = []
        static_parking_site_inputs: list[StaticParkingSiteInput] = []

        for row in worksheet.iter_rows(min_row=2):
            # ignore empty lines as LibreOffice sometimes adds empty rows at the end of a file
            if row[0].value is None:
                continue
            parking_site_dict = self.map_row_to_parking_site_dict(mapping, row)

            try:
                static_parking_site_inputs.append(self.static_parking_site_validator.validate(parking_site_dict))
            except ValidationError as e:
                static_parking_site_errors.append(
                    ImportParkingSiteException(
                        uid=parking_site_dict.get('uid'),
                        message=f'invalid static parking site data: {e.to_dict()}',
                    )
                )
                continue

        return self.generate_import_source_result(
            static_parking_site_inputs=static_parking_site_inputs,
            static_parking_site_errors=static_parking_site_errors,
        )

    def map_row_to_parking_site_dict(self, mapping: dict[str, int], row: list[Cell]) -> dict[str, Any]:
        parking_site_dict: dict[str, str] = {}
        for field in mapping.keys():
            parking_site_dict[field] = row[mapping[field]].value

        parking_site_dict['name'] = f"{parking_site_dict['street']} {parking_site_dict['name']}" 
        parking_site_dict['uid'] = name_to_id(parking_site_dict['uid'], parking_site_dict['name'])
        parking_site_dict['static_data_updated_at'] = datetime.now(tz=timezone.utc).isoformat()

        return parking_site_dict

