"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from abc import ABC, abstractmethod
from io import StringIO
from typing import Any

from common.exceptions import ImportSourceException
from common.models import ImportSourceResult

from .base_converter import BaseConverter


class CsvConverter(BaseConverter, ABC):
    @abstractmethod
    def handle_csv_string(self, data: StringIO) -> ImportSourceResult:
        pass

    def get_mapping_by_header(self, header_row: dict[str, str], row: list[Any]) -> list[str]:
        header_keys = header_row.keys()
        mapping: list[str] = []
        for col in row:
            if col not in header_keys:
                raise ImportSourceException(
                    uid=self.source_info.id,
                    message=f'invalid header column {col}',
                )
            mapping.append(header_row[col])
        return mapping

    @abstractmethod
    def handle_csv(self, data: list[list]) -> ImportSourceResult:
        pass
