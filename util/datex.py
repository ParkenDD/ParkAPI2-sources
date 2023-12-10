from typing import List

from .structs import LotInfo, LotData
from .strings import name_to_legacy_id, guess_lot_type, parse_geojson

class DatexScraperMixin:
    """
    This Mixin defines provides an implementation of get_lot_data and 
    get_lot_infos that should work with most DATEXII ParkingFacility publications.

    Subclasses should provide the dynamic parking facility publication url as POOl.source_url 
    and the static parking facility publication as class variable:

    STATIC_LOTS_URL: str

    See stuttgart.py for an example.

    """
    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.source_url, encoding='UTF-8', parser='xml')


        last_updated = self.to_utc_datetime(soup.find("publicationTime").text)

        lots = []

        for facility in soup.select("parkingFacilityTableStatusPublication > parkingFacilityStatus"):
            lot_id = facility.find("parkingFacilityReference")["id"]

            capacity_shorttermoverride = facility.find("totalParkingCapacityShorttermOverride")

            parkingFacilityStatusTime = facility.find("parkingFacilityStatusTime")
            try:
                lot_timestamp = self.to_utc_datetime(parkingFacilityStatusTime.text) if parkingFacilityStatusTime else last_updated  
            except:
                lot_timestamp = last_updated
            # TODO: Need not find out difference between
            #   totalNumberOfOccupiedParkingSpaces and totalNumberOfVacantParkingSpaces
            #   e.g. first goes to zero or might disappear when closed while second remains
            try:
                lot_occupied = int(facility.find("totalNumberOfOccupiedParkingSpaces").text)
            except:
                lot_occupied = None

            try:
                lot_free = int(facility.find("totalNumberOfVacantParkingSpaces").text)
            except:
                lot_free = None

            state = facility.find("parkingFacilityStatus")
            
            if state and state.text in [LotData.Status.open, LotData.Status.closed]:
                state = state.text
            elif state and state.text == "spacesAvailable":
                state = LotData.Status.open
            else:
                state = LotData.Status.nodata

            lots.append(
                LotData(
                    id=name_to_legacy_id(self.POOL.id, lot_id),
                    timestamp=now,
                    lot_timestamp=lot_timestamp,
                    status=state,
                    num_occupied=lot_occupied,
                    num_free=lot_free,
                    capacity=int(capacity_shorttermoverride.text) if capacity_shorttermoverride else None,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        url = self.STATIC_LOTS_URL
        soup = self.request_soup(url, encoding='UTF-8', parser='xml')
        
        lots = []
        for facility in soup.find_all("parkingFacility"):
            coord = self._get_facility_coords(facility)
            lots.append(
                LotInfo(
                    id=name_to_legacy_id(self.POOL.id, facility["id"]),
                    name=self._get_facility_name(facility),
                    type=LotInfo.Types.unknown,  # there's no data
                    source_url=self.POOL.source_url,
                    latitude=coord["latitude"] if coord else None,
                    longitude=coord["longitude"] if coord else None,
                    capacity=int(facility.find("totalParkingCapacity").text),
                    has_live_capacity=True,
                )
            )

        return lots

    def _get_facility_name(self, facility):
        # Try name (used by Stuttgart)
        pfname = facility.select_one("parkingFacilityName > values > value")
        if pfname:
            return pfname.text

        # If not, try parkingfacilitydescription (as (misused?) by Frankfurt)
        dfdesc = facility.find("parkingfacilitydescription")
        if dfdesc:
            return dfdesc.text

        return None

    def _get_facility_coords(self, facility):
        

        point = facility.find("pointCoordinates")
        if not point:
            point = facility.find("locationForDisplay")
        if not point:
            return None
    
        else:
            return { 
                "latitude": float(point.find("latitude").text),
                "longitude": float(point.find("longitude").text)
            }
