'''
Created on 2020-09-19

@author: wf
'''
import unittest
import geograpy
from geograpy.locator import Locator
from collections import Counter
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
        print ("found %d names" % len(nameRecords))
        wc=Counter()
        for nameRecord in nameRecords:
            name=nameRecord['name']
            words=re.split(r"\W+",name)
            wc[len(words)]+=1
        print (wc.most_common(20))
        
    def testExamples(self):
        '''
        test examples
        '''
        examples=['Amsterdam, Netherlands', 'Vienna, Austria','Vienna IL','Paris - Texas', 'Paris TX']
        countries=['NL','AT','US','US','US']
        for index,example in enumerate(examples):
            city=geograpy.locate(example)
            if self.debug:
                print(city)
            self.assertEquals(countries[index],city.country.iso)
            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()