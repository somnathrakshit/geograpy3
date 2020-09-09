from geograpy.places import PlaceContext
import unittest

class TestPlaces(unittest.TestCase):


    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass
    
    def testStackoverflow55548116(self):
        '''
        see https://stackoverflow.com/questions/55548116/geograpy3-library-is-not-working-properly-and-give-traceback-error
        '''
        feedContent=['Las Vegas is a city in Nevada']
        placesInFeed=[]
        for content in feedContent:

            if content != "":
                place = PlaceContext(content)
                placesInFeed.append(place.places)
        
            else:
                placesInFeed.append("null")

    def testPlaces(self):
        '''
        test places
        '''
        pc = PlaceContext(['Ngong', 'Nairobi', 'Kenya'])
        pc.set_countries()
        pc.set_regions()
        pc.set_cities()
        pc.set_other()
        
        if self.debug:
            print ("countries=%s" % pc.countries)
            print ("cities=%s" % pc.cities)
            
        assert len(pc.countries) == 3
        assert len(pc.cities) == 1
        # assert len(pc.other) == 1
        # assert 'Ngong' in pc.other
    
        assert pc.cities_for_name('Nairobi')[0][4] == 'Kenya'
        assert pc.regions_for_name('Ohio')[0][4] == 'United States'
    
        pc = PlaceContext(['Mumbai'])
        pc.set_countries()
        pc.set_regions()
        pc.set_cities()
        pc.set_other()
        if self.debug:
            print(pc)


if __name__ == "__main__":
    unittest.main()
