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
import glob
import urllib
import re
import csv
import sys
import gzip
import shutil
import json
from pathlib import Path

from lodstorage.entity import EntityManager
from lodstorage.storageconfig import StorageConfig, StoreMode
from sklearn.neighbors import BallTree
from geograpy.wikidata import Wikidata
from lodstorage.sql import SQLDB
from geograpy.utils import remove_non_ascii
from geograpy import wikidata
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from lodstorage.jsonable import JSONAble
from math import radians, cos, sin, asin, sqrt
from geograpy.utils import Profiler, Download

class LocationManager(EntityManager):
    '''
    a list of locations
    '''
    
    def __init__(self, name:str, entityName:str, entityPluralName:str, listName:str=None, tableName:str=None,clazz=None, primaryKey:str=None, config:StorageConfig=None, handleInvalidListTypes=True, filterInvalidListTypes=False, debug=False):
        '''
        construct me

        Args:
            name(string): name of this LocationManager
            entityName(string): entityType to be managed e.g. Country
            entityPluralName(string): plural of the the entityType e.g. Countries
            listName(str): the name of the list to hold
            tableName(str): the name of the table to use
            config(StorageConfig): the configuration to be used if None a default configuration will be used
            handleInvalidListTypes(bool): True if invalidListTypes should be converted or filtered
            filterInvalidListTypes(bool): True if invalidListTypes should be deleted
            debug(boolean): override debug setting when default of config is used via config=None
        '''
        if config is None:
            config=LocationContext.getDefaultConfig()
        super().__init__(name=name,
                          entityName=entityName,
                          entityPluralName=entityPluralName,
                          listName=listName,
                          clazz=clazz,
                          tableName=tableName,
                          primaryKey=primaryKey,
                          config=config,
                          handleInvalidListTypes=handleInvalidListTypes,
                          filterInvalidListTypes=filterInvalidListTypes,
                          debug=debug)
        self.balltree = None
        self.locationByWikidataID={}
        if config is not None and config.mode==StoreMode.SQL:
            self.sqldb=self.getSQLDB(config.cacheFile)

    def getBallTuple(self, cache:bool=True):
        '''
        get the BallTuple=BallTree,validList of this location list
        
        Args:
            cache(bool): if True calculate and use a cached version otherwise recalculate on
            every call of this function
            
        Returns:
            BallTree,list: a sklearn.neighbors.BallTree for the given list of locations, list: the valid list of locations
            list: valid list of locations
        '''
        validList = []
        if self.balltree is None or not cache:
            coordinatesrad = []
            for location in self.getList():
                if location.lat and location.lon:
                    latlonrad = (radians(location.lat), radians(location.lon))
                    coordinatesrad.append(latlonrad)
                    validList.append(location)
            self.ballTuple = BallTree(coordinatesrad, metric='haversine'), validList
        return self.ballTuple
    
    def fromCache(self,force=False,getListOfDicts=None,sampleRecordCount=-1):
        '''
        get me from the cache
        '''
        super().fromCache(force, getListOfDicts, sampleRecordCount)
        self.locationByWikidataID={}
        for entry in self.getList():
            self.locationByWikidataID[entry.wikidataid]=entry

    def getLocationByID(self, wikidataID:str):
        '''
        Returns the location object that corresponds to the given location

        Args:
            wikidataID: wikidataid of the location that should be returned

        Returns:
            Location object
        '''
        location=None
        if wikidataID in self.locationByWikidataID:
            location=self.locationByWikidataID[wikidataID]
        return location
    
    def add(self,location):
        '''
        add the given location to me 
        
        Args:
            location(object): the location to be added and put in my hash map
        '''
        self.getList().append(location)
        if hasattr(location,"wikidataid"):
            self.locationByWikidataID[location.wikidataid]=location

    
    @staticmethod
    def getBackupDirectory():
        path = str(Path(Path.home(), ".geograpy3"))
        return path
    
    @classmethod
    def downloadBackupFileFromGitHub(cls,fileName:str, targetDirectory:str=None, force:bool=False):
        '''
        download the given fileName from the github data directory
        
        Args:
            fileName(str): the filename to download
            targetDirectory(str): download the file this directory
            force(bool): force the overwriting of the existent file
        
        Return:
            str: the local file
        '''
        # Data is downloaded from the github wiki - to modify the data clone the wiki
        # as documented in https://github.com/somnathrakshit/geograpy3/wiki
        # git clone https://github.com/somnathrakshit/geograpy3.wiki.git
        url = f"https://raw.githubusercontent.com/wiki/somnathrakshit/geograpy3/data/{fileName}.gz"
        if targetDirectory is None:
            targetDirectory=LocationManager.getBackupDirectory()
        backupFile = Download.downloadBackupFile(url, fileName, targetDirectory, force)
        return backupFile

    def getByName(self, *names:str):
        '''
        Get locations matching given names
        Args:
            name: Name of the location

        Returns:
            Returns locations that match the given name
        '''
        query = f"SELECT * FROM {self.clazz.__name__}Lookup WHERE label IN ({','.join('?'*len(names))})"
        sqldb=self.getSQLDB(self.config.cacheFile)
        locationRecords = sqldb.query(query, params=tuple(names))
        locations=self._locationsFromLookup(*locationRecords)
        return locations

    def getLocationsByWikidataId(self, *wikidataId:str):
        '''
        Returns Location objects for the given wikidataids
        Args:
            *wikidataId(str): wikidataIds of the locations that should be returned

        Returns:
            Location objects matching the given wikidataids
        '''
        wikidataIds=set(wikidataId)
        if wikidataIds is None or not wikidataIds:
            return
        query=f"SELECT * FROM {self.clazz.__name__}Lookup WHERE wikidataid IN ({','.join('?'*len(wikidataIds))})"
        sqldb = self.getSQLDB(self.config.cacheFile)
        locationRecords=sqldb.query(query, params=tuple(list(wikidataIds)))
        if locationRecords:
            locations=self._locationsFromLookup(*locationRecords)
            return locations
        else:
            if self.debug:
                print("No Records matching the given wikidataIds found.")
            return

    def _locationsFromLookup(self, *locationRecords:dict):
        '''
        Convert given lookup records to the corresponding location objects
        Args:
            *locationRecords: lookup records of locations

        Returns:
            List of Location objects based on the given records
        '''
        if self.clazz is City:
            locations=[City.fromCityLookup(record) for record in locationRecords]
        elif self.clazz is Region:
            locations = [Region.fromRegionLookup(record) for record in locationRecords]
        elif self.clazz is Country:
            locations = [Country.fromCountryLookup(record) for record in locationRecords]
        else:
            locations=[self.clazz.fromRecord(lr) for lr in locationRecords]
        return locations

    def getLocationByIsoCode(self, isoCode:str):
        '''
        Get possible locations matching the given isoCode
        Args:
            isoCode: isoCode of possible Locations

        Returns:
            List of wikidata ids of locations matching the given isoCode
        '''
        if isinstance(self, RegionManager) or isinstance(self, CountryManager):
            if isinstance(self, RegionManager):
                query = f"SELECT wikidataid FROM {self.tableName} WHERE iso LIKE (?) OR iso LIKE (?)"
                params = (f"%-{isoCode}", isoCode,)
            else:
                query = f"SELECT wikidataid FROM {self.tableName} WHERE iso LIKE (?)"
                params = (isoCode,)
            sqldb = self.getSQLDB(self.config.cacheFile)
            qres = sqldb.query(query, params)
            locationIds = [record['wikidataid'] for record in qres if 'wikidataid' in record]
            return locationIds
        else:
            return []

