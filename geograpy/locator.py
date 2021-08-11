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
from lodstorage.jsonable import JSONAble, JSONAbleList
from math import radians, cos, sin, asin, sqrt


class LocationManager(EntityManager):
    '''
    a list of locations
    '''
    
    def __init__(self,name,entityName,entityPluralName:str,listName:str=None,clazz=None,primaryKey:str=None,config=None,handleInvalidListTypes=False,filterInvalidListTypes=False,debug=False):
        '''
        construct me

        Args:
            name(string): name of this LocationManager
            entityName(string): entityType to be managed e.g. Country
            entityPluralName(string): plural of the the entityType e.g. Countries
            config(StorageConfig): the configuration to be used if None a default configuration will be used
            handleInvalidListTypes(bool): True if invalidListTypes should be converted or filtered
            filterInvalidListTypes(bool): True if invalidListTypes should be deleted
            debug(boolean): override debug setting when default of config is used via config=None
        '''
        super(LocationManager, self).__init__(name=name,
                                              entityName=entityName,
                                              entityPluralName=entityPluralName,
                                              listName=listName,
                                              clazz=clazz,
                                              tableName=name,
                                              primaryKey=primaryKey,
                                              config=config,
                                              handleInvalidListTypes=handleInvalidListTypes,
                                              filterInvalidListTypes=filterInvalidListTypes,
                                              debug=debug)
        self.balltree= None
        
    def getBallTuple(self,cache:bool=True):
        '''
        get the BallTuple=BallTree,validList of this location list
        
        Args:
            cache(bool): if True calculate and use a cached version otherwise recalculate on
            every call of this function
            
        Returns:
            BallTree,list: a sklearn.neighbors.BallTree for the given list of locations, list: the valid list of locations
            list: valid list of locations
        '''
        validList=[]
        if self.balltree is None or not cache:
            coordinatesrad=[]
            for location in self.getList():
                if location.lat and location.lon:
                    latlonrad=(radians(location.lat),radians(location.lon))
                    coordinatesrad.append(latlonrad)
                    validList.append(location)
            self.ballTuple = BallTree(coordinatesrad, metric='haversine'),validList
        return self.ballTuple

    def getLocationByID(self, wikidataID:str):
        '''
        Returns the location object that corresponds to the given location

        Args:
            wikidataID: wikidataid of the location that should be returned

        Returns:
            Location object
        '''
        for location in self.getList():
            if 'wikidataid' in location.__dict__:
                if location.wikidataid == wikidataID:
                    return location
        return None


    @staticmethod
    def getURLContent(url:str):
        with urllib.request.urlopen(url) as urlResponse:
            content = urlResponse.read().decode()
            return content

    @staticmethod
    def getFileContent(path:str):
        with open(path, "r") as file:
            content=file.read()
            return content

    @staticmethod
    def getBackupDirectory():
        home = str(Path.home())
        path = f"{home}/.geograpy3"
        return path

    @staticmethod
    def downloadBackupFile(url:str, fileName:str, force:bool=False):
        '''
        Downloads from the given url the zip-file and extracts the file corresponding to the given fileName.

        Args:
            url: url linking to a downloadable gzip file
            fileName: Name of the file that should be extracted from gzip file
            force (bool): True if the download should be forced

        Returns:
            Name of the extracted file with path to the backup directory
        '''
        backupDirectory=LocationManager.getBackupDirectory()
        extractTo= f"{backupDirectory}/{fileName}"
        # we might want to check whether a new version is available
        if not os.path.isfile(extractTo) or force:
            if not os.path.isdir(backupDirectory):
                os.makedirs(backupDirectory)
            zipped = f"{extractTo}.gz"
            print(f"Downloading {zipped} from {url} ... this might take a few seconds")
            urllib.request.urlretrieve(url, zipped)
            print(f"unzipping {extractTo} from {zipped}")
            with gzip.open(zipped, 'rb') as gzipped:
                with open(extractTo, 'wb') as unzipped:
                    shutil.copyfileobj(gzipped, unzipped)
            if not os.path.isfile(extractTo):
                raise (f"could not extract {fileName} from {zipped}")
        return extractTo

    def getByName(self, name:str):
        '''
        Get locations matching given name
        Args:
            name: Name of the location

        Returns:
            Returns locations that match the given name
        '''
        if self.config.mode is StoreMode.SQL:
            sqlDB=self.getSQLDB(self.config.cacheFile)
            queryResult=sqlDB.query(f"SELECT wikidataid "
                                    f"FROM {self.tableName} "
                                    f"WHERE name LIKE '{name}' ")
            res=[]
            for record in queryResult:
                if 'wikidataid' in record:
                    location=[location for location in self.getList() if location.wikidataid==record['wikidataid']]
                    res.extend(location)
            return res
        else:
            return [city for city in self.getList() if city.name==name]


