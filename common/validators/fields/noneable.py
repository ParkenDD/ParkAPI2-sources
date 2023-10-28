"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from copy import deepcopy
from typing import Any, Optional

from validataclass.validators import Noneable


class ExcelNoneable(Noneable):
    def validate(self, input_data: Any, **kwargs) -> Optional[Any]:
        """
        Validate input data.

        If the input is None, return None (or the value specified in the `default` parameter). Otherwise, pass the input
        to the wrapped validator and return its result.
        """
        if input_data is None or input_data in ['', '-']:
            return deepcopy(self.default_value)

        return super().validate(input_data, **kwargs)
