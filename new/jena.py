import pytz
from datetime import datetime, time
from typing import List

from util import *


class Jena(ScraperBase):

    POOL = PoolInfo(
        id="jena",
        name="Jena",
        public_url="https://mobilitaet.jena.de/de/parken",
        source_url="https://opendata.jena.de/data/parkplatzbelegung.xml",
        timezone="Europe/Berlin",
        attribution_url="https://opendata.jena.de/dataset/parken",
        attribution_license="dl-de/by-2-0",
        attribution_contributor="Kommunal Service Jena",
    )

    def get_lot_data(self) -> List[LotData]:
        lot_vacancy = self.request_soup(url = self.POOL.source_url, parser = "xml")
        lot_info = self.request_json("https://opendata.jena.de/dataset/1a542cd2-c424-4fb6-b30b-d7be84b701c8/resource/76b93cff-4f6c-47fa-ab83-b07d64c8f38a/download/parking.json")
        
        lots = []

        for lot in lot_info["parkingPlaces"]:
            # the lots from both sources need to be matched
            lot_data_list = [
                _lot for _lot in lot_vacancy.find_all("parkingFacilityStatus")
                    if hasattr(_lot.parkingFacilityReference, "attr")
                    and _lot.parkingFacilityReference.attrs["id"] == lot["general"]["name"]
            ]

            if len(lot_data_list) > 0:
                vacant = lot_data_list[0].totalNumberOfVacantParkingSpaces.text
                occupied = lot_data_list[0].totalNumberOfOccupiedParkingSpaces.text
                total = lot_data_list[0].totalParkingCapacityShortTermOverride.text
                lot_timestamp = self._iso_string_to_timestamp(lot_data_list[0].parkingFacilityStatusTime.text)
            else:
                vacant = None
                occupied = None
                total = lot["details"]["parkingCapacity"]["totalParkingCapacityShortTermOverride"]
                lot_timestamp = None
            
            # note: both api's have different values for the total parking capacity,
            # but the vacant slot are based on the total parking capacity from the same api,
            # so that is used if available

            # also in the vacancy api the total capacity for the "Goethe Gallerie" are 0 if it is closed

            lots.append(
                LotData(
                    id = name_to_id("jena", lot["general"]["name"]),
                    timestamp = self._iso_string_to_timestamp(lot_vacancy.find("publicationTime").text),
                    status = self._get_status(lot),
                    capacity = int_or_none(total),
                    num_free = int_or_none(vacant),
                    num_occupied = int_or_none(occupied),
                    lot_timestamp = lot_timestamp
                )
            )

        return lots

    def get_lot_infos(self) -> List[LotInfo]:
        lot_vacancy = self.request_soup(url = self.POOL.source_url, parser = "xml")
        lot_info = self.request_json("https://opendata.jena.de/dataset/1a542cd2-c424-4fb6-b30b-d7be84b701c8/resource/76b93cff-4f6c-47fa-ab83-b07d64c8f38a/download/parking.json")
        
        lots = []

        for lot in lot_info["parkingPlaces"]:
            # the lots from both sources need to be matched
            lot_data_list = [
                _lot for _lot in lot_vacancy.find_all("parkingFacilityStatus")
                    if hasattr(_lot.parkingFacilityReference, "attr")
                    and _lot.parkingFacilityReference.attrs["id"] == lot["general"]["name"]
            ]

            if len(lot_data_list) > 0:
                total = lot_data_list[0].totalParkingCapacityShortTermOverride.text
            else:
                total = lot["details"]["parkingCapacity"]["totalParkingCapacityShortTermOverride"]
            
            # note: both api's have different values for the total parking capacity,
            # but the vacant slot are based on the total parking capacity from the same api,
            # so that is used if available

            # also in the vacancy api the total capacity for the "Goethe Gallerie" are 0 if it is closed
                
            if lot["general"]["objectType"] == "Parkplatz":
                lot_type = LotInfo.Types.lot
            elif lot["general"]["objectType"] == "Parkhaus":
                lot_type = LotInfo.Types.garage
            else:
                lot_type = LotInfo.Types.unknown

            lot_id = lot["general"]["name"].lower().replace(" ", "-").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")

            lots.append(
                LotInfo(
                    id = name_to_id("jena", lot["general"]["name"]),
                    name = lot["general"]["name"],
                    type = lot_type,
                    public_url = "https://mobilitaet.jena.de/de/" + lot_id,
                    source_url = self.POOL.source_url,
                    address = lot["details"]["parkingPlaceAddress"]["parkingPlaceAddress"],
                    capacity = int_or_none(total),
                    has_live_capacity = (len(lot_data_list) > 0),
                    latitude=lot["general"]["coordinates"]["lat"],
                    longitude=lot["general"]["coordinates"]["lng"],
                )
            )

        return lots
    
    def _iso_string_to_timestamp(self, iso_string):
        return datetime.strptime(iso_string[:-6], "%Y-%m-%dT%H:%M:%S.%f")
    
    # the rest of the code is there to deal with the api's opening/charging hours objects
    # example:
    # "openingTimes": [
    #   {
    #     "alwaysCharged": True,
    #     "dateFrom": 2,
    #     "dateTo": 5,
    #     "times": [
    #       {
    #         "from": "07:00",
    #         "to": "23:00"
    #       }
    #     ]
    #   },
    #   {
    #     "alwaysCharged": False,
    #     "dateFrom": 7,
    #     "dateTo": 1,
    #     "times": [
    #       {
    #         "from": "10:00",
    #         "to": "03:00"
    #       }
    #     ]
    #   }
    # ]

    # def _parse_opening_hours(self, lot_data):
    #     if lot_data["parkingTime"]["openTwentyFourSeven"]: return "24/7"

    #     return self.parse_times(lot_data["parkingTime"]["openingTimes"])

    # def _parse_charged_hours(self, lot_data):
    #     charged_hour_objs = []

    #     ph_info = "An Feiertagen sowie außerhalb der oben genannten Zeiten ist das Parken gebührenfrei."

    #     if not lot_data["parkingTime"]["chargedOpeningTimes"] and lot_data["parkingTime"]["openTwentyFourSeven"]:
    #         if lot_data["priceList"]:
    #             if ph_info in str(lot_data["priceList"]["priceInfo"]):
    #                 return "24/7; PH off"
    #             else: return "24/7"
    #         else: return "off"

    #     # charging hours can also be indicated by the "alwaysCharged" variable in "openingTimes"
    #     elif not lot_data["parkingTime"]["chargedOpeningTimes"] and not lot_data["parkingTime"]["openTwentyFourSeven"]:
    #         for oh in lot_data["parkingTime"]["openingTimes"]:
    #             if "alwaysCharged" in oh and oh["alwaysCharged"]: charged_hour_objs.append(oh)
    #         if len(charged_hour_objs) == 0: return "off"

    #     elif lot_data["parkingTime"]["chargedOpeningTimes"]:
    #         charged_hour_objs = lot_data["parkingTime"]["chargedOpeningTimes"]

    #     charged_hours = self.parse_times(charged_hour_objs)

    #     if ph_info in str(lot_data["priceList"]["priceInfo"]):
    #         charged_hours += "; PH off"

    #     return charged_hours

    # # creatin osm opening_hours strings from opening/charging hours objects
    # def _parse_times(times_objs):
    #     DAYS = ["", "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    #     ohs = ""

    #     for index, oh in enumerate(times_objs):
    #         part = ""

    #         if oh["dateFrom"] == oh["dateTo"]:
    #             part += DAYS[oh["dateFrom"]]
    #         else:
    #             part += DAYS[oh["dateFrom"]] + "-" + DAYS[oh["dateTo"]]

    #         part += " "

    #         for index2, time in enumerate(oh["times"]):
    #             part += time["from"] +  "-" + time["to"]
    #             if index2 != len(oh["times"]) - 1: part += ","

    #         if index != len(times_objs) - 1: part += "; "

    #         ohs += part

    #     return ohs

    def _get_status(self, lot_data):
        if lot_data["parkingTime"]["openTwentyFourSeven"]: return "open"

        # check for public holiday?

        for oh in lot_data["parkingTime"]["openingTimes"]:
            now = datetime.now(pytz.timezone("Europe/Berlin"))

            weekday = now.weekday() + 1

            # oh rules can also go beyond week ends (e.g. from Sunday to Monday)
            # this need to be treated differently
            if oh["dateFrom"] <= oh["dateTo"]:
                if not (weekday >= oh["dateFrom"]) or not (weekday <= oh["dateTo"] + 1): continue
            else:
                if weekday > oh["dateTo"] + 1 and weekday < oh["dateFrom"]: continue

            for times in oh["times"]:
                time_from = self._get_timestamp_without_date(time.fromisoformat(times["from"]).replace(tzinfo=pytz.timezone("Europe/Berlin")))
                time_to = self._get_timestamp_without_date(time.fromisoformat(times["to"]).replace(tzinfo=pytz.timezone("Europe/Berlin")))

                time_now = self._get_timestamp_without_date(now)

                # time ranges can go over to the next day (e.g 10:00-03:00)
                if time_to >= time_from:
                    if time_now >= time_from and time_now <= time_to:
                        return "open"
                    else: continue

                else:
                    if oh["dateFrom"] <= oh["dateTo"]:
                        if (time_now >= time_from and weekday >= oh["dateFrom"] and weekday <= oh["dateTo"]
                        or time_now <= time_to and weekday >= oh["dateFrom"] + 1 and weekday <= oh["dateTo"] + 1):
                            return "open"
                        else: continue

                    else:
                        if (time_now >= time_from and (weekday >= oh["dateFrom"] or weekday <= oh["dateTo"])
                        or time_now <= time_to and (weekday >= oh["dateFrom"] + 1 or weekday <= oh["dateTo"] + 1)):
                            return "open"
                        else: continue 

        # if no matching rule was found, the lot is closed
        return "closed"

    def _get_timestamp_without_date (self, date_obj):
        return date_obj.hour * 3600 + date_obj.minute * 60 + date_obj.second
