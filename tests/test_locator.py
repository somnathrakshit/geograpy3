'''
Created on 2020-09-19

@author: wf
'''
import os.path
import tempfile
import unittest
from pathlib import Path

from lodstorage.storageconfig import StorageConfig

import geograpy
import getpass
from geograpy.locator import Locator, City,CountryManager, Location, LocationContext
from collections import Counter
from lodstorage.uml import UML
import re
from tests.basetest import Geograpy3Test

class TestLocator(Geograpy3Test):
    '''
    test the Locator class from the location module
    '''   
    
    def lookupQuery(self,viewName,whereClause):
        loc=Locator.getInstance()
        queryString=f"SELECT * FROM {viewName} where {whereClause} AND pop is not NULL ORDER by pop desc"
        lookupRecords=loc.sqlDB.query(queryString)
        return lookupRecords
    
    def checkExpected(self,lod,expected):
        emap={}
        found={}
        for key,value in expected:
            emap[key]=value
        for record in lod:
            name=record["name"]
            pop=record["pop"]
            if name in emap and pop> emap[name]:
                found[name]=record
                if self.debug:
                    print(f"{name}:{pop:.0f}")
    
        self.assertEqual(len(found),len(emap))
        
    def testHasViews(self):
        '''
        test that the views are available
        '''
        loc=Locator.getInstance()
        viewsMap=loc.sqlDB.getTableDict(tableType="view")
        for view in ["CityLookup","RegionLookup","CountryLookup"]:
            self.assertTrue(view in viewsMap)
       
    
    def testCityLookup(self):
        '''
        test the cityLookup to city/region/country object cluster 
        '''
        cityLookupRecords=self.lookupQuery("CityLookup", "label in ('Berlin','Paris','Athens','Singapore')")
        expected=[("Berlin",3644000),("Paris",2175000),("Athens",600000),("Singapore",5800000)]
        self.checkExpected(cityLookupRecords,expected)   
         
    def testRegionLookup(self):
        '''
        test region Lookup
        '''   
        regionLookupRecords=self.lookupQuery("RegionLookup", "label in ('CA')")
        expected=[("California",39000000)]
        self.checkExpected(regionLookupRecords,expected) 
        
    def testCountryLookup(self):
        '''
        test country Lookup
        '''
        #self.debug=True
        countryLookupRecords=self.lookupQuery("CountryLookup", "label in ('CA')")
        expected=[("Canada",37000000)]
        self.checkExpected(countryLookupRecords,expected) 
        
    def testIsoRegexp(self):
        '''
        test regular expression for iso codes
        '''
        loc=Locator.getInstance()
        self.assertFalse(loc.isISO('Singapore'))   
         
        query="""
select distinct iso from countries
union 
select distinct iso from regions
"""     
        loc.populate_db()
        isocodeRecords=loc.sqlDB.query(query)
        for isocodeRecord in isocodeRecords:
            isocode=isocodeRecord['iso']
            if isocode:
                isIso=loc.isISO(isocode)
                if not isIso and self.debug:
                    print(isocode)
                self.assertTrue(isIso)
        
    def testWordCount(self):
        '''
        test the word count 
        '''
        loc=Locator.getInstance()
        query="SELECT name from CITIES"
        nameRecords=loc.sqlDB.query(query)
        if self.debug:
            print ("testWordCount: found %d names" % len(nameRecords))
        wc=Counter()
        for nameRecord in nameRecords:
            name=nameRecord['name']
            words=re.split(r"\W+",name)
            wc[len(words)]+=1
        if self.debug:
            print ("most common 20: %s" % wc.most_common(20))
        
    def testUML(self):
        '''
        test adding population data from wikidata to GeoLite2 information
        '''
        Locator.resetInstance()
        loc=Locator.getInstance()  
        loc.populate_db()
        user=getpass.getuser()
        if self.debug:
            print ("current user is %s" % user)
        tableList=loc.sqlDB.getTableList()
        uml=UML()
        title="""geograpy Tables
2021-08-13
[[https://github.com/somnathrakshit/geograpy3 © 2020-2021 geograpy3 project]]"""
        plantUml=uml.tableListToPlantUml(tableList,title=title, packageName="geograpy3")
        showUml=True
        if showUml or self.debug:
            print (plantUml)
            
    def checkExamples(self,examples,countries,debug=False,check=True):
        '''
        
        check that the given example give results in the given countries
        Args:
            examples(list): a list of example location strings
            countries(list): a list of expected country iso codes
        '''
        for index,example in enumerate(examples):
            city=geograpy.locateCity(example,debug=debug)
            if self.debug:
                print("%3d: %22s->%s" % (index,example,city))
            if check:
                self.assertEqual(countries[index],city.country.iso) 
                
    def testGetCountry(self):
        '''
        test getting a country by name or ISO
        '''
        locator=Locator()
        debug=True
        examples=[("DE","Germany"),("US","United States of America"),("USA",None)]
        for name,expectedName in examples:
            country=locator.getCountry(name)
            if debug:
                print(country)
            if expectedName is None:
                self.assertIsNone(country)
            else:
                self.assertIsNotNone(country)
                self.assertEqual(expectedName,country.name)
            
    def testIssue15(self):
        '''
        https://github.com/somnathrakshit/geograpy3/issues/15
        test Issue 15 Disambiguate via population, gdp data
        '''
        examples=['Paris','Vienna', 'Berlin']
        countries=['FR','AT', 'DE']
        self.checkExamples(examples, countries)
        pass
    
    def testIssue17(self):
        '''
        test issue 17:
        
        https://github.com/somnathrakshit/geograpy3/issues/17
        
        [BUG] San Francisco, USA and Auckland, New Zealand should be locatable #17
        '''
        examples=['San Francisco, USA','Auckland, New Zealand']
        countries=['US','NZ']
        self.checkExamples(examples, countries)
        
    def testIssue19(self):
        '''
        test issue 19
        '''
        examples=['Puebla City, Mexico','Newcastle, UK','San Juan, Puerto Rico']
        countries=['MX','GB','US']
        # For Puerto Rico exist two iso codes one as country and one as US region see https://en.wikipedia.org/wiki/Puerto_Rico in the dataset it is recognized as US region
        self.checkExamples(examples, countries)
        
    
        
    def testStackOverflow64379688(self):
        '''
        compare old and new geograpy interface
        '''
        examples=['John Doe 160 Huntington Terrace Newark, New York 07112 United States of America',
                  'John Doe 30 Huntington Terrace Newark, New York 07112 USA',
                  'John Doe 22 Huntington Terrace Newark, New York 07112 US',
                  'Mario Bianchi, Via Nazionale 256, 00148 Roma (RM) Italia',
                  'Mario Bianchi, Via Nazionale 256, 00148 Roma (RM) Italy',
                  'Newark','Rome']
        for example in examples:
            city=geograpy.locateCity(example,debug=False)
            if self.debug:
                print(city)
            
    def testStackOverflow64418919(self):
        '''
        https://stackoverflow.com/questions/64418919/problem-retrieving-region-in-us-with-geograpy3
        '''
        examples=['Seattle']
        for example in examples:
            city=geograpy.locateCity(example,debug=False)
            print(city)
        
    def testProceedingsExample(self):
        '''
        test a proceedings title Example
        '''
        examples=['''Proceedings of the 
IEEE 14th International Conference on 
Semantic Computing, ICSC 2020, 
San Diego, CA, USA, 
February 3-5, 2020''']
        for example in examples:
            places = geograpy.get_place_context(text=example) 
            if self.debug:
                print(places)
            city=geograpy.locateCity(example,debug=False)
            if self.debug:
                print(city)
        
        
    def testDelimiters(self):
        '''
        test the delimiter statistics for names
        '''
        loc=Locator.getInstance()
        loc.populate_db()
        
        ddls=["DROP VIEW IF EXISTS allNames","""CREATE VIEW allNames as select name from countries
        union select name from regions
        union select name from cities"""]
        for ddl in ddls:
            loc.sqlDB.execute(ddl)
        query="SELECT name from allNames"
        nameRecords=loc.sqlDB.query(query)
        show=self.debug
        show=True
        if show:
            print("found %d name records" % len(nameRecords))
        ordC=Counter()
        for nameRecord in nameRecords:
            name=nameRecord["name"]
            for char in name:
                code=ord(char)
                if code<ord("A"):
                    ordC[code]+=1
        for index,countT in enumerate(ordC.most_common(10)):
            code,count=countT
            if show:
                print ("%d: %d %s -> %d" % (index,code,chr(code),count))
    
    
    def testIssue22(self):  
        '''
        https://github.com/somnathrakshit/geograpy3/issues/22
        '''  
        url='https://en.wikipedia.org/wiki/2012_Summer_Olympics_torch_relay'
        places = geograpy.get_geoPlace_context(url = url)
        if self.debug:
            print(places)
        self.assertTrue(len(places.countries)>5)
        self.assertTrue(len(places.regions)>5)
        self.assertTrue(len(places.cities)>20)
            
        
    def testExamples(self):
        '''
        test examples
        '''
        examples=['Paris, US-TX','Amsterdam, Netherlands', 'Vienna, Austria','Vienna, Illinois, US','Paris, Texas', 
                  'Austin, TX','Austin, Texas',
                  ]
        countries=['US','NL','AT','US','US','US','US']
        self.checkExamples(examples, countries,debug=False)

    def testIssue41_CountriesFromErdem(self):
        '''
        test getting Country list from Erdem

        '''
        countryList=CountryManager.fromErdem()
        self.assertEqual(247,len(countryList.countries))
        if self.debug:
            for country in countryList.countries:
                print(country)
                
    def testIssue_42_distance(self):
        '''
        test haversine and location
        '''
        loc1=Location()
        loc1.lat=0
        loc1.lon=0
        loc2=Location()
        loc2.lat=90
        loc2.lon=0
        d=loc1.distance(loc2)
        #self.debug=True
        if self.debug:
            print(d)
        self.assertAlmostEqual(10007.54,d,delta=0.1)

    def testIssue_59_db_download(self):
        '''
        tests the correct downloading of the backup database in different configurations
        '''
        def getConfig(tmpdir:str):
            config=StorageConfig(cacheFile="locations.db", cacheDirName="geograpyTest", cacheRootDir=tmpdir)
            config.cacheFile=f"{config.getCachePath()}/{config.cacheFile}"
            return config

        def downloadAndTestDB(config:StorageConfig, loc:Locator=None, forceUpdate:bool=False):
            '''downloads and tests the downloaded db'''
            if loc is None:
                loc = Locator(storageConfig=config)
            loc.downloadDB(forceUpdate=forceUpdate)
            self.assertTrue(os.path.exists(config.cacheFile))
            self.assertTrue(loc.db_has_data())
            return loc

        # test downloading with no file in dir
        with tempfile.TemporaryDirectory() as tmpdir:
            config=getConfig(tmpdir)
            downloadAndTestDB(config)

        # test downloading with empty file in dir
        with tempfile.TemporaryDirectory() as tmpdir:
            config=getConfig(tmpdir)
            Path(config.cacheFile).touch()   # create empty file
            loc=downloadAndTestDB(config)

            # test downloading with forceUpdate
            # drop a important table to check if it is restored
            loc.sqlDB.execute("DROP TABLE countries")
            self.assertFalse(loc.db_has_data())
            downloadAndTestDB(config,loc=loc, forceUpdate=True)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
