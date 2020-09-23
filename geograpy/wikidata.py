'''
Created on 2020-09-23

@author: wf
'''
from lodstorage.sparql import SPARQL

class Wikidata(object):
    '''
    Wikidata access
    '''

    def __init__(self, endpoint='https://query.wikidata.org/sparql'):
        '''
        Constructor
        '''
        self.endpoint=endpoint
        
    def getCities(self):
        '''
        get the cities from Wikidata
        '''
        queryString="""# get a list of cities
# for geograpy3 library
# see https://github.com/somnathrakshit/geograpy3/issues/15
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
# get City details with Country
SELECT DISTINCT ?country ?countryLabel ?countryIsoCode ?countryPopulation ?countryGDP_perCapita ?region ?regionLabel ?regionIsoCode ?city ?cityLabel ?coord ?cityPopulation ?date ?ratio WHERE {
  # run for Paris as example only
  # if you uncomment this line this query might run for some 3 hours on a local wikidata copy using Apache Jena
  VALUES ?city {wd:Q90}.
  # instance of City Q515
  # instance of human settlement https://www.wikidata.org/wiki/Q486972
  ?city wdt:P31/wdt:P279* wd:Q486972 .
  # label of the City
  ?city rdfs:label ?cityLabel filter (lang(?cityLabel) = "en").
  # get the coordinates
  ?city wdt:P625 ?coord.
  # region this country belongs to
  # https://www.wikidata.org/wiki/Property:P361
  OPTIONAL {
    # part of
    # https://www.wikidata.org/wiki/Property:P361
    ?city wdt:P131 ?region.
    # first order region
    ?region wdt:P31/wdt:P279* wd:Q10864048.
    ?region rdfs:label ?regionLabel filter (lang(?regionLabel) = "en").
    ?region wdt:P300 ?regionIsoCode
  }
  # country this city belongs to
  ?city wdt:P17 ?country .
  # label for the country
  ?country rdfs:label ?countryLabel filter (lang(?countryLabel) = "en").
  # https://www.wikidata.org/wiki/Property:P297 ISO 3166-1 alpha-2 code
  ?country wdt:P297 ?countryIsoCode.
  # population of country
  ?country wdt:P1082 ?countryPopulation.
  # https://www.wikidata.org/wiki/Property:P2132
  # nonminal GDP per capita
  ?country wdt:P2132 ?countryGDP_perCapita.
  # population of city
  ?city p:P1082 ?populationStatement .
  ?populationStatement ps:P1082 ?cityPopulation.
  ?populationStatement pq:P585 ?date
  FILTER NOT EXISTS { ?city p:P1082/pq:P585 ?date_ . FILTER (?date_ > ?date) }
  BIND ( concat(str(round(10000*?cityPopulation/?countryPopulation)/100), '%') AS ?ratio)
}"""
        wd=SPARQL(self.endpoint)
        results=wd.query(queryString)
        self.cityList=wd.asListOfDicts(results)
        
    def getCountries(self):
        '''
        get a list of countries
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
SELECT DISTINCT ?country ?countryLabel ?countryIsoCode ?countryPopulation ?countryGDP_perCapita ?coord  WHERE {
  # instance of City Country
  ?country wdt:P31/wdt:P279* wd:Q3624078 .
  # label for the country
  ?country rdfs:label ?countryLabel filter (lang(?countryLabel) = "en").
  # get the coordinates
  ?country wdt:P625 ?coord.
  # https://www.wikidata.org/wiki/Property:P297 ISO 3166-1 alpha-2 code
  ?country wdt:P297 ?countryIsoCode.
  # population of country
  ?country wdt:P1082 ?countryPopulation.
  # https://www.wikidata.org/wiki/Property:P2132
  # nonminal GDP per capita
  ?country wdt:P2132 ?countryGDP_perCapita.
}"""
        wd=SPARQL(self.endpoint)
        results=wd.query(queryString)
        self.countryList=wd.asListOfDicts(results)
        