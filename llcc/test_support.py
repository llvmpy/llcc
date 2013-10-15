from __future__ import print_function
import os
import sys
import re
import unittest

class TestSystem(object):
    def __init__(self):
        self.suite = unittest.TestSuite()
        self.regex_tests = re.compile('^test', re.I)

    def discover(self, mod):
        path = mod.__path__[0]
        self.scan_directory(mod.__name__, path)

    def scan_directory(self, mod ,curdir):
        listing = os.listdir(curdir)
        files = ('.'.join((mod, f.split('.', 1)[0])) for f in listing
                 if f.startswith('test_') and f.endswith('.py'))
        for f in files:
            self.find_tests_in_file(f)

    def find_tests_in_file(self, f):
        mod = __import__(f)
        for n in f.split('.')[1:]:
            mod = getattr(mod, n)
        for name, obj in vars(mod).items():
            if self.regex_tests.match(name):
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                    self.suite.addTest(unittest.makeSuite(obj))

    def run(self, **kwargs):
        if sys.version_info[:2] <= (2, 6):
            del kwargs['buffer']

        runner = unittest.TextTestRunner(**kwargs)
        testresult = runner.run(self.suite)
        return testresult
