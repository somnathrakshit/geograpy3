'''
Created on 2020-09-19

@author: wf
'''

import unittest


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
    
    def testCityLookup(self):
        '''
        test the cityLookup to city/region/country object cluster 
        '''
        loc=Locator.getInstance()
        loc.populate_db()
        queryString="SELECT * FROM CityLookup where name in ('Berlin','Paris') ORDER by pop desc"
        cityLookupRecords=loc.sqlDB.query(queryString)
        berlinFound=False
        parisFound=False
        for cityLookupRecord in cityLookupRecords:
            city=City.fromCityLookup(cityLookupRecord)
            if city.pop is not None:
                if city.name=="Berlin" and city.pop>3644000:
                    berlinFound=True
                if city.name=="Paris" and city.pop>2175000:
                    parisFound=True
            if self.debug:
                print(f"{city}:{city.pop}")
        self.assertTrue(berlinFound)
        self.assertTrue(parisFound)
         
        
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
        examples=['Paris','Vienna']
        countries=['FR','AT']
        # TODO: Berlin, DE fails
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
        countries=['MX','GB','PR']
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

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
