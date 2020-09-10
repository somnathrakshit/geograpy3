import jellyfish


def remove_non_ascii(s):
    ''' 
    remove non ascii chars from the given string
    Args:
        s(string): the string to remove chars from
    Returns:
        string: the result string with non-ascii chars removed
        
    hat tip: http://stackoverflow.com/a/1342373/2367526    
    '''
    return "".join(i for i in s if ord(i) < 128)


def fuzzy_match(s1, s2, max_dist=.8):
    ''' 
    fuzzy match the given two strings with the given maximum distance
    Args:
        s1(string): first string
        s2(string): second string
        max_dist(float): the distance - default: 0.8
    Returns:
        float: jellyfish jaro_winkler_similarity based on https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance
    '''
    return jellyfish.jaro_winkler_similarity(s1, s2) >= max_dist