class CountryManager(LocationManager):
    '''
    a list of countries
    '''
    
    def __init__(self, name:str="CountryManager",primaryKey:str=None,config=None,handleInvalidListTypes=False,filterInvalidListTypes=False,debug=False):
        super(CountryManager, self).__init__(name=name,
                                             entityName="country",
                                             entityPluralName="countries",
                                             clazz=Country,
                                             primaryKey=primaryKey,
                                             config=config,
                                             handleInvalidListTypes=handleInvalidListTypes,
                                             filterInvalidListTypes=filterInvalidListTypes,
                                             debug=debug
                                             )
       
    @classmethod
    def from_sqlDb(cls,sqlDB):
        countryManager=CountryManager(name="countries_sql")
        query="select * from countries"
        countryLod=sqlDB.query(query)
        for countryRecord in countryLod:
            country=Country()
            country.name=countryRecord["countryLabel"]
            country.iso=countryRecord["countryIsoCode"]
            # TODO Fix table to supply lat/lon directly
            coordStr=countryRecord["countryCoord"]
            country.lat,country.lon=Wikidata.getCoordinateComponents(coordStr)
            countryManager.getList().append(country)
        return countryManager
        

    @classmethod
    def fromErdem(cls):
        '''
        get country list provided by Erdem Ozkol https://github.com/erdem
        '''
        countryManager=CountryManager(name="countries_erdem")
        countryJsonUrl="https://gist.githubusercontent.com/erdem/8c7d26765831d0f9a8c62f02782ae00d/raw/248037cd701af0a4957cce340dabb0fd04e38f4c/countries.json"
        with urllib.request.urlopen(countryJsonUrl) as url:
            jsonCountryList=json.loads(url.read().decode())
            for jsonCountry in jsonCountryList:
                country=Country()
                country.name=jsonCountry['name']
                country.iso=jsonCountry['country_code']
                country.lat=jsonCountry['latlng'][0]
                country.lon=jsonCountry['latlng'][1]
                countryManager.getList().append(country)

        return countryManager
            

    @classmethod
    def fromWikidata(cls):
        '''
        get country list form wikidata
        '''
        countryManager=CountryManager(name="countries_wikidata")
        wikidata=Wikidata()

        wikidata.getCountries()
        if 'countryList' in wikidata.__dict__:
            for countryRecord in wikidata.countryList:
                country = Country()
                country.wikidataid=Wikidata.getWikidataId(countryRecord['country'])
                country.name = countryRecord['countryLabel']
                country.iso = countryRecord['countryIsoCode']
                lon, lat = Wikidata.getCoordinateComponents(countryRecord['countryCoord'])
                country.lat = lat
                country.lon = lon
                country.population = countryRecord['countryPopulation']
                countryManager.getList().append(country)
        return countryManager

    @classmethod
    def fromJSONBackup(cls, config:StorageConfig=None):
        '''
        get country list from json backup (json backup is based on wikidata query results)

        Returns:
            CountryList based on the json backup
        '''
        countryManager=CountryManager(name="countries_json", config=config)
        countryManager.fromCache(force=True, getListOfDicts=cls.getLocationLodFromJsonBackup)
        return countryManager

    @classmethod
    def getLocationLodFromJsonBackup(cls):
        fileName = "countries_geograpy3.json"
        url = "https://raw.githubusercontent.com/wiki/somnathrakshit/geograpy3/data/countries_geograpy3.json.gz"
        backupFile = LocationManager.downloadBackupFile(url, fileName)
        jsonStr = LocationManager.getFileContent(backupFile)
        lod = json.loads(jsonStr)['countries']
        return lod


