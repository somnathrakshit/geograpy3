from geograpy.places import PlaceContext
import unittest

class TestPlaces(unittest.TestCase):
    '''
    test Places 
    '''


    def setUp(self):
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
            
        self.assertEqual(1,len(pc.countries))
        self.assertEqual("Kenya",pc.countries[0])
        self.assertEqual(2,len(pc.cities))
        cityNames=['Nairobi','Ohio','Amsterdam']
        countries=['Kenya','United States','Netherlands']
        for index,cityName in enumerate(cityNames):
            cities=pc.cities_for_name(cityName)
            country=cities[0].country
            self.assertEqual(countries[index],country.name)
    
        pc = PlaceContext(['Mumbai'])
        if self.debug:
            print(pc)


if __name__ == "__main__":
    unittest.main()
