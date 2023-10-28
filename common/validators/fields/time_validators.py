"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import time
from typing import Any

from validataclass.validators import TimeValidator


class ExcelTimeValidator(TimeValidator):
    def validate(self, input_data: Any, **kwargs) -> time:
        if isinstance(input_data, time):
            return input_data

        return super().validate(input_data, **kwargs)
