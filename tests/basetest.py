"""
Created on 2021-08-13

@author: wf
"""
import getpass
import json
import os
from unittest import TestCase

from geograpy.action_stats import ActionStats
from geograpy.locator import Locator
from geograpy.utils import Profiler
from geograpy.wikidata import Wikidata


class Geograpy3Test(TestCase):
    """
    base test for geograpy 3 tests
    """

    # Default endpoints to try (in order)
    WIKIDATA_ENDPOINTS = [
        "wikidata-qlever",
        "wikidata-qlever-dbis",
        "wikidata-main",
        "wikidata-dbis"
    ]

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

    def getWorkingWikidataEndpoint(self, min_success_ratio: float = 0.5) -> Wikidata:
        """
        get a working Wikidata endpoint by testing availability

        Args:
            min_success_ratio(float): minimum ratio of successful endpoints (default: 0.5)

        Returns:
            Wikidata: a working Wikidata instance or None if none available
        """
        stats = ActionStats()
        working_wd = None

        for endpoint_name in self.WIKIDATA_ENDPOINTS:
            try:
                wd = Wikidata(endpoint_name=endpoint_name, profile=False)
                is_available = wd.testAvailability()
                stats.add(is_available)
                if is_available and working_wd is None:
                    working_wd = wd
                if self.debug:
                    print(f"{endpoint_name}: {'✅' if is_available else '❌'}")
            except Exception as ex:
                stats.add(False)
                if self.debug:
                    print(f"{endpoint_name}: ❌ {ex}")

        if self.debug:
            print(f"Endpoint availability: {stats}")

        # Check if we have enough working endpoints
        if stats.ratio < min_success_ratio:
            print(f"Not enough endpoints available: {stats}")
            return None

        return working_wd

    def handleWikidataException(self, ex):
        """
        handle a Wikidata exception
        Args:
            ex(Exception): the exception to handle - e.g. timeout
        """
        msg = str(ex)
        print(f"Wikidata test failed {msg}")
        # only raise exception for real problems
        if "HTTP Error 500" in msg or "HTTP Error 503" in msg:
            print("test can not work if server has problems")
            return
        if isinstance(ex, json.decoder.JSONDecodeError):
            print("potential SPARQLWrapper issue")
            return
        raise ex
