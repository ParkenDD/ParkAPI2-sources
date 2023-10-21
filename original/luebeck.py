"""
Original code and data by Thalheim

This is a rewrite, not using the original geojson!

Former urls were:
- http://www.kwl-luebeck.de/parken/aktuelle-parkplatzbelegung/
- http://kwlpls.adiwidjaja.info

both not working anymore.

New website supplies all meta information and the new geojson
is made from scratch.

The legacy IDs are kept as far as the lot name did not change.
"""
import urllib.parse
from typing import List

from util import *


class Luebeck(ScraperBase):

    POOL = PoolInfo(
        id="luebeck",
        name="Lübeck",
        public_url="https://www.parken-luebeck.de/",
        source_url=None,
        timezone="Europe/Berlin",
        attribution_contributor="KWL GmbH",
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        """
        Expects lot data in a structure like the following:

        <div class="location-list--item info-18 location list item list-Parkplatz Straßenrand list-PPS" data-location-uid="18" data-lat="53.86631000" data-lng="10.67123000" data-art="Parkplatz Straßenrand" data-city="Lübeck" data-title="Am Bahnhof / Handelshof - Parkplatz Straßenrand" data-live="" data-plz="23558 "> 
            <div class="location-list-inner"> 
                <header> 
                    <div class="header"> 
                        <a title="Parkplatz Straßenrand" rel="location-id-18" href="/detail/pps-am-bahnhof-handelshof/"> 
                            <span class="location-list-item" data-art="Parkplatz Straßenrand"> 
                                <span class="header h4 name loocation--name">Am Bahnhof / Handelshof</span> | 
                                <span>Parkplatz Straßenrand</span> 
                            </span> 
                        </a> 
                    </div> 
                </header> 
                <div class="location--data" style="display: none;"> 
                    <span class="name">Am Bahnhof / Handelshof </span>
                    <span class="art">Parkplatz Straßenrand</span>
                    <span class="city">Lübeck</span> 
                </div> 
                <div class="location--info"> 
                    <span class="opening">durchgehend</span> 
                    <div class="services"> 
                        <span class="service-7" title="MWST frei"></span> 
                        <span class="phoneparking" title="Handyparken"></span> 
                        <span class="logo-kwl"></span> 
                    </div>
                </div> 
            </div> 
            <div class="location--availability-info"> 
                <div class="data-live-error">Keine Live-Daten verfügbar <br />
                    <span class="free-spots">/ 12</span>
                </div> 
            </div> 
        </div> 
        """

        timestamp = self.now()
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_tag in soup.find("div", id="infos").find_all("div", class_="location-list--item"):

            free_tag = lot_tag.find("div", class_="free-live-spots")
            if not free_tag:
                continue

            lot_name = lot_tag["data-title"].split(" - ", 1)[0]
            free_spots_tag = lot_tag.find("div", class_="free-spots")
            if not free_spots_tag:
                status = LotData.Status.closed
                num_free = 0
                capacity = 0
            else:    
                num_free = int_or_none(free_tag.text)
                capacity = int_or_none(lot_tag.find("div", class_="free-spots").text.strip("/ "))
                status = LotData.Status.open

                if num_free is None:
                    status = LotData.Status.nodata

            lots.append(
                LotData(
                    timestamp=timestamp,
                    id=name_to_legacy_id("luebeck", lot_name),
                    status=status,
                    num_free=num_free,
                    capacity=capacity,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        soup = self.request_soup(self.POOL.public_url)

        lots = []
        for lot_tag in soup.find("div", id="infos").find_all("div", class_="location-list--item"):

            free_tag = lot_tag.find("div", class_="free-live-spots")
            if not free_tag:
                continue

            capacity = int_or_none(lot_tag.find("div", class_="free-spots").text.strip("/ "))
            lot_name = lot_tag["data-title"].split(" - ", 1)[0]

            public_url = urllib.parse.urljoin(self.POOL.public_url, lot_tag.find("a")["href"])

            lots.append(
                LotInfo(
                    id=name_to_legacy_id("luebeck", lot_name),
                    name=lot_name,
                    type=guess_lot_type(lot_tag["data-art"]),
                    capacity=capacity,
                    latitude=float_or_none(lot_tag["data-lat"]),
                    longitude=float_or_none(lot_tag["data-lng"]),
                    public_url=public_url,
                    has_live_capacity=True,
                    **self.get_lot_page_infos(public_url),
                )
            )

        return lots

    def get_lot_page_infos(self, url: str) -> dict:
        soup = self.request_soup(url)

        address = get_soup_text(soup.find("div", class_="long-parking-address"))
        if address.startswith("Adresse"):
            address = address[7:]
        address = address.strip()

        return {
            "address": address
        }
