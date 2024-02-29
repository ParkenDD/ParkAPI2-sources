"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import time
from decimal import Decimal
from enum import Enum
from typing import Optional

from validataclass.dataclasses import Default, validataclass
from validataclass.validators import (
    BooleanValidator,
    DataclassValidator,
    EmailValidator,
    EnumValidator,
    IntegerValidator,
    ListValidator,
    Noneable,
    NumericValidator,
    StringValidator,
    TimeValidator,
)

from common.validators import ParkingSiteTypeInput


class PbwParkingSiteType(Enum):
    PARKPLATZ = 'Parkplatz'
    PARKBEREICH = 'Parkbereich'
    PARKHAUS = 'Parkhaus'
    PARKGARAGE = 'Parkgarage'
    PARKIERUNGSAREAL = 'Parkierungsareal'
    GESAMTAREAL = 'Gesamtareal'

    def to_parking_site_type_input(self) -> ParkingSiteTypeInput:
        # TODO: find out more details about this enumeration for a proper mapping
        return {
            self.PARKPLATZ: ParkingSiteTypeInput.ON_STREET,
            self.PARKBEREICH: ParkingSiteTypeInput.ON_STREET,
            self.PARKHAUS: ParkingSiteTypeInput.CAR_PARK,
            self.PARKGARAGE: ParkingSiteTypeInput.UNDERGROUND,
            self.PARKIERUNGSAREAL: ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
            self.GESAMTAREAL: ParkingSiteTypeInput.OFF_STREET_PARKING_GROUND,
        }.get(self, ParkingSiteTypeInput.OTHER)


class PbwParkingSiteShortType(Enum):
    PP = 'PP'
    PG = 'PG'
    PH = 'PH'
    PA = 'PA'


@validataclass
class PbwCityInput:
    id: int = IntegerValidator(allow_strings=True)
    name: str = StringValidator()
    count_objects: str = IntegerValidator(allow_strings=True)


@validataclass
class PbwParkingSiteInput:
    id: int = IntegerValidator(allow_strings=True)
    id_city: int = IntegerValidator(allow_strings=True)
    name: str = StringValidator()


@validataclass
class PbwParkingSiteObjectInput:
    name: str = StringValidator(min_length=1, max_length=256)
    plz: str = StringValidator()
    ort: str = StringValidator()
    land: str = StringValidator()
    strasse: str = StringValidator()
    art_lang: PbwParkingSiteType = EnumValidator(PbwParkingSiteType)
    art_kurz: PbwParkingSiteShortType = EnumValidator(PbwParkingSiteShortType)  # TODO: Meaning?
    # id_extern  # TODO: ugly typing: bool and str


@validataclass
class PbwRealtimeParkingSiteInput:
    kurzparker_frei: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)
    ladeplaetze_frei: Optional[int] = Noneable(IntegerValidator(min_value=0)), Default(None)


@validataclass
class PbwParkingSitePositionInput:
    longitude: Decimal = NumericValidator()
    latitude: Decimal = NumericValidator()


@validataclass
class PbwParkingSitePlacesInput:
    gesamt: int = IntegerValidator(min_value=0)
    behinderte: int = IntegerValidator(min_value=0)
    familien: int = IntegerValidator(min_value=0)
    frauen: int = IntegerValidator(min_value=0)
    elektrofahrzeuge: int = IntegerValidator(min_value=0)


@validataclass
class PbwParkingSiteTypeInput:
    dauerparker: bool = BooleanValidator()
    kurzparker: bool = BooleanValidator()
    eparker: bool = BooleanValidator()
    # TODO: more attributes?


@validataclass
class PbwParkingSiteSetupInput:
    aufzug: bool = BooleanValidator()
    videoaufzeichnung: bool = BooleanValidator()
    schuelerkunst: bool = BooleanValidator()
    wc: bool = BooleanValidator()
    wc_mitarbeiter: bool = BooleanValidator()
    behindertenstellplaetze: bool = BooleanValidator()
    familienstellplaetze: bool = BooleanValidator()
    frauenstellplaetze: bool = BooleanValidator()
    p_and_r: bool = BooleanValidator()
    regenschirmautomat: bool = BooleanValidator()
    notrufmoeglichkeiten: bool = BooleanValidator()
    servicepersonal: bool = BooleanValidator()
    parkplatzreservierung: bool = BooleanValidator()
    serviceangebote: Optional[str] = Noneable(StringValidator())
    einfahrtshoehe: Optional[Decimal] = Noneable(NumericValidator())
    einfahrtsbreite: Optional[Decimal] = Noneable(NumericValidator())
    stellplatzbreite_max: Optional[Decimal] = Noneable(NumericValidator())
    stellplatzbreite_min: Optional[Decimal] = Noneable(NumericValidator())


@validataclass
class PbwParkingSitePaymentInput:
    barzahlung: bool = BooleanValidator()
    ec_karte: bool = BooleanValidator()
    visa_karte: bool = BooleanValidator()
    kreditkarte: bool = BooleanValidator()
    parken_laden_karte: bool = BooleanValidator()
    parknow_karte: bool = BooleanValidator()


@validataclass
class PbwParkingSiteChargeStationParameterInput:
    e_parken_karte: bool = BooleanValidator()
    enbwmobility: bool = BooleanValidator()
    barrierefrei: bool = BooleanValidator()
    hubject: bool = BooleanValidator()


@validataclass
class PbwParkingSiteMobilityCardInput:
    parken_laden_karte: bool = BooleanValidator()
    parknow_karte: bool = BooleanValidator()
    polygocard: bool = BooleanValidator()
    v_parken_karte: bool = BooleanValidator()


@validataclass
class PbwParkingSiteContactInput:
    anrede: str = StringValidator()
    vorname: str = StringValidator()
    nachname: str = StringValidator()
    mail: str = EmailValidator()
    telefon: str = StringValidator()


