"""
Original code and data by Kliemann
"""
from typing import List

import datetime 
import utm


from util import *


class Hamburg(ScraperBase):

    POOL = PoolInfo(
        id="hamburg",
        name="Hamburg",
        public_url="https://www.hamburg.de/parken/",
        source_url="https://geodienste.hamburg.de/HH_WFS_Verkehr_opendata?service=WFS&request=GetFeature&VERSION=1.1.0&typename=verkehr_parkhaeuser",
        timezone="UTC",
        attribution_contributor=None,
        attribution_license=None,
        attribution_url=None,
    )

    def get_lot_data(self) -> List[LotData]:
        lots = []

        soup = self.request_soup(self.POOL.source_url)
        last_updated = self.to_utc_datetime(soup.find('wfs:featurecollection')["timestamp"])

        for member in soup.find('wfs:featurecollection').find_all('gml:featuremember'):
            count = None
            try:
                count = int(member.find('de.hh.up:stellplaetze_gesamt').string)
            except AttributeError:
                pass

            free = None
            state = "nodata"
            situation = member.find('de.hh.up:situation')
            if situation and situation.string != "keine Auslastungsdaten":
                free = int(member.find('de.hh.up:frei').string)
                status = member.find('de.hh.up:status').string
                if status == "frei" or status == "besetzt":
                    state = "open"
                elif status == "störung":
                    state = "error"
                else:
                    state = "closed"

            lot_id = member.find('de.hh.up:id').string

            received = member.find('de.hh.up:received')
            if received:
                timestamp_string = received.string
                lot_timestamp = datetime.datetime.strptime(timestamp_string, "%d.%m.%Y, %H:%M")
            else:
                lot_timestamp = None

            lots.append(
                LotData(
                    timestamp=last_updated,
                    lot_timestamp=lot_timestamp,
                    # TODO: Note that original id is just 'lot_id' without the prefix
                    #   but that's not a good idea.
                    id=name_to_id("hamburg", lot_id),
                    capacity=count,
                    num_free=free,
                    status=state,
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        self.request_timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)

        lots = []

        for member in soup.find('wfs:featurecollection').find_all('gml:featuremember'):
            name = member.find('de.hh.up:name').string
            count = None
            try:
                count = int(member.find('de.hh.up:stellplaetze_gesamt').string)
            except AttributeError:
                pass

            lot_type = member.find('de.hh.up:art').string
            lot_type = guess_lot_type(lot_type)
            # In case of status=Störung, temporarilly no situtation is delivered
            has_live_capacity = not member.find('de.hh.up:situation') or member.find('de.hh.up:situation').string != "keine Auslastungsdaten"
            lot_id = member.find('de.hh.up:id').string
            address = ""
            try:
                address = member.find('de.hh.up:einfahrt').string
            except AttributeError:
                try:
                    address = member.find('de.hh.up:strasse').string
                    try:
                        address += " " + member.find('de.hh.up:hausnr').string
                    except (AttributeError, TypeError):
                        pass
                except AttributeError:
                    pass
            address = address.lstrip(" ,")

            coord_member = member.find('gml:pos')
            if coord_member:
                coord_string = coord_member.string.split()
                latlon = utm.to_latlon(float(coord_string[0]), float(coord_string[1]), 32, 'U')
                coords = {
                    "lat": latlon[0],
                    "lng": latlon[1]
                }
            else:
                coords = None

            lots.append(
                LotInfo(
                    id=name_to_id("hamburg", lot_id),
                    name=name,
                    type=lot_type,
                    address=address or None,
                    capacity=count,
                    has_live_capacity=has_live_capacity,
                    latitude=coords["lat"] if coords else None,
                    longitude=coords["lng"] if coords else None,
                )
            )

        return lots

