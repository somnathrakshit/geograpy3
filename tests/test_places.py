from geograpy.places import PlaceContext
from geograpy.locator import Locator
import unittest
from tests.basetest import Geograpy3Test

class TestPlaces(Geograpy3Test):
    '''
    test Places 
    '''


    def setUp(self):
        super().setUp()
        Locator.resetInstance()
        self.debug=True
        pass


    def tearDown(self):
        pass
    
    
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


if __name__ == "__main__":
    unittest.main()
