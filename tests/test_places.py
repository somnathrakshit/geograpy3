import geograpy
from geograpy.places import PlaceContext
from geograpy.locator import Locator
import unittest
from tests.basetest import Geograpy3Test

class TestPlaces(Geograpy3Test):
    '''
    test Places 
    '''


    def setUp(self):
        super().setUp(debug=False)
        Locator.resetInstance()
        pass
    
    def testIssue25(self):
        '''
        https://github.com/somnathrakshit/geograpy3/issues/25
        '''
        pc=PlaceContext(place_names=["Bulgaria","Croatia","Czech Republic","Hungary"])
        if self.debug:
            print (pc.countries)

    def testGetRegionNames(self):
        '''
        test getting region names
        '''
        pc=PlaceContext(place_names=["Berlin"])
        regions=pc.getRegions("Germany")
        self.assertEqual(16,len(regions))
        for region in regions:
            if self.debug:
                print(region)
            self.assertTrue(region.iso.startswith("DE"))
        regionNames=pc.get_region_names("Germany")
        self.assertEqual(16,len(regionNames))
        if self.debug:
            print(regionNames)


    def testPlaces(self):
        '''
        test places
        '''
        pc = PlaceContext(['Ngong', 'Nairobi', 'Kenya'],setAll=False)
        pc.setAll()
       
        
        if self.debug:
            print (pc)

        # Ngong is a city in Cameroon and Kenya
        self.assertEqual(2,len(pc.countries))
        self.assertTrue("Kenya" in pc.countries)
        self.assertEqual(2,len(pc.cities))
        cityNames=['Nairobi','Ohio','Amsterdam']
        countries=['Kenya','United States of America','Netherlands']
        for index,cityName in enumerate(cityNames):
            cities=pc.cities_for_name(cityName)
            country=cities[0].country
            self.assertEqual(countries[index],country.name)
    
        pc = PlaceContext(['Mumbai'])
        if self.debug:
            print(pc)
            
    def testIssue49(self):
        '''
        country recognition
        '''
        show=self.debug
        texts=['United Kingdom','UK','Great Britain','GB','United States']
        expected=["United Kingdom","United Kingdom","United Kingdom","United Kingdom","United States of America"]
        if show:
            print("lookup with geograpy.get_geoPlace_context")
        for text in texts:
            countries=geograpy.get_geoPlace_context(text=text).countries
            if show:
                print (f"{text}:{countries}")
        if show:
            print("lookup with PlaceContext")
        for i,text in enumerate(texts):
            pc=PlaceContext([text])  
            pc.set_countries()
            if show:
                print (f"{text}:{pc.countries}")
            self.assertEqual([expected[i]],pc.countries)


if __name__ == "__main__":
    unittest.main()
