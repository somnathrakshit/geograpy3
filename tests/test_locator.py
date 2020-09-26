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
        self.debug=False
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
"""     
        loc.populate_db()
        isocodeRecords=loc.sqlDB.query(query)
        for isocodeRecord in isocodeRecords:
            isocode=isocodeRecord['isocode']
            if isocode:
                self.assertTrue(loc.isISO(isocode))
        
        
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
        
        
        
    def testExamples(self):
        '''
        test examples
        '''
        Locator.resetInstance()
        Locator.useWikiData=False
        examples=['Amsterdam, Netherlands', 'Vienna, Austria','Vienna IL','Paris - Texas', 'Paris TX',
                  'Austin, TX','Austin Texas','Auckland, New Zealand']
        countries=['NL','AT','US','US','US','US','US','NZ']
        for index,example in enumerate(examples):
            city=geograpy.locate(example)
            if self.debug:
                print("%22s->%s" % (example,city))
            self.assertEqual(countries[index],city.country.iso)
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
