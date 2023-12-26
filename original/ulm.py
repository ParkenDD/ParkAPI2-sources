"""
Original code and data by Quint
"""
from typing import List

from util import *


class Ulm(ScraperBase):

    POOL = PoolInfo(
        id="ulm",
        name="Ulm",
        public_url="https://www.parken-in-ulm.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="Ulmer Parkbetriebs-GmbH",
        attribution_license=None,
        attribution_url="https://www.parken-in-ulm.de/impressum.php",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        root = self.request_soup(self.POOL.public_url)

        lots = []

        section = root.find('section', class_='s_live_counter')
        cards = section.find_all('div', class_='card-container')
        for card in cards:
            parking_name = card.find('a', class_='stretched-link').text
            parking_data = card.find('div', class_='counter-text').get_text().strip().split(' / ')
            if parking_data[1] == '?':
                parking_state = LotData.Status.open
                parking_free = int_or_none(parking_data[0])
            else:
                parking_state = LotData.Status.nodata
                parking_free = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("ulm", parking_name),
                    status=parking_state,
                    num_free=parking_free,
                    capacity=int_or_none(parking_data[1]),
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        return self.get_v1_lot_infos_from_geojson("Ulm")
