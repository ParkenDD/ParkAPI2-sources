from typing import List

import pyproj

from util import *


class Stuttgart(DatexScraperMixin, ScraperBase):
    """
    This Scraper scrapes the re-published datex publications of the city of Stuttgart, to avoid
    the currently still necessary certifcates for MDM data portal access.

    Note: the static publication currently doesn't publish some important information like coordinates,
    type, address. I (Holger Bruch) contacted the data owner and asked for additional information in the
    publication.

    In case this information will not be provided soon, the geojson will need to be enhanced manually :-/
    """

    POOL = PoolInfo(
        id='stuttgart',
        name='Stuttgart',
        public_url='https://service.mdm-portal.de/mdm-portal-application/publDetail.do?publicationId=3059002',
        source_url='https://data.mfdz.de/DATEXII_Parkdaten_dynamisch_Stuttgart/body.xml',
        attribution_contributor='Landeshauptstadt Stuttgart, Tiefbauamt, mirrored by MFDZ',
        attribution_license='dl-de/by-2-0',
    )

    STATIC_LOTS_URL = 'https://data.mfdz.de/DATEXII_Parkdaten_statisch_Stuttgart/body.xml'

    UTM32_PROJ = pyproj.Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=True)

    def _get_facility_coords(self, facility):
        umt32_coord = super()._get_facility_coords(facility)

        if umt32_coord == None:
            return None

        wgs84_coord = self.UTM32_PROJ(umt32_coord['longitude'], umt32_coord['latitude'], inverse=True)

        return {'latitude': round(wgs84_coord[1], 6), 'longitude': round(wgs84_coord[0], 6)}
