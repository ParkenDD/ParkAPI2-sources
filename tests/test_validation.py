import unittest
from copy import deepcopy
from typing import Optional, Tuple, List

from util.validate import validate_snapshot

SNAPSHOTS = {
    "valid": {
        "pool": {
            "id": "pool-1",
            "name": "Pool 1",
            "public_url": "https://example.com",
            "timezone": "Europe/Berlin",
            "source_url": None,
            "attribution_license": "CC-0",
            "attribution_contributor": "The City Of Example",
            "attribution_url": "https://example.com/license"
        },
        "lots": [
            {
                "id": "pool-1-lot-1",
                "name": "Lot 1",
                "type": "lot",
                "public_url": None,
                "source_url": "https://example.com/source",
                "address": "Some\nAddress",
                "capacity": 100,
                "has_live_capacity": True,
                "latitude": 50.,
                "longitude": 10.,
                "timestamp": "2021-11-29T09:10:30",
                "lot_timestamp": "2021-11-29T09:09:36",
                "status": "open",
                "num_free": 60,
                "num_occupied": 40,
            },
        ]
    },
    "warnings": {
        "pool": {
            "id": "pool-2",
            "name": "Pool 2",
            "public_url": "https://example.com",
            "timezone": "Europe/Berlin",
            "source_url": None,
            "attribution_license": None,                    # missing license
            "attribution_contributor": None,
            "attribution_url": None,
        },
        "lots": [
            {
                "id": "pool-2-lot-1",
                "name": "Lot 1",
                "type": "unknown",                          # not a good type
                "public_url": None,
                "source_url": "https://example.com/source",
                "address": None,                            # no address
                "capacity": None,                           # no capacity
                "has_live_capacity": False,
                "latitude": None,                           # no coordinates
                "longitude": None,
                "timestamp": "2021-11-29T09:10:30",
                "lot_timestamp": None,
                "status": "unknown",
                "num_free": None,                           # no data
                "num_occupied": None,
            },
        ]
    }
}


class TestValidation(unittest.TestCase):
    maxDiff = None

    @classmethod
    def split_errors_warnings(cls, validation: dict) -> Tuple[List[dict], List[dict]]:
        validations = validation["validations"]
        return (
            list(filter(lambda v: v["priority"] == 0, validations)),
            list(filter(lambda v: v["priority"] != 0, validations))
        )

    def test_validation_errors(self):
        self.assertEqual(
            [{"message": "'pool' is a required property: {}", "path": "", "priority": 0}],
            self.split_errors_warnings(validate_snapshot({}))[0]
        )

        self.assertEqual(
            [{"message": "[] is not of type 'object': []", "path": "pool", "priority": 0}],
            self.split_errors_warnings(validate_snapshot({
                "pool": [],
                "lots": [],
            }))[0]
        )

        self.assertEqual(
            [{"message": "'id' is a required property: {}", "path": "pool", "priority": 0}],
            self.split_errors_warnings(validate_snapshot({
                "pool": {},
                "lots": [],
            }))[0]
        )

        self.assertEqual(
            [],
            self.split_errors_warnings(validate_snapshot(SNAPSHOTS["valid"]))[0]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        bad_pool_id = "x" * 65
        snapshot["pool"]["id"] = bad_pool_id

        self.assertEqual(
            [{"message": f"'{bad_pool_id}' is too long: {bad_pool_id}", "path": "pool.id", "priority": 0}],
            self.split_errors_warnings(validate_snapshot(snapshot))[0]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["lots"][0]["source_url"] = 23
        self.assertEqual(
            [{"message": "23 is not of type 'string': 23", "path": "lots.0.source_url", "priority": 0}],
            self.split_errors_warnings(validate_snapshot(snapshot))[0]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["pool"]["source_url"] = "www.example.com"
        self.assertEqual(
            [{"message": "'www.example.com' does not match '^[a-z]+://.+': www.example.com", "path": "pool.source_url", "priority": 0}],
            self.split_errors_warnings(validate_snapshot(snapshot))[0]
        )

    def test_validation_warnings(self):
        self.assertEqual(
            [],
            self.split_errors_warnings(validate_snapshot(SNAPSHOTS["valid"]))[1]
        )

        self.assertEqual(
            [
                {"message": "Pool 'pool-2' should have 'attribution_license'", "path": "pool.attribution_license", "priority": 3},
                {"message": "Pool 'pool-2' should have 'attribution_contributor'", "path": "pool.attribution_contributor", "priority": 3},
                {"message": "Pool 'pool-2' should have 'attribution_url'", "path": "pool.attribution_url", "priority": 3},
                {"message": "Lot 'pool-2-lot-1' should have a type other than 'unknown'", "path": "lots.0.type", "priority": 2},
                {"message": "Lot 'pool-2-lot-1' should have 'latitude'", "path": "lots.0.latitude", "priority": 1},
                #{"message": "Lot 'pool-2-lot-1' should have 'longitude'", "path": "lots.0.longitude", "priority": 1},
                {"message": "Lot 'pool-2-lot-1' should have 'address'", "path": "lots.0.address", "priority": 1},
                {"message": "Lot 'pool-2-lot-1' should have 'capacity'", "path": "lots.0.capacity", "priority": 1},
                {"message": "Lot 'pool-2-lot-1' should have 'num_free' or 'num_occupied'", "path": "lots.0.num_free", "priority": 4}
            ],
            self.split_errors_warnings(validate_snapshot(SNAPSHOTS["warnings"]))[1]
        )

        snapshot = deepcopy(SNAPSHOTS["valid"])
        snapshot["lots"][0]["num_free"] = None
        snapshot["lots"][0]["capacity"] = None  # only specifying num_occupied

        self.assertEqual(
            [
                {"message": "Lot 'pool-1-lot-1' should have 'capacity'", "path": "lots.0.capacity", "priority": 1},
                {"message": "Lot 'pool-1-lot-1' should have 'capacity' when defining 'num_occupied'", "path": "lots.0.capacity", "priority": 2}
            ],
            self.split_errors_warnings(validate_snapshot(snapshot))[1]
        )
