import urllib.parse
from typing import List

import bs4

from ..util import *


class Braunschweig(ScraperBase):

    POOL = PoolInfo(
        id="braunschweig",
        name="Braunschweig",
        public_url="https://www.braunschweig.de/tourismus/anreise/parken.php",
        source_url="https://www.braunschweig.de/apps/pulp/result/parkhaeuser.geojson",
        attribution_contributor="Stadt Braunschweig",
    )

    STATUS_MAPPING = {
        "open": LotData.Status.open,
        "closed": LotData.Status.closed,
    }

    
    """
    geojson_response will be cached as get_lot_info and get_lot_data access it.
    As long as no braunschweig.geojson is stored, the lot info is extracted dynamically from
    the json response.
    """
    geojson_response = None

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        lots = []

        if not self.geojson_response:
            self.geojson_response = self.request_json(self.POOL.source_url)

        for feature in self.geojson_response["features"]:
            props = feature["properties"]

            status = self.STATUS_MAPPING.get(props["openingState"]) or LotData.Status.unknown
            if props.get("free") is None:
                status = LotData.Status.nodata

            lots.append(
                LotData(
                    id=name_to_id("braunschweig", props["name"]),
                    timestamp=timestamp,
                    lot_timestamp=self.to_utc_datetime(props["timestamp"]) if props.get("timestamp") else None,
                    status=status,
                    num_free=props.get("free"),
                    capacity=props.get("capacity"),
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lots = []
        self.geojson_response = self.request_json(self.POOL.source_url)
        for feature in self.geojson_response["features"]:
            props = feature["properties"]

            soup = bs4.BeautifulSoup(props["description"], features="html.parser")
            address = soup.find("h4").find_next_sibling("div")
            public_url = address.find("a")["href"].replace("http:", "https:")

            lots.append(
                LotInfo(
                    id=name_to_id("braunschweig", props["name"]),
                    name=props["name"],
                    capacity=props.get("capacity"),
                    address=get_soup_text(address),
                    longitude=feature["geometry"]["coordinates"][0],
                    latitude=feature["geometry"]["coordinates"][1],
                    public_url=public_url,
                    source_url=self.POOL.source_url,
                    has_live_capacity=True,
                )
            )

        return lots
