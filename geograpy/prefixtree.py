'''
Created on 2020-09-20

@author: wf
'''
import re
#import marisa_trie
# wraps marisa-trie
# see https://marisa-trie.readthedocs.io/en/latest/tutorial.html#tutorial


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
        self.lookup = {'count': 0, 'words': {}}

    def getCount(self):
        '''
        get my total count

        Returns:
            int: the total number of entries
        '''
        count = self.lookup['count']
        return count

    def getWords(self, name):
        '''
        split the given name into words

        Args:
            name(string): the name to split

        Returns:
            list: a list of words
        '''
        words = re.split(r"\W+", name)
        return words

    def add(self, name):
        '''
        add the given name to the prefix Tree

        Args:
            name(string): the name to add
        '''
        words = self.getWords(name)
        prefix = self.lookup
        prefix['count'] += 1
        for word in words:
            if word:
                if word in prefix['words']:
                    prefix['count'] += 1
                    prefix = prefix['words'][word]
                else:
                    prefix['words'][word] = {'count': 0, 'words': {}}

    def countStartsWith(self, namePrefix):
        '''
        count how many entries start with the given namePrefix

        Args:
            namePrefix(string): the prefix to check
        '''
        words = self.getWords(namePrefix)
        prefix = self.lookup
        for word in words:
            if word in prefix['words']:
                prefix = prefix['words'][word]
            else:
                return 0
        return len(prefix['words'].values())

    def add2Table(self, prefix, prefixStr, table, level):
        '''
        recursively add prefix tree entries to a table 

        Args:
            prefix(dict): the dictionary to start with
            prefixStr(string): the prefix string up to this level
            table(list): a "flat" list of dicts as a table
            level(int): the level (length of word sequence) on which to add
        '''
        for word in prefix['words'].keys():
            prefixNode = prefix['words'][word]
            count = prefixNode['count']
            if count > 1:
                table.append(
                    {'level': level, 'prefix': prefixStr+word, 'count': count})
                self.add2Table(prefixNode, prefixStr+word+" ", table, level+1)

    def store(self, sqlDB):
        '''
        store my prefix information to the given SQL database

        Args:
            sqlDB(SQLDB): the SQL database to use for storing
        '''
        prefixTable = []
        self.add2Table(self.lookup, '', prefixTable, 1)
        entityName = "prefixes"
        primaryKey = 'prefix'
        entityInfo = sqlDB.createTable(
            prefixTable[:100], entityName, primaryKey, withDrop=True)
        sqlDB.store(prefixTable, entityInfo, executeMany=False)
