"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import re
from typing import Any

from validataclass.exceptions import ValidationError
from validataclass.validators import IntegerValidator


class GermanDurationIntegerValidator(IntegerValidator):
    pattern = re.compile(r'^([0-9]*) (Stunde|Stunden|Tag|Tage|Woche|Wochen|Monat|Monate|Quartal|Quartale)$')
    unit_factors: dict[str, int] = {
        'Stunde': 60 * 60,
        'Stunden': 60 * 60,
        'Tag': 60 * 60 * 24,
        'Tage': 60 * 60 * 24,
        'Woche': 60 * 60 * 24 * 7,
        'Wochen': 60 * 60 * 24 * 7,
        'Monat': 60 * 60 * 24 * 30,
        'Monate': 60 * 60 * 24 * 30,
        'Quartal': 60 * 60 * 24 * 30,
        'Quartale': 60 * 60 * 24 * 30,
    }

    def validate(self, input_data: Any, **kwargs) -> int:
        if not isinstance(input_data, str):
            return super().validate(input_data, **kwargs)

        input_match = re.match(self.pattern, input_data)

        if input_match is None:
            raise ValidationError(code='invalid_string_input', reason='invalid string input')

        value = int(input_match.group(1))
        unit = input_match.group(2)

        return self.unit_factors[unit] * value
