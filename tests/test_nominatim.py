'''
Created on 2021-08-20

@author: wf
'''

from tests.basetest import Geograpy3Test
from geograpy.nominatim import NominatimWrapper
class TestGeopy(Geograpy3Test):
    '''
    test geopy and other nominatim handlers
    '''

    def testNominatim(self):
        '''
        test nominatim results - especially the extra tags
        '''
        examples=[{
            "city":"London",
            "q": "Q84",
            "expected": "England"
        },{
            "city":"Dublin",
            "q": "Q1761",
            "expected": "Éire"
        },{
            "city":"Vienna Austria",
            "q": "Q1741",
            "expected": "Österreich"
        },{
            "city":"Athens, Georgia",
            "q": "Q203263",
            "expected": "Athens-Clarke County"
        },
        # inconsistent results - 2021-12-27
        #{
        #    "city":"St. Petersburg",
        #    "q": "Q656",
        #    "expected": "Санкт-Петербург"
        #},
        {
            # so for St. Petersburg we need to be more specific
            "city":"St. Petersburg, Russia",
            "q": "Q656",
            # to get the russian one
            "expected": "Санкт-Петербург"
        },{
            "city":"Arlington, VA",
            "q": "Q107126",
            "expected": "Virginia"
        }
        ]
        
        nw=NominatimWrapper()
        show=self.debug
        # show=True
        if show:
            print(nw.cacheDir)
        for example in examples:
            city=example["city"]
            location = nw.geolocator.geocode(city)
            wikidataId=nw.lookupWikiDataId(city)
            q=example["q"]
            expected=example["expected"] 
            if show:
                print(f"{city:<22}:{str(wikidataId):<7}/{str(q):<7}:{location}→{expected}")
            self.assertEqual(str(q),str(wikidataId))
            self.assertTrue(expected in str(location),f"{location}→{expected}")
        pass