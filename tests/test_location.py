'''
Created on 2021-06-09

@author: wf
'''
import unittest
import numpy as np
from geograpy.locator import Locator, CountryList, CityList, RegionList
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

    def testRegionListFromJSONBackup(self):
        '''
        tests the loading and parsing of the RegionList form the json backup file
        '''
        regionList=RegionList.fromJSONBackup()
        self.assertTrue('regions' in regionList.__dict__)
        self.assertTrue(len(regionList.regions) >= 1000)
        # check if California is in the list
        ca_present=False
        for region in regionList.regions:
            if 'wikidataid' in region.__dict__:
                if region.wikidataid == "Q99":
                    ca_present = True
                    break
        self.assertTrue(ca_present)

    def testCountryListFromJSONBackup(self):
        '''
        tests the loading and parsing of the RegionList form the json backup file
        '''
        countryList=CountryList.fromJSONBackup()
        self.assertTrue('countries' in countryList.__dict__)
        self.assertTrue(len(countryList.countries) >= 180)
        # check if California is in the list
        us_present=False
        for country in countryList.countries:
            if 'wikidataid' in country.__dict__:
                if country.wikidataid == "Q30":
                    us_present = True
                    break
        self.assertTrue(us_present)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()