class RegionManager(LocationManager):
    '''
    a list of regions
    '''

    def __init__(self, name: str = "RegionManager", primaryKey: str = None, config=None, handleInvalidListTypes=False,
                 filterInvalidListTypes=False, debug=False):
        super(RegionManager, self).__init__(name=name,
                                             entityName="region",
                                             entityPluralName="regions",
                                             clazz=Region,
                                             primaryKey=primaryKey,
                                             config=config,
                                             handleInvalidListTypes=handleInvalidListTypes,
                                             filterInvalidListTypes=filterInvalidListTypes,
                                             debug=debug
                                             )
        
    @classmethod
    def from_sqlDb(cls,sqlDB, config:StorageConfig=None):
        regionManager=RegionManager(name="regions_sql", config=config)
        query="select * from regions"
        regionsLod=sqlDB.query(query)
        for regionRecord in regionsLod:
            region=Region()
            region.name=regionRecord["regionLabel"]
            region.iso=regionRecord["regionIsoCode"]
            # TODO Fix table to supply lat/lon directly
            coordStr=regionRecord["location"]
            region.lat,region.lon=Wikidata.getCoordinateComponents(coordStr)
            regionManager.getList().append(region)
        return regionManager

    @classmethod
    def fromWikidata(cls, config:StorageConfig=None):
        '''
        get region list form wikidata
        '''
        regionManager=RegionManager(name="regions_wikidata", config=config)
        regionIDs=[]
        wikidata = Wikidata()
        wikidata.getRegions()
        for regionRecord in wikidata.regionList:
            if 'region' in regionRecord:
                wikidataid=Wikidata.getWikidataId(regionRecord['region'])
                if wikidataid in regionIDs:
                    # complete existing region entry
                    region=regionManager.getLocationByID(wikidataid)
                    # current assumption is that only population and label are duplicates
                    if 'labels' in regionRecord:
                        if 'labels' in region.__dict__:
                            if isinstance(region.labels, list):
                                if regionRecord['labels'] in region.labels:
                                    region.labels.append(regionRecord['labels'])
                            else:
                                labels=[]
                                labels.append(region.labels)
                                labels.append(regionRecord['labels'])
                                region.labels=labels
                        else:
                            region.__dict__['labels']=[regionRecord['labels']]
                    if 'regionPopulation' in regionRecord:
                        population=None
                        if 'population' in region.__dict__:
                            population=max(regionRecord['regionPopulation'], region.population)
                        else:
                            population=regionRecord['regionPopulation']
                        region.population = population
                else:
                    # add new region to the regionList
                    region=Region()
                    region.wikidataid=wikidataid
                    region.name = regionRecord['regionLabel']
                    region.iso = regionRecord['regionIsoCode']
                    if 'location' in regionRecord:
                        lon, lat = Wikidata.getCoordinateComponents(regionRecord['location'])
                        region.lat = lat
                        region.lon = lon
                    if 'regionPopulation' in regionRecord:
                        region.population=regionRecord['regionPopulation']
                    if 'country' in regionRecord:
                        country=regionRecord['country']
                        country_wikidataid=Wikidata.getWikidataId(country)
                        region.country_wikidataid=country_wikidataid
                    regionIDs.append(wikidataid)
                    regionManager.getList().append(region)
        return regionManager

    @classmethod
    def fromJSONBackup(cls, config:StorageConfig=None):
        '''
        get region list from json backup (json backup is based on wikidata query results)

        Returns:
            RegionList based on the json backup
        '''
        regionManager = RegionManager(name="regions_json", config=config)
        regionManager.fromCache(force=True, getListOfDicts=cls.getLocationLodFromJsonBackup)
        return regionManager

    @classmethod
    def getLocationLodFromJsonBackup(cls):
        fileName = "regions_geograpy3.json"
        url = "https://raw.githubusercontent.com/wiki/somnathrakshit/geograpy3/data/regions_geograpy3.json.gz"
        backupFile = LocationManager.downloadBackupFile(url, fileName)
        jsonStr = LocationManager.getFileContent(backupFile)
        lod = json.loads(jsonStr)['regions']
        return lod


