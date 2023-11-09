# Data sources for [ParkAPI2](https://github.com/ParkenDD/ParkAPI2)

[![test](https://github.com/ParkenDD/ParkAPI2-sources/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/ParkenDD/ParkAPI2-sources/actions/workflows/tests.yml)

This repository hosts the data sources (downloader, scraper, converter) for the [parkendd.de](https://parkendd.de/) service which lists 
the number of free spaces of parking lots across Germany and abroad.

The repository for the database and API is [ParkAPI2](https://github.com/ParkenDD/ParkAPI2) or ParkAPIv3.


## Usage

There are two approaches to get Data into ParkAPI:

* Either, you poll data from a data source. This can be a website your scrape as well as a structured data source.
  In both cases you do one or more HTTP requests against another server, analyze and validate the polled data
  transform it into ParkAPIs on data model.
* Or, you have an external service which pushes data to an endpoint you provide. Then you have all the data in your 
  system and have to analyze, validate and transform it. The endpoint is provided by a web-service, usually ParkAPIv3,
  but the actual data transformation is done in ParkAPI-sources.


### Polling / Scraping data

The [scraper.py](scraper.py) file is a command-line tool for 
developing, testing and finally integrating new data sources.
It's output is always [json](https://www.json.org/) formatted.

Each data source is actually called a `Pool` and usually represents
one website from which lot data is collected.

#### Listing

To view the list of all pool IDs, type:
```bash
python scraper.py list
```

#### Scraping 

To download and extract data, type:
```bash
python scraper.py scrape [-p <pool-id> ...] [--cache]
```

The `-p` or `--pools` parameter optionally filters the available sources
by a list of pool IDs. 

The optional `--cache` parameter caches all web requests which is a fair thing to do
during scraper development. If you have old cache files and want to create new ones
then run with `--cache write` to fire new web requests and write the new files and then
use `--cache` afterwards.


#### Validation

```bash
python scraper.py validate [-mp <max-priority>] [-p <pool-id> ...] [--cache]
```

The `validate` command validates the resulting snapshot data against the 
[json schema](schema.json) and prints warnings for fields that *should* be defined.
Use `-mp 0` or `--max-priority 0` to only print severe errors and 
`--max-priority 1` to include warnings about missing data in the most
important fields like `latitude`, `longitude`, `address` and `capacity`.

Use `validate-text` to print the data in human-friendly format. 


### Pushed data

ParkApi-sources cannot have REST entrypoints, so it provides a helper script which helps to handle dumped requests.
This can be eg an Excel or a JSON file which will be pushed against the REST endpoint, but if we stay in our 
ParkAPI2-sources project, it has to exist as a file and will be used as command line parameter for our 
`test-push-converter.py`.

ParkAPIv3 converters are build for a deep integration into another system. Therefore, input and output are Python
objects including all advantages of having defined data formats beyond JSON. `test-push-converter.py` is the script 
which uses these interfaces the way a third application would do.

ParkAPIv3 converters come with a quite strict validation in order to prevent invalid input data. It also comes with some
base classes to help you with specific data formats.

At the moment, ParkAPIv3 converter support a lot more fields than ParkAPI2-converters. Most of the fields will be
backported to the ParkAPIv2 converters, though.

Usage of `test-push-converter.py` is quite simple: it requires the data source uid and the path to the file you want to 
handle:

```
python test-push-converter.py some-identifier ./temp/some-excel.xlsx
```


## Contribution

Please feel free to ask questions by opening a 
[new issue](https://github.com/ParkenDD/ParkAPI2-sources/issues).

### Polling / Scraping data

A data source needs to define a `PoolInfo` object and 
for each parking lot a `LotInfo` and a `LotData` object
(defined in [util/structs.py](util/structs.py)). 
The python file that defines the source can be placed at 
the project root or in a sub-directory and is automatically
detected by `scraper.py` as long as the `util.ScraperBase`
class is sub-classed.

An example for scraping an html-based website:

```python
from typing import List
from util import *


class MyCity(ScraperBase):
    
    POOL = PoolInfo(
        id="my-city",
        name="My City",
        public_url="https://www.mycity.de/parken/",
        source_url="https://www.mycity.de/parken/auslastung/",
        attribution_license="CC-0",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)
        
        lots = []
        for div in soup.findall("div", {"class": "special-parking-div"}):

            # ... get info from html dom

            lots.append(
                LotData(
                    id=name_to_id("mycity", lot_id),
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    status=state,
                    num_occupied=lot_occupied,
                    capacity=lot_total,
                )
            )

        return lots
```

The `PoolInfo` is a static attribute of the scraper class and
the `get_lot_data` method must return a list of `LotData` objects. 
It's really basic and does not contain any further information about the 
parking lot, only the ID, status, free spaces and total capacity.


### Meta information

Additional lot information is either taken from a 
[geojson](https://geojson.org/) file or the `get_lot_infos` method
of the scraper class. The `scraper.py` will merge the `LotInfo` and
the `LotData` together to create the final output which must
comply with the [json schema](schema.json).

The geojson file should have the same name as the scraper file, 
e.g. `example.geojson`. **If the file exists**, it will be used and 
it's `properties` must fit the `util.structs.LotInfo` object.
**If it's not existing**, the method `get_lot_infos` on the scraper 
class will be called an should return a list of `LotInfo` objects. 

*Some* websites do provide most of the required information and it might 
be easier to scrape it from the web pages instead of writing the geojson 
file by hand. However, it might not be good practice to scrape this info 
every other minute. To generate a geojson file from the lot_info data:

```bash
# delete the old file if it exists
rm example.geojson  
# run `get_lot_infos` and write to geojson 
#   (and filter for the `example` pool) 
python scraper.py write-geojson -p example
``` 

The command `show-geojson` will write the contents to stdout for inspection.


### Pushed data

Pushed data is handled by converters which are children of `BaseConverter`. There are four different abstract base 
classes for JSON, XML, CSV and XLSX which do already part of the loading, eg the XLSX base class already loads the data
and starts with a `openpyxl` `Workbook`. To implement a new data source, you have to build the converter which accepts
the specific data and returns a validated `StaticParkingSiteInput`s or `RealtimeParkingSiteInput`s bound together with
extended information about errors in a `ImportSourceResult`.

Any `BaseConverter` needs (just like the `ScraperBase`) a property called `source_info` in order to provide basic
information as `SourceInfo` instance (which a `PoolInfo` for now, but may be extended). The unique identifier there
are the one you use in `test-push-converter.py`.

A new converter will look like this:

```python
class MyNewConverter(XlsxConverter):
    source_info = SourceInfo(
        id='my-unique-id',
        name='My Name',
        public_url='https://an-url.org',
    )

    def handle_xlsx(self, workbook: Workbook) -> ImportSourceResult:
        result = ImportSourceResult()
        # do your specific handling with workbook
        return result
```

While `./common` contains all helpers and base classes, actual converters should be put into the new `./v3` folder.

If you identify code which might end up into the base classes (or even justify a new base class eg for handling a whole 
class of Excel files which all look quite identical), feel free to add new base classes to the base class library in 
`./common/base_converter`.

Please keep in mind that all new code should run through `ruff` and `black` to maintain a nice style. 
