'''
The locator module allows to get detailed city 
information including the region and country of a city from a 
location string.

Examples for location strings are:

    Amsterdam, Netherlands
    Vienna, Austria
    Vienna, IL
    Paris - Texas
    Paris TX
    
the locator will lookup the cities and try to disambiguate the result based on the country or region information found.

The results in string representationa are:
    
    Amsterdam (NH(North Holland) - NL(Netherlands))
    Vienna (9(Vienna) - AT(Austria))
    Vienna (IL(Illinois) - US(United States))
    Paris (TX(Texas) - US(United States)) 
    Paris (TX(Texas) - US(United States))
    
Each city returned has a city.region and city.country attribute with the details of the city.
    

Created on 2020-09-18

@author: wf
'''
import os
import re
import csv
import pycountry
from geograpy.prefixtree import PrefixTree
from lodstorage.sql import SQLDB
from .utils import remove_non_ascii

class City(object):
    '''
    a single city as an object
    '''
    def __init__(self):
        pass
    
    def __str__(self):
        text="%s (%s - %s)" % (self.name,self.region,self.country)
        return text
    
    @staticmethod
    def fromGeoLite2(record):
        city=City()
        city.name=record['city_name']
        city.region=Region.fromGeoLite2(record)
        city.country=Country.fromGeoLite2(record)
        return city
    
class Region(object):
    '''
    a Region (Subdivision)
    '''
    def __init__(self):
        pass
    
    def __str__(self):
        text="%s(%s)" % (self.iso,self.name)
        return text
    
    @staticmethod
    def fromGeoLite2(record):
        '''
        create  a region from a Geolite2 record
        
        Args:
            record(dict): the records as returned from a Query
            
        Returns:
            Region: the corresponding region information
        '''
        region=Region()
        region.name=record['subdivision_1_name']
        region.iso=record['subdivision_1_iso_code'] 
        return region   
    
class Country(object):
    '''
    a country
    '''
    def __init__(self):
        pass
    
    def __str__(self):
        text="%s(%s)" % (self.iso,self.name)
        return text
    
    @staticmethod 
    def fromGeoLite2(record):
        '''
        create a country from a geolite2 record
        '''
        country=Country()
        country.name=record['country_name']
        country.iso=record['country_iso_code']
        return country
    
    @staticmethod
    def fromPyCountry(pcountry):
        '''
        Args:
            pcountry(PyCountry): a country as gotten from pycountry
        Returns: 
            Country: the country 
        '''
        country=Country()
        country.name=pcountry.name
        country.iso=pcountry.alpha_2
        return country

