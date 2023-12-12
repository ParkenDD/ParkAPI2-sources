"""
Copyright 2023 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import pyproj
from lxml.etree import Element
from validataclass.exceptions import ValidationError

from common.base_converter import XmlConverter
from common.exceptions import ImportParkingSiteException
from common.models import ImportSourceResult
from common.validators import StaticParkingSiteInput, RealtimeParkingSiteInput
from util import SourceInfo


class StuttgartConverter(XmlConverter):
    proj: pyproj.Proj = pyproj.Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=True)

    source_info = SourceInfo(
        id='stuttgart',
        name='Stuttgart',
        public_url='https://service.mdm-portal.de/mdm-portal-application/publDetail.do?publicationId=3059002',
        attribution_contributor='Landeshauptstadt Stuttgart, Tiefbauamt',
        attribution_license='dl-de/by-2-0',
    )

    def handle_xml(self, root: Element) -> ImportSourceResult:
        data = self.xml_helper.xml_to_dict(
            root,
            conditional_remote_type_tags=[
                ('values', 'value'),
                ('periodName', 'values'),
                ('parkingFacilityName', 'values'),
                ('openingTimes', 'period'),
            ],
            ensure_array_keys=['parkingFacility', 'parkingFacilityStatus'],
        )
        items_base = data.get('d2LogicalModel', {}).get('payloadPublication', {}).get('genericPublicationExtension', {})
        if items_base.get('parkingFacilityTablePublication'):
            static_items = items_base.get('parkingFacilityTablePublication', {}).get('parkingFacilityTable', {}).get('parkingFacility', [])

            static_parking_sites: list[StaticParkingSiteInput] = []
            errors: list[ImportParkingSiteException] = []
            for static_item in static_items:
                try:
                    static_parking_sites.append(self._handle_static_item(static_item))
                except ValidationError as e:
                    errors.append(
                        ImportParkingSiteException(
                            uid=static_item.get('id'),
                            message=str(e.to_dict()),
                        )
                    )

            return self.generate_import_source_result(
                static_parking_site_inputs=static_parking_sites,
                static_parking_site_errors=errors,
            )

        if items_base.get('parkingFacilityTableStatusPublication'):
            realtime_items = items_base.get('parkingFacilityTableStatusPublication', {}).get('parkingFacilityStatus', {})
            realtime_parking_sites: list[RealtimeParkingSiteInput] = []
            errors: list[ImportParkingSiteException] = []

            for realtime_item in realtime_items:
                try:
                    realtime_parking_sites.append(self._handle_realtime_item(realtime_item))
                except ValidationError as e:
                    errors.append(
                        ImportParkingSiteException(
                            uid=realtime_item.get('id'),
                            message=str(e.to_dict()),
                        ),
                    )

            return self.generate_import_source_result(
                realtime_parking_site_inputs=realtime_parking_sites,
                realtime_parking_site_errors=errors,
            )

    def _handle_static_item(self, item: dict) -> StaticParkingSiteInput:
        input_data = {
            'uid': item.get('id'),
            'name': item.get('parkingFacilityName'),
            'has_realtime_data': True,
            'capacity': int(item.get('totalParkingCapacity')),
            'static_data_updated_at': item.get('parkingFacilityRecordVersionTime'),
        }

        # Coordinates
        coordinates_base = item.get('facilityLocation', {}).get('locationForDisplay', {})
        coordinates = self.proj(float(coordinates_base.get('longitude')), float(coordinates_base.get('latitude')), inverse=True)
        input_data['lat'] = coordinates[1]
        input_data['lon'] = coordinates[0]

        # max_height
        height_base = item.get('characteristicsOfPermittedVehicles', {}).get('heightCharacteristic', {})
        if height_base.get('comparisonOperator') == 'lessThan' and height_base.get('vehicleHeight'):
            input_data['max_height'] = int(float(height_base.get('vehicleHeight')) * 1000)

        # Sub-Capacities
        mapping: list[tuple[tuple[str, str], str]] = [
            (('personTypeForWhichSpacesAssigned', 'disabled'), 'capacity_disabled'),
            (('personTypeForWhichSpacesAssigned', 'families'), 'capacity_family'),
            (('personTypeForWhichSpacesAssigned', 'women'), 'capacity_woman'),
            (('characteristicsOfVehiclesForWhichSpacesAssigned', {'fuelType': 'battery'}), 'capacity_charging'),
        ]

        for sub_capacity in item.get('assignedParkingSpaces', []):
            for key, value in sub_capacity.get('assignedParkingSpaces', {}).get('descriptionOfAssignedParkingSpaces', {}).items():
                for map_key_components, final_key in mapping:
                    if map_key_components[0] == key and map_key_components[1] == value:
                        input_data[final_key] = int(sub_capacity.get('assignedParkingSpaces')['numberOfAssignedParkingSpaces'])
                        break

        # TODO: parse opening times with more information, for now they are broken

        return self.static_parking_site_validator.validate(input_data)

    def _handle_realtime_item(self, item: dict) -> RealtimeParkingSiteInput:
        input_data = {
            'uid': item.get('parkingFacilityReference', {}).get('id'),
            'realtime_capacity': int(item.get('totalNumberOfVacantParkingSpaces', 0)),
            'realtime_data_updated_at': item.get('parkingFacilityStatusTime'),
        }

        status_list: list[str] = item.get('parkingFacilityStatus', [])
        if 'open' in status_list:
            input_data['realtime_opening_status'] = 'open'
        elif 'closed' in status_list:
            input_data['realtime_opening_status'] = 'closed'

        return self.realtime_parking_site_validator.validate(input_data)
