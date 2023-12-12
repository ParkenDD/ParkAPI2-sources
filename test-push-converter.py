"""
Copyright 2023 binary butterfly GmbH
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

from common.base_converter import BaseConverter, CsvConverter, JsonConverter, XlsxConverter, XmlConverter
from common.encoding import DefaultJSONEncoder
from common.models import ImportSourceResult

DATA_TYPES = {
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'csv': 'text/csv',
    'xml': 'application/xml',
    'json': 'application/json',
}


def main():
    parser = argparse.ArgumentParser(
        prog='ParkAPI-Sources Test Script',
        description='This script helps to develop ParkAPI-Sources converter',
    )
    parser.add_argument('source_uid')
    parser.add_argument('file_path')
    args = parser.parse_args()
    source_uid: str = args.source_uid
    file_path: Path = Path(args.file_path)

    if not file_path.is_file():
        sys.exit('Error: please add a file as second argument.')

    file_ending = None
    for ending in DATA_TYPES:
        if file_path.name.endswith(f'.{ending}'):
            file_ending = ending

    if file_ending is None:
        sys.exit(f'Error: invalid ending. Allowed endings are: {", ".join(DATA_TYPES.keys())}')

    if file_ending == 'xlsx':
        converter: XlsxConverter = get_converter(source_uid, XlsxConverter)  # type: ignore
        workbook = load_workbook(filename=str(file_path.absolute()))
        result: ImportSourceResult = converter.handle_xlsx(workbook)

    elif file_ending == 'csv':
        converter: CsvConverter = get_converter(source_uid, CsvConverter)  # type: ignore
        with file_path.open() as csv_file:
            rows = list(csv.reader(csv_file))
        result: ImportSourceResult = converter.handle_csv(rows)

    elif file_ending == 'xml':
        converter: XmlConverter = get_converter(source_uid, XmlConverter)  # type: ignore
        with file_path.open() as xml_file:
            root_element = etree.fromstring(xml_file.read(), parser=etree.XMLParser(resolve_entities=False))  # noqa: S320
        result: ImportSourceResult = converter.handle_xml(root_element)

    else:
        converter: JsonConverter = get_converter(source_uid, JsonConverter)  # type: ignore
        with file_path.open() as json_file:
            data = json.load(json_file)
        result: ImportSourceResult = converter.handle_json(data)

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


def get_converter(source_uid: str, class_to_find: Type[BaseConverter]) -> BaseConverter:
    package_dir = Path(__file__).parent.joinpath('v3')
    for _, module_name, _ in iter_modules([str(package_dir)]):
        # load all modules in converters
        module = import_module(f'v3.{module_name}')
        # look for attributes
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if not isclass(attribute):
                continue
            if not issubclass(attribute, class_to_find) or attribute is class_to_find:
                continue
            # at this point we can be sure that attribute is a BaseConverter child, so we can initialize and register it
            if attribute.source_info.id == source_uid:  # type: ignore
                return attribute()

    raise Exception('converter not found')


if __name__ == '__main__':
    main()