class CityManager(LocationManager):
    '''
    a list of cities
    '''

    def __init__(self, name: str = "CityManager", primaryKey: str = None, config=None, handleInvalidListTypes=False,
                 filterInvalidListTypes=False, debug=False):
        super(CityManager, self).__init__(name=name,
                                            entityName="city",
                                            entityPluralName="cities",
                                            clazz=City,
                                            primaryKey=primaryKey,
                                            config=config,
                                            handleInvalidListTypes=handleInvalidListTypes,
                                            filterInvalidListTypes=filterInvalidListTypes,
                                            debug=debug
                                            )

    @classmethod
    def fromWikidata(cls, fromBackup:bool = True, countryIDs:list=None, regionIDs:list=None , config:StorageConfig=None):
        '''
        get city list form wikidata

        Args:
            fromBackup(bool): If True instead of querying wikidata a backup of the wikidata results is used to create the city list. Otherwise wikidata is queried for the city data. Default is True
            countryIDs(list): List of countryWikiDataIDs. Limits the returned cities to the given countries
            regionIDs(list): List of regionWikiDataIDs. Limits the returned cities to the given regions

        Returns:
            CityList based wikidata query results
        '''
        if fromBackup:
            cityList = cls.fromJSONBackup(config=config)
            return cityList
        cityManager=CityManager(name="cities_wikidata", config=config)
        cityIDs=[]
        wikidata = Wikidata()
        cityLOD=wikidata.getCities(region=regionIDs, country=countryIDs)
        for cityRecord in cityLOD:
            if 'city' in cityRecord:
                wikidataid = Wikidata.getWikidataId(cityRecord['city'])
                cityManager.updateCity(wikidataid, cityRecord)
        return cityManager

    def updateCity(self, wikidataid:str, cityRecord:dict):
        '''
        Updates the city corresponding to the given city with the given data.
        If the city does not exist a new city object is created and added to this CityList
        Args:
            wikidataid(str): wikidata id of the city that should be updated/added
            cityRecord(dict): data of the given city that should be updated/added

        Returns:
            Nothing
        '''
        city = self.getLocationByID(wikidataid)
        if city is not None:
            # city already in the cityList -> merge
            # current assumption is that only population and label are duplicates
            if 'labels' in cityRecord:
                if 'labels' in city.__dict__:
                    if isinstance(city.labels, list):
                        if cityRecord['labels'] in city.labels:
                            city.labels.append(cityRecord['labels'])
                    else:
                        labels = []
                        labels.append(city.labels)
                        labels.append(cityRecord['labels'])
                        city.labels = labels
                else:
                    city.__dict__['labels'] = [cityRecord['labels']]
            if 'cityPop' in cityRecord:
                population = None
                if 'population' in city.__dict__ and city.population is not None:
                    if cityRecord['cityPop'] is None:
                        population=city.population
                    else:
                        population = max(float(cityRecord['cityPop']), float(city.population))
                else:
                    population = cityRecord['cityPop']
                city.population = population
        else:
            # add new city to list
            city = City()
            city.wikidataid = wikidataid
            city.name = cityRecord['cityLabel']
            if 'countryCoord' in cityRecord:
                lon, lat = Wikidata.getCoordinateComponents(cityRecord['cityCoord'])
                city.lat = lat
                city.lon = lon
            if 'country' in cityRecord:
                country = cityRecord['country']
                country_wikidataid = Wikidata.getWikidataId(country)
                city.country_wikidataid = country_wikidataid
            if 'region' in cityRecord:
                region = cityRecord['region']
                region_wikidataid = Wikidata.getWikidataId(region)
                city.region_wikidataid = region_wikidataid
            if 'cityPop' in cityRecord:
                city.population = cityRecord['cityPop']
            self.getList().append(city)

    @classmethod
    def fromJSONBackup(cls, config:StorageConfig=None):
        '''
        get city list from json backup (json backup is based on wikidata query results)

        Args:
            jsonStr(str): JSON string the CityList should be loaded from. If None json backup is loaded. Default is None

        Returns:
            CityList based on the json backup
        '''
        cityManager = CityManager(name="cities_json", config=config)
        cityManager.fromCache(force=True, getListOfDicts=cls.getLocationLodFromJsonBackup)
        return cityManager

    @classmethod
    def getLocationLodFromJsonBackup(cls):
        fileName = "cities_geograpy3.json"
        url = "https://raw.githubusercontent.com/wiki/somnathrakshit/geograpy3/data/cities_geograpy3.json.gz"
        backupFile = LocationManager.downloadBackupFile(url, fileName)
        jsonStr = LocationManager.getFileContent(backupFile)
        lod=json.loads(jsonStr)['cities']
        return lod
    
