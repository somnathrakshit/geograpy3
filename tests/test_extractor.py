from geograpy.extraction import Extractor
import unittest

class TestExtractor(unittest.TestCase):
    '''
    test the extractor
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass
    
    def check(self,places,expectedList):
        '''
        check the places for begin non empty and having at least the expected List of
        elements
        
        Args:
            places(Places): the places to check
            expectedList(list): the list of elements to check
        '''
        if self.debug:
            print(places)
        self.assertTrue(len(places)>0)
        for expected in expectedList:
            self.assertTrue(expected in places)

    def testExtractorFromUrl(self):
        '''
        test the extractor
        '''
        e = Extractor(url='http://www.bbc.com/news/world-europe-26919928')
        e.find_entities()
        self.check(e.places,['Russia','Kiev'])
        
    def testExtractorFromText(self):
        '''
        test different texts for getting geo context information
        '''
        text = """ Perfect just Perfect! It's a perfect storm for Nairobi on a 
        Friday evening! horrible traffic here is your cue to become worse @Ma3Route """
    
        e2 = Extractor(text=text)
        e2.find_entities()
        self.check(e2.places,['Nairobi'])
    
        text3 = """ Risks of Cycling in Nairobi:http://www.globalsiteplans.com/environmental-design/engineering-environmental-design/the-risky-affair-of-cycling-in-nairobi-kenya/ ... via @ConstantCap @KideroEvans @county_nairobi @NrbCity_Traffic """
        e3 = Extractor(text=text3)
        e3.find_entities()
        self.check(e3.places,['Nairobi'])
    
        text4 = """ @DurbanSharks [Africa Renewal]It is early morning in Nairobi, the Kenyan capital. The traffic jam along Ngong """
        e4 = Extractor(text=text4)
        e4.find_entities()
        self.check(e4.places,['Nairobi','Ngong'])
    
        # unicode
        text5 = u""" There is a city called New York in the United States."""
        e5 = Extractor(text=text5)
        e5.find_entities()
        self.check(e5.places,['New York','United States'])
    
        # unicode and two words
        text6 = u""" There is a city called São Paulo in Brazil."""
        e6 = Extractor(text=text6)
        e6.find_entities()
        self.check(e6.places,['São Paulo'])

    def testStackOverflow54721435(self):
        '''
        see https://stackoverflow.com/questions/54721435/unable-to-extract-city-names-from-a-text-using-geograpypython
        '''
        text='I live in Kadawatha a suburb of Colombo  Sri Lanka'
        e=Extractor(text=text)
        e.find_entities()
        print(e.places)
        
    def testStackoverflow55548116(self):
        '''
        see https://stackoverflow.com/questions/55548116/geograpy3-library-is-not-working-properly-and-give-traceback-error
        '''
        feedContent=['Las Vegas is a city in Nevada']
        placesInFeed=[]
        
        for content in feedContent:
            if content != "":
                e=Extractor(text=content)
                e.find_entities()
                places = e.places
                if self.debug:
                    print(places)
                placesInFeed.append(places)    
        

if __name__ == "__main__":
    unittest.main()
