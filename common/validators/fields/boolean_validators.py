"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from typing import Any

from validataclass.validators import BooleanValidator


class ExtendedBooleanValidator(BooleanValidator):
    string_mapping = {
        'ja': True,
        'yes': True,
        'nein': False,
        'no': False,
    }

    def validate(self, input_data: Any, **kwargs) -> bool:
        if isinstance(input_data, str):
            input_data = self.string_mapping.get(input_data.lower(), input_data)

        return super().validate(input_data, **kwargs)
