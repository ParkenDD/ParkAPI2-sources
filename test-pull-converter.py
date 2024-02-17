"""
Copyright 2024 binary butterfly GmbH
Use of this source code is governed by an MIT-style license that can be found in the LICENSE.txt.
"""

import argparse
import csv
import json
import sys
from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules
from typing import Type

from lxml import etree
from openpyxl.reader.excel import load_workbook

from common.base_converter import BaseConverter, CsvConverter, JsonConverter, PullConverter, XlsxConverter, XmlConverter
from common.encoding import DefaultJSONEncoder
from common.models import ImportSourceResult


def main():
    parser = argparse.ArgumentParser(
        prog='ParkAPI-Sources Test Script',
        description='This script helps to develop ParkAPI-Sources converter',
    )
    parser.add_argument('source_uid')
    args = parser.parse_args()
    source_uid: str = args.source_uid

    converter: PullConverter = get_converter(source_uid)

    result: ImportSourceResult = converter.get_static_parking_sites()
    # print_result(result)

    result: ImportSourceResult = converter.get_realtime_parking_sites()
    print_result(result)


def print_result(result: ImportSourceResult):
    if result.static_parking_site_inputs:
        print('### static data ###')  # noqa: T201
        for static_parking_site_input in result.static_parking_site_inputs:
            print(json.dumps(filter_none(static_parking_site_input.to_dict()), indent=2, cls=DefaultJSONEncoder))  # noqa: T201

    if result.realtime_parking_site_inputs:
        print('### realtime data ###')  # noqa: T201
        for realtime_parking_site_input in result.realtime_parking_site_inputs:
            print(json.dumps(filter_none(realtime_parking_site_input.to_dict()), indent=2, cls=DefaultJSONEncoder))  # noqa: T201

    print('### failures ###')  # noqa: T201
    print(f'static_parking_site_error_count: {result.static_parking_site_error_count}')  # noqa: T201
    print(f'realtime_parking_site_error_count: {result.realtime_parking_site_error_count}')  # noqa: T201
    print(f'static_parking_site_errors: {result.static_parking_site_errors}')  # noqa: T201
    print(f'realtime_parking_site_errors: {result.realtime_parking_site_errors}')  # noqa: T201


def filter_none(data: dict) -> dict:
    return {key: value for key, value in data.items() if value is not None}


def get_converter(source_uid: str) -> PullConverter:
    package_dir = Path(__file__).parent.joinpath('v3')
    for _, module_name, _ in iter_modules([str(package_dir)]):
        # load all modules in converters
        module = import_module(f'v3.{module_name}')
        # look for attributes
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if not isclass(attribute):
                continue
            if not issubclass(attribute, PullConverter) or attribute is PullConverter:
                continue
            # at this point we can be sure that attribute is a BaseConverter child, so we can initialize and register it
            if attribute.source_info.id == source_uid:  # type: ignore
                return attribute()

    raise Exception('converter not found')


if __name__ == '__main__':
    main()
