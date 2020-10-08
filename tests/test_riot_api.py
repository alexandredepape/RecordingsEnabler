import os
import unittest

import cassiopeia
import datapipelines
import dotenv

import porofessor_extractor
from riot_api_manager import get_all_challenger_players

dotenv.load_dotenv()
cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)
    def test_match_duration(self):
        nb_deltas = 0
        sum_deltas = 0
        region = 'KR'
        challengers = get_all_challenger_players(region)

        for challenger in challengers:
            summoner_name = challenger.get('summoner_name')
            summoner_id = challenger.get('summoner_id')
            print(summoner_name)
            summoner = cassiopeia.get_summoner(id=summoner_id, region=region)
            print(summoner.id)
            try:
                current_match = summoner.current_match
            except datapipelines.common.NotFoundError:
                continue
            duration = current_match.duration
            print(f'{duration.seconds=}')
            poro_match = porofessor_extractor.get_match_data(summoner_name, region)
            if not poro_match:
                continue
            print(f'{poro_match.get("duration").seconds}')
            sum_deltas += duration.seconds - poro_match.get("duration").seconds
            nb_deltas += 1
        print(f'average delta : {sum_deltas//nb_deltas}')
    def test_get_match(self):
        name = 'Bmav'
        region = 'KR'
        summoner = cassiopeia.get_summoner(name=name, region=region)
        try:
            current_match = summoner.current_match
            seconds = current_match.duration.seconds

            print(seconds)
            if current_match.duration.days < 0:
                print(f'{current_match.duration.days=}')
        except datapipelines.common.NotFoundError:
            print('nothing found')
        poro_match = porofessor_extractor.get_match_data(name, region)
        print(f'{poro_match.get("duration").seconds}')
        print(f'Delta = {poro_match.get("duration").seconds - seconds}')
if __name__ == '__main__':
    unittest.main()
