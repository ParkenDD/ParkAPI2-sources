"""
Original code and data by Quint
"""
import re
from urllib.parse import urljoin
from typing import List, Tuple, Generator, Optional, Dict

import bs4

from util import *


class Karlsruhe(ScraperBase):

    POOL = PoolInfo(
        id="karlsruhe",
        name="Karlsruhe",
        public_url="https://web1.karlsruhe.de/service/Parken/",
        source_url="",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Karlsruhe",
        attribution_license=None,
        attribution_url=None,
    )

    RE_CAPACITY = re.compile(r"Insgesamt (\d+) Parkplätze")

    id_mapping: Dict[str, str] = {
        'karlsruhestaatstheater': 'karlsruheamstaatstheater',
        'karlsruhegaleriakarlsruhe': 'karlsruhekarstadt',
        'karlsruhekreuzstrasse': 'karlsruhekreuzstrasseca',
        'karlsruhemendelssohnplatz': 'karlsruhemendelssohnplatzscheckin',
    }

    def get_lot_data(self) -> List[LotData]:
        """
        Expects parking lot data in the format:

        <div class="parkhaus">
            <br />
            <div class="fuellstand p-style">
                044
                <br />
                <span class="">
                    frei
                    <br />
                </span>
            </div>
            <a href="detail.php?id=S01" class='link-style website-link' title='Parkhaus Landesbibliothek'>
                Landesbibliothek
            </a>
            <br />
            <img src="pix-leer.gif" width="30" height="30" title="Parkhaus mit freien Plätzen" align="left" vspace="2"/>
            Insgesamt 86 Parkplätze.
        </div>
        """

        soup = self.request_soup(self.POOL.public_url)

        lots = []
        timestamp = self.now()

        lots_elems = soup.find_all( 'div', class_='parkhaus')
        for parking_lot in lots_elems :
            lot_name = parking_lot.find('a').text
            
            status = LotData.Status.open
            num_free = 0
            parking_fuellstand = parking_lot.find( 'div', class_='fuellstand')
            try :
                if ( parking_fuellstand == None ) :
                    status = LotData.Status.nodata
                else :
                    temp = parking_fuellstand.text.split()
                    num_free = int(temp[0])
            except :
                status = LotData.Status.unknown

            num_total = 0
            
            match_num_total = self.RE_CAPACITY.search(parking_lot.text)
            if match_num_total:
                num_total = int_or_none(match_num_total.groups()[0])
                if num_total == 0:
                    status = LotData.Status.nodata
            else:
                num_free, num_total = None, None

            legacy_id = self.name_to_legacy_id(lot_name)
            lots.append(
                LotData(
                    timestamp=timestamp,
                    #lot_timestamp=lot_timestamp,
                    id=self.id_mapping.get(legacy_id, legacy_id),
                    status=status,
                    num_free=num_free,
                    capacity=num_total,
                )
            )
        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        """
        Generates current lot information from v1 data, updated by 
        data parsed from current public_url and detail pages linked there.
        Only currently existing parking lots are returned, though their IDs 
        might have been mapped to their v1 names for backward compatibility.
        """
        v1_lot_map = {
            lot.id: lot
            for lot in self.get_v1_lot_infos_from_geojson("Karlsruhe")
        }

        lots = []
        soup = self.request_soup(self.POOL.public_url)
        lots_elems = soup.find_all( 'div', class_='parkhaus')
        for parking_lot in lots_elems:
            lot_name = parking_lot.find('a').text
            lot_id = self.name_to_legacy_id(lot_name)
            public_url = urljoin(self.POOL.public_url, parking_lot.find('a')['href'])
            details = self._get_lot_details(public_url)
            
            v1_lot = v1_lot_map.get(lot_id)
            v1_lot_props = vars(v1_lot) if v1_lot else {}
            
            # kwargs is the merge of multiple data sources, defaults are 
            # overridden by v1 info, which are overridden by parsed data
            kwargs = {"type": "garage"} | v1_lot_props | dict(
                    id=self.id_mapping.get(lot_id, lot_id),
                    name=lot_name,
                    has_live_capacity=True,
                    capacity=v1_lot_props.get("total"),
                    public_url=public_url,
                ) | details
            lots.append(LotInfo(**kwargs))

        return lots

    def _get_lot_details(self, url) -> dict:
        """
        Retrieves information from lot details page, i.e. capacity and address
        :param url, url of the details page
        :return 
        """
        details_soup = self.request_soup(url)
        td_mappings = {"Adresse": "address", "Kurzparker-Stellplätze": "capacity"}
        trs = details_soup.find_all("tr")

        details = {}
        for tr in trs:
            key = td_mappings.get(tr.td.text)
            if key == "capacity":
                details[key] = int_or_none(tr.td.find_next_sibling("td").text)
            elif key == "address":
                details[key] = "\n".join(tr.td.find_next_sibling("td").strings).replace('\xa0', ' ')

        return details

