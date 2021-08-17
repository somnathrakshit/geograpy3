'''
Created on 16.08.2021

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from geograpy.locator import City,CityManager,CountryManager,RegionManager,LocationContext
from geograpy.wikidata import Wikidata
from geograpy.utils import Profiler
import json
import os
import getpass

class TestCachingCitiesByRegion(Geograpy3Test):


    def setUp(self):
        pass


    def tearDown(self):
        pass
    
    def cacheRegionCities2Json(self,limit,showDone=False):
        wd=Wikidata()
        config=LocationContext.getDefaultConfig()
        countryManager= CountryManager(config=config)
        countryManager.fromCache()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        regionList=regionManager.getList()   
        total=len(regionList) 
        cachePath=f"{config.getCachePath()}/regions"
        if not os.path.exists(cachePath):
                os.makedirs(cachePath)
        for index,region in enumerate(regionList):
            if index>=limit:
                break
            regionId=region.wikidataid
            msg=f"{index+1:4d}/{total:4d}:getting cities for {region.name} {region.iso}"
            jsonFileName=f"{cachePath}/{region.iso}.json"
            if os.path.isfile(jsonFileName):
                if showDone:
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
        
    def testReadCachedCitiesByRegion(self):
        '''
        test reading the cached json Files
        '''
        config=LocationContext.getDefaultConfig()
        jsonFiles=CityManager.getJsonFiles(config)
        msg=f"reading {len(jsonFiles)} cached city by region JSON cache files"
        self.assertTrue(len(jsonFiles)>2000)
        profiler=Profiler(msg)
        cityManager=CityManager(config=config)
        cityManager.getList().clear()
        for jsonFileName in jsonFiles:
            with open(jsonFileName) as jsonFile:
                cities4Region = json.load(jsonFile)
                for city4Region in cities4Region:
                    city=City()
                    city.fromDict(city4Region)
                    cityManager.add(city)
                    pass
        cityManager.store()
        profiler.time()
                



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()