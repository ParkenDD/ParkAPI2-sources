"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import time
from typing import Optional

from validataclass.dataclasses import Default, ValidataclassMixin, validataclass

from .base_validators import StaticParkingSiteInput
from .fields import (
    ExcelNoneable,
    ExcelTimeValidator,
    ExtendedBooleanValidator,
    GermanDurationIntegerValidator,
    NumberCastingStringValidator,
)


@validataclass
class ExcelStaticParkingSiteInput(StaticParkingSiteInput):
    uid: str = NumberCastingStringValidator(min_length=1, max_length=256)
    has_lighting: Optional[bool] = ExcelNoneable(ExtendedBooleanValidator())
    has_fee: Optional[bool] = ExcelNoneable(ExtendedBooleanValidator())
    is_supervised: Optional[bool] = ExcelNoneable(ExtendedBooleanValidator())
    has_realtime_data: Optional[bool] = ExcelNoneable(ExtendedBooleanValidator(), default=False)
    max_stay: Optional[int] = ExcelNoneable(GermanDurationIntegerValidator()), Default(None)


@validataclass
class ExcelOpeningTimeInput(ValidataclassMixin):
    opening_hours_is_24_7: Optional[bool] = ExcelNoneable(ExtendedBooleanValidator()), Default(None)
    opening_hours_weekday_begin: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)
    opening_hours_weekday_end: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)
    opening_hours_saturday_begin: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)
    opening_hours_saturday_end: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)
    opening_hours_sunday_begin: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)
    opening_hours_sunday_end: Optional[time] = ExcelNoneable(ExcelTimeValidator()), Default(None)

    def get_osm_opening_hours(self) -> str:
        if self.opening_hours_is_24_7 is True:
            return '24/7'
        # TODO: opening hours over midnight
        opening_hours_fragments = []
        if self.opening_hours_weekday_begin and self.opening_hours_weekday_end:
            opening_hours_fragments.append(
                f'Mo-Fr {self.opening_hours_weekday_begin.strftime("%H:%M")}' f'-{self.opening_hours_weekday_end.strftime("%H:%M")}',
            )
        if self.opening_hours_saturday_begin and self.opening_hours_saturday_end:
            opening_hours_fragments.append(
                f'Sa {self.opening_hours_saturday_begin.strftime("%H:%M")}' f'-{self.opening_hours_saturday_end.strftime("%H:%M")}',
            )
        if self.opening_hours_sunday_begin and self.opening_hours_sunday_end:
            opening_hours_fragments.append(
                f'Su {self.opening_hours_sunday_begin.strftime("%H:%M")}' f'-{self.opening_hours_sunday_end.strftime("%H:%M")}',
            )
        return '; '.join(opening_hours_fragments)
