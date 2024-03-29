"""
Created on 2021-08-17

@author: th
"""
import math
import unittest

from lodstorage.sql import SQLDB

from geograpy.locator import CityManager, CountryManager, LocationContext, RegionManager
from geograpy.wikidata import Wikidata
from tests.basetest import Geograpy3Test


class TestCachingLocationLabels(Geograpy3Test):
    """
    adds location label tables

    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCacheLocationLabels(self):
        """
        Generates the location label tabels in the SQL db fro countries, regions and cities by querying wikidata for
        the rdfs:label and skos:altLa of each location.
        A view containing all location labels is also created.
        """
        testLocationLabelExtraction = False
        if testLocationLabelExtraction:
            wd = Wikidata()
            config = LocationContext.getDefaultConfig()
            countryManager = CountryManager(config=config)
            regionManager = RegionManager(config=config)
            cityManager = CityManager(config=config)
            sqlDb = SQLDB(dbname=config.cacheFile, debug=self.debug)
            for manager in countryManager, regionManager, cityManager:
                manager.fromCache()
                wikidataIdQuery = (
                    f"SELECT DISTINCT wikidataid FROM {manager.entityPluralName}"
                )
                wikidataIdQueryRes = sqlDb.query(wikidataIdQuery)
                wikidataIds = [l["wikidataid"] for l in wikidataIdQueryRes]

                chunkSize = 1000
                iterations = math.ceil(len(wikidataIds) / chunkSize)
                progress = 0
                res = []
                for i in range(iterations):
                    workOnIds = wikidataIds[i * chunkSize : (i + 1) * chunkSize]
                    progress += len(workOnIds)
                    index = 0
                    values = ""
                    for location in workOnIds:
                        spacer = "  \n\t\t\t" if index % 10 == 0 else " "
                        values += f"{spacer}wd:{wd.getWikidataId(location)}"
                        index += 1
                    query = self.getLablesQuery(values)
                    res.extend(
                        wd.query(
                            f"Query {i}/{iterations} - Querying {manager.entityName} Labels",
                            queryString=query,
                        )
                    )
                wd.store2DB(res, tableName=f"{manager.entityName}_labels", sqlDB=sqlDb)
            self.createViews(sqlDB=sqlDb)

    def getLablesQuery(self, wikidataIds: str):
        """
        get the query for the alternatives labels for the given values

        wikidataIds(str): a list of wikidataids
        """
        query = (
            """# get alternative labels for the given wikidata 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wd: <http://www.wikidata.org/entity/>
SELECT DISTINCT ?wikidataid ?label ?lang
WHERE{
  VALUES ?wikidataid { %s }
  ?wikidataid rdfs:label|skos:altLabel ?label
  BIND(lang(?label) AS ?lang)
  FILTER(lang(?label)="en")
}"""
            % wikidataIds
        )
        return query

    def createViews(self, sqlDB):
        viewDDLs = [
            "DROP VIEW IF EXISTS location_labels",
            """
                CREATE VIEW location_labels AS 
                SELECT *, "Country" AS "hierarchy" 
                FROM country_labels 
                UNION 
                SELECT *, "Region" AS "hierarchy" 
                FROM region_labels 
                UNION 
                SELECT *, "City" AS "hierarchy" 
                FROM city_labels
        """,
            "DROP INDEX if EXISTS cityLabelByWikidataid",
            "CREATE INDEX cityLabelByWikidataid ON city_labels (wikidataid)",
            "DROP INDEX if EXISTS regionLabelByWikidataid",
            "CREATE INDEX regionLabelByWikidataid ON region_labels (wikidataid)",
            "DROP INDEX if EXISTS countryLabelByWikidataid",
            "CREATE INDEX countryLabelByWikidataid ON country_labels (wikidataid)",
        ]
        for viewDDL in viewDDLs:
            sqlDB.execute(viewDDL)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
