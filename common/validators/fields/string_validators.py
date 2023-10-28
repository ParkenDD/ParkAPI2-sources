"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from typing import Any

from validataclass.validators import StringValidator


class NumberCastingStringValidator(StringValidator):
    def validate(self, input_data: Any, **kwargs) -> str:
        if isinstance(input_data, int) or isinstance(input_data, float):
            input_data = str(input_data)

        return super().validate(input_data, **kwargs)
