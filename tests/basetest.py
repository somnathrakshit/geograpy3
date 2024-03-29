"""
Created on 2021-08-13

@author: wf
"""
import getpass
import json
import os
from unittest import TestCase

from geograpy.locator import Locator
from geograpy.utils import Profiler


class Geograpy3Test(TestCase):
    """
    base test for geograpy 3 tests
    """

    def setUp(self, debug=False):
        """
        setUp test environment
        """
        TestCase.setUp(self)
        self.debug = debug
        msg = f"test {self._testMethodName}, debug={self.debug}"
        self.profile = Profiler(msg)
        Locator.resetInstance()
        locator = Locator.getInstance()
        locator.downloadDB()
        # actively test Wikidata tests?
        self.testWikidata = False

    def tearDown(self):
        TestCase.tearDown(self)
        self.profile.time()

    def inCI(self):
        """
        are we running in a Continuous Integration Environment?
        """
        publicCI = getpass.getuser() in ["travis", "runner"]
        jenkins = "JENKINS_HOME" in os.environ
        return publicCI or jenkins

    def handleWikidataException(self, ex):
        """
        handle a Wikidata exception
        Args:
            ex(Exception): the exception to handle - e.g. timeout
        """
        msg = str(ex)
        print(f"Wikidata test failed {msg}")
        # only raise exception for real problems
        if "HTTP Error 500" in msg:
            print("test can not work if server has problems")
            return
        if isinstance(ex, json.decoder.JSONDecodeError):
            print("potential SPARQLWrapper issue")
            return
        raise ex
