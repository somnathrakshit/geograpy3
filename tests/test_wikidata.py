'''
Created on 2020-09-23

@author: wf
'''
import unittest
from geograpy.wikidata import Wikidata
from geograpy.locator import Locator
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
import getpass
import time

class TestWikidata(unittest.TestCase):
    '''
    test the wikidata access for cities
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass

    def testLocatorWithWikiData(self):
        '''
        test Locator in useWikiData mode
        '''
        Locator.useWikiData=True
        Locator.resetInstance()
        loc=Locator.getInstance()
        loc.populate_db()
        tableList=loc.sqlDB.getTableList()
        self.assertTrue(loc.db_recordCount(tableList,"countries")>=190)
        self.assertTrue(loc.db_recordCount(tableList,"regions")>=3000)
        self.assertTrue(loc.db_recordCount(tableList,"City_wikidata")>=100000)

    def testWikidataCountries(self):
        '''
        test getting country information from wikidata
        '''
        wikidata=Wikidata()
        wikidata.getCountries()
        self.assertTrue(len(wikidata.countryList)>=190)

    def testWikidataCities(self):
        '''
        test getting city information from wikidata
        
1372    Singapore
749    Beijing, China
704    Paris, France
649    Barcelona, Spain
625    Rome, Italy
616    Hong Kong
575    Bangkok, Thailand
502    Vienna, Austria
497    Athens, Greece
483    Shanghai, China
        '''
        # Wikidata time outs in CI environment need to be avoided
        return 
        if getpass.getuser()!="wf":
            return
        regions=[
            {"name": "Singapore", "country": "Q334", "region": None, "cities":46},
            {"name": "Beijing", "country": None, "region": "Q956", "cities":25},
            {"name": "Paris","country": None, "region": "Q13917", "cities":1242},
            {"name": "Barcelona","country": None, "region": "Q5705", "cities":1242},
            {"name": "Rome","country": None, "region": "Q1282", "cities":1242}
        ]
        wikidata=Wikidata()
        if getpass.getuser()=="wf":
            # use 2018 wikidata copy
            wikidata.endpoint="http://blazegraph.bitplan.com/sparql"
            # use 2020 wikidata copy
            #wikidata.endpoint="http://jena.zeus.bitplan.com/wikidata"
        for region in regions:
            starttime=time.time()
            print("searching cities for %s" % region["name"])
            cityList=wikidata.getCities(country=region["country"], region=region["region"])
            print("Found %d cities for %s in %5.1f s" % (len(cityList),region["name"],time.time()-starttime))
            if self.debug:
                print(cityList[:10])
            #self.assertEqual(region['cities'],len(cityList))
            pass
        
    def test_WikiDataCityListViaBlazegraph(self):
        queryString="""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
SELECT ?city ?cityLabel ?cityPop ?geoNameId
WHERE {
  # geoName Identifier
  ?city wdt:P1566 ?geoNameId.
  # instance of human settlement https://www.wikidata.org/wiki/Q486972
  ?city wdt:P31/wdt:P279* wd:Q486972 .
  # population of city
  OPTIONAL { ?city wdt:P1082 ?cityPop.}

  # label of the City
  ?city rdfs:label ?cityLabel filter (lang(?cityLabel) = "en").
}"""
        if getpass.getuser()=="wf":
            wikidata=Wikidata()
            # use 2018 wikidata copy
            wikidata.endpoint="http://blazegraph.bitplan.com/sparql"
            print("getting city population getonames crossref")
            starttime=time.time()
            wd=SPARQL(wikidata.endpoint)
            results=wd.query(queryString)
            cityList=wd.asListOfDicts(results)
            print("Found %d cities  in %5.1f s" % (len(cityList),time.time()-starttime))
            loc=Locator.getInstance()
            dbFile=loc.db_path+"/city_wikidata_population.db"
            sqlDB=SQLDB(dbFile)
            entityInfo=sqlDB.createTable(cityList[:100],"cities",primaryKey=None,withDrop=True)
            sqlDB.store(cityList,entityInfo,fixNone=True)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
