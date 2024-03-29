"""
Created on 2021-08-13

@author: wf
"""
import tempfile
import unittest

from lodstorage.storageconfig import StorageConfig

from geograpy.locator import (
    CityManager,
    CountryManager,
    LocationContext,
    LocationManager,
    RegionManager,
)
from tests.basetest import Geograpy3Test


class TestLocationContext(Geograpy3Test):
    """
    test the location Context - these are potentially long running tests
    """

    def getStorageConfig(self):
        # config=StorageConfig.getDefault()
        config = LocationContext.getDefaultConfig()
        return config

    def checkNoDuplicateWikidataIds(
        self, locationManager: LocationManager, primaryKey=None, expectedDuplicates=0
    ):
        """
        check that there are no duplicate Wikidata Q identifiers in the given

        """
        locationsByWikiDataId, duplicates = locationManager.getLookup(primaryKey)
        showLimit = 10
        if len(duplicates) > 0:
            for i, duplicate in enumerate(duplicates):
                if i < showLimit:
                    if self.debug:
                        print(f"{i}:{duplicate}")
                else:
                    break
        self.assertTrue(len(duplicates) <= expectedDuplicates)
        return locationsByWikiDataId

    def testCountryManager(self):
        """
        tests the loading and parsing of the RegionManager form the json backup file
        """
        countryManager = CountryManager(config=self.getStorageConfig())
        countryManager.fromCache()
        self.assertTrue(hasattr(countryManager, "countries"))
        self.assertTrue(len(countryManager.countries) >= 200)
        # check if California is in the list
        countriesByWikidataId = self.checkNoDuplicateWikidataIds(
            countryManager, "wikidataid"
        )
        self.assertTrue("Q30" in countriesByWikidataId)

    def testRegionManager(self):
        """
        tests the loading and parsing of the RegionManager form the json backup file
        """
        regionManager = RegionManager(config=self.getStorageConfig())
        regionManager.fromCache()
        self.assertTrue(hasattr(regionManager, "regions"))
        self.assertTrue(len(regionManager.regions) >= 1000)
        regionsByWikidataId = self.checkNoDuplicateWikidataIds(
            regionManager, "wikidataid", 54
        )
        self.assertTrue("Q99" in regionsByWikidataId)

    def testCityManager(self):
        """
        tests the loading and parsing of the cityList form the json backup file
        """
        cityManager = CityManager(config=self.getStorageConfig())
        cityManager.fromCache()
        self.assertTrue(hasattr(cityManager, "cities"))
        self.assertTrue(len(cityManager.cities) >= 200000)
        # check if Los Angeles is in the list (popular city should always be in the list)
        _citiesByWikiDataIdNoDuplicates = self.checkNoDuplicateWikidataIds(
            cityManager, "wikidataid", 304000
        )  # ToDo: Reduce number of duplicates
        citiesByWikiDataId = cityManager.getLookup("wikidataid", withDuplicates=True)
        self.assertTrue("Q65" in citiesByWikiDataId)

    def testLocationContextFromCache(self):
        """
        test loading LocationContext from cache
        """
        testCache = False
        if self.inCI() or testCache:
            locationContext = LocationContext.fromCache()
            locationContext.load()
            self.assertTrue(len(locationContext.countries) > 180)
            self.assertTrue(len(locationContext.regions) > 3500)
            self.assertTrue(len(locationContext.cities) > 1000000)

    def testIssue_59_db_download(self):
        """
        tests if the cache database is downloaded if not present
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StorageConfig(cacheFile="locations.db", cacheRootDir=tmpdir)
            config.cacheFile = f"{config.getCachePath()}/{config.cacheFile}"
            loc = LocationContext.fromCache(config=config)
            locations = loc.locateLocation("Germany")
            self.assertTrue(len(locations) > 0)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
