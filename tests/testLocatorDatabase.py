"""
Created on 16.08.2021

@author: wf
"""
import os
import tempfile
import unittest

from lodstorage.storageconfig import StorageConfig

from geograpy.locator import LocationContext, Locator
from tests.basetest import Geograpy3Test


class TestLocatorDatabase(Geograpy3Test):
    """
    test the locator database handling
    """

    def testLocatorWithWikiData(self):
        """
        test Locator
        """
        Locator.resetInstance()
        loc = Locator.getInstance()
        # forceUpdate=True
        forceUpdate = False
        loc.populate_db(force=forceUpdate)
        tableList = loc.sqlDB.getTableList()
        expectedCities = 800000
        self.assertTrue(loc.db_recordCount(tableList, "countries") >= 200)
        self.assertTrue(loc.db_recordCount(tableList, "regions") >= 3000)
        self.assertTrue(loc.db_recordCount(tableList, "cities") >= expectedCities)

    def testHasData(self):
        """
        check has data and populate functionality
        """
        testDownload = False
        if self.inCI() or testDownload:
            with tempfile.TemporaryDirectory() as cacheRootDir:
                config = StorageConfig(
                    cacheRootDir=cacheRootDir, cacheDirName="geograpy3"
                )
                config.cacheFile = (
                    f"{config.getCachePath()}/{LocationContext.db_filename}"
                )
                loc = Locator(storageConfig=config)
                if os.path.isfile(loc.db_file):
                    os.remove(loc.db_file)
                # reinit sqlDB
                loc = Locator(storageConfig=config)
                self.assertFalse(loc.db_has_data())
                loc.populate_db()
                self.assertTrue(loc.db_has_data())


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
