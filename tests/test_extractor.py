from geograpy.extraction import Extractor
import geograpy
import unittest
from tests.basetest import Geograpy3Test

class TestExtractor(Geograpy3Test):
    '''
    test Extractor
    '''
    
    
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
        url='https://en.wikipedia.org/wiki/Louvre'
        e = Extractor(url=url)
        e.find_geoEntities()
        self.check(e.places,['Paris','France'])
        
    def testGeograpyIssue32(self):
        '''
        test https://github.com/ushahidi/geograpy/issues/32
        '''
        # do not test since url is unreliable
        return 
        url = "https://www.politico.eu/article/italy-incurable-economy/" 
        places = geograpy.get_geoPlace_context(url = url) 
        if self.debug:
            print(places)
        self.assertSetEqual({'Italy','Germany','France','United States of America','Belgium','Canada'}, set(places.countries))
        self.assertSetEqual({'Rome', 'Brussels', 'Italy','Germany'},set(places.cities))   # Notes: Italy is also city in US-NY, Germany is also city in US-TX
            
    def testGetGeoPlace(self):
        '''
        test geo place handling
        '''
        # 'http://www.bbc.com/news/world-europe-26919928'
        # broken since 2020-10 - returns javascript instead of plain html
        url='https://en.wikipedia.org/wiki/Golden_spike'
        places=geograpy.get_geoPlace_context(url=url)
        debug=self.debug
        #debug=True
        if debug:
            print(places)
        self.assertTrue("Ogden" in places.cities)
        self.assertTrue('Utah' in places.regions)
        self.assertTrue('United States of America' in places.countries)
        
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

    def testIssue7(self):
        '''
        test https://github.com/somnathrakshit/geograpy3/issues/7
        disambiguating countries
        '''
        localities=['Vienna, Illinois,','Paris, Texas','Zaragoza, Spain','Vienna, Austria',
                    
                    ]
        expected=[
            {'iso': 'US'},
            {'iso': 'US'},
            {'iso': 'ES'},
            {'iso': 'AT'},
        ]
        for index,locality in enumerate(localities):
            city=geograpy.locateCity(locality,debug=False)
            if self.debug:
                print(f"  {city}")
            self.assertEqual(expected[index]['iso'],city.country.iso)
       
    def testIssue10(self):
        '''
        test https://github.com/somnathrakshit/geograpy3/issues/10
        Add ISO country code
        ''' 
        localities=[
            'Singapore',
            'Beijing, China',
            'Paris, France',
            'Barcelona, Spain',
            'Rome, Italy',
            'San Francisco, US',
            'Bangkok, Thailand',
            'Vienna, Austria',
            'Athens, Greece',
            'Shanghai, China']
        expectedCountry=[
            'SG',
            'CN','FR','ES','IT','US','TH','AT','GR','CN']
        debug=self.debug
        for index,locality in enumerate(localities):
            city=geograpy.locateCity(locality)
            if debug:
                print("  %s" % city)
            self.assertEqual(expectedCountry[index],city.country.iso)
        
    def testIssue9(self):
        '''
        test https://github.com/somnathrakshit/geograpy3/issues/9
        [BUG]AttributeError: 'NoneType' object has no attribute 'name' on "Pristina, Kosovo"
        '''    
        locality="Pristina, Kosovo"
        gp=geograpy.get_geoPlace_context(text=locality)
        if self.debug:
            print("  %s" % gp.countries)
            print("  %s" % gp.regions)
            print("  %s" % gp.cities)
    
    def testStackoverflow62152428(self):
        '''
        see https://stackoverflow.com/questions/62152428/extracting-country-information-from-description-using-geograpy?noredirect=1#comment112899776_62152428
        '''
        examples={2: 'Socialist Republic of Alachua', 3: 'Hérault, France', 4: 'Gwalior, India', 5: 'Zaragoza,España', 6:'Zaragoza, Spain', 7: 'amsterdam ', 8: 'Evesham', 9: 'Rochdale'}  
        for index,text in examples.items():
            places=geograpy.get_geoPlace_context(text=text)
            if self.debug:
                print("example %d: %s" % (index,places.countries))
        
    def testStackoverflow43322567(self):
        '''
        see https://stackoverflow.com/questions/43322567
        '''
        url='https://en.wikipedia.org/wiki/U.S._state'
        e=Extractor(url=url)
        places=e.find_geoEntities()
        self.check(places,['Alabama','Virginia','New York'])
        if self.debug:
            print(places)
        
    def testStackoverflow54712198(self):
        '''
        see https://stackoverflow.com/questions/54712198/not-only-extracting-places-from-a-text-but-also-other-names-in-geograpypython
        '''
        text='''Opposition Leader Mahinda Rajapaksa says that the whole public administration has collapsed due to the constitution council’s arbitrary actions. The Opposition Leader said so in response to a query a journalised raised after a meeting held...'''
        e=Extractor(text)
        places=e.find_geoEntities()
        if self.debug:
            print(places)
        self.assertEqual([],places)
        
        
    def testStackoverflow54077973(self):
        '''
        see https://stackoverflow.com/questions/54077973/geograpy3-library-for-extracting-the-locations-in-the-text-gives-unicodedecodee
        '''
        address = 'Jersey City New Jersey 07306'
        e=Extractor(text=address)
        e.find_entities()
        self.check(e.places,['Jersey','City'])
     

    def testStackOverflow54721435(self):
        '''
        see https://stackoverflow.com/questions/54721435/unable-to-extract-city-names-from-a-text-using-geograpypython
        '''
        text='I live in Kadawatha a suburb of Colombo  Sri Lanka'
        e=Extractor(text=text)
        e.find_entities()
        if self.debug:
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