class CountryManager(LocationManager):
    '''
    a list of countries
    '''
    
    def __init__(self, name:str="CountryManager", config:StorageConfig=None, debug=False):
        super().__init__(name=name,
                            entityName="country",
                            entityPluralName="countries",
                            clazz=Country,
                            primaryKey="wikidataid",
                            tableName="countries",
                            config=config,
                            debug=debug
                            )
        self.wd=Wikidata()
        self.getListOfDicts=self.wd.getCountries

    @classmethod
    def fromErdem(cls):
        '''
        get country list provided by Erdem Ozkol https://github.com/erdem
        '''
        countryManager = CountryManager(name="countries_erdem")
        countryJsonUrl = "https://gist.githubusercontent.com/erdem/8c7d26765831d0f9a8c62f02782ae00d/raw/248037cd701af0a4957cce340dabb0fd04e38f4c/countries.json"
        with urllib.request.urlopen(countryJsonUrl) as url:
            jsonCountryList = json.loads(url.read().decode())
            for jsonCountry in jsonCountryList:
                country = Country()
                country.name = jsonCountry['name']
                country.iso = jsonCountry['country_code']
                country.lat = jsonCountry['latlng'][0]
                country.lon = jsonCountry['latlng'][1]
                countryManager.add(country)

        return countryManager


class RegionManager(LocationManager):
    '''
    a list of regions
    '''

    def __init__(self, name:str="RegionManager", config:StorageConfig=None,debug=False):
        super().__init__(name=name,
                            entityName="region",
                            entityPluralName="regions",
                            clazz=Region,
                            primaryKey="regionId",
                            tableName="regions",
                            config=config,
                            debug=debug
                        )
        self.wd=Wikidata()
        def _queryRegions(**kwargs):
            return [*self.wd.getRegions(**kwargs), *self.wd.getCityStates(**kwargs)]
        self.getListOfDicts=_queryRegions


class CityManager(LocationManager):
    '''
    a list of cities
    '''

    def __init__(self, name:str="CityManager",config:StorageConfig=None,debug=False):
        super().__init__(name=name,
                            entityName="city",
                            entityPluralName="cities",
                            clazz=City,
                            primaryKey=None,
                            tableName="cities",
                            config=config,
                            debug=debug
                        )
        self.wd=Wikidata()
        self.getListOfDicts=self.wd.getCities
       
    @classmethod    
    def getJsonFiles(cls,config:StorageConfig) -> list: 
        '''
        get the list of the json files that have my data
        
        Return:
            list: a list of json file names
        
        '''
        jsondir=f"{config.getCachePath()}/regions"
        if not os.path.exists(jsondir):
                os.makedirs(jsondir)
        jsonFiles = sorted(glob.glob(f"{jsondir}/*.json"), key=lambda path:int(re.findall(r'\d+', path)[0]))
        return jsonFiles
        
    
