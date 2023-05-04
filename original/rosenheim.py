"""
Original code and data by Quint
"""
from typing import List

from util import *


class Rosenheim(ScraperBase):

    POOL = PoolInfo(
        id="rosenheim",
        name="Rosenheim",
        public_url="https://www.rosenheim.de/buergerservice/mobilitaet/parken",
        source_url="https://www.rosenheim.de/?id=1&type=1452982642&L=0&tx_in2rocitymap_in2rocitymap%5Btype%5D=parking_space&tx_in2rocitymap_in2rocitymap%5Blang%5D=de-DE&tx_in2rocitymap_in2rocitymap%5BdirectoryFilter%5D=544&tx_in2rocitymap_in2rocitymap%5BapiAction%5D=getAvailableParking&tx_in2rocitymap_in2rocitymap%5BCategory%5D=21",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Rosenheim",
        attribution_license=None,
        attribution_url=None,
    )

    LOT_URL = "https://www.rosenheim.de/?id=1&type=1452982642&L=0&tx_in2rocitymap_in2rocitymap%5Btype%5D=parking_space&tx_in2rocitymap_in2rocitymap%5Blang%5D=de-DE&tx_in2rocitymap_in2rocitymap%5BdirectoryFilter%5D=544&tx_in2rocitymap_in2rocitymap%5BapiAction%5D=categorizedMap&tx_in2rocitymap_in2rocitymap%5BCategory%5D=21"
    
    def get_lot_data(self) -> List[LotData]:
        """
        Rosenheim's source_url refers to a json on following structure:
         {
            "<parkingid>":{"id":"<parkingid>","currentParkingSpacesCount":"<num_free>"},
            ...
         }"

         The parkingid is an internal numeric id, which currently is not available via LotInfo.
         For this reason, we request the parkings as well dynamically and use their IDs.
        """
        timestamp = self.now()
        dataJSON = self.request_json(self.POOL.source_url)

        # Retrieve static parking information to access internal id
        lot_infos = self._get_lot_infos_as_dicts()

        lots = []
        for lot in lot_infos :
            internal_lot_id = lot["external_id"]
            realtime_info = dataJSON.get(str(internal_lot_id))
            
            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=lot["id"],
                    status=LotData.Status.open,
                    num_free=int_or_none(realtime_info['currentParkingSpacesCount']),
                    capacity=int_or_none(lot["capacity"]),
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_dicts = self._get_lot_infos_as_dicts()
        lots = []
        for lot in lot_dicts:
            # For now, remove external_id, which is not supported by LotInfo yet
            lot.pop("external_id")
            lots.append(LotInfo(**lot))
  
        return lots

    def name_to_legacy_id(self, lot_name) -> str:
        legacy_name = lot_name.replace('-', '').replace(' ', '').replace('+', '')
        return name_to_legacy_id(self.POOL.id, legacy_name)

    def _get_lot_infos_as_dicts(self) -> dict:
        geojson_response = self.request_json(self.LOT_URL)

        lots = []
        for marker in geojson_response['markers']:
            lot_name = marker["name"]
            lot_id = self.name_to_legacy_id(lot_name)
            lat = marker["position"]["lat"]
            lng = marker["position"]["lng"]
            lot_url = "https://www.rosenheim.de"+marker["externalDetailPage"]

            lots.append({
                "id": lot_id,
                "external_id": marker["id"],
                "name": lot_name,
                "type": "garage",
                "latitude": lat or None,
                "longitude": lng or None,
                "public_url": lot_url,
                "source_url": self.POOL.public_url,
                "address": marker["address"].split("<")[0],
                "capacity": marker["parkingSpaces"],
                "has_live_capacity": marker["fetchDynamicParkingSpacesCount"],
            })
            
        return lots
