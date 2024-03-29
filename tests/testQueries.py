"""
Created on 2021-08-19

@author: wf
"""
import os
import re
import unittest

from lodstorage.query import Query, QueryManager

from geograpy.locator import LocationContext, Locator
from tests.basetest import Geograpy3Test


class TestQueries(Geograpy3Test):
    """
    test queries for documentation, bug reports and the like
    """

    def getQueryManager(self):
        """
        get the query manager
        """
        cachedir = LocationContext.getDefaultConfig().getCachePath()
        scriptDir = os.path.dirname(__file__)
        for path in cachedir, f"{scriptDir}/../geograpy/data":
            qYamlFile = f"{path}/queries.yaml"
            if os.path.isfile(qYamlFile):
                qm = QueryManager(lang="sql", debug=self.debug, queriesPath=qYamlFile)
                return qm
        return None

    def documentQueryResult(self, query, lod, tablefmt, show=False):
        """
        document the query results
        """
        for record in lod:
            for key in record.keys():
                value = record[key]
                if value is not None:
                    if isinstance(value, str):
                        if re.match(r"Q[0-9]+", value):
                            if tablefmt == "github":
                                record[
                                    key
                                ] = f"[{value}](https://www.wikidata.org/wiki/{value})"
                            elif tablefmt == "mediawiki":
                                record[
                                    key
                                ] = f"[https://www.wikidata.org/wiki/{value} {value}]"
        doc = query.documentQueryResult(lod, tablefmt=tablefmt, floatfmt=".0f")
        if show:
            print(doc)

    def testQueries(self):
        """
        test preconfigured queries
        """
        qm = self.getQueryManager()
        self.assertIsNotNone(qm)
        locator = Locator.getInstance()
        show = self.debug
        # show=True
        for _name, query in qm.queriesByName.items():
            qlod = locator.sqlDB.query(query.query)
            for tablefmt in ["mediawiki", "github"]:
                self.documentQueryResult(query, qlod, tablefmt, show=show)

        pass

    def testQuery(self):
        """
        test a single query
        """
        queries = [
            (
                "LocationLabel Count",
                """select count(*),hierarchy 
from location_labels
group by hierarchy""",
            ),
            ("NY example", "select * from cityLookup where label='New York City'"),
            (
                "Berlin example",
                "select * from cityLookup where label='Berlin' order by pop desc,regionName",
            ),
            (
                "Issue #25",
                "select * from countryLookup where label in ('France', 'Hungary', 'Poland', 'Spain', 'United Kingdom')",
            ),
            (
                "Issue #25 Bulgaria",
                "select * from cityLookup where label in ('Bulgaria','Croatia','Hungary','Czech Republic') order by pop desc,regionName",
            ),
        ]
        for tableName in ["countries", "regions", "cities"]:
            queries.append(
                (
                    f"unique wikidataids for {tableName}",
                    f"select count(distinct(wikidataid)) as wikidataids from {tableName}",
                )
            )
            queries.append(
                (
                    f"total #records for {tableName}",
                    f"select count(*) as recordcount from {tableName}",
                )
            )
        locator = Locator.getInstance()
        for title, queryString in queries:
            query = Query(name=title, query=queryString, lang="sql")
            qlod = locator.sqlDB.query(queryString)
            for tablefmt in ["mediawiki", "github"]:
                self.documentQueryResult(query, qlod, tablefmt, show=True)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
