import math
import unittest
from lodstorage.sql import SQLDB
from tests.basetest import Geograpy3Test
from geograpy.locator import RegionManager, LocationContext, CountryManager, CityManager
from geograpy.wikidata import Wikidata


class TestCachingCitiesByRegion(Geograpy3Test):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCacheLocationLabels(self):
        wd=Wikidata()
        config = LocationContext.getDefaultConfig()
        countryManager=CountryManager(config=config)
        regionManager = RegionManager(config=config)
        cityManager=CityManager(config=config)
        sqlDb=SQLDB(dbname=config.cacheFile, debug=self.debug)
        for manager in countryManager, regionManager, cityManager:
            manager.fromCache()
            wikidataIdQuery = f"SELECT DISTINCT wikidataid FROM {manager.entityPluralName}"
            wikidataIdQueryRes = sqlDb.query(wikidataIdQuery)
            wikidataIds = [l['wikidataid'] for l in wikidataIdQueryRes]

            chunkSize=1000
            iterations = math.ceil(len(wikidataIds) / chunkSize)
            progress = 0
            res=[]
            for i in range(iterations):
                workOnIds = wikidataIds[i * chunkSize:(i + 1) * chunkSize]
                progress += len(workOnIds)
                index = 0
                values = ""
                for location in workOnIds:
                    spacer = "  \n\t\t\t" if index % 10 == 0 else " "
                    values += f"{spacer}wd:{wd.getWikidataId(location)}"
                    index += 1
                query = self.getLablesQuery(values=values)
                res.extend(wd.query(f"Query {i}/{iterations} - Querying {manager.entityName} Labels", queryString=query))
            wd.store2DB(res, tableName=f"{manager.entityName}_labels", sqlDB=sqlDb)
        self.createViews(sqlDB=sqlDb)


    def getLablesQuery(self, values:str):
        query = """SELECT DISTINCT ?locationId ?label
            WHERE{
                VALUES ?wikidataid {%s}
                ?wikidataid rdfs:label|skos:altLabel ?label
                FILTER(lang(?label)="en")
            }""" % values
        return query

    def createViews(self, sqlDB):
        viewDDLs = ["DROP VIEW IF EXISTS location_labels", """
                CREATE VIEW location_labels AS 
                SELECT *, "Country" AS "hierarchy" 
                FROM country_labels 
                UNION 
                SELECT *, "Region" AS "hierarchy" 
                FROM region_labels 
                UNION 
                SELECT *, "City" AS "hierarchy" 
                FROM city_labels
        """]
        for viewDDL in viewDDLs:
            sqlDB.execute(viewDDL)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()