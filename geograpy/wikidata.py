'''
Created on 2020-09-23

@author: wf
'''
import re
from geograpy.utils import Profiler
from lodstorage.sparql import SPARQL

class Wikidata(object):
    '''
    Wikidata access
    '''

    def __init__(self, endpoint='https://query.wikidata.org/sparql',profile:bool=True):
        '''
        Constructor
        '''
        self.endpoint=endpoint
        self.profile=profile
        
    def query(self,msg,queryString:str,limit=None)->list:
        '''
        get the query result
        
        Args:
            msg(str): the profile message to display
            queryString(str): the query to execute
            
        Return:
            list: the list of dicts with the result
        '''
        profile=Profiler(msg,profile=self.profile)
        wd=SPARQL(self.endpoint)
        limitedQuery=queryString
        if limit is not None:
            limitedQuery=f"{queryString} LIMIT {limit}"
        results=wd.query(limitedQuery)
        lod=wd.asListOfDicts(results)
        for record in lod:
            for key in list(record.keys()):
                value=record[key]
                if isinstance(value,str):
                    if value.startswith("http://www.wikidata.org/"):
                        record[key]=self.getWikidataId(value)
                    if key.lower().endswith("coord"):
                        lat, lon = Wikidata.getCoordinateComponents(value)
                        record["lat"]=lat
                        record["lon"]=lon
                        record.pop(key)
            
                        
        profile.time(f"({len(lod)})")
        return lod
    
    def store2DB(self,lod,tableName:str,primaryKey:str=None,sqlDB=None):
        '''
        store the given list of dicts to the database
        
        Args:
            lod(list): the list of dicts
            tableName(str): the table name to use
            primaryKey(str): primary key (if any)
            sqlDB(SQLDB): target SQL database
        '''
        msg=f"Storing {tableName}"
        profile=Profiler(msg,profile=self.profile)
        entityInfo = sqlDB.createTable(lod, entityName=tableName, primaryKey=primaryKey, withDrop=True,sampleRecordCount=-1)
        sqlDB.store(lod, entityInfo, fixNone=True)
        profile.time()
        
    def getCountries(self,limit=None):
        '''
        get a list of countries
        
        `try query <https://query.wikidata.org/#%23%20get%20a%20list%20of%20countries%0A%23%20for%20geograpy3%20library%0A%23%20see%20https%3A%2F%2Fgithub.com%2Fsomnathrakshit%2Fgeograpy3%2Fissues%2F15%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX%20wd%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fentity%2F%3E%0APREFIX%20wdt%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fdirect%2F%3E%0APREFIX%20p%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2F%3E%0APREFIX%20ps%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fstatement%2F%3E%0APREFIX%20pq%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fqualifier%2F%3E%0A%23%20get%20City%20details%20with%20Country%0ASELECT%20DISTINCT%20%3Fcountry%20%3FcountryLabel%20%3FcountryIsoCode%20%3FcountryPopulation%20%3FcountryGDP_perCapita%20%3Fcoord%20%20WHERE%20%7B%0A%20%20%23%20instance%20of%20City%20Country%0A%20%20%3Fcountry%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ3624078%20.%0A%20%20%23%20label%20for%20the%20country%0A%20%20%3Fcountry%20rdfs%3Alabel%20%3FcountryLabel%20filter%20%28lang%28%3FcountryLabel%29%20%3D%20%22en%22%29.%0A%20%20%23%20get%20the%20coordinates%0A%20%20%3Fcountry%20wdt%3AP625%20%3Fcoord.%0A%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP297%20ISO%203166-1%20alpha-2%20code%0A%20%20%3Fcountry%20wdt%3AP297%20%3FcountryIsoCode.%0A%20%20%23%20population%20of%20country%0A%20%20%3Fcountry%20wdt%3AP1082%20%3FcountryPopulation.%0A%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP2132%0A%20%20%23%20nonminal%20GDP%20per%20capita%0A%20%20%3Fcountry%20wdt%3AP2132%20%3FcountryGDP_perCapita.%0A%7D>`_
      
        '''
        queryString="""# get a list of countries
# for geograpy3 library
# see https://github.com/somnathrakshit/geograpy3/issues/15
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
# get City details with Country
SELECT DISTINCT ?wikidataid ?name ?iso ?pop ?coord
WHERE {
  BIND (?countryQ AS ?wikidataid)

  # instance of Country
  # inverse path see https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/query_optimization#Inverse_property_paths
  wd:Q6256 ^wdt:P279*/^wdt:P31 ?countryQ .
  
  # VALUES ?country { wd:Q55}.
  # label for the country
  ?countryQ rdfs:label ?name filter (lang(?name) = "en").
  # get the continent (s)
  #OPTIONAL {
  #  ?country wdt:P30 ?continent.
  #  ?continent rdfs:label ?continentLabel filter (lang(?continentLabel) = "en").
  #}
  # get the coordinates
  OPTIONAL { 
      ?countryQ wdt:P625 ?coord.
  } 
  # https://www.wikidata.org/wiki/Property:P297 ISO 3166-1 alpha-2 code
  ?countryQ wdt:P297 ?iso.
  # population of country   
  OPTIONAL
  { 
    SELECT ?countryQ (max(?countryPopulationValue) as ?pop)
    WHERE {
      ?countryQ wdt:P1082 ?countryPopulationValue
    } group by ?countryQ
  }
  # https://www.wikidata.org/wiki/Property:P2132
  # nominal GDP per capita
  # OPTIONAL { ?country wdt:P2132 ?countryGDP_perCapitaValue. }
}
ORDER BY ?iso"""
        msg="Getting countries from wikidata ETA 10s"
        countryList=self.query(msg, queryString,limit=limit)
        return countryList

    def getRegions(self,limit=None):
        '''
        get Regions from Wikidata
        
        `try query <https://query.wikidata.org/#%23%20get%20a%20list%20of%20regions%0A%23%20for%20geograpy3%20library%0A%23%20see%20https%3A%2F%2Fgithub.com%2Fsomnathrakshit%2Fgeograpy3%2Fissues%2F15%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX%20wd%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fentity%2F%3E%0APREFIX%20wdt%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fdirect%2F%3E%0APREFIX%20wikibase%3A%20%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0ASELECT%20%3Fcountry%20%3FcountryLabel%20%3FcountryIsoCode%20%3Fregion%20%3FregionIsoCode%20%3FregionLabel%20%3Fpopulation%20%3Flocation%0AWHERE%0A%7B%0A%20%20%23%20administrative%20unit%20of%20first%20order%0A%20%20%3Fregion%20wdt%3AP31%2Fwdt%3AP279%2a%20wd%3AQ10864048.%0A%20%20OPTIONAL%20%7B%0A%20%20%20%20%20%3Fregion%20rdfs%3Alabel%20%3FregionLabel%20filter%20%28lang%28%3FregionLabel%29%20%3D%20%22en%22%29.%0A%20%20%7D%0A%20%20%23%20filter%20historic%20regions%0A%20%20%23%20FILTER%20NOT%20EXISTS%20%7B%3Fregion%20wdt%3AP576%20%3Fend%7D%0A%20%20%23%20get%20the%20population%0A%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP1082%0A%20%20OPTIONAL%20%7B%20%3Fregion%20wdt%3AP1082%20%3Fpopulation.%20%7D%0A%20%20%23%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP297%0A%20%20OPTIONAL%20%7B%20%0A%20%20%20%20%3Fregion%20wdt%3AP17%20%3Fcountry.%0A%20%20%20%20%23%20label%20for%20the%20country%0A%20%20%20%20%3Fcountry%20rdfs%3Alabel%20%3FcountryLabel%20filter%20%28lang%28%3FcountryLabel%29%20%3D%20%22en%22%29.%0A%20%20%20%20%3Fcountry%20wdt%3AP297%20%3FcountryIsoCode.%20%0A%20%20%7D%0A%20%20%23%20isocode%20state%2Fprovince%0A%20%20%3Fregion%20wdt%3AP300%20%3FregionIsoCode.%0A%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP625%0A%20%20OPTIONAL%20%7B%20%3Fregion%20wdt%3AP625%20%3Flocation.%20%7D%0A%7D>`_
        '''
        queryString="""# get a list of regions
# for geograpy3 library
# see https://github.com/somnathrakshit/geograpy3/issues/15
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT DISTINCT ?countryId (?regionQ as ?wikidataid) ?name ?iso ?pop ?coord
WHERE
{
  # administrative unit of first order
  ?regionQ wdt:P31/wdt:P279* wd:Q10864048.
  OPTIONAL {
     ?regionQ rdfs:label ?name filter (lang(?name) = "en").
  }
  # isocode state/province (mandatory - filters historic regions while at it ...)
  # filter historic regions
  # FILTER NOT EXISTS {?region wdt:P576 ?end}
  { 
    SELECT ?regionQ (max(?regionAlpha2) as ?iso) (max(?regionPopulationValue) as ?pop) (max(?locationValue) as ?coord)
    WHERE {
      ?regionQ wdt:P300 ?regionAlpha2.
      # get the population
      # https://www.wikidata.org/wiki/Property:P1082
      OPTIONAL {
        ?regionQ wdt:P1082 ?regionPopulationValue
      } 
      # get the location
      # https://www.wikidata.org/wiki/Property:P625
      OPTIONAL {
        ?regionQ wdt:P625 ?locationValue. 
       }
    } GROUP BY ?regionQ
  }
  # # https://www.wikidata.org/wiki/Property:P297
  OPTIONAL { 
    ?regionQ wdt:P17 ?countryId.
  }
} ORDER BY ?iso"""
        msg="Getting regions from wikidata ETA 15s"
        regionList=self.query(msg, queryString,limit=limit)
        return regionList

        
    def getCities(self,limit=1000000):
        '''
        get all human settlements as list of dict with duplicates for label, region, country ...
        '''
        queryString="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT DISTINCT (?cityQ as ?wikidataid) ?city ?altLabel ?geoNameId ?gndId ?cityPopulation ?cityCoord ?regionId ?countryId
