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
import urllib
import re
import csv
import pycountry
import sys
import gzip
import shutil
from geograpy.wikidata import Wikidata
from lodstorage.sql import SQLDB
from geograpy.utils import remove_non_ascii
from geograpy import wikidata
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

class City(object):
    '''
    a single city as an object
    '''
    def __init__(self):
        pass
    
    def __str__(self):
        text="%s (%s - %s)" % (self.name,self.region,self.country)
        return text
    
    
    def setValue(self,name,record):
        '''
        set a field value with the given name  to
        the given record dicts corresponding entry or none
        
        Args:
            name(string): the name of the field
            record(dict): the dict to get the value from
        '''
        if name in record:
            value=record[name]
        else:
            value=None
        self.__dict__[name]=value
            
    @staticmethod
    def fromGeoLite2(record):
        city=City()
        city.name=record['name']
        if not city.name:
            city.name=record['wikidataName']
        city.setValue('population',record)
        city.setValue('gdp',record)
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
        region.name=record['regionName']
        region.iso="%s-%s" % (record['countryIsoCode'],record['regionIsoCode']) 
        return region   
    
    @staticmethod
    def fromWikidata(record):
        '''
        create  a region from a Wikidata record
        
        Args:
            record(dict): the records as returned from a Query
            
        Returns:
            Region: the corresponding region information
        '''
        region=Region()
        region.name=record['regionLabel']
        region.iso=record['regionIsoCode'] 
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
        country.name=record['countryName']
        country.iso=record['countryIsoCode']
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
        self.db_path=os.path.dirname(os.path.realpath(__file__)) 
        self.db_file = db_file or self.db_path+"/locs.db"
        self.view="GeoLite2CityLookup"
        self.sqlDB=SQLDB(self.db_file,errorDebug=True)
        self.getAliases()
        self.dbVersion="2020-09-27 16:48:09"
        
    @staticmethod
    def resetInstance():
        Locator.locator=None    
    
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
        
    def locateCity(self,places):
        '''
        locate a city, region country combination based on the given wordtoken information
        
        Args:
            places(list): a list of places derived by splitting a locality e.g.  "San Francisco, CA"
            leads to "San Francisco", "CA"
        
        Returns:
            City: a city with country and region details
        '''
        # make sure the database is populated
        self.populate_db()
        country=None
        cities=[]
        regions=[]
        # loop over all word elements
        for place in places:
            place=place.strip()
            if place in self.aliases:
                place=self.aliases[place]
            foundCountry=self.getCountry(place)
            if foundCountry is not None:
                country=foundCountry
            foundCities=self.cities_for_name(place)
            cities.extend(foundCities)
            foundRegions=self.regions_for_name(place)
            regions.extend(foundRegions)
        foundCity=self.disambiguate(country, regions, cities)
        return foundCity
    
    def isISO(self,s):
        '''
        check if the given string is an ISO code
        
        Returns:
            bool: True if the string is an ISO Code
        '''
        m=re.search(r"^([A-Z]{1,2}\-)?[0-9A-Z]{1,3}$",s)
        result=m is not None
        return result
               
    def disambiguate(self,country,regions,cities,byPopulation=True): 
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
            print("regions: %s" % "\n\t".join(str(r) for r in regions))
            print("cities: %s" % "\n\t".join(str(c) for c in cities))
        foundCity=None
        # is the city information unique?
        if len(cities)==1:
            foundCity=cities[0]
        else: 
            if len(cities)>1:
                if country is not None:
                    for city in cities:
                        if self.debug:
                            print("city %s: " %(city))
                        if city.country.iso==country.iso:
                            foundCity=city
                            break
                if foundCity is None and len(regions)>0:
                    for region in regions:
                        for city in cities:
                            if city.region.iso==region.iso and not city.region.name==city.name:
                                foundCity=city
                                break;
                        if foundCity is not None:
                            break
                if foundCity is None and byPopulation:
                    foundCity=max(cities,key=lambda city:0 if city.population is None else city.population)
                    pass
                    
        return foundCity    
    
    def cities_for_name(self, cityName):
        '''
        find cities with the given cityName
        
        Args:
            cityName(string): the potential name of a city
        
        Returns:
            a list of city records
        '''
        cities=[]
        for column in ['name','wikidataName']:
            cityRecords=self.places_by_name(cityName, column)
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
            columnName="regionIsoCode"
        else:
            columnName='regionLabel'
        query="SELECT * from regions WHERE %s = (?)" % (columnName)
        params=(region_name,)
        regionRecords=self.sqlDB.query(query,params)
        for regionRecord in regionRecords:
            regions.append(Region.fromWikidata(regionRecord))
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
        #if country is None:
        #    query="SELECT * FROM countries WHERE countryLabel = (?)"""
        #    params=(name,)
        #    countryRecords=self.sqlDB.query(query,params)
        #    if len(countryRecords)>0:
        #        pass
        return country
    
    def getView(self):
        '''
        get the view to be used
        
        Returns:
            str: the SQL view to be used for CityLookups e.g. GeoLite2CityLookup
        '''
        view=self.view
        return view
 
    def places_by_name(self, placeName, columnName):
        '''
        get places by name and column
        Args:
            placeName(string): the name of the place
            columnName(string): the column to look at
        '''
        if not self.db_has_data():
            self.populate_db()
        view=self.getView()
        query='SELECT * FROM %s WHERE %s = (?)' % (view,columnName)
        params=(placeName,)
        cities=self.sqlDB.query(query,params)
        return cities
    
    def getGeolite2Cities(self):
        '''
        get the Geolite2 City-Locations as a list of Dicts
        
        Returns:
            list: a list of Geolite2 City-Locator dicts
        '''
        cities=self.readCSV("GeoLite2-City-Locations-en.csv")
        return cities
    
    def readCSV(self,fileName):
        records=[]
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        csvfile="%s/data/%s" % (cur_dir,fileName)
        with open(csvfile) as info:
            reader = csv.DictReader(info)
            for row in reader:
                records.append(row)
        return records
     
    def recreateDatabase(self):
        '''
        recreate my lookup database
        '''
        print("recreating database ... %s" % self.db_file)
        self.populate_db(force=True)
                
    def populate_db(self,force=False):
        '''
        populate the cities SQL database which caches the information from the GeoLite2-City-Locations.csv file
        
        Args:
            force(bool): if True force a recreation of the database
        '''
        hasData=self.db_has_data()
        if force:
            self.populate_Cities(self.sqlDB)
            self.populateFromWikidata(self.sqlDB)
            self.getWikidataCityPopulation(self.sqlDB)
            self.createViews(self.sqlDB)
            self.populate_Version(self.sqlDB)
    
        elif not hasData:
            url="http://wiki.bitplan.com/images/confident/locs.db.gz"
            zipped=self.db_file+".gz"
            print("Downloading %s from %s ... this might take a few seconds" % (zipped,url))
            urllib.request.urlretrieve(url,zipped)
            print("unzipping %s from %s" % (self.db_file,zipped))
            with gzip.open(zipped, 'rb') as gzipped:
                with open(self.db_file, 'wb') as unzipped:
                    shutil.copyfileobj(gzipped, unzipped)
        if not os.path.isfile(self.db_file):
            raise("could not create lookup database %s" % self.db_file)
            
    def populate_Version(self,sqlDB):
        '''
        populate the version table
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        versionList=[{"version":self.dbVersion}]
        entityInfo=sqlDB.createTable(versionList,"Version","version",withDrop=True)
        sqlDB.store(versionList,entityInfo)
        
    def getAliases(self):
        '''
        get the aliases hashTable
        '''
        aliases=self.readCSV("aliases.csv")
        self.aliases={}
        for alias in aliases:
            self.aliases[alias['name']]=alias['alias']
        
    def populateFromWikidata(self,sqlDB):
        '''
        populate countries and regions from Wikidata
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        self.populate_Countries(sqlDB)
        self.populate_Regions(sqlDB)
        return
        # ignore the following code as of 2020-09-26
        self.populate_Cities_FromWikidata(sqlDB)
        viewDDLs=["DROP VIEW IF EXISTS WikidataCityLookup","""
CREATE VIEW WikidataCityLookup AS
SELECT 
  name AS name,
  regionLabel as regionName,
  regionIsoCode as regionIsoCode,
  countryLabel as countryName,
  countryIsoCode as countryIsoCode,
  cityPopulation as population,
  countryGDP_perCapita as gdp
FROM City_wikidata
"""]
#                  subdivision_1_name AS regionName,
#  subdivision_1_iso_code as regionIsoCode,
#  country_name AS countryName,
#  country_iso_code as countryIsoCode
        for viewDDL in viewDDLs:
            self.sqlDB.execute(viewDDL)
           
    def populate_Countries(self,sqlDB):
        '''
        populate database with countries from wikiData
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        print("retrieving Country data from wikidata ... (this might take a few seconds)")
        wikidata=Wikidata()
        wikidata.getCountries()
        entityInfo=sqlDB.createTable(wikidata.countryList,"countries",None,withDrop=True,sampleRecordCount=200)
        sqlDB.store(wikidata.countryList,entityInfo,fixNone=True)

    def populate_Regions(self,sqlDB):
        '''
        populate database with regions from wikiData
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        print("retrieving Region data from wikidata ... (this might take a minute)")
        wikidata=Wikidata()
        wikidata.getRegions()
        entityInfo=sqlDB.createTable(wikidata.regionList[:5000],"regions",primaryKey=None,withDrop=True)
        sqlDB.store(wikidata.regionList,entityInfo,fixNone=True)
   
    def populate_Cities_FromWikidata(self,sqlDB):
        '''
        populate the given sqlDB with the Wikidata Cities
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        dbFile=self.db_path+"/City_wikidata.db"
        if not os.path.exists(dbFile):
            print("Downloading %s ... this might take a few seconds" % dbFile)
            dbUrl="http://wiki.bitplan.com/images/confident/City_wikidata.db"
            urllib.request.urlretrieve(dbUrl,dbFile)
        wikiCitiesDB=SQLDB(dbFile)
        wikiCitiesDB.copyTo(sqlDB)
        
    def getWikidataCityPopulation(self,sqlDB,endpoint=None):
        '''
        Args:
            sqlDB(SQLDB): target SQL database
            endpoint(str): url of the wikidata endpoint or None if default should be used
        '''
        dbFile=self.db_path+"/city_wikidata_population.db"
        rawTableName="cityPops"
        # is the wikidata population database available?
        if not os.path.exists(dbFile):
            # shall we created it from a wikidata query?
            if endpoint is not None:
                wikidata=Wikidata()
                wikidata.endpoint=endpoint
                cityList=wikidata.getCityPopulations()
                wikiCitiesDB=SQLDB(dbFile) 
                entityInfo=wikiCitiesDB.createTable(cityList[:300],rawTableName,primaryKey=None,withDrop=True)
                wikiCitiesDB.store(cityList,entityInfo,fixNone=True)
            else:
                # just download a copy 
                print("Downloading %s ... this might take a few seconds" % dbFile)
                dbUrl="http://wiki.bitplan.com/images/confident/city_wikidata_population.db"
                urllib.request.urlretrieve(dbUrl,dbFile)
        # (re) open the database
        wikiCitiesDB=SQLDB(dbFile) 
          
        # check whether the table is populated
        tableList=sqlDB.getTableList()        
        tableName="citiesWithPopulation"     
      
        if self.db_recordCount(tableList, tableName)<10000:
            # check that database is writable
            # https://stackoverflow.com/a/44707371/1497139
            sqlDB.execute("pragma user_version=0")
            # makes sure both tables are in target sqlDB
            wikiCitiesDB.copyTo(sqlDB)
            # create joined table
            sqlQuery="""
              select 
    geoname_id,
    city_name,
    cp.cityLabel,
    country_iso_code,
    country_name,
    subdivision_1_iso_code,
    subdivision_1_name,
    cp.city as wikidataurl,
    cp.cityPop 
  from cities c 
  join cityPops cp 
  on c.geoname_id=cp.geoNameId 
union  
  select 
    geoNameId as geoname_id,
    null as city_name,
    cityLabel,
    countryIsoCode as country_iso_code,
    countryLabel as country_name,
    null as subdivision_1_iso_code,
    null as subdivision_1_name,
    city as wikidataurl,
    cityPop 
  from cityPops 
  where cityPop is not Null
group by geoNameId
order by cityPop desc
            """
            cityList=sqlDB.query(sqlQuery) 
            entityInfo=sqlDB.createTable(cityList,tableName,primaryKey=None,withDrop=True,sampleRecordCount=500)
            sqlDB.store(cityList,entityInfo,fixNone=True)
            # remove raw Table
            #sqlCmd="DROP TABLE %s " %rawTableName
            #sqlDB.execute(sqlCmd)
            
     
    def populate_Cities(self,sqlDB):
        '''
        populate the given sqlDB with the Geolite2 Cities
        
        Args:
            sqlDB(SQLDB): the SQL database to use
        '''
        cities=self.getGeolite2Cities()
        entityName="cities"
        primaryKey="geoname_id"
        entityInfo=sqlDB.createTable(cities[:100],entityName,primaryKey,withDrop=True)
        sqlDB.store(cities,entityInfo,executeMany=False)
        
    def createViews(self,sqlDB):
        viewDDLs=["DROP VIEW IF EXISTS GeoLite2CityLookup","""
CREATE VIEW GeoLite2CityLookup AS
SELECT 
  city_name AS name,
  cityLabel AS wikidataName,
  wikidataurl,
  cityPop,
  subdivision_1_name AS regionName,
  subdivision_1_iso_code as regionIsoCode,
  country_name AS countryName,
  country_iso_code as countryIsoCode

FROM citiesWithPopulation
"""]
        for viewDDL in viewDDLs:
            sqlDB.execute(viewDDL)
        
    
    def db_recordCount(self,tableList,tableName):
        '''
        count the number of records for the given tableName
        
        Args:
            tableList(list): the list of table to check
            tableName(str): the name of the table to check
            
        Returns
            int: the number of records found for the table 
        '''
        tableFound=False
        for table in tableList:
            if table['name']==tableName:
                tableFound=True
                break
        count=0
        if tableFound:    
            query="SELECT Count(*) AS count FROM %s" % tableName
            countResult=self.sqlDB.query(query)
            count=countResult[0]['count']
        return count
     
    def db_has_data(self):
        '''
        check whether the database has data / is populated
        
        Returns:
            boolean: True if the cities table exists and has more than one record
        '''
        tableList=self.sqlDB.getTableList()
        hasCities=self.db_recordCount(tableList,"citiesWithPopulation")>10000
        hasCountries=self.db_recordCount(tableList,"countries")>100
        hasRegions=self.db_recordCount(tableList,"regions")>1000
        hasVersion=self.db_recordCount(tableList,"Version")==1
        versionOk=False
        if hasVersion:
            query="SELECT version from Version"
            dbVersionList=self.sqlDB.query(query)
            versionOk=dbVersionList[0]['version']==self.dbVersion
        #hasWikidataCities=self.db_recordCount(tableList,'City_wikidata')>100000
        ok=hasVersion and versionOk and hasCities and hasRegions and hasCountries
        return ok
    
__version__ = '0.1.15'
__date__ = '2020-09-26'
__updated__ = '2020-09-26'    

DEBUG = 1

    
def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)    
        
    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    user_name="Wolfgang Fahl"
    program_license = '''%s

  Created by %s on %s.
  Copyright 2020 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc,user_name, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="if True show debug information")
        parser.add_argument("-cm", "--correctSpelling", dest="correctMisspelling", action="store_true", help="if True correct typical misspellings")
        parser.add_argument("-db", "--recreateDatabase", dest='recreateDatabase',action="store_true", help="recreate the database")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)

        # Process arguments
        args = parser.parse_args()
        loc=Locator.getInstance(correctMisspelling=args.correctMisspelling,debug=args.debug)
        if args.recreateDatabase:
            loc.recreateDatabase()
        else:
            print ("no other functionality yet ...")
        
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2     
        
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())        