class Earth:
    radius = 6371.000  # radius of earth in km

class Location(JSONAble):
    '''
    Represents a Location
    '''
    def __init__(self, **kwargs):
        self.__dict__=kwargs
        
    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "Los Angeles",
            "wikidataid": "Q65",
            "lat": 34.05223,
            "lon": -118.24368,
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
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        return c * Earth.radius

    def getNClosestLocations(self, lookupLocationManager,n:int):
        """
        Gives a list of up to n locations which have the shortest distance to 
        me as calculated from the given listOfLocations
        
        Args:
            lookupLocationManager(LocationManager): a LocationManager object to use for lookup
            n(int): the maximum number of closest locations to return 
        
        Returns:
            list: a list of result Location/distance tuples
        """
        balltree,lookupListOfLocations=lookupLocationManager.getBallTuple()
        # check for n+1 entries since we might have my own record in the lookup list which we'll ignore late
        distances,indices = balltree.query([[radians(self.lat),radians(self.lon)]], k=n+1, return_distance=True)
        resultLocations=self.balltreeQueryResultToLocationManager(distances[0],indices[0],lookupListOfLocations)
        return resultLocations
        
    def getLocationsWithinRadius(self,lookupLocationManager,radiusKm:float):
        """
        Gives the n closest locations to me from the given lookupListOfLocations
        
        Args:
            lookupLocationManager(LocationManager): a LocationManager object to use for lookup
            radiusKm(float): the radius in which to check (in km)
            
        Returns:
            list: a list of result Location/distance tuples
        """
        balltree,lookupListOfLocations=lookupLocationManager.getBallTuple()
        
        indices,distances = balltree.query_radius([[radians(self.lat),radians(self.lon)]], r=radiusKm / Earth.radius,
                                                    return_distance=True)
        locationList=self.balltreeQueryResultToLocationManager(distances[0],indices[0],lookupListOfLocations)
        return locationList
    
    def balltreeQueryResultToLocationManager(self,distances,indices,lookupListOfLocations):
        '''
        convert the given ballTree Query Result to a LocationManager
        
        Args:
            distances(list): array of distances
            indices(list): array of indices
            lookupListOfLocations(list): a list of valid locations to use for lookup
            
        Return:
            list: a list of result Location/distance tuples
        '''
        locationListWithDistance=[]
        for i,locationIndex in enumerate(indices):
            distance=distances[i]*Earth.radius 
            location=lookupListOfLocations[locationIndex]
            # do not add myself or any other equivalent location
            if not distance<0.0001:
                locationListWithDistance.append((location,distance))
        # sort by distance (Ball tree only does this for one of the queries ...)        
        locationListWithDistance = sorted(locationListWithDistance, key=lambda lwd: lwd[1])
        return locationListWithDistance

    def distance(self,other)->float:
        '''
        calculate the distance to another Location
        
        Args:
            other(Location): the other location
            
        Returns:
            the haversine distance in km
        '''
        # see https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
        distance=Location.haversine(self.lon,self.lat,other.lon,other.lat)
        return distance

    def isKnownAs(self, name)->bool:
        '''
        Checks if this location is known under the given name

        Args:
            name(str): name the location should be checked against

        Returns:
            True if the given name is either the name of the location or present in the labels of the location
        '''
        isKnown=False
        if 'labels' in self.__dict__:
            if name in self.labels:
                isKnown=True
        if 'name' in self.__dict__:
            if name == self.name:
                isKnown=True
        return isKnown
        
    