WHERE {
  # instance of human settlement https://www.wikidata.org/wiki/Q486972
  wd:Q486972 ^wdt:P279*/^wdt:P31 ?cityQ .
  # Values
  # VALUES  ?cityQ { wd:Q656 }
 
  # label of the City
  ?cityQ rdfs:label ?city filter (lang(?city) = "en").
  
  OPTIONAL {
     ?cityQ skos:altLabel ?altLabel .
     FILTER (lang(?altLabel) = "en")
  }
  
  # geoName Identifier
  OPTIONAL {
      ?cityQ wdt:P1566 ?geoNameId.
  }

  # GND-ID
  OPTIONAL { 
      ?cityQ wdt:P227 ?gndId. 
  }
  
  # population of city
  OPTIONAL { 
    SELECT ?cityQ (max(?cityPopulationValue) as ?cityPopulation)
    WHERE {
      ?cityQ wdt:P1082 ?cityPopulationValue
    } group by ?cityQ
  }
  
  OPTIONAL{
     ?cityQ wdt:P625 ?cityCoord .
  }
  
  # region this city belongs to
  OPTIONAL {
    ?cityQ wdt:P131 ?regionId .     
  }

  # country this city belongs to
  OPTIONAL {
      ?cityQ wdt:P17 ?countryId .
  }
  
}
"""
        msg="Getting cities (human settlements) from wikidata ETA 50 s"
        citiesList=self.query(msg, queryString,limit=limit)
        return citiesList
    
    def getCitiesForRegion(self,regionId,msg):
        '''
        get the cities for the given Region
        '''
        regionPath="?region ^wdt:P131/^wdt:P131/^wdt:P131 ?cityQ." if regionId in ["Q980","Q21"] else "?cityQ wdt:P131* ?region." 
        queryString="""# get cities by region for geograpy3
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
}""" % (regionId,regionPath)           
        regionCities=self.query(msg, queryString)
        return regionCities

    def getCityStates(self, limit=None):
        '''
        get city states from Wikidata

        `try query <https://query.wikidata.org/#%23%20get%20a%20list%20of%20city%20states%0A%23%20for%20geograpy3%20library%0APREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX%20wd%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fentity%2F%3E%0APREFIX%20wdt%3A%20%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fdirect%2F%3E%0APREFIX%20wikibase%3A%20%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0ASELECT%20DISTINCT%20%3FcountryId%20%28%3FcityStateQ%20as%20%3Fwikidataid%29%20%3Fname%20%3Fiso%20%3Fpop%20%3Fcoord%0AWHERE%0A%7B%0A%20%20%23%20all%20citiy%20states%0A%20%20%3FcityStateQ%20wdt%3AP31%20wd%3AQ133442%20.%0A%20%20%3FcityStateQ%20rdfs%3Alabel%20%3Fname%20filter%20%28lang%28%3Fname%29%20%3D%20%22en%22%29.%0A%20%20%7B%20%0A%20%20%20%20SELECT%20%3FcityStateQ%20%28max%28%3FisoCode%29%20as%20%3Fiso%29%20%28max%28%3FpopulationValue%29%20as%20%3Fpop%29%20%28max%28%3FlocationValue%29%20as%20%3Fcoord%29%0A%20%20%20%20WHERE%20%7B%0A%20%20%20%20%20%20%3FcityStateQ%20wdt%3AP300%7Cwdt%3AP297%20%3FisoCode.%0A%20%20%20%20%20%20%23%20get%20the%20population%0A%20%20%20%20%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP1082%0A%20%20%20%20%20%20OPTIONAL%20%7B%0A%20%20%20%20%20%20%20%20%3FcityStateQ%20wdt%3AP1082%20%3FpopulationValue%0A%20%20%20%20%20%20%7D%20%0A%20%20%20%20%20%20%23%20get%20the%20location%0A%20%20%20%20%20%20%23%20https%3A%2F%2Fwww.wikidata.org%2Fwiki%2FProperty%3AP625%0A%20%20%20%20%20%20OPTIONAL%20%7B%0A%20%20%20%20%20%20%20%20%3FcityStateQ%20wdt%3AP625%20%3FlocationValue.%20%0A%20%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%20GROUP%20BY%20%3FcityStateQ%0A%20%20%7D%0A%20%20OPTIONAL%20%7B%20%0A%20%20%20%20%3FcityStateQ%20wdt%3AP17%20%3FcountryId.%0A%20%20%7D%0A%7D%20ORDER%20BY%20%3Fiso>`_
        '''
        queryString = """# get a list of city states
