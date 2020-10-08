import os
import unittest

from cassiopeia import cassiopeia, Region
from dotenv import load_dotenv

from recording_enabler import check_in_game

load_dotenv()

cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))


class MyTestCase(unittest.TestCase):
    def test_check_in_game(self):

        region = Region.korea
        summoner_name = 'hide on bush'
        summoner = cassiopeia.get_summoner(name=summoner_name, region=region)
        summoner_id = summoner.id
        print(check_in_game(region, summoner_id))


if __name__ == '__main__':
    unittest.main()
