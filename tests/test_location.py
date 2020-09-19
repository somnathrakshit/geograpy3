'''
Created on 2020-09-19

@author: wf
'''
import unittest
from geograpy.location import Location
import os

class TestLocation(unittest.TestCase):
    '''
    test the Location class from the location module
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
        loc=Location()
        cities=loc.getGeolite2Cities()
        if self.debug:
            print("Found %d cities " % len(cities)) 
        self.assertEqual(121223,len(cities))
        pass
    
    def testHasData(self):
        '''
        check has data and populate functionality
        '''
        loc=Location()
        if os.path.isfile(loc.db_file):
            os.remove(loc.db_file)
        # reinit sqlDB
        loc=Location()
        self.assertFalse(loc.db_has_data())
        loc.populate_db()
        self.assertTrue(loc.db_has_data())

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()