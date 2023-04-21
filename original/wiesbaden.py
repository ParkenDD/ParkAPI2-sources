"""
Original code and data by Quint
"""
import datetime
from typing import List, Tuple, Generator

from util import *


class Wiesbaden(ScraperBase):

    POOL = PoolInfo(
        id="wiesbaden",
        name="Wiesbaden",
        public_url="https://www.wiesbaden.de/leben-in-wiesbaden/verkehr/auto/parken/parkhaeuser.php",
        source_url="https://geoportal.wiesbaden.de/parkleitsystem/parkhaeuser.php",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Wiesbaden",
        attribution_license=None,
        attribution_url=None,
    )

    STATUS_MAPPING = {
        "OK": LotData.Status.open,
        # TODO: After opening times lots show all numbers but this status
        #   so i guess it means "closed"
        "Nicht OK": LotData.Status.closed,
        "Übertragungsstörung": LotData.Status.error,
    }

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
            
        lots = []
        for source_url, attributes in self.iter_lot_attributes():
            if not "name" in attributes: 
                log("Error: incomplete attributes for ", source_url)
                continue

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("wiesbaden", attributes["name"]),
                    status=self.STATUS_MAPPING.get(attributes["status"], LotData.Status.unknown),
                    num_free=int_or_none(attributes["num_free"]),
                    capacity=int_or_none(attributes["capacity"]),
                )
            )

        return lots

    def iter_lot_attributes(self) -> Generator[Tuple[datetime.datetime, str, dict], None, None]:
        soup = self.request_soup(self.POOL.source_url)
        for row in soup.find_all("tr"):
            tds = row.find_all("td")

            if tds[0].find("h4"):
                # skip heading
                continue

            name = tds[0].text.strip()
            num_free = tds[1].text.split('/')[0].strip()
            capacity = tds[1].text.split('/')[1].strip()
            status = tds[3].text.strip()
            attributes = {
                "name": name, 
                "num_free": num_free, 
                "capacity": capacity, 
                "status": status
            }
            
            yield self.POOL.source_url, attributes

    def get_lot_infos(self) -> List[LotInfo]:
        
        lot_map = {
            lot.id: lot
            for lot in self.get_v1_lot_infos_from_geojson("Wiesbaden")
        }
        
        lots = []
        for source_url, attributes in self.iter_lot_attributes():
            name = attributes["name"]
            legacy_id = self.name_to_legacy_id(name)

            kwargs = vars(lot_map[legacy_id]) if legacy_id in lot_map else {}
            kwargs.update(dict(
                name=name,
                id=legacy_id,
                has_live_capacity=True,
                source_url=source_url,
            ))

            lots.append(LotInfo(**kwargs))

        return lots

    def name_to_legacy_id(self, name):
        NEW_TO_LEGACY = {
            "Mauritius Galerie": "Mauritius-Parkhaus",
            "City 1": "City I",
            "City 2": "City II",
        }
        legacy_name = NEW_TO_LEGACY.get(name, name)
        return name_to_legacy_id(self.POOL.id, name)