class Earth:
    radius = 6371.000  # radius of earth in km


class Location(JSONAble):
    '''
    Represents a Location
    '''

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])
        
    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "Los Angeles",
            "wikidataid": "Q65",
            "lat": 34.05223,
            "lon":-118.24368,
            "partOf": "US/CA",
            "level": 5,
            "locationKind": "City",
            "comment": None,
            "population": 3976322
        }]
        return samplesLOD

    @staticmethod
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a)) 
        return c * Earth.radius

    def getNClosestLocations(self, lookupLocationManager, n:int):
        """
        Gives a list of up to n locations which have the shortest distance to 
        me as calculated from the given listOfLocations
        
        Args:
            lookupLocationManager(LocationManager): a LocationManager object to use for lookup
            n(int): the maximum number of closest locations to return 
        
        Returns:
            list: a list of result Location/distance tuples
        """
        balltree, lookupListOfLocations = lookupLocationManager.getBallTuple()
        # check for n+1 entries since we might have my own record in the lookup list which we'll ignore late
        distances, indices = balltree.query([[radians(self.lat), radians(self.lon)]], k=n + 1, return_distance=True)
        resultLocations = self.balltreeQueryResultToLocationManager(distances[0], indices[0], lookupListOfLocations)
        return resultLocations
        
    def getLocationsWithinRadius(self, lookupLocationManager, radiusKm:float):
        """
        Gives the n closest locations to me from the given lookupListOfLocations
        
        Args:
            lookupLocationManager(LocationManager): a LocationManager object to use for lookup
            radiusKm(float): the radius in which to check (in km)
            
        Returns:
            list: a list of result Location/distance tuples
        """
        balltree, lookupListOfLocations = lookupLocationManager.getBallTuple()
        
        indices, distances = balltree.query_radius([[radians(self.lat), radians(self.lon)]], r=radiusKm / Earth.radius,
                                                    return_distance=True)
        locationList = self.balltreeQueryResultToLocationManager(distances[0], indices[0], lookupListOfLocations)
        return locationList
    
    def balltreeQueryResultToLocationManager(self, distances, indices, lookupListOfLocations):
        '''
        convert the given ballTree Query Result to a LocationManager
        
        Args:
            distances(list): array of distances
            indices(list): array of indices
            lookupListOfLocations(list): a list of valid locations to use for lookup
            
        Return:
            list: a list of result Location/distance tuples
        '''
        locationListWithDistance = []
        for i, locationIndex in enumerate(indices):
            distance = distances[i] * Earth.radius 
            location = lookupListOfLocations[locationIndex]
            # do not add myself or any other equivalent location
            if not distance < 0.0001:
                locationListWithDistance.append((location, distance))
        # sort by distance (Ball tree only does this for one of the queries ...)        
        locationListWithDistance = sorted(locationListWithDistance, key=lambda lwd: lwd[1])
        return locationListWithDistance

    def distance(self, other) -> float:
        '''
        calculate the distance to another Location
        
        Args:
            other(Location): the other location
            
        Returns:
            the haversine distance in km
        '''
        # see https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        distance = Location.haversine(self.lon, self.lat, other.lon, other.lat)
        return distance

    def isKnownAs(self, name) -> bool:
        '''
        Checks if this location is known under the given name

        Args:
            name(str): name the location should be checked against

        Returns:
            True if the given name is either the name of the location or present in the labels of the location
        '''
        isKnown = False
        if hasattr(self, 'labels'):
            if name in self.labels:
                isKnown = True
        if hasattr(self, 'name'):
            if name == self.name:
                isKnown = True
        return isKnown

    @staticmethod
    def partialDict(record, clazz, keys=None):
        if keys is None:
            keys = clazz.getSamples()[0].keys()
        pDict = {k: v for k, v in record.items() if k in keys}
        return pDict

    @staticmethod
    def mappedDict(record, keyMapList: list):
        keyMap = {}
        for mkey, mValue in keyMapList:
            keyMap[mkey] = mValue
        pDict = {keyMap[k]: v for k, v in record.items() if k in keyMap.keys()}
        return pDict

    @classmethod
    def fromRecord(cls,regionRecord: dict):
        '''
        create  a location from a dict record

        Args:
            regionRecord(dict): the records as returned from a Query

        Returns:
            Region: the corresponding region information
        '''
        location=cls()
        location.fromDict(regionRecord)
        return location

    
