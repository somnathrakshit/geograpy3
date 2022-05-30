import gzip
import shutil
import jellyfish
import time
import urllib.request
import os

class Download:
    '''
    Utility functions for downloading data
    '''
    
    @staticmethod
    def getURLContent(url:str):
        with urllib.request.urlopen(url) as urlResponse:
            content = urlResponse.read().decode()
            return content

    @staticmethod
    def getFileContent(path:str):
        with open(path, "r") as file:
            content = file.read()
            return content

    @staticmethod
    def needsDownload(filePath:str,force:bool=False)->bool:
        '''
        check if a download of the given filePath is necessary that is the file
        does not exist has a size of zero or the download should be forced
        
        Args:
            filePath(str): the path of the file to be checked
            force(bool): True if the result should be forced to True
            
        Return:
            bool: True if  a download for this file needed
        '''
        if not os.path.isfile(filePath):
            result=True
        else:
            stats=os.stat(filePath)
            size=stats.st_size
            result=force or size==0
        return result

    @staticmethod
    def downloadBackupFile(url:str, fileName:str, targetDirectory:str, force:bool=False):
        '''
        Downloads from the given url the zip-file and extracts the file corresponding to the given fileName.

        Args:
            url: url linking to a downloadable gzip file
            fileName: Name of the file that should be extracted from gzip file
            targetDirectory(str): download the file this directory
            force (bool): True if the download should be forced

        Returns:
            Name of the extracted file with path to the backup directory
        '''
        extractTo = f"{targetDirectory}/{fileName}"
        # we might want to check whether a new version is available
        if Download.needsDownload(extractTo, force=force):
            if not os.path.isdir(targetDirectory):
                os.makedirs(targetDirectory)
            zipped = f"{extractTo}.gz"
            print(f"Downloading {zipped} from {url} ... this might take a few seconds")
            urllib.request.urlretrieve(url, zipped)
            print(f"Unzipping {extractTo} from {zipped}")
            with gzip.open(zipped, 'rb') as gzipped:
                with open(extractTo, 'wb') as unzipped:
                    shutil.copyfileobj(gzipped, unzipped)
                print("Extracting completed")
            if not os.path.isfile(extractTo):
                raise (f"could not extract {fileName} from {zipped}")
        return extractTo


class Profiler:
    '''
    simple profiler
    '''
    def __init__(self,msg,profile=True):
        '''
        construct me with the given msg and profile active flag
        
        Args:
            msg(str): the message to show if profiling is active
            profile(bool): True if messages should be shown
        '''
        self.msg=msg
        self.profile=profile
        self.starttime=time.time()
        if profile:
            print(f"Starting {msg} ...")
    
    def time(self,extraMsg=""):
        '''
        time the action and print if profile is active
        '''
        elapsed=time.time()-self.starttime
        if self.profile:
            print(f"{self.msg}{extraMsg} took {elapsed:5.1f} s")
        return elapsed
        
        
def remove_non_ascii(s):
    ''' 
    Remove non ascii chars from the given string 
    Args:
        s: 
            string: The string to remove chars from 
    Returns:
        string: The result string with non-ascii chars removed 
        
    Hat tip: http://stackoverflow.com/a/1342373/2367526    
    '''
    return "".join(i for i in s if ord(i) < 128)


def fuzzy_match(s1, s2, max_dist=.8):
    ''' 
    Fuzzy match the given two strings with the given maximum distance
    jellyfish jaro_winkler_similarity based on https://en.wikipedia.org/wiki/Jaro-Winkler_distance
    Args:
        s1: 
            string: First string 
        s2: 
            string: Second string 
        max_dist: 
            float: The distance - default: 0.8 
    Returns:
        True if the match is greater equals max_dist. Otherwise false
    '''
    return jellyfish.jaro_winkler_similarity(s1, s2) >= max_dist
