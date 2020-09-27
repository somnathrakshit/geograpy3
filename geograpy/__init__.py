'''
main geograpy 3 module
'''
from geograpy.extraction import Extractor
from geograpy.places import PlaceContext
from geograpy.locator import Locator
from geograpy.labels import Labels

def get_geoPlace_context(url=None, text=None,debug=False):
    '''
    Get a place context for a given text with information
    about country, region, city and other
    based on NLTK Named Entities having the Geographic(GPE) label.
    
    Args:
        url(String): the url to read text from (if any)
        text(String): the text to analyze
        debug(boolean): if True show debug information
    
    Returns:
        places: 
            PlaceContext: the place context
    '''    
    places=get_place_context(url, text, labels=Labels.geo, debug=debug)
    return places
    
def get_place_context(url=None, text=None,labels=Labels.default, debug=False):
    '''
    Get a place context for a given text with information
    about country, region, city and other
    based on NLTK Named Entities in the label set Geographic(GPE), 
    Person(PERSON) and Organization(ORGANIZATION).
    
    Args:
        url(String): the url to read text from (if any)
        text(String): the text to analyze
        debug(boolean): if True show debug information
    
    Returns:
        pc: 
            PlaceContext: the place context
    '''
    e = Extractor(url=url, text=text,debug=debug)
    e.find_entities(labels=labels)

    pc = PlaceContext(e.places)
    pc.setAll()
    return pc

def locateCity(location,correctMisspelling=False,debug=False):
    '''
    locate the given location string
    Args:
        location(string): the description of the location
    Returns:
        Locator: the location
    '''
    e = Extractor(text=location,debug=debug)
    e.split()
    loc=Locator.getInstance(correctMisspelling=correctMisspelling,debug=debug)
    city=loc.locateCity(e.places)
    return city
    
