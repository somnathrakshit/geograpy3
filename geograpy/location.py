'''
Created on 2020-09-18

@author: wf
'''
import os
import csv
import sqlite3
import pycountry
from .utils import remove_non_ascii

class Location(object):
    '''
    location handling
    '''

    def __init__(self, db_file=None,debug=False):
        '''
        Constructor
        '''
        self.debug=debug
        db_file = db_file or os.path.dirname(os.path.realpath(__file__)) + "/locs.db"
        self.conn = sqlite3.connect(db_file)
        self.conn.text_factory = lambda x: str(x, 'utf-8', 'ignore')
        self.country=None
        self.city=None
        self.region=None
        
    def locate(self,places):
        '''
        locate a city, region country combination based on the places information
        
        Args:
            places(list): a list of place tokens e.g. "Vienna, Austria"
        
        Returns:
            Location: a complete location with potentially country, region and city
        '''
        # city candidates - may be from multiple countries
        country=None
        cities=[]
        regions=[]
        for place in places:
            foundCountry=self.getCountry(place)
            if foundCountry is not None:
                country=foundCountry
            foundCities=self.cities_for_name(place)
            if foundCities is not None:
                cities.extend(foundCities)
            foundRegions=self.regions_for_name(place)
            if foundRegions is not None:
                regions.extend(foundRegions)
        self.disambiguate(country, regions, cities)
       
    def disambiguate(self,country,regions,cities): 
        '''
        try determining country, regions and city from the potential choices
        '''
        if self.debug:
            print("countries: %s " % country)
            print("regions: %s" % regions)
            print("cities: %s" % cities)
        self.country=country
        # is the city information unique?
        if len(cities)==1:
            self.city=cities[0]
        elif len(cities)>1 and self.country is not None:
            for city in cities:
                cityCountry=city[3]
                if self.debug:
                    print("city country %s (%s): " %(cityCountry,city))
                if cityCountry==self.country.alpha_2:
                    self.city=city
    
    def cities_for_name(self, city_name):
        '''
        find cities with the given city_name
        
        Args:
            city_name(string): the potential name of a city
        
        Returns:
            a list of city records
        '''
        return self.places_by_name(city_name, 'city_name')

    def regions_for_name(self, region_name):
        return self.places_by_name(region_name, 'subdivision_name')
    
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

    def is_a_country(self, name,correctMisspelling=True):
        '''
        check if the given string name is a country
        
        Args:
            name(string): the string to check
        Returns:
            True: if pycountry thinks the string is a country
        '''
        country=self.getCountry(name,correctMisspelling)
        result=country is not None
        return result
       
    def getCountry(self,name,correctMisspelling=True):
        '''
        get the country for the given name    
        Args:
            name(string): the name of the country to lookup
            correctMispelling(boolean): if True correct typical misspellings
        Returns:     
            country: the country if one was found or None if not
        '''
        if correctMisspelling:
            name = self.correct_country_misspelling(name)
        country=pycountry.countries.get(name=name)
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

        cur = self.conn.cursor()
        cur.execute('SELECT * FROM cities WHERE ' + column_name + ' = "' + place_name + '"')
        rows = cur.fetchall()

        if len(rows) > 0:
            return rows

        return None
        
    def populate_db(self):
        '''
        populate the cities SQL database which caches the information from the GeoLite2-City-Locations.csv file
        '''
        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS cities")

        cur.execute(
            "CREATE TABLE cities(geoname_id INTEGER, continent_code TEXT, continent_name TEXT, country_iso_code TEXT, country_name TEXT, subdivision_iso_code TEXT, subdivision_name TEXT, city_name TEXT, metro_code TEXT, time_zone TEXT)")
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        with open(cur_dir + "/data/GeoLite2-City-Locations.csv") as info:
            reader = csv.reader(info)
            for row in reader:
                cur.execute("INSERT INTO cities VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", row)
            self.conn.commit()

    def db_has_data(self):
        '''
        check whether the database has data / is populated
        
        Returns:
            boolean: True if the cities table exists and has more than one record
        '''
        cur = self.conn.cursor()

        cur.execute("SELECT Count(*) FROM sqlite_master WHERE name='cities';")
        data = cur.fetchone()[0]

        if data > 0:
            cur.execute("SELECT Count(*) FROM cities")
            data = cur.fetchone()[0]
            return data > 0
        return False    
        