'''
Created on 2020-09-23

@author: wf
'''
import unittest
from geograpy.wikidata import Wikidata
from geograpy.locator import Locator

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
        loc=Locator.getInstance()
        loc.populate_db()
    
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
        '''
        wikidata=Wikidata()
        wikidata.getCities()
        if self.debug:
            print(wikidata.cityList)
        self.assertEquals(1,len(wikidata.cityList))
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()