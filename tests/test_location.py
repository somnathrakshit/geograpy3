'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator,CountryList , Country, Earth
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
        ballTree=countryList.getBallTree()
        self.assertEqual("BallTree",type(ballTree).__name__)
        self.assertAlmostEqual(247, ballTree.sum_weight, delta=0.1)
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

    def testCountryMatching(self):
        '''
        test country matches
        '''
        locator=Locator()
        if not locator.db_has_data():
            locator.populate_db()
        lookupCountryList=CountryList.fromErdem()
        countryList2=CountryList.from_sqlDb(locator.sqlDB)
        for country in countryList2.countries:
            locationListWithDistances=country.getNClosestLocations(lookupCountryList,3)
            print(country)
            for i,locationWithDistance in enumerate(locationListWithDistances):
                location,distance=locationWithDistance
                print(f"    {i}:{location}-{distance:.0f} km")
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()