class Locator(object):
    '''
    location handling
    '''
    
    # singleton instance
    locator=None

    def __init__(self, db_file=None,correctMisspelling=False,debug=False):
        '''
        Constructor
        
        Args:
            db_file(str): the path to the database file
            correctMispelling(bool): if True correct typical misspellings
            debug(bool): if True show debug information
        '''
        self.debug=debug
        self.correctMisspelling=correctMisspelling
        self.db_file = db_file or os.path.dirname(os.path.realpath(__file__)) + "/locs.db"
        self.sqlDB=SQLDB(self.db_file,errorDebug=True)
    
    @staticmethod
    def getInstance(correctMisspelling=False,debug=False):
        '''
        get the singleton instance of the Locator. If parameters are changed on further calls
        the initial parameters will still be in effect since the original instance will be returned!
        
        Args:
            correctMispelling(bool): if True correct typical misspellings
            debug(bool): if True show debug information
        '''
        if Locator.locator is None:
            Locator.locator=Locator(correctMisspelling=correctMisspelling,debug=debug)
        return Locator.locator
        
    def locate(self,places):
        '''
        locate a city, region country combination based on the places information
        
        Args:
            places(list): a list of place tokens e.g. "Vienna, Austria"
        
        Returns:
            City: a city with country and region details
        '''
        # make sure the database is populated
        self.populate_db()
        country=None
        cities=[]
        regions=[]
        level=1
        prefix=''
        for place in places:
            isPrefix=self.isPrefix(prefix+place,level)
            isAmbigous=False
            if not isPrefix:
                prefix=''
            checkPlace=prefix+place
            if isPrefix:
                isAmbigous=self.isAmbiguousPrefix(prefix+place)
                level+=1
                prefix="%s%s " % (prefix,place)
            if not isPrefix or isAmbigous:
                foundCountry=self.getCountry(checkPlace)
                if foundCountry is not None:
                    country=foundCountry
                foundCities=self.cities_for_name(checkPlace)
                cities.extend(foundCities)
                foundRegions=self.regions_for_name(checkPlace)
                regions.extend(foundRegions)
        foundCity=self.disambiguate(country, regions, cities)
        return foundCity
    
    def isAmbiguousPrefix(self,name):
        '''
        check if the given name is an ambiguous prefix
        
        Args:
            name(string): the city name to check
            
        Returns:
            bool: True if this is a known prefix that is ambigous that is there is also a city with 
            such a name    
        '''
        query="select name from ambiguous where name=?"
        params=(name,)
        aResult=self.sqlDB.query(query,params)
        result=len(aResult)>0
        return result
    
    def isISO(self,s):
        '''
        check if the given string is an ISO code
        
        Returns:
            bool: True if the string is an ISO Code
        '''
        m=re.search(r"^[0-9A-Z]{1,3}$",s)
        result=m is not None
        return result

    def isPrefix(self,name,level):
        '''
        check if the given name is a city prefix at the given level
        
        Args:
            name(string): the city name to check
            level(int): the level on which to check (number of words)
            
        Returns:
            bool: True if this is a known prefix of multiple cities e.g. "San", "New", "Los"
        '''
        query="SELECT count from prefixes where prefix=? and level=?"
        params=(name,level)
        prefixResult=self.sqlDB.query(query,params)
        result=len(prefixResult)>0
        return result
               
    def disambiguate(self,country,regions,cities): 
        '''
        try determining country, regions and city from the potential choices
        
        Args:
            country(Country): a matching country found
            regions(list): a list of matching Regions found
            cities(list): a list of matching cities found
            
        Return:
            City: the found city or None
        '''
        if self.debug:
            print("countries: %s " % country)
            print("regions: %s" % regions)
            print("cities: %s" % cities)
        foundCity=None
        # is the city information unique?
        if len(cities)==1:
            foundCity=cities[0]
        else: 
            if len(cities)>1 and country is not None:
                for city in cities:
                    if self.debug:
                        print("city %s: " %(city))
                    if city.country.iso==country.iso:
                        foundCity=city
                        break
            if len(cities)>1 and len(regions)>0:
                for region in regions:
                    for city in cities:
                        if city.region.iso==region.iso and not city.region.name==city.name:
                            foundCity=city
                            break;
                    if foundCity is not None:
                        break
        return foundCity    
    
    def cities_for_name(self, city_name):
        '''
        find cities with the given city_name
        
        Args:
            city_name(string): the potential name of a city
        
        Returns:
            a list of city records
        '''
        cities=[]
        cityRecords=self.places_by_name(city_name, 'city_name')
        for cityRecord in cityRecords:
            cities.append(City.fromGeoLite2(cityRecord))
        return cities

    def regions_for_name(self, region_name):
        '''
        get the regions for the given region_name (which might be an ISO code)
        
        Args:
            region_name(string): region name
            
        Returns:
            list: the list of cities for this region
        '''
        regions=[]
        if self.isISO(region_name):
            regionRecords=self.places_by_name(region_name,'subdivision_1_iso_code')
        else:
            regionRecords=self.places_by_name(region_name, 'subdivision_1_name')
        for regionRecord in regionRecords:
            regions.append(Region.fromGeoLite2(regionRecord))
        return regions                     
    
    def correct_country_misspelling(self, name):
        '''
        correct potential misspellings 
        Args:
            name(string): the name of the country potentially misspelled
        Return:
            string: correct name of unchanged
        '''
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        with open(cur_dir + "/data/ISO3166ErrorDictionary.csv") as info:
            reader = csv.reader(info)
            for row in reader:
                if name in remove_non_ascii(row[0]):
                    return row[2]
        return name

    def is_a_country(self, name):
        '''
        check if the given string name is a country
        
        Args:
            name(string): the string to check
        Returns:
            True: if pycountry thinks the string is a country
        '''
        country=self.getCountry(name)
        result=country is not None
        return result
       
    def getCountry(self,name):
        '''
        get the country for the given name    
        Args:
            name(string): the name of the country to lookup
        Returns:     
            country: the country if one was found or None if not
        '''
        if self.isISO(name):
            pcountry=pycountry.countries.get(alpha_2=name)
        else:
            if self.correctMisspelling:
                name = self.correct_country_misspelling(name)
            pcountry=pycountry.countries.get(name=name)
        country=None
        if pcountry is not None:
            country=Country.fromPyCountry(pcountry)
        return country
 
    def places_by_name(self, place_name, column_name):
        '''
        get places by name and column
        Args:
            place_name(string): the name of the place
            column_name(string): the column to look at
        '''
        if not self.db_has_data():
            self.populate_db()
        query='SELECT * FROM cities WHERE ' + column_name + ' = (?)'
        params=(place_name,)
        cities=self.sqlDB.query(query,params)
        return cities
    
    def getGeolite2Cities(self):
        '''
        get the Geolite2 City-Locations as a list of Dicts
        
        Returns:
            list: a list of Geolite2 City-Locator dicts
        '''
        cities=[]
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        csvfile=cur_dir + "/data/GeoLite2-City-Locations-en.csv"
        with open(csvfile) as info:
            reader = csv.DictReader(info)
            for row in reader:
                cities.append(row)
        return cities
                
    def populate_db(self,force=False):
        '''
        populate the cities SQL database which caches the information from the GeoLite2-City-Locations.csv file
        '''
        if not self.db_has_data() or force:
            self.populate_Cities(self.sqlDB)
            self.populate_PrefixTree(self.sqlDB)
            self.populate_PrefixAmbiguities(self.sqlDB)
    
    def populate_Cities(self,sqlDB):
        '''
        populate the given sqlDB with the Geolite2 Cities
        
        Args:
            sqlDB(SQLDB): the SQL database to use
        '''
        cities=self.getGeolite2Cities()
        entityName="cities"
        primaryKey="geoname_id"
        entityInfo=sqlDB.createTable(cities[:100],entityName,primaryKey)
        sqlDB.store(cities,entityInfo,executeMany=False)
        
    def populate_PrefixAmbiguities(self,sqlDB):
        '''
        create a table with ambiguous prefixes
        
        Args:
            sqlDB(SQLDB): the SQL database to use
        '''
        query="""select distinct city_name as name 
from cities c join prefixes p on c.city_name=p.prefix
order by city_name"""
        ambigousPrefixes=sqlDB.query(query)
        entityInfo=sqlDB.createTable(ambigousPrefixes, "ambiguous","name",withDrop=True)
        sqlDB.store(ambigousPrefixes,entityInfo)
        return ambigousPrefixes
        
    def populate_PrefixTree(self,sqlDB):
        '''
        calculate the PrefixTree info
        
        Args:
            sqlDb: the SQL Database to use
        
        Returns:
            PrefixTree: the prefix tree
        '''
        query="SELECT city_name AS name from CITIES"
        nameRecords=sqlDB.query(query)
        trie=PrefixTree()   
        for nameRecord in nameRecords:
            name=nameRecord['name']
            trie.add(name)
        trie.store(sqlDB)   
        return trie     
     
    def db_has_data(self):
        '''
        check whether the database has data / is populated
        
        Returns:
            boolean: True if the cities table exists and has more than one record
        '''
        query1="SELECT Count(*) AS count FROM sqlite_master WHERE name='cities';"
        tableResult=self.sqlDB.query(query1)
        count=tableResult[0]['count']
        if count>0:
            query2="SELECT Count(*) AS count FROM cities"
            countResult=self.sqlDB.query(query2)
            count=countResult[0]['count']
            return count > 10000
        return False    
        