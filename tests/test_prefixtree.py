'''
Created on 2020-09-20

@author: wf
'''
import unittest
from geograpy.locator import Locator
from geograpy.prefixtree import PrefixTree
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
        loc=Locator.getInstance()
        query="SELECT city_name AS name from CITIES"
        nameRecords=loc.sqlDB.query(query)
        trie=PrefixTree()   
        for nameRecord in nameRecords:
            name=nameRecord['name']
            trie.add(name)
        if self.debug:
            print("found %d city names" % trie.count)
       
        prefixes=['New','Las','San','Hong']
        expected=[172,62,310,0]
        for index,prefix in enumerate(prefixes):
            count=trie.startsWith(prefix)
            if self.debug:
                print ("there are %3d cities with prefix %s" % (count,prefix))
            self.assertEqual(expected[index],count)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()