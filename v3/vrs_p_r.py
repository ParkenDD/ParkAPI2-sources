"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone
from typing import Any

import pyproj
from openpyxl.cell import Cell

from common.base_converter import NormalizedXlsxConverter
from util import SourceInfo


class VrsParkAndRideConverter(NormalizedXlsxConverter):
    proj: pyproj.Proj = pyproj.Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=True)

    source_info = SourceInfo(
        id='vrs-p-r',
        name='Verband Region Stuttgart: Park and Ride',
        public_url='https://www.region-stuttgart.org/de/bereiche-aufgaben/mobilitaet/park-ride/',
    )

    # If there are more tables with our defined format, it would make sense to move header_row to XlsxConverter
    header_row: dict[str, str] = {
        'AnlagenNr': 'uid',
        'AnlageNamen': 'name',
        'Art_der_Anlage': 'type',
        'BetreiberName': 'operator_name',
        'POINT_X': 'lon_utm',
        'POINT_Y': 'lat_utm',
        'Anzahl_Stellplätze_gesamt': 'capacity',
        'Anzahl_Carsharing_Stellplätze': 'capacity_carsharing',
        'Anzahl_E_Ladestationen': 'capacity_charging',
        'Anzahl_Behindertenparkplätze': 'capacity_disabled',
        'Gebühren': 'has_fee',
        'Durchgehend_geöffnet': 'opening_hours_is_24_7',
        # Maximale_Parkdauer is there, but is not parsable
        # Other opening times are there, but not parsable
    }

    def map_row_to_parking_site_dict(self, mapping: dict[str, int], row: list[Cell]) -> dict[str, Any]:
        parking_site_dict: dict[str, str] = {}
        for field in mapping.keys():
            parking_site_dict[field] = row[mapping[field]].value

        coordinates = self.proj(float(parking_site_dict.get('lon_utm')), float(parking_site_dict.get('lat_utm')), inverse=True)
        parking_site_dict['lat'] = coordinates[1]
        parking_site_dict['lon'] = coordinates[0]

        parking_site_dict['type'] = self.type_mapping.get(parking_site_dict.get('type'))
        parking_site_dict['static_data_updated_at'] = datetime.now(tz=timezone.utc).isoformat()

        return parking_site_dict