class City(Location):
    '''
    a single city as an object
    '''

    def __init__(self, **kwargs):
        super(City, self).__init__(**kwargs)
        if 'level' not in self.__dict__:
            self.__dict__['level']=5
        if 'locationKind' not in self.__dict__:
            self.__dict__['locationKind']="City"
        self._country=None
        self._region=None

    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "Los Angeles",
            "wikidataid": "Q65",
            "lat": 34.05223,
            "lon": -118.24368,
            "partOf": "US/CA",
            "level": 5,
            "locationKind": "City",
            "comment": None,
            "population": "3976322",
            "region_wikidataid": "Q99",
            "country_wikidataid": "Q30"
        }]
        return samplesLOD
    
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

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, country):
        self._country=country

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, region):
        self._region=region
        
class Region(Location):
    '''
    a Region (Subdivision)
    '''

    def __init__(self, **kwargs):
        super(Region, self).__init__(**kwargs)
        if 'level' not in self.__dict__:
            self.__dict__['level']=4
        if 'locationKind' not in self.__dict__:
            self.__dict__['locationKind']="Region"
        self._country=None

    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "California",
            "wikidataid": "Q99",
            "lat": 37.0,
            "lon": -120.0,
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

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, country):
        self._country=country

class Country(Location):
    '''
    a country
    '''
    def __init__(self,lookupSource='sqlDB', **kwargs):
        '''
        coonstruct me
        '''
        super(Country, self).__init__(**kwargs)
        if 'level' not in self.__dict__:
            self.__dict__['level']=3
        if 'locationKind' not in self.__dict__:
            self.__dict__['locationKind']="Country"


    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "United States of America",
            "wikidataid": "Q30",
            "lat": 39.82818,
            "lon": -98.5795,
            "partOf": "North America",
            "level": 3,
            "locationKind": "Country",
            "comment": None,
            "labels":["USA", "US", "United States of America"],
            "iso":"US"
        }]
        return samplesLOD

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


