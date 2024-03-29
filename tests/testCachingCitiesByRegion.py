"""
Created on 2021-08-16

@author: wf
"""
import getpass
import json
import os
import re
import unittest

from geograpy.locator import (
    City,
    CityManager,
    CountryManager,
    LocationContext,
    RegionManager,
)
from geograpy.utils import Profiler
from geograpy.wikidata import Wikidata
from tests.basetest import Geograpy3Test


class TestCachingCitiesByRegion(Geograpy3Test):
    """
    The wikidata city query times out even on the wikidata copy in the RWTH i5 infrastructure
    Therefore we need to split the queries to a reasonable size so that each individual query does not time out.

    A query per region is done some 3000 times.
    The query used here works for most regions except a few where the query needs to be modified to not go the full depth of
    the Property
       located in the administrative territorial entity (P131)
    but limit it

    """

    def cacheRegionCities2Json(self, limit, showDone=False):
        # TODO - refactor to Locator/LocationContext - make available via command line
        wd = Wikidata()
        config = LocationContext.getDefaultConfig()
        countryManager = CountryManager(config=config)
        countryManager.fromCache()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        regionList = regionManager.getList()
        total = len(regionList)
        cachePath = f"{config.getCachePath()}/regions"
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        for index, region in enumerate(regionList):
            if index >= limit:
                break
            regionId = region.wikidataid
            msg = f"{index+1:4d}/{total:4d}:getting cities for {region.name} {region.iso} {region.wikidataid}"
            jsonFileName = f"{cachePath}/{region.iso}.json"
            if os.path.isfile(jsonFileName):
                if showDone:
                    print(msg)
            else:
                try:
                    regionCities = wd.getCitiesForRegion(regionId, msg)
                    jsonStr = json.dumps(regionCities)
                    with open(jsonFileName, "w") as jsonFile:
                        jsonFile.write(jsonStr)
                except Exception as ex:
                    self.handleWikidataException(ex)

    def testGetCitiesByRegion(self):
        """
        test counting human settlement types
        """
        if self.inCI():
            limit = 50
        elif getpass.getuser() == "wf":
            limit = 5000
        else:
            limit = 0
        self.cacheRegionCities2Json(limit=limit)

    def testReadCachedCitiesByRegion(self):
        """
        test reading the cached json Files
        """
        # This is to populate the cities database
        return
        config = LocationContext.getDefaultConfig()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        regionByIso, _dup = regionManager.getLookup("iso")
        self.assertEqual(56, len(_dup))
        jsonFiles = CityManager.getJsonFiles(config)
        msg = f"reading {len(jsonFiles)} cached city by region JSON cache files"
        self.assertTrue(len(jsonFiles) > 2000)
        profiler = Profiler(msg)
        cityManager = CityManager(config=config)
        cityManager.getList().clear()
        for jsonFileName in jsonFiles:
            isoMatch = re.search(r"/([^\/]*)\.json", jsonFileName)
            if not isoMatch:
                print(f"{jsonFileName} - does not match a known region's ISO code")
            else:
                rIso = isoMatch.group(1)
                region = regionByIso[rIso]
                with open(jsonFileName) as jsonFile:
                    cities4Region = json.load(jsonFile)
                    for city4Region in cities4Region:
                        city = City()
                        city.fromDict(city4Region)
                        # fix regionId
                        if hasattr(city, "regionId"):
                            city.partOfRegionId = city.regionId
                        city.regionId = region.wikidataid
                        cityManager.add(city)
                        pass
        cityManager.store()
        profiler.time()

    def testCityFromCityStates(self):
        """
        tests if city states are queried correctly if given the region
        For city states the city is region and city (in some cases also country).
        This test ensures that by querying for the cities of a region the city states include themself in the result
        (the result for cities in city-states often includes the municipalities)
        """
        wd = Wikidata()
        cityStateRecords = wd.getCityStates()
        for cityStateRecord in cityStateRecords:
            regionId = cityStateRecord.get("wikidataid")
            regionCities = wd.getCitiesForRegion(
                regionId, msg=f"Query for cities in {cityStateRecord.get('name')}"
            )
            foundCities = [c.get("wikidataid") for c in regionCities]
            self.assertTrue(regionId in foundCities)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
