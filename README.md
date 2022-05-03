# Data sources for [ParkAPI2](https://github.com/ParkenDD/ParkAPI2)

[![test](https://github.com/ParkenDD/ParkAPI2-sources/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/ParkenDD/ParkAPI2-sources/actions/workflows/tests.yml)

This repository hosts the data sources (downloader, scraper) for the
[parkendd.de](https://parkendd.de/) service which lists the 
number of free spaces of parking lots across Germany and abroad.

## Usage

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


## Contribution

Please feel free to ask questions by opening a 
[new issue](https://github.com/ParkenDD/ParkAPI2-sources/issues).

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
