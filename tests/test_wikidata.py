'''
Created on 2020-09-23

@author: wf
'''
import unittest
from geograpy.wikidata import Wikidata
from geograpy.locator import Locator
import getpass
from tests.basetest import Geograpy3Test
from lodstorage.sql import SQLDB
from lodstorage.storageconfig import StorageConfig

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

    def testGetAllWikidataCities(self):
        '''
        test getting city information from wikidata
        
        '''
        # Wikidata time outs in CI environment need to be avoided
        if getpass.getuser()!="wf":
            return
        config=StorageConfig.getSQL(debug=self.debug)
        config.cacheRootDir="/tmp/wdhs"
        cachedir=config.getCachePath()
        config.cacheFile=f"{cachedir}/hs.db"
        # use 2018 wikidata copy
        # wikidata.endpoint="http://blazegraph.bitplan.com/sparql"
        # use 2020 wikidata copy
        wikidata=Wikidata()
        wikidata.endpoint="https://confident.dbis.rwth-aachen.de/jena/wdhs/sparql"
        #wikidata.endpoint="http://jena.bitplan.com/wdhs/sparql"
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
        sqlDB=SQLDB(config.cacheFile)
        entityInfo=sqlDB.createTable(cityList,"hs",withDrop=True)
        sqlDB.store(cityList, entityInfo,fixNone=True)
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
