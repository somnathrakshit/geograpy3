'''
Created on 2020-09-23

@author: wf
'''
import unittest
from geograpy.wikidata import Wikidata
from geograpy.locator import Locator
import urllib

import getpass
import time
from tests.basetest import Geograpy3Test

class TestWikidata(Geograpy3Test):
    '''
    test the wikidata access for cities
    '''

    def testLocatorWithWikiData(self):
        '''
        test Locator 
        '''
        Locator.resetInstance()
        loc=Locator.getInstance()
        loc.populate_db()
        tableList=loc.sqlDB.getTableList()
        self.assertTrue(loc.db_recordCount(tableList,"countries")>=190)
        self.assertTrue(loc.db_recordCount(tableList,"regions")>=3000)
        self.assertTrue(loc.db_recordCount(tableList,"cities")>=100000)

    def testWikidataCountries(self):
        '''
        test getting country information from wikidata
        '''
        wikidata=Wikidata()
        try:
            wikidata.getCountries()
            self.assertTrue(len(wikidata.countryList)>=190)
        except Exception as ex:
            self.handleWikidataException(ex)
            pass

    def testWikidataCities(self):
        '''
        test getting city information from wikidata
        
        '''
        # Wikidata time outs in CI environment need to be avoided
        if getpass.getuser()!="wf":
            return
        # use 2018 wikidata copy
        # wikidata.endpoint="http://blazegraph.bitplan.com/sparql"
        # use 2020 wikidata copy
        wikidata=Wikidata()
        wikidata.endpoint="http://jena.bitplan.com/wdhs/sparql"
        regions=[
            {"name": "Singapore", "country": "Q334", "region": None, "cities":46},
            {"name": "Beijing", "country": None, "region": "Q956", "cities":25},
            {"name": "Paris","country": None, "region": "Q13917", "cities":1242},
            {"name": "Barcelona","country": None, "region": "Q5705", "cities":1242},
            {"name": "Rome","country": None, "region": "Q1282", "cities":1242}
        ]
        limit=1000000 if self.inCI() else 100
        expected=200000 if self.inCI() else limit
        cityList=wikidata.getAllCities(limit=limit)
        self.assertTrue(len(cityList)>=expected)
       
        #for region in regions:
        #    starttime=time.time()
        #    regionName=region["name"]
        #    print(f"searching cities for {regionName}" )
        #    cityList=wikidata.getCities(country=region["country"], region=region["region"])
        #    print("Found %d cities for %s in %5.1f s" % (len(cityList),region["name"],time.time()-starttime))
        #    if self.debug:
        #        print(cityList[:10])
        #    #self.assertEqual(region['cities'],len(cityList))
        #    pass

    def testGetCitiesOfRegion(self):
        '''
        Test getting cities based on region wikidata id
        '''
        # Wikidata time outs in CI environment need to be avoided
        if getpass.getuser()!="wf":
            return
        wikidata = Wikidata()
        californiaWikidataId="Q99"
        cities=wikidata.getCitiesOfRegion(californiaWikidataId, 1)
        if self.debug:
            print(cities)
        # [{'city': 'http://www.wikidata.org/entity/Q1050826', 'cityLabel': 'Greater Los Angeles Area', 'cityPop': 18550288.0, 'cityCoord': 'Point(-118.25 35.05694444)'}]
        wikidataURL="http://www.wikidata.org/entity/Q1050826"
        if cities and len(cities)>0:
            biggestCity=cities[0]
            self.assertEqual(biggestCity['city'], wikidataURL)
        else:
            self.fail("California should have at least one city")

    def testGetWikidataId(self):
        '''
        test getting a wikiDataId from a given URL
        '''
        # test entity
        wikidataURL="https://www.wikidata.org/wiki/Q1"
        expectedID="Q1"
        wikiDataId=Wikidata.getWikidataId(wikidataURL)
        self.assertEqual(wikiDataId, expectedID)
        # test property
        wikidataURLProperty="https://www.wikidata.org/wiki/Property:P31"
        expectedPropertyID="P31"
        propertyId=Wikidata.getWikidataId(wikidataURLProperty)
        self.assertEqual(expectedPropertyID, propertyId)

    def testGetCoordinateComponents(self):
        '''
        test the splitting of coordinate components in WikiData query results
        '''
        cList=[
            {
              "coordinate":'Point(-118.25 35.05694444)',
              "expected":(-118.25,35.05694444)
            }
        ]
        for c  in cList:
            coordinate=c["coordinate"]
            expLat,expLon=c["expected"]
            lon, lat=Wikidata.getCoordinateComponents(coordinate)
            self.assertEqual(expLat, lat)
            self.assertEqual(expLon, lon)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
