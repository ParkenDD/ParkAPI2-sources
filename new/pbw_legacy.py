"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from util import ScraperBase, PoolInfo
from util.legacy_mixin import LegacyMixin
from v3.pbw import PbwPullConverter


class PbwLegacy(LegacyMixin, PbwPullConverter, ScraperBase):

    POOL = PoolInfo(
        id='pbw_legacy',
        name='PBW',
        public_url='https://www.pbw.de',
    )
