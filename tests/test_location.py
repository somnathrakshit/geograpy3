'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator, LocationManager, CityManager, CountryManager, RegionManager, Country, LocationContext
from sklearn.neighbors import BallTree

from math import radians
import getpass
import os


class TestLocationHierarchy(unittest.TestCase):
    '''
    tests for the location hierarchy
    '''

    @staticmethod
    def inCI():
        '''
        are we running in a Continuous Integration Environment?
        '''
        publicCI = getpass.getuser() in ["travis", "runner"] 
        jenkins = "JENKINS_HOME" in os.environ;
        return publicCI or jenkins

    def setUp(self):
        self.debug = False
        self.testWikidata = False
        self.locationContext = None
        pass

    def tearDown(self):
        pass

    def getLocationContext(self):
        if self.locationContext is None:
            self.locationContext = LocationContext.fromJSONBackup()
        return self.locationContext
            
    def testDistance(self):
        '''
        test calculcating the distance of two points using the haversine function
        '''
        # https://stackoverflow.com/a/64585765/1497139
        earth_radius = 6371000  # meters in earth
        test_radius = 1300000  # meters
        
        test_points = [[32.027240, -81.093190], [41.981876, -87.969982]]
        test_points_rad = np.array([[radians(x[0]), radians(x[1])] for x in test_points ])
        
        tree = BallTree(test_points_rad, metric='haversine')
        ind, results = tree.query_radius(test_points_rad, r=test_radius / earth_radius,
        return_distance=True)
        if self.debug:
            print(ind)
            print(results * earth_radius / 1000)

    def testIssue45_BallTree(self):
        '''
        test calculation a ball tree for a given list of locations
        '''
        countryList = CountryManager.fromErdem()
        ballTree, validList = countryList.getBallTuple()
        self.assertEqual(245, len(validList))
        self.assertEqual("BallTree", type(ballTree).__name__)
        self.assertAlmostEqual(245, ballTree.sum_weight, delta=0.1)
        pass

    def checkLocationListWithDistances(self, locationListWithDistances, expectedCount, expectedClosest, expectedDistance):
        '''
        check the location list with the given distances
        '''
        if self.debug:
            for i, locationWithDistance in enumerate(locationListWithDistances):
                location, distance = locationWithDistance
                print(f"{i}:{location}-{distance:.0f} km")
        self.assertEqual(len(locationListWithDistances), expectedCount)
        closestLocation, distance = locationListWithDistances[0]
        self.assertEqual(expectedClosest, closestLocation.name)
        self.assertAlmostEqual(expectedDistance, distance, delta=1)

    def testClosestLocation(self):
        '''
        test getting the closes Location to a given location
        '''
        # sample Country: Germany
        country = Country()
        country.name = 'Germany'
        country.lat = 51.0
        country.lon = 9.0
        # get a country list
        lookupCountryManager = CountryManager.fromErdem()
        # get the closest 2 locations for the given countryList
        countryListWithDistances = country.getNClosestLocations(lookupCountryManager, 2)
        self.checkLocationListWithDistances(countryListWithDistances, 2, "Luxembourg", 244)

        countryListWithDistances = country.getLocationsWithinRadius(lookupCountryManager, 300)
        self.checkLocationListWithDistances(countryListWithDistances, 2, "Luxembourg", 244)

    def testRegionMatching(self):
        '''
        test region matches
        '''
        locator = Locator()
        if not locator.db_has_data():
            locator.populate_db()
        countryList = CountryManager.fromErdem()
        regionList = RegionManager.from_sqlDb(locator.sqlDB)
        for country in countryList.countries:
            locationListWithDistances = country.getNClosestLocations(regionList, 3)
            if self.debug:
                print(f"{country}{country.lat:.2f},{country.lon:.2f}")
            for i, locationWithDistance in enumerate(locationListWithDistances):
                location, distance = locationWithDistance
                if self.debug:
                    print(f"    {i}:{location}-{distance:.0f} km")
        pass

    def testLocationListLoading(self):
        '''
        test loading the locations from Json
        '''
        samples = """
        {
            "countries": [
                {
                    "name": "Afghanistan",
                    "wikidataid": "Q889",
                    "lat": 34,
                    "lon": 66,
                    "coordinates": "34,66",
                    "partOf": null,
                    "level": 3,
                    "locationKind": "Country",
                    "comment": null,
                    "iso": "AF"
                },
                {
                    "name": "United States of America",
                    "wikidataid": "Q30",
                    "lat": 39.82818,
                    "lon": -98.5795,
                    "partOf": "Noth America",
                    "level": 3,
                    "locationKind": "Country",
                    "comment": null,
                    "labels": [
                        "America",
                        "UNITED STATES OF AMERICA",
                        "USA",
                        "United States",
                        "United States of America (the)"
                    ],
                    "iso": "US"
                },
                {
                    "name": "Australia",
                    "wikidataid": "Q408",
                    "lat": -28,
                    "lon": 137,
                    "coordinates": "-28,137",
                    "partOf": null,
                    "level": 3,
                    "locationKind": "Country",
                    "comment": null,
                    "labels": [
                        "AUS"
                    ],
                    "iso": "AU"
                }
            ]
        }
        """
        cm = CountryManager();
        cm.restoreFromJsonStr(samples)
        countriesByWikiDataId, _dup = cm.getLookup("wikidataid")
        self.assertTrue("Q30" in countriesByWikiDataId)
        
    def handleWikidataException(self, ex):
        '''
        handle a Wikidata exception
        Args:
            ex(Exception): the exception to handle - e.g. timeout
        '''
        msg = str(ex)
        print(f"Wikidata test failed {msg}")
        # only raise exception for real problems
        if "HTTP Error 500" in msg:
            print("test can not work if server has problems")
            return
        raise ex
    
    def checkNoDuplicateWikidataIds(self, locationManager:LocationManager):
        '''
        check that there are no duplicate Wikidata Q identifiers in the given
        
        '''
        locationsByWikiDataId, duplicates = locationManager.getLookup("wikidataid")
        if len(duplicates) > 0:
            for i, duplicate in enumerate(duplicates):
                    print(f"{i}:{duplicate}")
        self.assertEqual(len(duplicates), 0)
        return locationsByWikiDataId
        
    def testCountryManagerFromWikidata(self):
        '''
        tests if the CountryManager id correctly loaded from Wikidata query result
        '''
        # wikidata query results are unreliable
        if TestLocationHierarchy.inCI() or self.testWikidata:
            try:
                countryManager = CountryManager.fromWikidata()
                self.assertTrue(len(countryManager.countries) >= 190)
                countriesByWikiDataId = self.checkNoDuplicateWikidataIds(countryManager)
                self.assertTrue("Q40" in countriesByWikiDataId)
                
            except Exception as ex:
                self.handleWikidataException(ex)
                
    def test_RegionManagerFromWikidata(self):
        '''
        tests the loading of the RegionManager from wikidata query results
        '''
        # wikidata query results are unreliable
        if TestLocationHierarchy.inCI() or self.testWikidata:
            try:
                regionManager = RegionManager.fromWikidata()
                # check amount of regions
                self.assertTrue(len(regionManager.regions) > 3500)
                regionsByWikiDataId = self.checkNoDuplicateWikidataIds(regionManager)
                # check if california is present
                self.assertTrue("Q99" in regionsByWikiDataId)
                ca = regionManager.getLocationByID("Q99")
                self.assertIsNotNone(ca)
                self.assertEqual(ca.name, "California")
            except Exception as ex:
                self.handleWikidataException(ex)

    def test_CityManagerFromWikidata(self):
        '''
        tests the loading of the RegionManager from wikidata query results
        '''
        # wikidata query results are unreliable
        self.testWikidata = True
        if TestLocationHierarchy.inCI() or self.testWikidata:
            try:
                regions = ["Q1198"]
                cityManager = CityManager.fromWikidata(regionIDs=regions, fromBackup=False)
                # check amount of regions
                self.assertTrue(len(cityManager.cities) > 1300)
                citiesByWikiDataId = self.checkNoDuplicateWikidataIds(cityManager)
                self.assertTrue("Q1017" in citiesByWikiDataId)
                # check if NRW is present (region of Germany)
                aachen = cityManager.getLocationByID("Q1017")
                self.assertIsNotNone(aachen)
                self.assertEqual(aachen.name, "Aachen")
            except Exception as ex:
                self.handleWikidataException(ex)

    def testCityManagerFromJSONBackup(self):
        '''
        tests the loading and parsing of the cityList form the json backup file
        '''
        cityManager = CityManager().fromJSONBackup()
        self.assertTrue(hasattr(cityManager, 'cities'))
        self.assertTrue(len(cityManager.cities) >= 400000)
        # check if Los Angeles is in the list (popular city should always be in the list)
        citiesByWikiDataId = self.checkNoDuplicateWikidataIds(cityManager)
        self.assertTrue("Q65" in citiesByWikiDataId)

    def testRegionManagerFromJSONBackup(self):
        '''
        tests the loading and parsing of the RegionManager form the json backup file
        '''
        regionList = RegionManager.fromJSONBackup()
        self.assertTrue('regions' in regionList.__dict__)
        self.assertTrue(len(regionList.regions) >= 1000)
        # check if California is in the list
        ca_present = False
        for region in regionList.regions:
            if 'wikidataid' in region.__dict__:
                if region.wikidataid == "Q99":
                    ca_present = True
                    break
        self.assertTrue(ca_present)

    def testCountryManagerFromJSONBackup(self):
        '''
        tests the loading and parsing of the RegionManager form the json backup file
        '''
        countryList = CountryManager.fromJSONBackup()
        self.assertTrue('countries' in countryList.__dict__)
        self.assertTrue(len(countryList.countries) >= 180)
        # check if California is in the list
        us_present = False
        for country in countryList.countries:
            if 'wikidataid' in country.__dict__:
                if country.wikidataid == "Q30":
                    us_present = True
                    break
        self.assertTrue(us_present)

    def test_getLocationByID(self):
        '''
        tests if the correct location for a given wikidataid is returned
        '''
        countryList = CountryManager.fromJSONBackup()
        country = countryList.getLocationByID("Q30")  # wikidataid of USA
        self.assertTrue('iso' in country.__dict__)
        self.assertEqual(country.iso, 'US')

    def test_LocationContext(self):
        '''
        tests the LocationContext class
        '''

        # test interlinking of city with region and country
        locationContext = self.getLocationContext()
        cities = locationContext.getCities('Los Angeles')
        la = [x for x in cities if x.wikidataid == "Q65"][0]
        self.assertEqual(la.name, 'Los Angeles')
        ca = la.region
        self.assertEqual(ca.name, 'California')
        us = la.country
        self.assertEqual(us.wikidataid, 'Q30')
        self.assertEqual(la.country, ca.country)

    def testLocateLocation(self):
        '''
        test LocationContext locateLocation
        '''
        exampleLocations = {
            "Washington, DC, USA": "Q61",
            "Bangalore": "Q1355",
            "Bangalore, India": "Q1355",
            "Xi'an": "Q5826",
            "Xi'an, China": "Q5826",
            "Virtual Event USA": "Q30",
            "Virtual USA": "Q30",
            "London United Kingdom": "Q84",
            "Brno":"Q14960",
            "Cancun":"Q8969",
            "St. Petersburg": "Q656",
            "Gothenburg Sweden": "Q25287",
            "Los Angeles California": "Q65",
            "Zurich, Switzerland": "Q72",
            "Barcelona Spain": "Q1492",
            "Vienna Austria": "Q1741",
            "Seoul Republic of Korea": "Q8684",
            "Seattle WA USA": "Q5083",
            "Singapore Singapore":"Q334",
            "Tokyo Japan": "Q1490",
            "Vancouver BC Canada": "Q24639",
            "Vancouver British Columbia Canada": "Q24639",
            "Amsterdam Netherlands":"Q727",
            "Paris France": "Q90",
            "Nagoya": "Q11751",
            "Marrakech":"Q101625",
            "Austin Texas":"Q16559",
            "Chicago IL USA":"Q1297",
            "Bangkok Thailand":"Q1861",
            "Firenze, Italy":"Q2044",
            "Florence Italy":"Q2044",
            "Timisoara":"Q83404",
            "Langkawi":"Q273303",
            "Beijing China":"Q956",
            "Berlin Germany": "Q64",
            "Prague Czech Republic":"Q1085",
            "Portland Oregon USA":"Q6106",
            "Portland OR USA":"Q6106",
            "Pittsburgh PA USA":"Q1342",
            "Новосибирск":"Q883",
            "Los Angeles CA USA":"Q65",
            "Kyoto Japan": "Q34600"
        }
        locationContext = self.getLocationContext()
        printPretty = lambda records:print([str(record) for record in records])
        failures = []
        for locationText in exampleLocations.keys():
            expectedLocationId = exampleLocations[locationText] 
            locations = locationContext.locateLocation(locationText)
            if len(locations) < 1:
                failures.append(locationText)
            else:
                location = locations[0]
                if self.debug:
                    printPretty(location)
                if not location.wikidataid == expectedLocationId:
                    failures.append(locationText)
        if self.debug:
            print(f"locationLooup failed for {failures}")
        self.assertEqual(0, len(failures))
        
    def testLocateLocationCountryRegionCity(self):
        '''
        test LocationContext locateLocation
        '''
        locationContext = self.getLocationContext()
        printPretty = lambda records:print([str(record) for record in records])
 
        pl1 = locationContext.locateLocation("Berlin", "USA")
        self.assertEqual("Germany", pl1[0].country.name)
        if self.debug:
            printPretty(pl1)
        pl2 = locationContext.locateLocation("Los Angeles, CA")
        if self.debug:
            printPretty(pl2)
        self.assertEqual("California", pl2[0].region.name)
        pl3 = locationContext.locateLocation("Germany, Aachen")
        if self.debug:
            printPretty(pl3)
        self.assertEqual("Aachen", pl3[0].name)
        self.assertEqual("Germany", pl3[0].country.name)

    def testLocationContextFromCache(self):
        '''
        test loading LocationContext from cache
        '''
        locationContext = LocationContext.fromCache()
        self.assertTrue(len(locationContext.countries) > 180)
        locationContext = LocationContext.fromCache(forceUpdate=True)
        self.assertTrue(len(locationContext.countries) > 180)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
