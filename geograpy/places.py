
import pycountry
from .utils import remove_non_ascii, fuzzy_match
from collections import Counter
from geograpy.locator import Locator

"""
Takes a list of place names and works place designation (country, region, etc) 
and relationships between places (city is inside region is inside country, etc)
"""

class PlaceContext(Locator):
    '''
    Adds context information to a place name
    '''

    def __init__(self, place_names, setAll=True):
        '''
        Constructor
        
        Args:
            place_names: 
                string: The place names to check
            setAll: 
                boolean: True if all context information should immediately be set
            db_file: 
                    string: Path to the database file to be used - if None the default "locs.db" will be used
        '''
        super().__init__()
        self.places = place_names
        if setAll:
            self.setAll()
            
    def __str__(self):
        '''
        Return a string representation of me
        '''
        text= "countries=%s\nregions=%s\ncities=%s\nother=%s" % (self.countries,self.regions,self.cities,self.other)
        return text

    def get_region_names(self, country_name):
        country_name = self.correct_country_misspelling(country_name)
        try:
            obj = pycountry.countries.get(name=country_name)
            regions = pycountry.subdivisions.get(country_code=obj.alpha2)
        except:
            regions = []

        return [r.name for r in regions]

    def setAll(self):
        '''
        Set all context information
        '''
        self.set_countries()
        self.set_regions()
        self.set_cities()
        self.set_other()
        
    def set_countries(self):
        '''
        get the country information from my places
        '''
        countries = []
        for place in self.places:
            country=self.getCountry(place)
            if country is not None:
                countries.append(country.name)

        self.country_mentions = Counter(countries).most_common()
        self.countries = list(set(countries))
        pass

    def set_regions(self):
        regions = []
        self.country_regions = {}
        region_names = {}

        if not self.countries:
            self.set_countries()

        def region_match(place_name, region_name):
            return fuzzy_match(remove_non_ascii(place_name),
                               remove_non_ascii(region_name))

        def is_region(place_name, region_names):
            return filter(lambda rn: region_match(place_name, rn), region_names)

        for country in self.countries:
            region_names = self.get_region_names(country)
            matched_regions = [p for p in self.places if is_region(p, region_names)]

            regions += matched_regions
            self.country_regions[country] = list(set(matched_regions))

        self.region_mentions = Counter(regions).most_common()
        self.regions = list(set(regions))

    def set_cities(self):
        '''
        set the cities information
        '''
        self.cities = []
        self.country_cities = {}
        self.address_strings = []

        if not self.countries:
            self.set_countries()

        if not self.regions:
            self.set_regions()

        if not self.db_has_data():
            self.populate_db()
        params=",".join("?" * len(self.places))
        query="SELECT * FROM cities WHERE city_name IN (" + params + ")"
        cities=self.sqlDB.query(query,self.places)

        for city in cities:
            country = None
            alpha_2=city['country_iso_code']
            country = pycountry.countries.get(alpha_2=alpha_2)
            if country is not None:
                country_name = country.name
            else:
                country_name = city['country_name']
     
            city_name = city['city_name']
            region_name = city['subdivision_1_name']

            if city_name not in self.cities:
                self.cities.append(city_name)

            if country_name not in self.countries:
                self.countries.append(country_name)
                self.country_mentions.append((country_name, 1))

            if country_name not in self.country_cities:
                self.country_cities[country_name] = []

            if city_name not in self.country_cities[country_name]:
                self.country_cities[country_name].append(city_name)

                if country_name in self.country_regions and region_name in self.country_regions[country_name]:
                    self.address_strings.append(city_name + ", " + region_name + ", " + country_name)

        all_cities = [p for p in self.places if p in self.cities]
        self.city_mentions = Counter(all_cities).most_common()

    def set_other(self):
        if not self.cities:
            self.set_cities()

        def unused(place_name):
            places = [self.countries, self.cities, self.regions]
            return all(self.correct_country_misspelling(place_name) not in l for l in places)

        self.other = [p for p in self.places if unused(p)]
