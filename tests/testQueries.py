'''
Created on 2021-08-19

@author: wf
'''
import unittest
from tests.basetest import Geograpy3Test
from lodstorage.query import QueryManager
from lodstorage.sql import EntityInfo
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
    
    def documentQuery(self,title:str,query:str,lod:list,tablefmt:str="mediawiki",withSourceCode=True,**kwArgs):
        '''
        document the given query
        
        Args:
            title(str): the title to use
            query(str): the SQL query
            lod: the list of dicts result
            tablefmt(str): the table format to use
            withSourceCode(bool): if True document the source code
            
        Return:
            str(
        '''
        if withSourceCode:
            sourceCode=""
            if tablefmt=="github":
                sourceCode=f"""```sql
{query}
```"""
            if tablefmt=="mediawiki":
                sourceCode=f"""== {title} ==
<source lang='sql'>
{query}
</source>
"""
            print (sourceCode)
        tab=tabulate(lod,headers="keys",tablefmt=tablefmt,**kwArgs)
        print(tab)
        
     
    def testQueries(self):
        '''
        test preconfigured queries
        '''
        qm=self.getQueryManager()
        self.assertIsNotNone(qm)
        locator=Locator.getInstance()
        for name,query in qm.queriesByName.items():
            lod=locator.sqlDB.query(query.query) 
            for tablefmt in ["mediawiki","github"]:
                self.documentQuery(name,query.query,lod,tablefmt=tablefmt,floatfmt=".0f")
        pass
    
    def testQuery(self):
        '''
        test a single query
        '''
        queries=[("LocationLabel Count","""select count(*),hierarchy 
from location_labels
group by hierarchy""")]
        for tableName in ["countries","regions","cities"]:
            queries.append((f"unique wikidataids for {tableName}",f"select count(distinct(wikidataid)) as wikidataids from {tableName}"))
            queries.append((f"total #records for {tableName}",f"select count(*) as recordcount from {tableName}"))            
        locator=Locator.getInstance()
        for title,query in queries:
            lod=locator.sqlDB.query(query) 
            for tablefmt in ["mediawiki"]:
                self.documentQuery(title,query,lod,tablefmt=tablefmt)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()