@validataclass
class PbwParkingSiteOpeningTimesInput:
    kurzparker_24_7: bool = BooleanValidator()
    kurzparker_kommentar: str = StringValidator()
    kurzparker_montag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_montag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_dienstag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_dienstag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_mittwoch_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_mittwoch_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_donnerstag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_donnerstag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_freitag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_freitag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_samstag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_samstag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_sonntag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_sonntag_bis: Optional[time] = Noneable(TimeValidator())
    kurzparker_feiertag_von: Optional[time] = Noneable(TimeValidator())
    kurzparker_feiertag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_24_7: bool = BooleanValidator()
    dauerparker_kommentar: str = StringValidator()
    dauerparker_montag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_montag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_dienstag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_dienstag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_mittwoch_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_mittwoch_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_donnerstag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_donnerstag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_freitag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_freitag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_samstag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_samstag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_sonntag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_sonntag_bis: Optional[time] = Noneable(TimeValidator())
    dauerparker_feiertag_von: Optional[time] = Noneable(TimeValidator())
    dauerparker_feiertag_bis: Optional[time] = Noneable(TimeValidator())


@validataclass
class PbwParkingSitePaymentPlaceInput:
    kassenautomat: str = StringValidator()
    standort: str = StringValidator()
    akzeptanz_karten: str = StringValidator()
    kommentar: str = StringValidator()


@validataclass
class PbwParkingSiteTariffInput:
    beschreibung: str = StringValidator()
    taktung: str = StringValidator()  # TODO: any way of make a nice output out of that?!
    gueltig_von: time = TimeValidator()
    gueltig_bis: time = TimeValidator()
    gueltig_montag: bool = BooleanValidator()
    gueltig_dienstag: bool = BooleanValidator()
    gueltig_mittwoch: bool = BooleanValidator()
    gueltig_donnerstag: bool = BooleanValidator()
    gueltig_freitag: bool = BooleanValidator()
    gueltig_samstag: bool = BooleanValidator()
    gueltig_sonntag: bool = BooleanValidator()
    gueltig_feiertag: bool = BooleanValidator()
    betrag: Optional[Decimal] = Noneable(NumericValidator())


@validataclass
class PbwParkingSiteChargeStationInput:
    anzahl_ladestationen: int = IntegerValidator(min_value=0)
    anzahl_ladepunkte: int = IntegerValidator(min_value=0)
    betreiber: str = StringValidator()
    nutzer: str = StringValidator()
    geraeteauswahl: str = StringValidator()
    modellbezeichnung: str = StringValidator()
    steckertypen: str = StringValidator()  # TODO: dereference that?
    standort: str = StringValidator()
    ladeleistung_maximal: int = IntegerValidator(min_value=0)
    ladeplatz_reservierung: bool = BooleanValidator()


@validataclass
class PbwParkingSiteCountInput:
    frauenstellplaetze: int = IntegerValidator(min_value=0)
    elektrofahrzeugstellplaetze: int = IntegerValidator(min_value=0)
    behindertenstellplaetze: int = IntegerValidator(min_value=0)
    familienstellplaetze: int = IntegerValidator(min_value=0)


@validataclass
class PbwParkingSiteDetailInput:
    # atm several validators are disabled as they are not used in further processing, and it would be bad if the validation fails
    # because of unused fields. But maybe we need it some day?
    id: int = IntegerValidator(allow_strings=True)
    objekt: PbwParkingSiteObjectInput = DataclassValidator(PbwParkingSiteObjectInput)
    # dynamisch: PbwRealtimeParkingSiteInput = DataclassValidator(PbwRealtimeParkingSiteInput)
    position: PbwParkingSitePositionInput = DataclassValidator(PbwParkingSitePositionInput)
    stellplaetze: PbwParkingSitePlacesInput = DataclassValidator(PbwParkingSitePlacesInput)
    typ: PbwParkingSiteTypeInput = DataclassValidator(PbwParkingSiteTypeInput)
    ausstattung: PbwParkingSiteSetupInput = DataclassValidator(PbwParkingSiteSetupInput)
    # elektroladestation: PbwParkingSiteChargeStationParameterInput = DataclassValidator(PbwParkingSiteChargeStationParameterInput)
    # mobilitaetskarte: PbwParkingSiteMobilityCardInput = DataclassValidator(PbwParkingSiteMobilityCardInput)
    # umgebung: list[str] = ListValidator(StringValidator())
    # ansprechpartner: PbwParkingSiteContactInput = DataclassValidator(PbwParkingSiteContactInput)
    # oeffnungszeiten: Optional[PbwParkingSiteOpeningTimesInput] = DataclassValidator(PbwParkingSiteOpeningTimesInput), Default(None)
    # bezahlstellen: list[PbwParkingSitePaymentPlaceInput] = ListValidator(DataclassValidator(PbwParkingSitePaymentPlaceInput)), Default([])
    # tarif: list[PbwParkingSiteTariffInput] = ListValidator(DataclassValidator(PbwParkingSiteTariffInput)), Default([])
    # ladestation: list[PbwParkingSiteChargeStationInput] = ListValidator(DataclassValidator(PbwParkingSiteChargeStationInput)), Default([])
    # ladetarif: list[PbwParkingSiteTariffInput] = ListValidator(DataclassValidator(PbwParkingSiteTariffInput)), Default([])
    # anzahl: PbwParkingSiteCountInput = DataclassValidator(PbwParkingSiteCountInput)


@validataclass
class PbwRealtimeInput:
    id: int = IntegerValidator(allow_strings=True)
    dynamisch: PbwRealtimeParkingSiteInput = DataclassValidator(PbwRealtimeParkingSiteInput)
