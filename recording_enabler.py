import datetime
import os
import queue
import time
import traceback
import logging

from concurrent.futures.thread import ThreadPoolExecutor

import datapipelines
from cassiopeia import get_summoner, cassiopeia, get_current_match

import opgg_extractor
import porofessor_extractor
import recorded_games_manager
from recorded_games_manager import already_enabled
from riot_api_manager import get_all_challenger_players

cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))
REGIONS_TO_SEARCH = ['KR']
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

        logger.info(f'Sleeping {RIOT_SPECTATOR_DELAY} before enabling again.')
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
                # duration = current_match.duration
                match_id = current_match.id
                # if duration.days < 0:
                #     pass
                # elif duration.seconds + RIOT_SPECTATOR_DELAY < MAXIMUM_RECORDING_TIME:
                #     logger.info(f'Match {match_id} of {summoner_name} is already {duration.seconds} seconds long')
                #     continue
            except datapipelines.common.NotFoundError:
                # logger.info(f'{summoner_name} not in game')
                continue
            opgg_match_data = opgg_extractor.get_match_data(summoner_name, region)
            if not opgg_match_data:
                logger.info(f'- "{summoner_name}" : Game not yet on OPGG')

                continue
            # match_id = opgg_match_data.get('match_id')
            if not opgg_match_data.get('is_ranked'):
                logger.info(f'{match_id} is not a ranked')
                continue
            try:
                porofessor_match_data = porofessor_extractor.get_match_data(summoner_name, region)
            except porofessor_extractor.PorofessorNoResponseException:
                return

            if not porofessor_match_data:
                logger.info(f'- "{summoner_name}" : Game not yet on POROFESSOR')

                continue

            porofessor_duration = porofessor_match_data.get('duration')
            if porofessor_duration.seconds > MAXIMUM_RECORDING_TIME:
                logger.info(f'{match_id} is already {porofessor_duration.seconds} seconds long')
                continue

            porofessor_players = porofessor_match_data.get('players')
            opgg_players_data = opgg_match_data.get('players_data')

            players_data = get_final_players_data(porofessor_players, opgg_players_data)
            if not players_data:
                continue
            if already_enabled(match_id):
                logger.info(f'{match_id} Already enabled.')

            request_worked = porofessor_extractor.request_recording(summoner_name, region)
            if request_worked:
                match = {
                    'match_id': match_id,
                    'region': region,
                    'duration': porofessor_duration.seconds,
                    'riot_duration': current_match.duration.seconds,
                    'inserted_at': datetime.datetime.now(),
                    'players_data': players_data
                }
                logger.info(f'Adding {match_id}')

                recorded_games_manager.add_game(match)
    except Exception:
        logger.error(traceback.print_exc())
        traceback.print_exception()

