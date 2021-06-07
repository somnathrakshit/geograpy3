'''
Created on 2020-09-19

@author: wf
'''
import unittest
import geograpy
import getpass
from geograpy.locator import Locator
from collections import Counter
from lodstorage.uml import UML
import os
import re

class TestLocator(unittest.TestCase):
    '''
    test the Locator class from the location module
    '''
    def setUp(self):
        self.debug=True
        pass

    def tearDown(self):
        pass

    def testGeolite2Cities(self):
        '''
        test the locs.db cache for cities
        '''
        loc=Locator()
        cities=loc.getGeolite2Cities()
        if self.debug:
            print("Found %d cities " % len(cities)) 
        self.assertEqual(121223,len(cities))
        pass
    
    def testHasData(self):
        '''
        check has data and populate functionality
        '''
        loc=Locator()
        if os.path.isfile(loc.db_file):
            os.remove(loc.db_file)
        # reinit sqlDB
        loc=Locator()
        self.assertFalse(loc.db_has_data())
        loc.populate_db()
        self.assertTrue(loc.db_has_data())
        
    def testIsoRegexp(self):
        '''
        test regular expression for iso codes
        '''
        loc=Locator.getInstance()
        self.assertFalse(loc.isISO('Singapore'))   
         
        query="""
        select distinct country_iso_code as isocode from cities 
union
select distinct subdivision_1_iso_code as isocode from cities 
union 
select distinct subdivision_1_iso_code as isocode from cities
union 
select distinct countryIsoCode as isocode from countries
union 
select distinct regionIsoCode as isocode from regions
"""     
        loc.populate_db()
        isocodeRecords=loc.sqlDB.query(query)
        for isocodeRecord in isocodeRecords:
            isocode=isocodeRecord['isocode']
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
        query="SELECT city_name AS name from CITIES"
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
        
    def testPopulation(self):
        '''
        test adding population data from wikidata to GeoLite2 information
        '''
        Locator.resetInstance()
        loc=Locator.getInstance()  
        loc.populate_db()
        endpoint=None
        user=getpass.getuser()
        if self.debug:
            print ("current user is %s" % user)
        # uncomment to refresh using wikidata
        # please note https://github.com/RDFLib/sparqlwrapper/issues/163 hits as of 2020-09
        # endpoint='https://query.wikidata.org/sparql'
        # uncomment to use your own wikidata copy as an endpoint
        # if user=="wf":
            # use 2020 Apache Jena based wikidata copy
            #endpoint="http://jena.zeus.bitplan.com/wikidata"
            # use 2018 Blazegraph based wikidata copy
            #endpoint="http://blazegraph.bitplan.com/sparql"
        loc.getWikidataCityPopulation(loc.sqlDB,endpoint)
        tableList=loc.sqlDB.getTableList()
        uml=UML()
        title="""geograpy Tables
2020-09-26
[[https://github.com/somnathrakshit/geograpy3 © 2020 geograpy3 project]]"""
        plantUml=uml.tableListToPlantUml(tableList,title=title, packageName="geograpy3")
        if self.debug:
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
            
    def testIssue15(self):
        '''
        https://github.com/somnathrakshit/geograpy3/issues/15
        test Issue 15 Disambiguate via population, gdp data
        '''
        examples=['Paris','Vienna']
        countries=['FR','AT']
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
            print(places)
            city=geograpy.locateCity(example,debug=False)
            print(city)
        
        
    def testDelimiters(self):
        '''
        test the delimiter statistics for names
        '''
        loc=Locator.getInstance()
        loc.populate_db()
        
        ddls=["DROP VIEW IF EXISTS allNames","""CREATE VIEW allNames as select countryLabel as name from countries
        union select regionLabel as name from regions
        union select city_name as name from cities
        union select cityLabel as name from cityPops"""]
        for ddl in ddls:
            loc.sqlDB.execute(ddl)
        query="SELECT name from allNames"
        nameRecords=loc.sqlDB.query(query)
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

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
