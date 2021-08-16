'''
Created on 16.08.2021

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from geograpy.locator import RegionManager,LocationContext
from geograpy.wikidata import Wikidata
import json
import os
import getpass
from aniso8601.builders import Limit
class TestCachingCitiesByRegion(Geograpy3Test):


    def setUp(self):
        pass


    def tearDown(self):
        pass
    
    def cacheRegionCities2Json(self,limit):
        wd=Wikidata()
        config=LocationContext.getDefaultConfig()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        regionList=regionManager.getList()   
        total=len(regionList) 
        cachePath=config.getCachePath()
        for index,region in enumerate(regionList):
            if index>=limit:
                break
            regionId=region.regionId
            msg=f"{index+1:4d}/{total:4d}:getting cities for {region.region}{region.regionIsoCode}"
            jsonFileName=f"{cachePath}/regions/{region.regionIsoCode}.json"
            if os.path.isfile(jsonFileName):
                print(msg)
            else:
                try:
                    regionCities=wd.getCitiesForRegion(regionId, msg)
                    jsonStr=json.dumps(regionCities)
                    with open(jsonFileName,"w") as jsonFile:
                        jsonFile.write(jsonStr)
                except Exception as ex:
                    self.handleWikidataException(ex)
                    
   


    def testGetCitiesByRegion(self):
        '''
        test counting human settlement types
        '''
        limit=5000 if getpass.getuser()=="wf" else 50
        self.cacheRegionCities2Json(limit=limit)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()