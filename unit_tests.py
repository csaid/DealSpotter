#!/bin/env python
"""
Unit tests for Craigslist project
"""

import unittest
import load_pages as lp
reload(lp)


class Test_find_model(unittest.TestCase):

    def setUp(self):
        self.models = set(["accord", "camry", "civic", "corolla"])

    def test_basic(self):
        self.assertEqual(
            lp.find_model(
                "my honda accord",
                self.models),
            'accord')

    def test_case_insensitive(self):
        self.assertEqual(
            lp.find_model(
                "my honda Accord",
                self.models),
            'accord')

    def test_non_model(self):
        self.assertEqual(lp.find_model("Harley", self.models), None)


class Test_find_year(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(lp.find_year("hello 1999"), 1999)

    def test_skip_too_high(self):
        self.assertEqual(lp.find_year("2015 2014"), 2014)

    def test_skip_too_low(self):
        self.assertEqual(lp.find_year("1979 2014"), 2014)

    def test_return_only_one(self):
        self.assertEqual(lp.find_year("2013 2014"), 2013)

    def test_return_none(self):
        self.assertEqual(lp.find_year("1979"), None)


class Test_find_miles(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(lp.find_miles("I have 20000 miles"), 20000)

    def test_case_insensitive(self):
        self.assertEqual(lp.find_miles("I have 20000 Miles"), 20000)

    def test_comma(self):
        self.assertEqual(lp.find_miles("I have 20,000 miles"), 20000)

    def test_pre(self):
        self.assertEqual(lp.find_miles("my miles: 20,000"), 20000)

    def test_mileage(self):
        self.assertEqual(lp.find_miles("my mileage: 20,000 xx"), 20000)

    def test_spaces(self):
        self.assertEqual(lp.find_miles("mileage  20,000 adsfadsf"), 20000)

    def test_characters1(self):
        self.assertEqual(lp.find_miles("mileage,, 20,000 adsfadsf"), 20000)

    def test_characters2(self):
        self.assertEqual(lp.find_miles("20,000 .?miles"), 20000)

    def test_k(self):
        self.assertEqual(lp.find_miles("20k .?miles"), 20000)

    def test_island(self):
        self.assertEqual(lp.find_miles("20,000"), None)


if __name__ == "__main__":
    unittest.main()
