'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator, LocationManager, CityManager, CountryManager, RegionManager, Country, LocationContext
from sklearn.neighbors import BallTree

from math import radians
from tests.basetest import Geograpy3Test

class TestLocationHierarchy(Geograpy3Test):
    '''
    tests for the location hierarchy
    '''

    def setUp(self):
        super().setUp()
        self.locationContext = None
        pass

    def getLocationContext(self):
        if self.locationContext is None:
            self.locationContext = LocationContext.fromCache()
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
        config=LocationContext.getDefaultConfig()
        regionManager=RegionManager(config=config)
        regionManager.fromCache()
        for country in countryList.countries:
            locationListWithDistances = country.getNClosestLocations(regionManager, 3)
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
    

    def test_getLocationByID(self):
        '''
        tests if the correct location for a given wikidataid is returned
        '''
        config=LocationContext.getDefaultConfig()
        countryManager = CountryManager(config=config)
        countryManager.fromCache()
        country = countryManager.getLocationByID("Q30")  # wikidataid of USA
        self.assertIsNotNone(country)
        self.assertTrue(hasattr(country, 'iso'))
        self.assertEqual(country.iso, 'US')

    def test_LocationContext(self):
        '''
        tests the LocationContext class
        '''

        # test interlinking of city with region and country
        locationContext = self.getLocationContext()
        cities = locationContext.cityManager.getByName('Los Angeles')
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
            locations = locationContext.locateLocation(locationText, verbose=True)
            if len(locations) < 1:
                failures.append(locationText)
            else:
                location = locations[0]
                if self.debug:
                    printPretty(location)
                if not location.wikidataid == expectedLocationId:
                    failures.append(locationText)
        showFailures=True
        if self.debug or showFailures:
            print(f"locationLooup failed for {failures}")
        self.assertTrue(len(failures)<=40)
        
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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