class City(Location):
    '''
    a single city as an object
    '''

    def __init__(self, **kwargs):
        super(City, self).__init__(**kwargs)
        if not hasattr(self, 'level'):
            setattr(self, 'level', 5)
        if not hasattr(self, 'locationKind'):
            setattr(self, 'locationKind', "City")
        self._country = None
        self._region = None

    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "Los Angeles",
            "wikidataid": "Q65",
            "lat": 34.05223,
            "lon":-118.24368,
            "geoNameId": "5368361",
            "gndId": "4036361-2",
            "partOf": "US/CA",
            "level": 5,
            "locationKind": "City",
            "pop": "3976322",
            "regionId": "Q99",
            "countryId": "Q30"
        }]
        return samplesLOD
    
    def __str__(self):
        name=self.name if hasattr(self,"name") else "?"
        text = f"{name} ({self.region} - {self.country})"
        return text

    @staticmethod
    def fromCityLookup(cityLookupRecord:dict):
        '''

        create a city from a cityLookupRecord and setting City, Region and Country while at it
        Args:
            cityRecord(dict): a map derived from the CityLookup view

        '''
        # we create city, region and country from scratch without true
        # object relational mapping and lookup from the locationContext 
        # this is only useful for small result sets that need no further interlinking
        city=City()
        # first take all params
        cityRecord=City.partialDict(cityLookupRecord,City)
        city.fromDict(cityRecord)

        regionRecord=City.mappedDict(cityLookupRecord,
            [("regionId","wikidataid"),("regionName","name"),("regionIso","iso"),("regionPop","pop"),("regionLat","lat"),("regionLon","lon")])
        city.region=Region.fromRecord(regionRecord)

        countryRecord=City.mappedDict(cityLookupRecord,
            [("countryId","wikidataid"),("countryName","name"),("countryIso","iso"),("countryLat","lat"),("countryLon","lon")])
        city.country=Country()
        city.country.fromDict(countryRecord)
        city.region.country=city.country
        return city
    
    def setValue(self, name, record):
        '''
        set a field value with the given name  to
        the given record dicts corresponding entry or none
        
        Args:
            name(string): the name of the field
            record(dict): the dict to get the value from
        '''
        if name in record:
            value = record[name]
        else:
            value = None
        setattr(self, name, value)

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, country):
        self._country = country

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, region):
        self._region = region

        
class Region(Location):
    '''
    a Region (Subdivision)
    '''

    def __init__(self, **kwargs):
        super(Region, self).__init__(**kwargs)
        if not hasattr(self, 'level'):
            setattr(self, 'level', 4)
        if not hasattr(self, 'locationKind'):
            setattr(self,'locationKind', "Region")
        self._country = None

    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "California",
            "wikidataid": "Q99",
            "lat": 37.0,
            "lon":-120.0,
            "partOf": "US",
            "level": 4,
            "locationKind": "Region",
            "comment": None,
            "labels": ["CA", "California"],
            "iso": "US-CA",
            "country_wikidataid": "Q30"
        }]
        return samplesLOD
    
    def __str__(self):
        text = f"{self.iso}({self.name})" 
        return text

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, country):
        self._country = country

    @staticmethod
    def fromRegionLookup(regionLookupRecord: dict):
        '''

        create a region from a regionLookupRecord and setting Region and Country while at it
        Args:
            regionRecord(dict): a map derived from the CityLookup view
        '''
        # we create region and country from scratch without true
        # object relational mapping and lookup from the locationContext
        # this is only useful for small result sets that need no further interlinking
        region = Region()
        # first take all params
        regionRecord = Location.partialDict(regionLookupRecord, Region)
        region.fromDict(regionRecord)
        countryRecord = Location.mappedDict(regionLookupRecord,
                                        [("countryId", "wikidataid"), ("countryName", "name"), ("countryIso", "iso"),
                                         ("countryLat", "lat"), ("countryLon", "lon")])
        region.country = Country()
        region.country.fromDict(countryRecord)
        return region


class Country(Location):
    '''
    a country
    '''

    def __init__(self, lookupSource='sqlDB', **kwargs):
        '''
        coonstruct me
        '''
        super(Country, self).__init__(**kwargs)
        if not hasattr(self, 'level'):
            setattr(self, 'level', 3)
        if not hasattr(self, 'locationKind'):
            setattr(self, 'locationKind', "Country")

    @classmethod
    def getSamples(cls):
        samplesLOD = [
            {
            'wikidataid': 'Q38', 
             'name': 'Italy', 
             'iso': 'IT', 
             'pop': 60317000.0, 
             'lat': 42.5, 
             'lon': 12.5,
            },
            {
            "name": "United States of America",
            "wikidataid": "Q30",
            "lat": 39.82818,
            "lon":-98.5795,
            "partOf": "North America",
            "level": 3,
            "locationKind": "Country",
            "comment": None,
            "labels":["USA", "US", "United States of America"],
            "iso":"US"
        }, {
            }]
        return samplesLOD

    def __str__(self):
        text = f"{self.iso}({self.name})" 
        return text

    @staticmethod
    def fromCountryLookup(countryLookupRecord: dict):
        '''

        create a region from a regionLookupRecord and setting Region and Country while at it
        Args:
            regionRecord(dict): a map derived from the CityLookup view
        '''
        # we create region and country from scratch without true
        # object relational mapping and lookup from the locationContext
        # this is only useful for small result sets that need no further interlinking
        country = Country()
        countryRecord = Location.partialDict(countryLookupRecord, Region)
        country.fromDict(countryRecord)
        return country


