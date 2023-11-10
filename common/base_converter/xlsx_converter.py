"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import ABC, abstractmethod

from openpyxl.cell import Cell
from openpyxl.workbook import Workbook
from validataclass.validators import DataclassValidator

from common.exceptions import ImportSourceException
from common.models import ImportSourceResult
from common.validators import ExcelOpeningTimeInput, ExcelStaticParkingSiteInput
from util import SourceInfo

from .base_converter import BaseConverter


class XlsxConverter(BaseConverter, ABC):
    static_parking_site_validator = DataclassValidator(ExcelStaticParkingSiteInput)
    excel_opening_time_validator = DataclassValidator(ExcelOpeningTimeInput)

    header_row: dict[str, str] = {}
    source_info: SourceInfo

    @abstractmethod
    def handle_xlsx(self, workbook: Workbook) -> ImportSourceResult:
        pass

    def get_mapping_by_header(self, row: tuple[Cell]) -> list[str]:
        header_keys = self.header_row.keys()
        mapping: list[str] = []
        for col in row:
            if col.value not in header_keys:
                raise ImportSourceException(
                    uid=self.source_info.id,
                    message=f'invalid header column {col.value}',
                )
            mapping.append(self.header_row[col.value])
        return mapping
