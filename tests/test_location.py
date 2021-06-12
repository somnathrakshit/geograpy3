'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator,CityList,CountryList,RegionList, Country, Earth
from sklearn.neighbors import BallTree
from math import radians

class TestLocationHierarchy(unittest.TestCase):
    '''
    tests for the location hierarchy
    '''


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testDistance(self):
        # https://stackoverflow.com/a/64585765/1497139
        earth_radius = Earth.radius*1000 # meters in earth
        test_radius = 1300000 # meters
        
        test_points = [[32.027240,-81.093190],[41.981876,-87.969982]]
        test_points_rad = np.array([[radians(x[0]), radians(x[1])] for x in test_points ])
        
        tree = BallTree(test_points_rad, metric = 'haversine')
        ind,results = tree.query_radius(test_points_rad, r=test_radius/earth_radius, 
        return_distance  = True)
        if self.debug:
            print(ind)
            print(results * earth_radius/1000)

    def testIssue45_BallTree(self):
        '''
        test calculation a ball tree for a given list of locations
        '''
        countryList=CountryList.fromErdem()
        ballTree,validList=countryList.getBallTuple()
        self.assertEqual(245,len(validList))
        self.assertEqual("BallTree",type(ballTree).__name__)
        self.assertAlmostEqual(245, ballTree.sum_weight, delta=0.1)
        pass
    
    def checkLocationListWithDistances(self,locationListWithDistances,expectedCount,expectedClosest,expectedDistance):
        '''
        check the location list with the given distances
        '''        
        if self.debug:
            for i,locationWithDistance in enumerate(locationListWithDistances):
                location,distance=locationWithDistance
                print(f"{i}:{location}-{distance:.0f} km")
        self.assertEqual(len(locationListWithDistances),expectedCount)
        closestLocation,distance=locationListWithDistances[0]
        self.assertEqual(expectedClosest,closestLocation.name)
        self.assertAlmostEqual(expectedDistance, distance,delta=1)

    def testClosestLocation(self):
        '''
        test getting the closes Location to a given location
        '''
        # sample Country: Germany
        country = Country()
        country.name= 'Germany'
        country.lat = 51.0
        country.lon = 9.0
        # get a country list
        lookupCountryList = CountryList.fromErdem()
        # get the closest 2 locations for the given countryList
        countryListWithDistances= country.getNClosestLocations(lookupCountryList,2)
        self.checkLocationListWithDistances(countryListWithDistances, 2, "Luxembourg", 244)

        countryListWithDistances=country.getLocationsWithinRadius(lookupCountryList, 300)
        self.checkLocationListWithDistances(countryListWithDistances, 2, "Luxembourg", 244)

    def testRegionMatching(self):
        '''
        test region matches
        '''
        locator=Locator()
        if not locator.db_has_data():
            locator.populate_db()
        countryList=CountryList.fromErdem()
        regionList=RegionList.from_sqlDb(locator.sqlDB)
        for country in countryList.countries:
            locationListWithDistances=country.getNClosestLocations(regionList,3)
            print(f"{country}{country.lat:.2f},{country.lon:.2f}")
            for i,locationWithDistance in enumerate(locationListWithDistances):
                location,distance=locationWithDistance
                print(f"    {i}:{location}-{distance:.0f} km")
        pass

    def testLocationListLoading(self):
        samples="""
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
        countries = CountryList().restoreFromJsonStr(samples)
        # USA is a country that should always be in the list test if present
        us_present = False
        for country in countries:
            if 'wikidataid' in country.__dict__:
                if country.wikidataid == "Q30":
                    us_present = True
                    break
        self.assertTrue(us_present)

    def testCountryListFromWikidata(self):
        '''
        tests if the CountryList id correctly loaded from Wikidata query result
        '''
        countryList=CountryList.fromWikidata()
        self.assertTrue(len(countryList.countries)>=190)

    def testCityListFromJSONBackup(self):
        '''
        tests the loading and parsing of the cityList form the json backup file
        '''
        cityList=CityList().fromJSONBackup()
        self.assertTrue('cities' in cityList.__dict__)
        self.assertTrue(len(cityList.cities)>=50000)
        # check if Los Angeles is in the list (popular city should always be in the list)
        la_present = False
        for city in cityList.cities:
            if 'wikidataid' in city.__dict__:
                if city.wikidataid == "Q65":
                    la_present = True
                    break
        self.assertTrue(la_present)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()