class LocationContext(object):
    '''
    Holds LocationManagers of all hierarchy levels and provides methods to traverse through the levels
    '''

    def __init__(self,countryManager:CountryManager, regionManager:RegionManager, cityManager:CityManager ):
        self.countryManager=countryManager
        self.regionManager=regionManager
        self.cityManager=cityManager
        self._countryLookup=countryManager.getLookup("wikidataid")[0]
        self._regionLookup=regionManager.getLookup("wikidataid")[0]
        self._cityLookup=cityManager.getLookup("wikidataid")[0]
        self.interlinkLocations()


    def interlinkLocations(self):
        '''
        Interlinks locations by adding the hierarchy references to the locations
        '''
        # interlink region with country
        for region in self.regions:
            country = self._countryLookup.get(getattr(region, 'country_wikidataid'))
            if country is not None and isinstance(country, Country):
                region.country = country

        # interlink city with region and country
        for city in self.cities:
            country = self._countryLookup.get(getattr(city, 'country_wikidataid'))
            if country is not None and isinstance(country, Country):
                city.country = country
            region = self._regionLookup.get(getattr(city, 'region_wikidataid'))
            if region is not None and isinstance(region, Region):
                city.region = region

    @classmethod
    def fromCache(cls, config:StorageConfig=None, forceUpdate:bool=False):
        '''
        Inits a LocationContext form Cache if existent otherwise init cache
        '''
        if config is None:
            config=cls.getDefaultConfig()
        cityManager=CityManager("cities", config=config)
        regionManager=RegionManager("regions", config=config)
        countryManager=CountryManager("countries",config=config)
        for manager in cityManager, regionManager, countryManager:
            manager.fromCache(force=forceUpdate, getListOfDicts=manager.getLocationLodFromJsonBackup)
        locationContext = LocationContext(countryManager, regionManager, cityManager)
        return locationContext

    @classmethod
    def fromJSONBackup(cls, config:StorageConfig=None):
        '''
        Inits a LocationContext form the JSON backup
        '''
        if config is None:
            config=cls.getDefaultConfig()
        countryList=CountryManager.fromJSONBackup(config=config)
        regionList=RegionManager.fromJSONBackup(config=config)
        cityList=CityManager.fromJSONBackup(config=config)
        for manager in countryList, regionList, cityList:
            manager.store()
        locationContext = LocationContext(countryList, regionList, cityList)
        return locationContext

    @staticmethod
    def getDefaultConfig()->StorageConfig:
        '''
        Returns default StorageConfig
        '''
        config = StorageConfig(cacheDirName="geograpy3")
        cachedir = config.getCachePath()
        config.cacheFile = f"{cachedir}/locations.db"
        return config

    @property
    def countries(self) -> list:
        return self.countryManager.getList()

    @property
    def regions(self)->list:
        return self.regionManager.getList()

    @property
    def cities(self) -> list:
        return self.cityManager.getList()

    def getCountries(self, name:str):
        '''Returns all countries that are known under the given name'''
        countries = self.countryManager.getByName(name)
        return countries

    def getRegions(self, name:str):
        '''Returns all regions that are known under the given name'''
        regions = self.regionManager.getByName(name)
        return regions

    def getCities(self, name:str):
        '''Returns all cities that are known under the given name'''
        cities=self.cityManager.getByName(name)
        return cities

    def locateLocation(self, *locations):
        '''
        Get possible locations for the given location names.
        Current prioritization of the results is city(ordered by population)→region→country
        ToDo: Extend the ranking of the results e.g. matching of multiple location parts increase ranking
        Args:
            *locations:

        Returns:

        '''
        if locations is None or locations is (None):
            return
        possibleLocations={
            self.cityManager.name:set(),
            self.regionManager.name: set(),
            self.countryManager.name: set()
        }
        locationParts=[]
        for location in locations:
            if location is not None:
                for locationPart in location.split(','):
                    locationParts.append(locationPart)
        for location in locationParts:
            location=location.strip()
            for manager in self.cityManager, self.regionManager, self.countryManager:
                possibleLocation=[]
                if Locator.isISO(location):
                    pl=[l for l in manager.getList() if hasattr(l, 'iso') and l.iso == location]
                    possibleLocation.extend(pl)
                possibleLocation.extend(manager.getByName(location))
                # search in location labels → currently not supported in sql backup (n:m relation)
                # pl=[l for l in manager.getList() if l.isKnownAs(location)]
                # possibleLocation.extend(pl)
                possibleLocations[manager.name]=possibleLocations[manager.name].union(set(possibleLocation))
        # reduce possible Locations e.g. remove regions and countries already identified by a city
        for city in possibleLocations[self.cityManager.name]:
            if city.region in possibleLocations[self.regionManager.name]:
                possibleLocations[self.regionManager.name].remove(city.region)
            if city.country in possibleLocations[self.countryManager.name]:
                possibleLocations[self.countryManager.name].remove(city.country)
        for region in possibleLocations[self.regionManager.name]:
            if region.country in possibleLocations[self.countryManager.name]:
                possibleLocations[self.countryManager.name].remove(region.country)
        # build final result in the order city→region→country
        cities=list(possibleLocations[self.cityManager.name])
        cities.sort(key=lambda c: int(getattr(c, 'population', 0)) if getattr(c, 'population') is not None else 0, reverse=True)
        res=[]
        res.extend(cities)
        res.extend(list(possibleLocations[self.regionManager.name]))
        res.extend(list(possibleLocations[self.countryManager.name]))
        return res



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

    @staticmethod
    def isISO(s):
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
            url="https://github.com/somnathrakshit/geograpy3/releases/download/0.1.27/locs.db.gz"
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
            dbUrl="https://github.com/somnathrakshit/geograpy3/releases/download/0.1.27/City_wikidata.db"
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
                dbUrl="https://github.com/somnathrakshit/geograpy3/releases/download/0.1.27/city_wikidata_population.db"
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
    
__version__ = '0.1.29'
__date__ = '2020-09-26'
__updated__ = '2021-07-12'    

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
  Copyright 2020-2021 Wolfgang Fahl. All rights reserved.

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
