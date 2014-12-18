#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Callable
from zmon_worker.tasks.zmontask import Try

import unittest


class TestTry(unittest.TestCase):

    def test_single_exception(self):
        t = Try(lambda: 1 / 0, lambda e: 2)
        self.assertIsInstance(t, Callable)
        result = t()
        self.assertEqual(result, 2)
        result = Try(lambda: 1 / 0, lambda e: e)()
        self.assertIsInstance(result, Exception)

    def test_nested_exception(self):
        t = Try(lambda: 1 / 0, Try(lambda: 2 / 0, lambda e: 4))
        self.assertIsInstance(t, Callable)
        result = t()
        self.assertEqual(result, 4)


if __name__ == '__main__':
    unittest.main()
