'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator,CountryList
from sklearn.neighbors import BallTree

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