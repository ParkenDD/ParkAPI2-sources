"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

from datetime import datetime, timezone

from common.validators import StaticParkingSiteInput
from v3.bahn_v2.validators import BahnParkingSiteCapacityType, BahnParkingSiteInput, NameContext


class BahnMapper:
    @staticmethod
    def map_static_parking_site(bahn_input: BahnParkingSiteInput) -> StaticParkingSiteInput:
        static_parking_site_input = StaticParkingSiteInput(
            uid=str(bahn_input.id),
            name=next(iter(name_input.name for name_input in bahn_input.name if name_input.context == NameContext.NAME)),
            lat=bahn_input.address.location.latitude,
            lon=bahn_input.address.location.longitude,
            operator_name=bahn_input.operator.name,
            address=f'{bahn_input.address.streetAndNumber}, {bahn_input.address.zip} {bahn_input.address.city}',
            capacity=bahn_input.capacity,
            type=bahn_input.type.name.to_parking_site_type_input(),
            has_realtime_data=False,  # TODO: change this as soon as Bahn offers proper rate limits
            static_data_updated_at=datetime.now(tz=timezone.utc),
            public_url=bahn_input.url,
        )
        if bahn_input.access.openingHours.is24h:
            static_parking_site_input.opening_hours = '24/7'

        for capacity_data in bahn_input.capacity:
            if capacity_data.type == BahnParkingSiteCapacityType.PARKING:
                static_parking_site_input.capacity = int(round(capacity_data.total))
            elif capacity_data.type == BahnParkingSiteCapacityType.HANDICAPPED_PARKING:
                static_parking_site_input.capacity_disabled = int(round(capacity_data.total))

        return static_parking_site_input
