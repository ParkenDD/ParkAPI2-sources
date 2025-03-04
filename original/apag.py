"""
Original code by Quint, Berke
"""
import re
from typing import Generator, List, Tuple

import bs4

from util import LotData, LotInfo, PoolInfo, ScraperBase, float_or_none, guess_lot_type, int_or_none, name_to_legacy_id


class Apag(ScraperBase):
    POOL = PoolInfo(
        id="apag",
        name="Aachener Parkhaus GmbH",
        public_url="https://www.apag.de/de/fahrzeug-parken-laden-fahrrad-abstellen",
    )

    # A couple of parkings are provided by Aachen as well.
    # As the Aachen datasource is structured, we prefer it and suppress
    # apag parkings which are also provided by provider aachen.
    LOT_IDS_TO_EXCLUDE = {
        "aachenparkhausebvcarré",
        "aachenparkhauseurogress",
        "aachenparkhauscouvenstrasse",
        "aachenparkhausadalbertstrasse",
        "aachenparkhausrathaus",
        "aachenparkhausgaleriakaufhofcity",
        "aachenparkhaushauptbahnhof",
        "aachenparkhausadalbertsteinweg",
    }

    def _get_parking_name(self, lot):
        return lot.find('a').find('div', class_='facility-title').text

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        lots = []

        for id_prefix, one_lot in self._lots_iterator(self.POOL.public_url):
            parking_name = self._get_parking_name(one_lot)

            parking_state = LotData.Status.open
            parking_free = None
            try:
                text = one_lot.find('div', class_='availability-car-parking').text
                parking_free = int(text)
            except:
                parking_state = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=now,
                    id=name_to_legacy_id(id_prefix, parking_name),
                    num_free=parking_free,
                    status=parking_state,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lots = []

        for id_prefix, one_lot in self._lots_iterator(self.POOL.public_url):
            parking_name = self._get_parking_name(one_lot)

            lot_url = one_lot.find("a").attrs["href"]
            lot_soup = self.request_soup(lot_url)

            elem_total = lot_soup.find_all("span", {"class": "capacity-parking"})
            elem_address = lot_soup.find("span", {"class": "facility-address"})
            elem_maps_link = lot_soup.find("a", {"class": "btn-route"})
            coord_match = re.search(r"@(\d+\.\d+),(\d+(\.\d+)?)", elem_maps_link["href"])

            type = guess_lot_type(parking_name)
            name = " ".join(parking_name.split()[1:])

            capacity = None
            for elem in elem_total:
                c = int_or_none(elem.text.split()[-1])
                if c is not None:
                    if capacity is None:
                        capacity = c
                    else:
                        capacity += c

            lots.append(
                LotInfo(
                    id=name_to_legacy_id(id_prefix, parking_name),
                    name=name,
                    type=type,
                    public_url=lot_url,
                    source_url=lot_url,
                    address="\n".join(line.strip() for line in elem_address.text.splitlines() if line.strip()),
                    capacity=capacity,
                    latitude=float_or_none(coord_match.group(1) if coord_match else None),
                    longitude=float_or_none(coord_match.group(2) if coord_match else None),
                )
            )

        return lots

    def _lots_iterator(self, url: str) -> Generator[Tuple[str, bs4.Tag], None, None]:
        soup = self.request_soup(url)
        cities = soup.find_all('li', class_='city-item')

        for city_items in cities:
            id_prefix = city_items["class"][1].replace('city-', '')
            parking_lots = city_items.find_all('li')
            for one_lot in parking_lots:
                # For now, ParkAPI does not support bicycle parking.
                # TODO add support for bicycle parking
                parking_id = name_to_legacy_id(id_prefix, self._get_parking_name(one_lot))

                if parking_id not in self.LOT_IDS_TO_EXCLUDE and 'Bike-Station' not in one_lot.find('a').text:
                    yield id_prefix, one_lot
