"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import csv
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any

from common.exceptions import ImportSourceException
from common.models import ImportSourceResult

from .base_converter import BaseConverter


class CsvConverter(BaseConverter, ABC):
    def handle_csv_string(self, data: StringIO) -> ImportSourceResult:
        return self.handle_csv(list(csv.reader(data, delimiter=';')))

    def get_mapping_by_header(self, header_row: dict[str, str], row: list[Any]) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for header_field, target_field in header_row.items():
            if header_field not in row:
                raise ImportSourceException(
                    uid=self.source_info.id,
                    message=f'cannot find header key {header_field}',
                )
            mapping[target_field] = row.index(header_field)
        return mapping

    @abstractmethod
    def handle_csv(self, data: list[list]) -> ImportSourceResult:
        pass
