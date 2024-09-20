from typing import List

from common.xml_helper import XMLHelper
from util import LotData, LotInfo, PoolInfo, ScraperBase, guess_lot_type


class Aachen(ScraperBase):
    STATIC_DATA_URL = "https://data.mfdz.de/DATEXII_Parkdaten_statisch_Aachen/body.xml"
    DYNAMIC_DATA_URL = "https://data.mfdz.de/DATEXII_Parkdaten_dynamisch_Aachen/body.xml"
    POOL_ID = "aachen"

    POOL = PoolInfo(
        id=POOL_ID,
        name="Aachen",
        public_url="https://mobilithek.info/offers/110000000003300000",
    )

    AACHEN_TO_APAG_IDS_MAPPING = {
        'aachenp1': 'aachenparkhauseurogress',
        'aachenp2': 'aachenparkhauscouvenstrasse',
        'aachenp3': 'aachenparkhausadalbertstrasse',
        'aachenp5': 'aachenparkhausrathaus',
        'aachenp6': 'aachenparkhausgaleriakaufhofcity',
        'aachenp7': 'aachenparkhaushauptbahnhof',
        'aachenp8': 'aachenparkhausadalbertsteinweg',
    }

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.DYNAMIC_DATA_URL, parser="xml")
        last_updated = self.to_utc_datetime(soup.find("publicationTime").text)

        lots = []

        for facility in soup.select("parkingStatusPublication > parkingRecordStatus"):
            lot_id = facility.find("parkingRecordReference")["id"]
            parkingStatusOriginTime = facility.find("parkingStatusOriginTime")
            last_updated_lot = self.to_utc_datetime(parkingStatusOriginTime.text) if parkingStatusOriginTime else None
            overrides = facility.find("parkingNumberOfSpacesOverride")
            lot_total = int(overrides.text) if overrides else None
            try:
                lot_occupied = int(facility.find("parkingNumberOfOccupiedSpaces").text)
            except Exception:
                lot_occupied = None

            state = facility.find("parkingSiteOpeningStatus")
            if state and state.text in [LotData.Status.open, LotData.Status.closed]:
                state = state.text
            else:
                state = LotData.Status.nodata

            lots.append(
                LotData(
                    id=self.name_to_legacy_id(lot_id),
                    timestamp=now,
                    lot_timestamp=last_updated_lot or last_updated,
                    status=state,
                    num_occupied=lot_occupied,
                    capacity=lot_total,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.STATIC_DATA_URL, parser="xml")

        lots = []
        for facility in soup.find_all("parkingRecord"):
            parkingNumberOfSpaces = facility.find("parkingNumberOfSpaces")
            capacity = int(parkingNumberOfSpaces.text) if parkingNumberOfSpaces else 0
            lots.append(
                LotInfo(
                    id=self.name_to_legacy_id(facility["id"]),
                    name=facility.find("parkingName").find("value").text,
                    type=guess_lot_type(facility.find("parkingLayout").text),
                    source_url=self.POOL.source_url,
                    latitude=float(facility.find("pointCoordinates").find("latitude").text),
                    longitude=float(facility.find("pointCoordinates").find("longitude").text),
                    capacity=capacity,
                    has_live_capacity=True,
                )
            )

        return lots

    def name_to_legacy_id(self, lot_id):
        lot_id = super().name_to_legacy_id(lot_id)
        return self.AACHEN_TO_APAG_IDS_MAPPING.get(lot_id, lot_id)