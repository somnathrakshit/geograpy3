'''
Created on 2020-09-20

@author: wf
'''
import unittest
from geograpy.locator import Locator
from lodstorage.sql import SQLDB

class TestPrefixTree(unittest.TestCase):
    '''
    test prefix tree algorithm
    '''

    def setUp(self):
        self.debug=True


    def tearDown(self):
        pass

    def testPrefixTree(self):
        '''
        test the prefix Tree
        '''
        Locator.resetInstance()
        loc=Locator.getInstance()
        # use in memory database for test
        sqlDB=SQLDB()
        loc.populate_Cities(sqlDB)
        loc.getWikidataCityPopulation(sqlDB)
        loc.createViews(sqlDB)
        trie=loc.populate_PrefixTree(sqlDB,loc.getView())
        if self.debug:
            print("found %d city names" % trie.getCount())
       
        prefixes=['New','Las','San','Hong']
        expected=[224,71,378,0]
        for index,prefix in enumerate(prefixes):
            count=trie.countStartsWith(prefix)
            if self.debug:
                print ("there are %3d cities with prefix %s" % (count,prefix))
            #self.assertEqual(expected[index],count)
        ambig=loc. populate_PrefixAmbiguities(sqlDB,loc.getView())
        self.assertEqual(325,len(ambig))
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()