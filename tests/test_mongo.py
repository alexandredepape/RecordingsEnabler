import unittest

from mongo.mongo_manager import create_index


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

    def test_create_index(self):
        create_index()

if __name__ == '__main__':
    unittest.main()
