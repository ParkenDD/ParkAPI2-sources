"""
Original code and data by Quint
"""
import urllib.parse
from typing import List

from ..util import *


class Mannheim(ScraperBase):

    POOL = PoolInfo(
        id="mannheim",
        name="Mannheim",
        public_url="https://www.parken-mannheim.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Mannheimer Parkhausbetriebe GmbH",
        attribution_license=None,
        attribution_url="https://www.parken-mannheim.de/impressum",
    )

    """
    Maps current parking lot names to their former name to provide
    backward compatibility.
    """
    LOT_LEGACY_NAME_MAPPINGS = {
        "Hauptbahnhof P3, Parkhaus": "Hauptbahnhof P3/P4 Parkhaus",
    }

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []

        # suche: <div id="parkhausliste-ct">
        # Note: page contains two elements with id parkhausliste-ct, the last one contains the lot data
        div_level1 = soup.find_all('div', id='parkhausliste-ct')[-1]
        # <p style="color: #7a7a7b; padding: 18px 0 8px 0">zuletzt aktualisiert am 19.06.2019, 15:27 Uhr</p>
        date_time = div_level1.find('p')
        last_updated = self.to_utc_datetime(date_time.text, 'zuletzt aktualisiert am %d.%m.%Y, %H:%M Uhr')

        # find all entries:
        div_level2 = div_level1.find('div')
        div_level3 = div_level2.find_all('div')
        count = 0
        while count < len(div_level3) - 2:
            parking_name = div_level3[count+1].text.strip()

            if parking_name in ('P20', 'UEG (Funktionskarten)'):
                # workaround: ignore entries which seem to be no parking lots
                count += 3
                continue
            
            parking_free = None
            parking_state = LotData.Status.open
            try:
                parking_free = int(div_level3[count+2].text)
            except:
                parking_state = LotData.Status.nodata

            count += 3

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=self.name_to_legacy_id(parking_name),
                    lot_timestamp=last_updated,
                    status=parking_state,
                    num_free=parking_free,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_map = {
            lot.id: lot
            for lot in self.get_v1_lot_infos_from_geojson("Mannheim")
        }

        soup = self.request_soup(self.POOL.public_url)
        lots = []

        # suche: <div id="parkhausliste-ct">
        div_level1 = soup.find_all('div', id='parkhausliste-ct')[-1]

        # find all entries:
        div_level2 = div_level1.find('div')
        div_level3 = div_level2.find_all('div')
        count = 0
        while count < len(div_level3) - 2:
            parking_name = div_level3[count+1].text.strip()

            if parking_name in ('P20', 'UEG (Funktionskarten)'):
                # workaround: ignore entries which seem to be no parking lots
                count += 3
                continue
            
            lot_id = self.name_to_legacy_id(parking_name)

            link = div_level3[count+1].find("a")
            count += 3
            
            kwargs = vars(lot_map[lot_id]) if lot_id in lot_map else {}
            kwargs.update(dict(
                id=lot_id,
                name=parking_name,
                public_url=urllib.parse.urljoin(self.POOL.public_url, link["href"])
            ))

            lots.append(LotInfo(**kwargs))

        return lots

    def name_to_legacy_id(self, lot_name) -> str:
        legacy_name = self.LOT_LEGACY_NAME_MAPPINGS.get(lot_name, lot_name)
        return name_to_legacy_id(self.POOL.id, legacy_name)

