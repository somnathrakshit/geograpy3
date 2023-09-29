'''
Created on 2021-12-27

@author: wf
'''
from OSMPythonTools.cachingStrategy import CachingStrategy, JSON
from OSMPythonTools.nominatim import Nominatim
from geopy.geocoders import Nominatim as GeoNominatim

from pathlib import Path
import os
import logging

class NominatimWrapper(object):
    '''
    Nominatim Wrapper to hide technical details of Nominatim interface
    '''

    def __init__(self, cacheDir:str=None,user_agent:str="ConferenceCorpus"):
        '''
        Constructor

            create a nominatim instance for the given cacheDir - if cacheDir is None use ~/.nominatim as cachedir
        
        Args:
            cacheDir(str): the path to the cache directory to be use by Noninatims JSON caching  Strategy
            user_agent(str): the user_agent to use for the geolocator
            
        '''
        if cacheDir is None:
            home = str(Path.home())
            cacheDir=f"{home}/.nominatim"     
        self.cacheDir=cacheDir
        if not os.path.exists(self.cacheDir):
            os.makedirs(cacheDir)
        logging.getLogger('OSMPythonTools').setLevel(logging.ERROR)     
        CachingStrategy.use(JSON, cacheDir=cacheDir)
        self.nominatim = Nominatim()  
        self.geolocator = GeoNominatim(user_agent=user_agent)

 
    def lookupWikiDataId(self,locationText:str):
        '''
        lookup the Wikidata Identifier for the given locationText (if any)
        
        Args:
            locationText(str): the location text to search for
            
        Return:
            the wikidata Q identifier most fitting the given location text
            
        '''
        wikidataId=None
        nresult=self.nominatim.query(locationText,params={"extratags":"1"})
        nlod=nresult._json
        if len(nlod)>0:
            nrecord=nlod[0]
            if "extratags" in nrecord:
                extratags=nrecord["extratags"]
                if "wikidata" in extratags:
                    wikidataId=extratags["wikidata"]
        return wikidataId
  
        
        