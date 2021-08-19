
from .utils import remove_non_ascii, fuzzy_match
from collections import Counter
from geograpy.locator import Locator, City, Region

"""
Takes a list of place names and works place designation (country, region, etc) 
and relationships between places (city is inside region is inside country, etc)
"""

class PlaceContext(Locator):
    '''
    Adds context information to a place name
    '''

    def __init__(self, place_names:list, setAll:bool=True,correctMisspelling:bool=False):
        '''
        Constructor
        
        Args:
            place_names:
                list: The place names to check
            setAll:
                boolean: True if all context information should immediately be set
            db_file:
                    string: Path to the database file to be used - if None the default "locs.db" will be used
        '''
        super().__init__()
        self.correctMisspelling=correctMisspelling
        self.places = self.normalizePlaces(place_names)
        if setAll:
            self.setAll()
            
    def __str__(self):
        '''
        Return a string representation of me
        '''
        text= "countries=%s\nregions=%s\ncities=%s\nother=%s" % (self.countries,self.regions,self.cities,self.other)
        return text

    def getRegions(self, countryName:str)->list:
        '''
        get a list of regions for the given countryName

        countryName(str): the countryName to check
        '''
        regions = []
        queryString="""SELECT r.*  FROM 
COUNTRIES c 
JOIN regions r ON r.countryId=c.wikidataid
WHERE c.name=(?)"""
        params=(countryName,)
        regionRecords=self.sqlDB.query(queryString, params)
        for regionRecord in regionRecords:
            region=Region.fromRecord(regionRecord)
            regions.append(region)
        return regions

    def get_region_names(self, countryName:str)->list:
        '''
        get region names for the given country
        
        Args:
            countryName(str): the name of the country
        '''
        if self.correctMisspelling:
            countryName = self.correct_country_misspelling(countryName)
        regionOfCountryQuery="""SELECT name 
        FROM regions 
        WHERE countryId IN (
            SELECT wikidataid 
            FROM countries
            WHERE name LIKE (?)
            OR wikidataid IN (
                SELECT wikidataid 
                FROM country_labels 
                WHERE label LIKE (?)
            )
        )"""
        regionRecords=self.sqlDB.query(regionOfCountryQuery, params=(countryName,countryName,))
        return [r.get('name') for r in regionRecords]

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
        '''
        get the region information from my places (limited to the already identified countries)
        '''
        regions = []
        self.country_regions = {}
        region_names = {}

        if not self.countries:
            self.set_countries()

        def region_match(place_name:str, region_name:str)->bool:
            '''
            Tests the similarity of the given strings after removing non ascii characters.
            Args:
                place_name(str): Place name
                region_name(str): valid region name to test against

            Returns:
                True if the similarity of both values is greater equals 80%. Otherwise False
            '''
            return fuzzy_match(remove_non_ascii(place_name),
                               remove_non_ascii(region_name))

        def is_region(place_name:str, region_names:list):
            '''
            Filters out the regions that are not similar to the given place_name
            Args:
                place_name(str): place name to check against the regions
                region_names(list): List of valid region names

            Returns:
                List of regions that are similar to the given place_name
            '''
            return any([region_match(place_name, rn) for rn in region_names])

        for country in self.countries:
            region_names = self.get_region_names(country)
            matched_regions = [p for p in set(self.places) if is_region(p, region_names)]

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
        # ToDo: Duplicate with Locator.city_for_name e.g. extend method to support multiple names
        placesWithoutDuplicates=set(self.places)
        params=",".join("?" * len(placesWithoutDuplicates))
        query="SELECT * FROM CityLookup WHERE name IN (" + params + ")"
        cityLookupRecords=self.sqlDB.query(query,list(placesWithoutDuplicates))
        cityLookupRecords.sort(key=lambda cityRecord: float(cityRecord.get('pop')) if cityRecord.get('pop') is not None else 0.0 , reverse=True)
        for cityLookupRecord in cityLookupRecords:
            city=City.fromCityLookup(cityLookupRecord)
           
            if city.name not in self.cities:
                self.cities.append(city.name)

            countryName=city.country.name
            if countryName not in self.countries:
                self.countries.append(countryName)
                self.country_mentions.append((countryName, 1))

            if countryName not in self.country_cities:
                self.country_cities[countryName] = []

            if city.name not in self.country_cities[countryName]:
                self.country_cities[countryName].append(city.name)
                regionName=city.region.name
                if countryName in self.country_regions and regionName in self.country_regions[countryName]:
                    address=f"{city.name}, {regionName}, {countryName}"
                    self.address_strings.append(address)

        all_cities = [p for p in self.places if p in self.cities]
        self.city_mentions = Counter(all_cities).most_common()

    def set_other(self):
        if not self.cities:
            self.set_cities()

        def unused(place_name):
            places = [self.countries, self.cities, self.regions]
            return all(self.correct_country_misspelling(place_name) not in l for l in places)

        self.other = [p for p in self.places if unused(p)]
