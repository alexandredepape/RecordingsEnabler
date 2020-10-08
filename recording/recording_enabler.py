import datetime
import os
import queue
import time
import traceback
import logging

from concurrent.futures.thread import ThreadPoolExecutor

import datapipelines
from cassiopeia import get_summoner, cassiopeia, get_current_match

from extractors import opgg_extractor, porofessor_extractor
from recording import recorded_games_manager
from recording.recorded_games_manager import already_enabled
from extractors.riot_api_manager import get_all_challenger_players

cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))
REGIONS_TO_SEARCH = ['KR', 'EUW']
MAXIMUM_RECORDING_TIME = 3 * 60
RIOT_SPECTATOR_DELAY = 3 * 60
NB_WORKERS = 5
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def search():
    while True:
        try:
            enable_challengers_games_recording()
        except Exception:
            traceback.print_exception()
            time.sleep(RIOT_SPECTATOR_DELAY)


def get_final_players_data(porofessor_players, opgg_players_data):
    players_data = {}
    for player_name in porofessor_players:
        if player_name not in opgg_players_data.keys():
            return
        players_data[player_name] = opgg_players_data[player_name]

    return players_data


def enable_challengers_games_recording():
    for region in REGIONS_TO_SEARCH:
        challengers = get_all_challenger_players(region)
        challengers_queue = queue.Queue()
        for challenger in challengers:
            challengers_queue.put(challenger)

        with ThreadPoolExecutor(max_workers=NB_WORKERS) as executor:
            for i in range(NB_WORKERS):
                executor.submit(check_in_game, challengers_queue, region)


def check_in_game(challengers_queue, region):
    logger.info("Worker here")
    try:
        while not challengers_queue.empty():
            challenger = challengers_queue.get()
            summoner_name = challenger.get('summoner_name')
            summoner_id = challenger.get('summoner_id')
            # logger.info(f'[{challengers_queue.qsize()}] Checking {summoner_name}')
            summoner = get_summoner(id=summoner_id, region=region)
            try:
                current_match = get_current_match(summoner, region)
                game_time = current_match.duration.total_seconds()
                match_id = current_match.id
                if game_time > 0:
                    logger.info(f'Match {match_id} of {summoner_name} is already {game_time} seconds long')
                    continue
            except datapipelines.common.NotFoundError:
                # logger.info(f'{summoner_name} not in game')
                continue

            if already_enabled(match_id):
                logger.info(f'{match_id} Already enabled.')

            request_worked = porofessor_extractor.request_recording(summoner_name, region)
            if request_worked:
                match = {
                    'match_id': match_id,
                    'region': region,
                    'game_time': game_time,
                    'inserted_at': datetime.datetime.now(),
                }

                recorded_games_manager.add_game(match)
    except Exception:
        logger.error(traceback.print_exc())
        traceback.print_exception()

