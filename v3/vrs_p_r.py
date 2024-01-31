"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from common.base_converter import NormalizedXlsxConverter
from util import SourceInfo


class VrsParkAndRideConverter(NormalizedXlsxConverter):
    source_info = SourceInfo(
        id='vrs-p-r',
        name='Verband Region Stuttgart: Park and Ride',
        public_url='https://www.region-stuttgart.org/de/bereiche-aufgaben/mobilitaet/park-ride/',
    )
