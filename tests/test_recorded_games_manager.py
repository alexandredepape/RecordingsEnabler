import logging
import unittest
from recording import recorded_games_manager
from mongo.mongo_manager import get_recorded_games_collection
from recording.recorded_games_manager import add_game

logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))


class MyTestCase(unittest.TestCase):
    def test_get_recorded_games(self):
        print(get_recorded_games_collection())

    def test_get_recorded_games(self):
        print(recorded_games_manager.get_recorded_games())

    def test_add_game(self):
        game = {
            'match_id': 4642342342
        }
        add_game(game)


if __name__ == '__main__':
    unittest.main()