# for geograpy3 library
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT DISTINCT ?countryId (?cityStateQ as ?wikidataid) ?name ?iso ?pop ?coord
WHERE
{
  # all citiy states
  ?cityStateQ wdt:P31 wd:Q133442 .
  ?cityStateQ rdfs:label ?name filter (lang(?name) = "en").
  { 
    SELECT ?cityStateQ (max(?isoCode) as ?iso) (max(?populationValue) as ?pop) (max(?locationValue) as ?coord)
    WHERE {
      ?cityStateQ wdt:P300|wdt:P297 ?isoCode.
      # get the population
      # https://www.wikidata.org/wiki/Property:P1082
      OPTIONAL {
        ?cityStateQ wdt:P1082 ?populationValue
      } 
      # get the location
      # https://www.wikidata.org/wiki/Property:P625
      OPTIONAL {
        ?cityStateQ wdt:P625 ?locationValue. 
       }
    } GROUP BY ?cityStateQ
  }
  OPTIONAL { 
    ?cityStateQ wdt:P17 ?countryId.
  }
} ORDER BY ?iso"""
        msg = "Getting regions from wikidata ETA 15s"
        cityStateList = self.query(msg, queryString, limit=limit)
        return cityStateList

    @staticmethod
    def getCoordinateComponents(coordinate:str) -> (float, float):
        '''
        Converts the wikidata coordinate representation into its subcomponents longitude and latitude
        Example: 'Point(-118.25 35.05694444)' results in ('-118.25' '35.05694444')

        Args:
            coordinate: coordinate value in the format as returned by wikidata queries

        Returns:
            Returns the longitude and latitude of the given coordinate as separate values
        '''
        # https://stackoverflow.com/a/18237992/1497139
        floatRegex=r"[-+]?\d+([.,]\d*)?"
        regexp=fr"Point\((?P<lon>{floatRegex})\s+(?P<lat>{floatRegex})\)"
        cMatch=None
        if coordinate:
            try:
                cMatch = re.search(regexp, coordinate)
            except Exception as ex:
                # ignore
                pass
        if cMatch:
            latStr=cMatch.group("lat")
            lonStr=cMatch.group("lon")
            lat,lon=float(latStr.replace(",",".")),float(lonStr.replace(",","."))
            if lon>180:
                lon=lon-360
            return lat,lon
        else:
            # coordinate does not have the expected format
            return None, None

    @staticmethod
    def getWikidataId(wikidataURL:str):
        '''
        Extracts the wikidata id from the given wikidata URL

        Args:
            wikidataURL: wikidata URL the id should be extracted from

        Returns:
            The wikidata id if present in the given wikidata URL otherwise None
        '''

        # regex pattern taken from https://www.wikidata.org/wiki/Q43649390 and extended to also support property ids
        wikidataidMatch = re.search(r"[PQ][1-9]\d*", wikidataURL)
        if wikidataidMatch and wikidataidMatch.group(0):
            wikidataid = wikidataidMatch.group(0)
            return wikidataid
        else:
            return None

    @staticmethod
    def getValuesClause(varName:str, values, wikidataEntities:bool=True):
        '''
        generates the SPARQL value clause for the given variable name containing the given values
        Args:
            varName: variable name for the ValuesClause
            values: values for the clause
            wikidataEntities(bool): if true the wikidata prefix is added to the values otherwise it is expected taht the given values are proper IRIs

        Returns:
            str
        '''
        clauseValues=""
        if isinstance(values, list):
            for value in values:
                if wikidataEntities:
                    clauseValues+=f"wd:{value} "
                else:
                    clauseValues+=f"{value} "
        else:
            if wikidataEntities:
                clauseValues = f"wd:{values} "
            else:
                clauseValues = f"{values} "
        clause = "VALUES ?%s { %s }" %(varName, clauseValues)
        return clause