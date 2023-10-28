"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def convert_to_serializable_value(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, bytes):
        return obj.decode()

    # Serialize data models (not only, but mostly ORM) using to_dict.
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()

    # Fallback to either the object's attribute dictionary or cast it to a string
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


class DefaultJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        return convert_to_serializable_value(obj)
