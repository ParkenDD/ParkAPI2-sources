"""
Original code and data by Költzsch, Thalheim
"""
import urllib.parse
from typing import List

from util import *


class Muenster(ScraperBase):

    POOL = PoolInfo(
        id="muenster",
        name="Münster",
        public_url="https://www.stadt-muenster.de/tiefbauamt/parkleitsystem",
        source_url="https://api.dashboard.smartcity.ms/parking",
        timezone="Europe/Berlin",
        attribution_contributor="dl-by-de/2.0",
        attribution_license="Stadt Münster",
        # see also https://opendata.stadt-muenster.de/dataset/parkleitsystem-parkhausbelegung-aktuell
        attribution_url="https://www.stadt-muenster.de/tiefbauamt/impressum.html",
    )

    STATE_MAP = {
        "frei": LotData.Status.open,
        "geschlossen": LotData.Status.closed,
        "besetzt": LotData.Status.open,
    }

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        lots = []
        
        fc = self.request_json(self.POOL.source_url)
        for feature in fc.get('features'):
            props = feature['properties']
            (lot_type, parking_name, parking_legacy_name) = self.process_name(props.get('NAME'))
            
            lots.append(
                LotData(
                    timestamp=timestamp,
                    #lot_timestamp=timestamp,
                    id=parking_legacy_name,
                    status=self.STATE_MAP.get(props.get('NAME'), LotData.Status.unknown),
                    num_free=int_or_none(props.get('parkingFree')),
                    capacity=int_or_none(props.get('parkingTotal')),
                )
            )

        return lots

    @classmethod
    def process_name(self, name):
        fixed_name = name.replace('Parkplatz Busparkplatz', 'Busparkplatz')
        split_name = fixed_name.split()

        lot_type_text = split_name[0]
        lot_name = (split_name[0] if len(split_name) == 1 else " ".join(split_name[1:])).strip()

        type_mapping = {
            "Parkplatz": LotInfo.Types.lot,
            "Parkhaus": LotInfo.Types.garage,
            "Busparkplatz": LotInfo.Types.bus,
        }
        lot_type = type_mapping.get(lot_type_text, LotInfo.Types.unknown)

        type_abbrevation_mapping = {
            LotInfo.Types.lot: 'pp',
            LotInfo.Types.garage: 'ph',
            LotInfo.Types.bus: '' 
        }
        type_abbrevation = type_abbrevation_mapping.get(lot_type, '')
        lot_legacy_name = name_to_legacy_id(self.POOL.id, type_abbrevation + lot_name)

        return lot_type, lot_name, lot_legacy_name

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.name: lot
            for lot in self.get_v1_lot_infos_from_geojson("Muenster")
        }

        lots = []
        
        fc = self.request_json(self.POOL.source_url)
        for feature in fc.get('features'):
            props = feature['properties']
            coord = feature['geometry']['coordinates']
            (lot_type, parking_name, parking_legacy_name) = self.process_name(props.get('NAME'))
            
            kwargs = vars(lot_map[parking_name]) if parking_name in lot_map else {}
            kwargs.update(dict(
                id=parking_legacy_name,
                name=parking_name,
                public_url=props.get('URL'),
                capacity=int_or_none(props.get('parkingTotal')),
                type=lot_type,
                has_live_capacity=True,
                longitude=str(round(coord[0],6)),
                latitude=round(coord[1],6),
            ))
         
            lots.append(LotInfo(**kwargs))

        return lots