class LocationContext(object):
    '''
    Holds LocationManagers of all hierarchy levels and provides methods to traverse through the levels
    '''
    db_filename="locations.db"

    def __init__(self, countryManager:CountryManager, regionManager:RegionManager, cityManager:CityManager, config:StorageConfig):
        '''
        construct me
        
        Args:
            countryManager(CountryManager): the country manager to be used
            regionManager(RegionManager): the region manager to be used
            cityManager(CityManager): the city manager to be used
        '''
        self.countryManager = countryManager
        self.regionManager = regionManager
        self.cityManager = cityManager
        self.locator=Locator(storageConfig=config)

    def interlinkLocations(self,warnOnDuplicates:bool=True,profile=True):
        '''
        Interlinks locations by adding the hierarchy references to the locations
        
        Args:
            warnOnDuplicates(bool): if there are duplicates warn 
        '''
        profile=Profiler("interlinking Locations", profile=profile) 
        duplicates=[]
        self._countryLookup, _dup = self.countryManager.getLookup("wikidataid")
        duplicates.extend(_dup)
        self._regionLookup, _dup = self.regionManager.getLookup("wikidataid")
        duplicates.extend(_dup)
        self._cityLookup, _dup = self.cityManager.getLookup("wikidataid")
        duplicates.extend(_dup)
        if len(duplicates)>0 and warnOnDuplicates:
            print(f"There are {len(duplicates)} duplicate wikidataids in the country,region and city managers used")
            if self.debug:
                print(duplicates)
        # interlink region with country
        for region in self.regions:
            country = self._countryLookup.get(getattr(region, 'countryId'))
            if country is not None and isinstance(country, Country):
                region.country = country

        # interlink city with region and country
        for city in self.cities:
            country = self._countryLookup.get(getattr(city, 'countryId'))
            if country is not None and isinstance(country, Country):
                city.country = country
            region = self._regionLookup.get(getattr(city, 'regionId'))
            if region is not None and isinstance(region, Region):
                city.region = region
        _elapsed=profile.time()
  
                
    def load(self,forceUpdate:bool=False,warnOnDuplicates:bool=False):
        '''
        load my data
        '''
        for manager in self.countryManager,self.regionManager,self.cityManager:
            manager.fromCache(force=forceUpdate)
        self.interlinkLocations(warnOnDuplicates=warnOnDuplicates)
    

    @classmethod
    def fromCache(cls, config:StorageConfig=None, forceUpdate:bool=False):
        '''
        Inits a LocationContext form Cache if existent otherwise init cache

        Args:
            config(StorageConfig): configuration of the cache if None the default config is used
            forceUpdate(bool): If True an existent cache will be over written
        '''
        if config is None:
            config = cls.getDefaultConfig()
        if Download.needsDownload(config.cacheFile):
            LocationManager.downloadBackupFileFromGitHub(fileName=cls.db_filename,
                                                         targetDirectory=config.getCachePath(),
                                                         force=forceUpdate)
        cityManager = CityManager("cities", config=config)
        regionManager = RegionManager("regions", config=config)
        countryManager = CountryManager("countries", config=config)
        locationContext = LocationContext(countryManager, regionManager, cityManager, config)
        return locationContext

    @staticmethod
    def getDefaultConfig() -> StorageConfig:
        '''
        Returns default StorageConfig
        '''
        config = StorageConfig(cacheFile=LocationContext.db_filename,cacheDirName="geograpy3")
        config.cacheFile=f"{config.getCachePath()}/{config.cacheFile}"
        return config

    @property
    def countries(self) -> list:
        return self.countryManager.getList()

    @property
    def regions(self) -> list:
        return self.regionManager.getList()

    @property
    def cities(self) -> list:
        return self.cityManager.getList()

    def locateLocation(self, *locations, verbose:bool=False):
        '''
        Get possible locations for the given location names.
        Current prioritization of the results is city(ordered by population)→region→country
        ToDo: Extend the ranking of the results e.g. matching of multiple location parts increase ranking
        Args:
            *locations:
            verbose(bool): If True combinations of locations names are used to improve the search results. (Increases lookup time)

        Returns:

        '''
        if locations is None or locations is (None):
            return
        locationParts = []
        for location in locations:
            if location is not None:
                for locationPart in location.split(','):
                    locationParts.append(locationPart)
        # Split locationParts even further
        lp=[]
        for locationPart in locationParts:
            parts=locationPart.split(' ')
            lp.extend(parts)
            # Spliting by space breakes the look up for cities such as 'Los Angeles'
            if verbose:
                numberParts=len(parts)
                if numberParts>1:
                    lp.extend([f"{parts[i]} {parts[i+1]}" for i in range(numberParts-1)])
                # if numberParts > 2:
                #     lp.extend([f"{parts[i]} {parts[i + 1]} {parts[i + 2]}" for i in range(numberParts - 2)])
        locationParts.extend(lp)
        locationParts=list(set(locationParts))   # remove duplicates

        cities=self.cityManager.getByName(*locationParts)
        regions = self.regionManager.getByName(*locationParts)
        countries = self.countryManager.getByName(*locationParts)

        # remove locations already identified by location in lower hierarchy
        getAttrValues=lambda locations, attr:[getattr(location,attr) for location in locations if hasattr(location, attr)]
        excludeRegionIds=getAttrValues(cities, 'regionId')
        regions=[region for region in regions if hasattr(region, 'wikidataid') and not region.wikidataid in excludeRegionIds]
        excludeCountryIds=[*getAttrValues(cities, "countryId"), *getAttrValues(regions, "countryId")]
        countries=[country for country in countries if hasattr(country, 'wikidataid') and not country.wikidataid in excludeCountryIds]

        # build final result in the order city→region→country
        cities.sort(key=lambda c: int(getattr(c, 'pop', 0)) if getattr(c, 'pop') is not None else 0, reverse=True)
        res = [*cities, *regions, *countries]
        return res



