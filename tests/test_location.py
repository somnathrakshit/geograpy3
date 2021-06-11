'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator,CountryList
from sklearn.neighbors import BallTree
from geograpy.locator import Location
import json
import pandas as pd

from math import radians
from sqlalchemy.sql.functions import cube

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
        earth_radius = 6371000 # meters in earth
        test_radius = 1300000 # meters
        
        test_points = [[32.027240,-81.093190],[41.981876,-87.969982]]
        test_points_rad = np.array([[radians(x[0]), radians(x[1])] for x in test_points ])
        
        tree = BallTree(test_points_rad, metric = 'haversine')
        ind,results = tree.query_radius(test_points_rad, r=test_radius/earth_radius, 
        return_distance  = True)
        if self.debug:
            print(ind)
            print(results * earth_radius/1000)



    def testMatchingv2(self):
        locator = Locator()
        if not locator.db_has_data():
            locator.populate_db()
        countryList = CountryList.fromErdem()
        jsonLoad = json.loads(countryList.toJSON())
        countries = pd.DataFrame(jsonLoad['countries'])
        countries['lat'] = pd.to_numeric(countries['lat'], downcast="float")
        countries['lon'] = pd.to_numeric(countries['lon'], downcast="float")
        countries['rad_lat'] = countries['lat'].apply(lambda x: radians(x))
        countries['rad_lon'] = countries['lon'].apply(lambda x: radians(x))
        coordinatesrad = np.array(list(zip(countries['rad_lat'], countries['rad_lon'])))
        balltree = BallTree(coordinatesrad, metric='haversine')
        test_radius = 500  # Kms
        test_NN= 5
        cl2 = CountryList.from_sqlDb(locator.sqlDB)
        for country in cl2.countries:
            testpoint = np.array([(radians(country.lat), radians(country.lon))])
            name = country.name
            results = Location.getClosestLocations(name, 2, countries, balltree,coordinatesrad, 'number')

            if results is not None:
                print(results.Country.values[-1], " is closest to ", name)
            else:
                print(country.name, 'not found')


    def testMatching(self):
        '''
        test country matches
        '''
        locator=Locator()
        if not locator.db_has_data():
            locator.populate_db()
        countryList=CountryList.fromErdem()
        # https://stackoverflow.com/a/39109296/1497139
        coords = np.array([[radians(country.lat), radians(country.lon)] for country in countryList.countries ])
        #https://en.wikipedia.org/wiki/Ball_tree
        tree = BallTree(coords, metric = 'haversine')
        cl2=CountryList.from_sqlDb(locator.sqlDB)
        earth_radius = 6371000 # meters in earth
        test_radius = 1300000 # meters
        maxDistRatio=test_radius/earth_radius
        for country in cl2.countries:
            testpoint=np.array([(radians(country.lat),radians(country.lon))])
            iclosest,dclosest=tree.query_radius(testpoint,maxDistRatio,return_distance  = True)
            print (country)
            iclosest=iclosest.tolist()
            dclosest=dclosest.tolist()
            for i,ci in enumerate(iclosest):
                countryIndex=ci[i]
                cCountry=cl2.countries[countryIndex]
                print(country,cCountry,dclosest[i])
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()