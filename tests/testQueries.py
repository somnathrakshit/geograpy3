'''
Created on 2021-08-19

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from lodstorage.query import QueryManager
from lodstorage.sql import EntityInfo
from lodstorage.query import Query
from geograpy.locator import LocationContext, Locator
import os
from tabulate import tabulate

class TestQueries(Geograpy3Test):
    '''
    test queries for documentation, bug reports and the like
    '''

    def getQueryManager(self):
        '''
        get the query manager
        '''
        cachedir=LocationContext.getDefaultConfig().getCachePath()
        scriptDir=os.path.dirname(__file__)
        for path in cachedir,f"{scriptDir}/../geograpy/data":
            qYamlFile=f"{path}/queries.yaml"
            if os.path.isfile(qYamlFile):
                qm=QueryManager(lang='sql',debug=self.debug,path=path)
                return qm
        return None
        
     
    def testQueries(self):
        '''
        test preconfigured queries
        '''
        show=self.debug
        qm=self.getQueryManager()
        self.assertIsNotNone(qm)
        locator=Locator.getInstance()
        for _name,query in qm.queriesByName.items():
            lod=locator.sqlDB.query(query.query) 
            for tablefmt in ["mediawiki","github"]:
                doc=query.documentQueryResult(lod,tablefmt=tablefmt,floatfmt=".0f")
                if show:
                    print(doc)
        pass
    
    def testQuery(self):
        '''
        test a single query
        '''
        show=True
        queries=[("LocationLabel Count","""select count(*),hierarchy 
from location_labels
group by hierarchy"""),("NY example","select * from cityLookup where label='New York City'")]
        for tableName in ["countries","regions","cities"]:
            queries.append((f"unique wikidataids for {tableName}",f"select count(distinct(wikidataid)) as wikidataids from {tableName}"))
            queries.append((f"total #records for {tableName}",f"select count(*) as recordcount from {tableName}"))            
        locator=Locator.getInstance()
        for title,queryString in queries:
            lod=locator.sqlDB.query(queryString) 
            for tablefmt in ["mediawiki","github"]:
                query=Query(name=title,query=queryString,lang="sql")
                doc=query.documentQueryResult(lod,tablefmt=tablefmt)
                if show:
                    print(doc)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()