class Locator(object):
    '''
    location handling
    '''
    
    # singleton instance
    locator = None

    def __init__(self, db_file=None, correctMisspelling=False, storageConfig:StorageConfig=None, debug=False):
        '''
        Constructor
        
        Args:
            db_file(str): the path to the database file
            correctMispelling(bool): if True correct typical misspellings
            storageConfig(StorageConfig): the storage Configuration to use
            debug(bool): if True show debug information
        '''
        self.debug = debug
        self.correctMisspelling = correctMisspelling
        if storageConfig is None:
            storageConfig=LocationContext.getDefaultConfig()
        self.storageConfig=storageConfig
        if db_file is None:
            self.db_path = self.storageConfig.getCachePath()
            self.db_file = self.storageConfig.cacheFile
        else:
            self.db_file=db_file
        self.view = "CityLookup"
        self.loadDB()
        self.getAliases()
        self.dbVersion = "2021-08-18 16:15:00"
        
    @staticmethod
    def resetInstance():
        Locator.locator = None    
    
    @staticmethod
    def getInstance(correctMisspelling=False, debug=False):
        '''
        get the singleton instance of the Locator. If parameters are changed on further calls
        the initial parameters will still be in effect since the original instance will be returned!
        
        Args:
            correctMispelling(bool): if True correct typical misspellings
            debug(bool): if True show debug information
        '''
        if Locator.locator is None:
            Locator.locator = Locator(correctMisspelling=correctMisspelling, debug=debug)
        return Locator.locator

    def normalizePlaces(self,places:list):
        '''
        normalize places

        Args:
            places(list) a list of places

        Return:
            list: stripped and aliased list of places
        '''
        nplaces=[]
        for place in places:
            place = place.strip()
            if place in self.aliases:
                place = self.aliases[place]
            nplaces.append(place)
        return nplaces

    def locateCity(self, places:list):
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
        country = None
        cities = []
        regions = []
        # loop over all word elements
        places=self.normalizePlaces(places)
        for place in places:
            foundCountry = self.getCountry(place)
            if foundCountry is not None:
                country = foundCountry
            foundCities = self.cities_for_name(place)
            cities.extend(foundCities)
            foundRegions = self.regions_for_name(place)
            regions.extend(foundRegions)
        foundCity = self.disambiguate(country, regions, cities)
        return foundCity

    @staticmethod
    def isISO(s):
        '''
        check if the given string is an ISO code (ISO 3166-2 code)
        see https://www.wikidata.org/wiki/Property:P300

        Returns:
            bool: True if the string might be an ISO Code as per a regexp check
        '''
        m = re.search(r"^([A-Z]{1,2}\-)?[0-9A-Z]{1,3}$", s)
        result = m is not None
        return result
               
    def disambiguate(self, country, regions, cities, byPopulation=True): 
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
        foundCity = None
        # is the city information unique?
        if len(cities) == 1:
            foundCity = cities[0]
        else: 
            if len(cities) > 1:
                if country is not None:
                    for city in cities:
                        if self.debug:
                            print("city %s: " % (city))
                        if city.country.iso == country.iso:
                            foundCity = city
                            break
                if foundCity is None and len(regions) > 0:
                    for region in regions:
                        for city in cities:
                            if city.region.iso == region.iso and not city.region.name == city.name:
                                foundCity = city
                                break
                        if foundCity is not None:
                            break
                if foundCity is None and byPopulation:
                    foundCity = max(cities, key=lambda city:0 if city.pop is None else city.pop)
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
        cities = []
        cityRecords = self.places_by_name(cityName, "name")
        for cityRecord in cityRecords:
            cities.append(City.fromCityLookup(cityRecord))
        return cities

    def regions_for_name(self, region_name):
        '''
        get the regions for the given region_name (which might be an ISO code)
        
        Args:
            region_name(string): region name
            
        Returns:
            list: the list of cities for this region
        '''
        regions = []    
        if self.isISO(region_name):
            columnName = "iso"
        else:
            columnName = 'name'
        query = f"SELECT * from regions WHERE {columnName} = (?)" 
        params = (region_name,)
        regionRecords = self.sqlDB.query(query, params)
        for regionRecord in regionRecords:
            regions.append(Region.fromRecord(regionRecord))
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
                if name == remove_non_ascii(row[0]):
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
        country = self.getCountry(name)
        result = country is not None
        return result
       
    def getCountry(self, name):
        '''
        get the country for the given name    
        Args:
            name(string): the name of the country to lookup
        Returns:     
            country: the country if one was found or None if not
        '''
        if self.isISO(name):
            query="SELECT * FROM countries WHERE iso = (?)"""
            params=(name,)
        else:
            if self.correctMisspelling:
                name = self.correct_country_misspelling(name)
            query="""SELECT * FROM countries 
WHERE name LIKE (?)
OR wikidataid in (SELECT wikidataid FROM country_labels WHERE label LIKE (?))"""
            params=(name,name,)
        country = None
        self.populate_db()
        countryRecords=self.sqlDB.query(query,params)
        if len(countryRecords)==1:
            country=Country.fromRecord(countryRecords[0])
            pass
        return country
    
    def getView(self):
        '''
        get the view to be used
        
        Returns:
            str: the SQL view to be used for CityLookups e.g. CityLookup
        '''
        view = self.view
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
        view = self.getView()
        query = f'SELECT * FROM {view} WHERE {columnName} = (?) ORDER BY pop DESC'
        params = (placeName,)
        cityLookupRecords = self.sqlDB.query(query, params)
        cityLookupRecords.sort(key=lambda cityRecord: float(cityRecord.get('pop')) if cityRecord.get('pop') is not None else 0.0,reverse=True)
        return cityLookupRecords
    
     
    def recreateDatabase(self):
        '''
        recreate my lookup database
        '''
        print(f"recreating database ... {self.db_file}")
        self.populate_db(force=True)
        
                
    def populate_db(self, force=False):
        '''
        populate the cities SQL database which caches the information from the GeoLite2-City-Locations.csv file
        
        Args:
            force(bool): if True force a recreation of the database
        '''
        hasData = self.db_has_data()
        if force:
            self.populate_Countries(self.sqlDB)
            self.populate_Regions(self.sqlDB)
            self.populate_Cities(self.sqlDB)
            self.createViews(self.sqlDB)
            self.populate_Version(self.sqlDB)
    
        elif not hasData:
            self.downloadDB()
        if not os.path.isfile(self.db_file):
            raise(f"could not create lookup database {self.db_file}")
        
    def downloadDB(self, forceUpdate:bool=False):
        '''
        download my database

        Args:
            forceUpdate(bool): force the overwriting of the existent file
        '''
        if Download.needsDownload(self.db_file) or forceUpdate:
            LocationManager.downloadBackupFileFromGitHub(fileName=LocationContext.db_filename,
                                                         targetDirectory=self.storageConfig.getCachePath(),
                                                         force=forceUpdate)
            self.loadDB()
        
            
    def populate_Version(self, sqlDB):
        '''
        populate the version table
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        versionList = [{"version":self.dbVersion}]
        entityInfo = sqlDB.createTable(versionList, "Version", "version", withDrop=True)
        sqlDB.store(versionList, entityInfo)
        
    def readCSV(self, fileName:str):
        '''
        read the given CSV file
        
        Args:
            fileName(str): the filename to read
        
        '''
        records = []
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        csvfile = f"{cur_dir}/data/{fileName}" 
        with open(csvfile) as info:
            reader = csv.DictReader(info)
            for row in reader:
                records.append(row)
        return records
        
    def getAliases(self):
        '''
        get the aliases hashTable
        '''
        aliases = self.readCSV("aliases.csv")
        self.aliases = {}
        for alias in aliases:
            self.aliases[alias['name']] = alias['alias']
        
           
    def populate_Countries(self, sqlDB):
        '''
        populate database with countries from wikiData
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        wikidata = Wikidata()
        countryList=wikidata.getCountries()
        wikidata.store2DB(countryList, "countries",primaryKey=None,sqlDB=sqlDB)
 
    def populate_Regions(self, sqlDB):
        '''
        populate database with regions from wikiData
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        wikidata = Wikidata()
        regionList=wikidata.getRegions()
        wikidata.store2DB(regionList, "regions", primaryKey=None, sqlDB=sqlDB)
   
    def populate_Cities(self, sqlDB):
        '''
        populate the given sqlDB with the Wikidata Cities
        
        Args:
            sqlDB(SQLDB): target SQL database
        '''
        #wikidata = Wikidata()
        #wikidata.endpoint="https://confident.dbis.rwth-aachen.de/jena/wdhs/sparql"
        #cityList=wikidata.getCities()
        #wikidata.store2DB(cityList, "cities",primaryKey=None,sqlDB=sqlDB)
        config=LocationContext.getDefaultConfig()
        regionManager = RegionManager(config=config)
        regionManager.fromCache()
        regionByIso,_dup=regionManager.getLookup("iso")
        jsonFiles=CityManager.getJsonFiles(config)
        msg=f"reading {len(jsonFiles)} cached city by region JSON cache files"
        profiler=Profiler(msg)
        cityManager=CityManager(config=config)
        cityManager.getList().clear()
        for jsonFileName in jsonFiles:
            isoMatch = re.search(r"/([^\/]*)\.json", jsonFileName)
            if not isoMatch:
                print(f"{jsonFileName} - does not match a known region's ISO code")
            else:
                rIso=isoMatch.group(1)
                region=regionByIso[rIso]
                with open(jsonFileName) as jsonFile:
                    cities4Region = json.load(jsonFile)
                    for city4Region in cities4Region:
                        city=City()
                        city.fromDict(city4Region)
                        if hasattr(city, "regionId"):
                            city.partOfRegionId=city.regionId
                        city.regionId=region.wikidataid
                        cityManager.add(city)
                        pass
        cityManager.store()
        profiler.time()
        
    def createViews(self, sqlDB):
        viewDDLs = ["DROP VIEW IF EXISTS CityLookup", """
CREATE VIEW CityLookup AS
SELECT 
   cl.label,
   ci.*,
   r.name as regionName ,r.iso as regionIso ,r.pop as regionPop,r.lat as regionLat, r.lon as regionLon,
   c.name as countryName,c.iso as countryIso,c.lat as CountryLat, c.lon as CountryLon
FROM 
city_labels cl
JOIN cities ci on ci.wikidataid=cl.wikidataid
JOIN regions r on ci.regionId=r.wikidataid
JOIN countries c on ci.countryId=c.wikidataid
""","DROP VIEW IF EXISTS RegionLookup",
"""CREATE VIEW RegionLookup AS
SELECT 
   rl.label,
   r.*,
   c.name as countryName,c.iso as countryIso,c.lat as CountryLat, c.lon as CountryLon
FROM 
region_labels rl
JOIN regions r on rl.wikidataid=r.wikidataid
JOIN countries c on r.countryId=c.wikidataid
""","DROP VIEW IF EXISTS CountryLookup",
"""CREATE VIEW CountryLookup AS
SELECT 
   cl.label,
   c.*
FROM 
country_labels cl
JOIN countries c on cl.wikidataid=c.wikidataid
""",
"DROP INDEX if EXISTS cityLabelByWikidataid",
"CREATE INDEX cityLabelByWikidataid ON city_labels (wikidataid)",
"DROP INDEX if EXISTS cityByWikidataid",
"CREATE INDEX cityByWikidataid ON cities (wikidataid)",
"DROP INDEX IF EXISTS cityByRegion",
"CREATE INDEX cityByRegion ON cities (regionId)",
"DROP INDEX IF EXISTS regionByCountry",
"CREATE INDEX regionByCountry ON regions (countryId)"]
        for viewDDL in viewDDLs:
            sqlDB.execute(viewDDL)
    
    def db_recordCount(self, tableList, tableName):
        '''
        count the number of records for the given tableName
        
        Args:
            tableList(list): the list of table to check
            tableName(str): the name of the table to check
            
        Returns
            int: the number of records found for the table 
        '''
        tableFound = False
        for table in tableList:
            if table['name'] == tableName:
                tableFound = True
                break
        count = 0
        if tableFound: 
            query = "SELECT Count(*) AS count FROM %s" % tableName
            countResult = self.sqlDB.query(query)
            count = countResult[0]['count']
        return count
     
    def db_has_data(self):
        '''
        check whether the database has data / is populated
        
        Returns:
            boolean: True if the cities table exists and has more than one record
        '''
        tableList = self.sqlDB.getTableList()
        hasCities = self.db_recordCount(tableList,"cities")>200000
        hasCountries = self.db_recordCount(tableList, "countries") > 200
        hasRegions = self.db_recordCount(tableList, "regions") > 3000
        hasVersion = self.db_recordCount(tableList, "Version") == 1
        versionOk = False
        if hasVersion:
            query = "SELECT version from Version"
            dbVersionList = self.sqlDB.query(query)
            versionOk = dbVersionList[0]['version'] == self.dbVersion
        # hasWikidataCities=self.db_recordCount(tableList,'City_wikidata')>100000
        ok = hasVersion and versionOk and hasCities and hasRegions and hasCountries
        return ok

    def loadDB(self):
        '''
        loads the database from cache and sets it as sqlDB property
        '''
        self.sqlDB = SQLDB(self.db_file, errorDebug=True)

    
__version__ = '0.2.2'
__date__ = '2020-09-26'
__updated__ = '2021-11-29'

DEBUG = 1

    
def main(argv=None):  # IGNORE:C0111
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
    user_name = "Wolfgang Fahl"
    program_license = '''%s

  Created by %s on %s.
  Copyright 2020-2021 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, user_name, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="if True show debug information")
        parser.add_argument("-cm", "--correctSpelling", dest="correctMisspelling", action="store_true", help="if True correct typical misspellings")
        parser.add_argument("-db", "--recreateDatabase", dest='recreateDatabase', action="store_true", help="recreate the database")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)

        # Process arguments
        args = parser.parse_args()
        loc = Locator.getInstance(correctMisspelling=args.correctMisspelling, debug=args.debug)
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
