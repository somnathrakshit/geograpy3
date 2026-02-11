"""
Created on 2020-09-23

@author: wf
"""
import os
import re

from lodstorage.query import QueryManager
from lodstorage.sparql import SPARQL

from geograpy.utils import Profiler


class Wikidata(object):
    """
    Wikidata access with proper User-Agent and rate limiting
    """

    # Rate limiting constants for Wikidata
    # see https://stackoverflow.com/questions/62396801/how-to-handle-too-many-requests-on-wikidata-using-sparqlwrapper
    CALLS_PER_MINUTE = 30

    def __init__(
        self,
        endpoint="https://query.wikidata.org/sparql",
        profile: bool = True,
        calls_per_minute: int = None
    ):
        """
        Constructor

        Args:
            endpoint(str): the SPARQL endpoint URL
            profile(bool): if True show profiling information
            calls_per_minute(int): rate limit for API calls (default: 30)
        """
        self.endpoint = endpoint
        self.profile = profile
        self.calls_per_minute = calls_per_minute or self.CALLS_PER_MINUTE
        # Load queries from queries.yaml
        module_dir = os.path.dirname(__file__)
        queries_path = os.path.join(module_dir, "data", "queries.yaml")
        self.qm = QueryManager(lang="sparql", queriesPath=queries_path, with_default=False)

    def query(self, msg, queryString: str, limit=None) -> list:
        """
        get the query result

        Args:
            msg(str): the profile message to display
            queryString(str): the query to execute

        Return:
            list: the list of dicts with the result
        """
        profile = Profiler(msg, profile=self.profile)
        # Create SPARQL instance with rate limiting and proper User-Agent
        wd = SPARQL(self.endpoint, calls_per_minute=self.calls_per_minute)
        limitedQuery = queryString
        if limit is not None:
            limitedQuery = f"{queryString} LIMIT {limit}"
        results = wd.query(limitedQuery)
        lod = wd.asListOfDicts(results)
        for record in lod:
            for key in list(record.keys()):
                value = record[key]
                if isinstance(value, str):
                    if value.startswith("http://www.wikidata.org/"):
                        record[key] = self.getWikidataId(value)
                    if key.lower().endswith("coord"):
                        lat, lon = Wikidata.getCoordinateComponents(value)
                        record["lat"] = lat
                        record["lon"] = lon
                        record.pop(key)

        profile.time(f"({len(lod)})")
        return lod

    def store2DB(self, lod, tableName: str, primaryKey: str = None, sqlDB=None):
        """
        store the given list of dicts to the database

        Args:
            lod(list): the list of dicts
            tableName(str): the table name to use
            primaryKey(str): primary key (if any)
            sqlDB(SQLDB): target SQL database
        """
        msg = f"Storing {tableName}"
        profile = Profiler(msg, profile=self.profile)
        entityInfo = sqlDB.createTable(
            lod,
            entityName=tableName,
            primaryKey=primaryKey,
            withDrop=True,
            sampleRecordCount=-1,
        )
        sqlDB.store(lod, entityInfo, fixNone=True)
        profile.time()

    def getCountries(self, limit=None):
        """
        get a list of countries
        """
        query = self.qm.queriesByName.get("Countries")
        if not query:
            raise ValueError("Countries query not found in queries.yaml")
        msg = "Getting countries from wikidata ETA 10s"
        countryList = self.query(msg, query.query, limit=limit)
        return countryList

    def getRegions(self, limit=None):
        """
        get Regions from Wikidata
        """
        query = self.qm.queriesByName.get("Regions")
        if not query:
            raise ValueError("Regions query not found in queries.yaml")
        msg = "Getting regions from wikidata ETA 15s"
        regionList = self.query(msg, query.query, limit=limit)
        return regionList

    def getCities(self, limit=1000000):
        """
        get all human settlements as list of dict with duplicates for label, region, country ...
        """
        query = self.qm.queriesByName.get("Cities")
        if not query:
            raise ValueError("Cities query not found in queries.yaml")
        msg = "Getting cities (human settlements) from wikidata ETA 50 s"
        citiesList = self.query(msg, query.query, limit=limit)
        return citiesList

    def getCitiesForRegion(self, regionId, msg):
        """
        get the cities for the given Region
        """
        regionPath = (
            "?region ^wdt:P131/^wdt:P131/^wdt:P131 ?cityQ."
            if regionId in ["Q980", "Q21"]
            else "?cityQ wdt:P131* ?region."
        )
        queryString = """# get cities by region for geograpy3
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>

SELECT distinct (?cityQ as ?wikidataid) ?name ?geoNameId ?gndId ?regionId ?countryId ?pop ?coord WHERE { 
  VALUES ?hsType {
      wd:Q1549591 wd:Q3957 wd:Q5119 wd:Q15284 wd:Q62049 wd:Q515 wd:Q1637706 wd:Q1093829 wd:Q486972 wd:Q532
  }
  
  VALUES ?region {
         wd:%s
  }
  
  # region the city should be in
  %s
  
  # type of human settlement to try
  ?hsType ^wdt:P279*/^wdt:P31 ?cityQ.
  
  # label of the City
  ?cityQ rdfs:label ?name filter (lang(?name) = "en").
   
  # geoName Identifier
  OPTIONAL {
      ?cityQ wdt:P1566 ?geoNameId.
  }

  # GND-ID
  OPTIONAL { 
      ?cityQ wdt:P227 ?gndId. 
  }
  
  OPTIONAL{
     ?cityQ wdt:P625 ?coord .
  }
  
  # region this city belongs to
  OPTIONAL {
    ?cityQ wdt:P131 ?regionId .     
  }
  
  OPTIONAL {
     ?cityQ wdt:P1082 ?pop
  }

  # country this city belongs to
  OPTIONAL {
      ?cityQ wdt:P17 ?countryId .
  }
}""" % (
            regionId,
            regionPath,
        )
        regionCities = self.query(msg, queryString)
        return regionCities

    def getCityStates(self, limit=None):
        """
        get city states from Wikidata
        """
        query = self.qm.queriesByName.get("CityStates")
        if not query:
            raise ValueError("CityStates query not found in queries.yaml")
        msg = "Getting regions from wikidata ETA 15s"
        cityStateList = self.query(msg, query.query, limit=limit)
        return cityStateList

    @staticmethod
    def getCoordinateComponents(coordinate: str) -> (float, float):
        """
        Converts the wikidata coordinate representation into its subcomponents longitude and latitude
        Example: 'Point(-118.25 35.05694444)' results in ('-118.25' '35.05694444')

        Args:
            coordinate: coordinate value in the format as returned by wikidata queries

        Returns:
            Returns the longitude and latitude of the given coordinate as separate values
        """
        # https://stackoverflow.com/a/18237992/1497139
        floatRegex = r"[-+]?\d+([.,]\d*)?"
        regexp = rf"Point\((?P<lon>{floatRegex})\s+(?P<lat>{floatRegex})\)"
        cMatch = None
        if coordinate:
            try:
                cMatch = re.search(regexp, coordinate)
            except Exception as ex:
                # ignore
                pass
        if cMatch:
            latStr = cMatch.group("lat")
            lonStr = cMatch.group("lon")
            lat, lon = float(latStr.replace(",", ".")), float(lonStr.replace(",", "."))
            if lon > 180:
                lon = lon - 360
            return lat, lon
        else:
            # coordinate does not have the expected format
            return None, None

    @staticmethod
    def getWikidataId(wikidataURL: str):
        """
        Extracts the wikidata id from the given wikidata URL

        Args:
            wikidataURL: wikidata URL the id should be extracted from

        Returns:
            The wikidata id if present in the given wikidata URL otherwise None
        """

        # regex pattern taken from https://www.wikidata.org/wiki/Q43649390 and extended to also support property ids
        wikidataidMatch = re.search(r"[PQ][1-9]\d*", wikidataURL)
        if wikidataidMatch and wikidataidMatch.group(0):
            wikidataid = wikidataidMatch.group(0)
            return wikidataid
        else:
            return None

    @staticmethod
    def getValuesClause(varName: str, values, wikidataEntities: bool = True):
        """
        generates the SPARQL value clause for the given variable name containing the given values
        Args:
            varName: variable name for the ValuesClause
            values: values for the clause
            wikidataEntities(bool): if true the wikidata prefix is added to the values otherwise it is expected taht the given values are proper IRIs

        Returns:
            str
        """
        clauseValues = ""
        if isinstance(values, list):
            for value in values:
                if wikidataEntities:
                    clauseValues += f"wd:{value} "
                else:
                    clauseValues += f"{value} "
        else:
            if wikidataEntities:
                clauseValues = f"wd:{values} "
            else:
                clauseValues = f"{values} "
        clause = "VALUES ?%s { %s }" % (varName, clauseValues)
        return clause
