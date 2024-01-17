"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional

from validataclass.dataclasses import Default, validataclass
from validataclass.validators import (
    BooleanValidator,
    DataclassValidator,
    DecimalValidator,
    EnumValidator,
    IntegerValidator,
    ListValidator,
    Noneable,
    NumericValidator,
    StringValidator,
    UrlValidator,
)

from common.validators import ParkingSiteTypeInput


class NameContext(Enum):
    NAME = 'NAME'
    DISPLAY = 'DISPLAY'
    LABEL = 'LABEL'
    SLOGAN = 'SLOGAN'


class BahnParkingSiteCapacityType(Enum):
    PARKING = 'PARKING'
    HANDICAPPED_PARKING = 'HANDICAPPED_PARKING'


class BahnParkingSiteType(Enum):
    PARKPLATZ = 'Parkplatz'
    TIEFGARAGE = 'Tiefgarage'
    PARKHAUS = 'Parkhaus'
    STRASSE = 'Straße'
    PARKDECK = 'Parkdeck'

    def to_parking_site_type_input(self) -> ParkingSiteTypeInput:
        # TODO: find out more details about this enumeration for a proper mapping
        return {
            self.PARKPLATZ: ParkingSiteTypeInput.ON_STREET,
            self.PARKHAUS: ParkingSiteTypeInput.CAR_PARK,
            self.TIEFGARAGE: ParkingSiteTypeInput.UNDERGROUND,
            self.STRASSE: ParkingSiteTypeInput.ON_STREET,
            self.PARKDECK: ParkingSiteTypeInput.CAR_PARK,
        }.get(self, ParkingSiteTypeInput.OTHER)


@validataclass
class BahnNameInput:
    name: str = StringValidator()
    context: NameContext = EnumValidator(NameContext)


@validataclass
class BahnTypeInput:
    name: BahnParkingSiteType = EnumValidator(BahnParkingSiteType)
    nameEn: str = StringValidator()
    abbreviation: str = StringValidator()


@validataclass
class BahnOperatorInput:
    name: str = StringValidator()
    # url: str = UrlValidator()  # TODO: urls are broken


@validataclass
class BahnLocationInput:
    longitude: Decimal = NumericValidator()
    latitude: Decimal = NumericValidator()


@validataclass
class BahnAdressInput:
    streetAndNumber: str = StringValidator()
    zip: str = StringValidator()
    city: str = StringValidator()
    phone: Optional[str] = Noneable(StringValidator())
    location: BahnLocationInput = DataclassValidator(BahnLocationInput)


@validataclass
class BahnCapacityInput:
    type: BahnParkingSiteCapacityType = EnumValidator(BahnParkingSiteCapacityType)
    total: int = IntegerValidator(allow_strings=True, min_value=0)


@validataclass
class BahnOpeningHoursInput:
    text: Optional[str] = StringValidator(), Default(None)
    is24h: bool = BooleanValidator()


@validataclass
class BahnClearanceInput:
    height: Optional[Decimal] = Noneable(DecimalValidator()), Default(None)
    width: Optional[Decimal] = Noneable(DecimalValidator()), Default(None)


@validataclass
class BahnRestrictionInput:
    clearance: BahnClearanceInput = DataclassValidator(BahnClearanceInput)


@validataclass
class BahnAccessInput:
    openingHours: BahnOpeningHoursInput = DataclassValidator(BahnOpeningHoursInput)
    restrictions: BahnRestrictionInput = DataclassValidator(BahnRestrictionInput)
    # TODO: ignored multible attributes which do not matter so far


@validataclass
class BahnParkingSiteInput:
    id: int = IntegerValidator(allow_strings=True)
    name: list[BahnNameInput] = ListValidator(DataclassValidator(BahnNameInput))
    url: str = UrlValidator()
    type: BahnTypeInput = DataclassValidator(BahnTypeInput)
    operator: BahnOperatorInput = DataclassValidator(BahnOperatorInput)
    address: BahnAdressInput = DataclassValidator(BahnAdressInput)
    capacity: list[BahnCapacityInput] = ListValidator(DataclassValidator(BahnCapacityInput))
    hasPrognosis: bool = BooleanValidator()
    access: BahnAccessInput = DataclassValidator(BahnAccessInput)
    # TODO: ignored multible attributes which do not matter so far
