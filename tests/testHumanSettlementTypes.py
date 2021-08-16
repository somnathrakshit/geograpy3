'''
Created on 16.08.2021

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from geograpy.locator import RegionManager,LocationContext
from geograpy.wikidata import Wikidata
import json
class TestHumanSettlementTypes(Geograpy3Test):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testCitiesByRegion(self):
        '''
        test counting human settlement types
        '''
        config=LocationContext.getDefaultConfig()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        wd=Wikidata()
        limit=5000
        regionList=regionManager.getList()   
        total=len(regionList) 
        for index,region in enumerate(regionList):
            regionId=region.regionId
            queryString="""SELECT distinct ?cityQ ?cityQLabel ?geoNameId ?gndId ?regionId ?countryId ?cityCoord ?cityPopulation WHERE { 
  VALUES ?hsType {
      wd:Q1549591 wd:Q3957 wd:Q5119 wd:Q15284 wd:Q62049 wd:Q515 wd:Q1637706 wd:Q1093829 wd:Q486972 wd:Q532
  }
  VALUES ?region {
         wd:%s
  }  
  ?cityQ wdt:P131* ?region.
  ?hsType ^wdt:P279*/^wdt:P31 ?cityQ.
   
  # geoName Identifier
  OPTIONAL {
      ?cityQ wdt:P1566 ?geoNameId.
  }

  # GND-ID
  OPTIONAL { 
      ?cityQ wdt:P227 ?gndId. 
  }
  
  OPTIONAL{
     ?cityQ wdt:P625 ?cityCoord .
  }
  
  # region this city belongs to
  OPTIONAL {
    ?cityQ wdt:P131 ?regionId .     
  }
  
  OPTIONAL {
     ?cityQ wdt:P1082 ?cityPopulation
  }

  # country this city belongs to
  OPTIONAL {
      ?cityQ wdt:P17 ?countryId .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}""" % regionId
            regionCities=wd.query(f"{index+1:4d}/{total:4d}:getting cities for {region.region}{region.regionIsoCode}", queryString)
            cachePath=config.getCachePath()
            jsonFileName=f"{cachePath}/regions/{region.regionIsoCode}.json"
            jsonStr=json.dumps(regionCities)
            with open(jsonFileName,"w") as jsonFile:
                jsonFile.write(jsonStr)
            if index>=limit:
                break



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()