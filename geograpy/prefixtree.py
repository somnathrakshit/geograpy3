'''
Created on 2020-09-20

@author: wf
'''
import re
#import marisa_trie
#wraps marisa-trie
#see https://marisa-trie.readthedocs.io/en/latest/tutorial.html#tutorial
class PrefixTree(object):
    '''
    prefix analysis and search
    
    see http://p-nand-q.com/python/data-types/general/tries.html
    '''

    def __init__(self):
        '''
        Constructor
        
        '''
        # self.trie=marisa_trie.Trie(keys)
        self.lookup={}
        self.count=0
        
    def getWords(self,name):    
        words=re.split(r"\W+",name)
        return words
    
    def add(self,name):
        words=self.getWords(name)
        prefix=self.lookup
        self.count+=1
        for word in words:
            if word in prefix:
                prefix=prefix[word]
            else:
                prefix[word]={}
    
    def startsWith(self,name):
        words=self.getWords(name)
        prefix=self.lookup
        for word in words:
            if word in prefix:
                prefix=prefix[word]
            else:
                return 0
        return len(prefix.values())
                