"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from validataclass.dataclasses import Default, ValidataclassMixin, validataclass
from validataclass.exceptions import DataclassPostValidationError, ValidationError
from validataclass.validators import (
    BooleanValidator,
    DateTimeValidator,
    EnumValidator,
    IntegerValidator,
    ListValidator,
    Noneable,
    NumericValidator,
    StringValidator,
)

from util import LotData, LotInfo


class ParkingSiteTypeInput(Enum):
    ON_STREET = 'ON_STREET'
    OFF_STREET_PARKING_GROUND = 'OFF_STREET_PARKING_GROUND'
    UNDERGROUND = 'UNDERGROUND'
    CAR_PARK = 'CAR_PARK'
    OTHER = 'OTHER'

    def to_lot_info_type(self) -> str:
        return {
            self.ON_STREET: 'street',
            self.OFF_STREET_PARKING_GROUND: 'lot',
            self.UNDERGROUND: 'underground',
            self.CAR_PARK: 'garage',
            self.OTHER: 'unknown',
        }.get(self, 'unknown')


class ParkAndRideTypeInput(Enum):
    CARPOOL = 'CARPOOL'
    TRAIN = 'TRAIN'
    BUS = 'BUS'
    TRAM = 'TRAM'


class OpeningStatusInput(Enum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    UNKNOWN = 'UNKNOWN'

    def to_lot_data_status(self) -> str:
        return {
            self.OPEN: 'open',
            self.CLOSED: 'closed',
            self.UNKNOWN: 'unknown',
        }.get(self, 'unknown')


@validataclass
class StaticParkingSiteInput(ValidataclassMixin):
    uid: str = StringValidator(min_length=1, max_length=256)
    name: str = StringValidator(min_length=1, max_length=256)
    operator_name: Optional[str] = Noneable(StringValidator(max_length=256)), Default(None)
    public_url: Optional[str] = Noneable(StringValidator(max_length=4096)), Default(None)
    address: Optional[str] = Noneable(StringValidator(max_length=512)), Default(None)
    description: Optional[str] = Noneable(StringValidator(max_length=4096)), Default(None)
    type: Optional[ParkingSiteTypeInput] = Noneable(EnumValidator(ParkingSiteTypeInput)), Default(None)

    max_stay: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    has_lighting: Optional[bool] = Noneable(BooleanValidator()), Default(None)
    fee_description: Optional[str] = Noneable(StringValidator(max_length=256)), Default(None)
    has_fee: Optional[bool] = Noneable(BooleanValidator()), Default(None)
    park_and_ride_type: Optional[list[ParkAndRideTypeInput]] = Noneable(ListValidator(EnumValidator(ParkAndRideTypeInput))), Default(None)
    is_supervised: Optional[bool] = Noneable(BooleanValidator()), Default(None)

    has_realtime_data: Optional[bool] = Noneable(BooleanValidator(), default=False), Default(False)
    static_data_updated_at: Optional[datetime] = DateTimeValidator(
        local_timezone=timezone.utc,
        target_timezone=timezone.utc,
        discard_milliseconds=True,
    )

    lat: Decimal = NumericValidator(min_value=90, max_value=90)
    lon: Decimal = NumericValidator(min_value=180, max_value=180)

    capacity: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_disabled: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_woman: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_family: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_charging: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_carsharing: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_truck: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    capacity_bus: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)

    opening_hours: Optional[str] = Noneable(StringValidator(max_length=512)), Default(None)

    def __post_init__(self):
        if self.lat == 0 and self.lon == 0:
            raise DataclassPostValidationError(error=ValidationError(code='lat_lon_zero', reason='Latitude and longitude are both zero.'))

    def to_lot_info(self) -> LotInfo:
        return LotInfo(
            id=self.uid,
            name=self.name,
            type=self.type.to_lot_info_type(),
            public_url=self.public_url,
            address=self.address,
            capacity=self.capacity,
            has_live_capacity=self.has_realtime_data,
            latitude=str(self.lat),
            longitude=str(self.lon),
        )


@validataclass
class RealtimeParkingSiteInput(ValidataclassMixin):
    uid: str = StringValidator(min_length=1, max_length=256)
    realtime_data_updated_at: datetime = DateTimeValidator(
        local_timezone=timezone.utc,
        target_timezone=timezone.utc,
        discard_milliseconds=True,
    )
    realtime_opening_status: OpeningStatusInput = (
        Noneable(EnumValidator(OpeningStatusInput), default=OpeningStatusInput.UNKNOWN),
        Default(OpeningStatusInput.UNKNOWN),
    )
    realtime_capacity: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_disabled: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_woman: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_family: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_charging: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_carsharing: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_truck: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_capacity_bus: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)

    realtime_free_capacity: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_disabled: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_woman: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_family: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_charging: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_carsharing: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_truck: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    realtime_free_capacity_bus: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)

    def to_lot_data(self) -> LotData:
        return LotData(
            timestamp=self.realtime_data_updated_at,
            id=self.uid,
            status=self.realtime_opening_status.to_lot_data_status(),
            num_free=self.realtime_free_capacity,
            capacity=self.realtime_capacity,
        )
