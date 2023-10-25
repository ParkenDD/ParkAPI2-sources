"""
Original code and data by Quint
"""
from typing import List

from util import *

import warnings


class Heidelberg(ScraperBase):

    POOL = PoolInfo(
        id="heidelberg",
        name="Heidelberg",
        public_url="https://parken.heidelberg.de",
        source_url="https://parken.heidelberg.de/v1/parking-location?key=3wU8F-5QycD-ZbaW9-R6uvj-xm1MG-X07ne",
        timezone="Europe/Berlin",
        attribution_contributor="Stadt Heidelberg",
        attribution_license=None,
        attribution_url=None,
    )

    ALLOW_SSL_FAILURE = "expired"
    HEADERS = {
        "Accept": "application/json; charset=utf-8",
        "Referer": "https://parken.heidelberg.de/",
    }

    def _should_ignore(self, parking_lot):
        if parking_lot['uid'] == '26':
            warnings.warn(f'Ignoring heidelbergp26kirchheim, as it has non static information')
            return True
        
        return False

    def get_lot_data(self) -> LotDataList[LotData]:
        timestamp = self.now()
        dataJSON = self.request_json(self.POOL.source_url)

        lots = LotDataList([], lot_error_count=0)

        last_updated = self.to_utc_datetime(dataJSON['data']['updated'])

        for parking_lot in dataJSON['data']['parkinglocations'] :
            # please keep the name in the geojson-file in the same form as delivered here (including spaces)
            parking_name = ('P'+str(parking_lot['uid'])+' '+parking_lot['name']).strip()
            parking_id = name_to_legacy_id(self.POOL.id, parking_name)

            # Note:
            if self._should_ignore(parking_lot):
                lots.lot_error_count += 1
                continue
            
            try:
                parking_capacity = int(parking_lot['parkingupdate']['total'])
                parking_occupied = int(parking_lot['parkingupdate']['current'])
                parking_state = LotData.Status.open

                if parking_lot['parkingupdate']['status'] == 'closed':
                    parking_state = LotData.Status.closed
                # TODO: There is also a parking_lot['is_closed'] flag
                #   which does not necessarily match the status above
                #   but the `parken.heidelberg.de` website actually
                #   considers both status to display a lot as closed
            except:
                lots.lot_error_count += 1
                parking_state = LotData.Status.nodata
                parking_occupied = None
                parking_capacity = None

            lots.append(
                LotData(
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    id=parking_id,
                    status=parking_state,
                    num_occupied=parking_occupied,
                    capacity=parking_capacity,
                )
            )

        return lots

    def get_lot_infos(self) -> LotInfoList[LotInfo]:
        lot_map = {
            lot.id: lot
            for lot in self.get_v1_lot_infos_from_geojson("Heidelberg")
        }

        dataJSON = self.request_json(self.POOL.source_url)

        lots = LotInfoList([], lot_error_count=0)

        for parking_lot in dataJSON['data']['parkinglocations'] :
            # please keep the name in the geojson-file in the same form as delivered here (including spaces)
            parking_name = ('P'+str(parking_lot['uid'])+' '+parking_lot['name']).strip()
            lot_id = name_to_legacy_id(self.POOL.id, parking_name)

            try:
                parking_capacity = int(parking_lot['parkingupdate']['total'])
            except:
                parking_capacity = None

            original_lot = vars(lot_map.get(lot_id)) if lot_id in lot_map else {}

            parking_id = name_to_legacy_id(self.POOL.id, parking_name)

            lat = original_lot.get("latitude")
            lon = original_lot.get("longitude")
            if lat is None or lon is None:
                # Note: the original ParkAPIv1 json had no coords, we explicitly set them here for no
                if parking_id == 'heidelbergp19campbellbarracks':
                    lat = 49.38794
                    lon = 8.68104
                else:
                    lots.lot_error_count += 1
                    warnings.warn(f"Lot '{parking_id}' has no coords. Skipping")
                    continue

            lots.append(
                LotInfo(
                    id=parking_id,
                    type=original_lot.get("type") or 'garage',
                    name=parking_name,
                    capacity=parking_capacity,
                    public_url=parking_lot.get("website"),
                    has_live_capacity=True,
                    address=parking_lot["address"].replace(" ,", ",").strip(" ,").replace(", ", "\n"),
                    latitude=lat,
                    longitude=lon,
                )
            )

        return lots
