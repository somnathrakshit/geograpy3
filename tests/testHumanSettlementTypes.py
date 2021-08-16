'''
Created on 16.08.2021

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from geograpy.locator import RegionManager,LocationContext
from geograpy.wikidata import Wikidata

class TestHumanSettlementTypes(Geograpy3Test):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testHsCounting(self):
        '''
        test counting human settlement types
        '''
        config=LocationContext.getDefaultConfig()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        wd=Wikidata()
        limit=25
        index=0
        for region in regionManager.getList():
            index+=1
            regionId=region.regionId
            queryString="""# human settlements in norther island
SELECT distinct ?region ?regionLabel ?hsType ?hsTypeLabel ?hsCount WHERE { 
  VALUES ?hsType {
      wd:Q1549591 wd:Q515 wd:Q1637706 wd:Q1093829 wd:Q486972 wd:Q532
  }
  {
    
    SELECT ?region ?hsType (count(?hs) as ?hsCount)
    WHERE {   
       VALUES ?region {
         wd:%s
       }  
       ?hs wdt:P131* ?region.
       ?hsType ^wdt:P279*/^wdt:P31 ?hs.
    } GROUP by ?hsType ?region
  }             
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}""" % regionId
            regionCounts=wd.query(f"getting hstype counts for {region.region}", queryString)
            if index>=limit:
                break



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()