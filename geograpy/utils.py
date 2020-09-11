import jellyfish


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
    Args:
        s1: 
            string: First string 
        s2: 
            string: Second string 
        max_dist: 
            float: The distance - default: 0.8 
    Returns:
        float: 
            jellyfish jaro_winkler_similarity based on https://en.wikipedia.org/wiki/Jaro-Winkler_distance
    '''
    return jellyfish.jaro_winkler_similarity(s1, s2) >= max_dist
