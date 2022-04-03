import datetime
import logging
import os
import time
import traceback
import datapipelines

from cassiopeia import get_summoner, cassiopeia, get_current_match, Queue, GameType

from extractors import porofessor_extractor
from extractors.riot_api_manager import get_all_challenger_players, get_current_game_version
from recording import recorded_games_manager
from recording.recorded_games_manager import already_enabled

cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))
REGIONS_TO_SEARCH = ['KR', 'EUW']
REGIONS_TO_SEARCH = ['EUW']
REGIONS_TO_SEARCH = ['KR']
RIOT_SPECTATOR_DELAY = 3 * 60

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def search():
    while True:
        try:
            enable_challengers_games_recording()
        except Exception as e:
            traceback.print_exc()
            logger.info(f'Sleeping some time because of {e}')
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
        challenger_ids = get_all_challenger_players(region)
        check_in_game(challenger_ids, region)


def check_in_game(challenger_ids, region):
    logger.info("Worker starts")
    for position, challenger_id in enumerate(challenger_ids):
        summoner = get_summoner(id=challenger_id, region=region)
        summoner_name = summoner.name
        logger.info(f'Checking \"{summoner_name}\" {position}/{len(challenger_ids)}')

        try:
            current_match = get_current_match(summoner, region)
            match_id = current_match.id
            game_time = current_match.duration.total_seconds()
            if current_match.type != GameType.matched:
                continue
            if current_match.queue != Queue.ranked_solo_fives:
                continue
            # On porofessor you can only spectate if time < 3 minutes and if game_time is
            # 3 minutes, on porofessor it is 0 seconds,
            if game_time > 0:
                minutes = str(datetime.timedelta(seconds=game_time))
                logger.info(f'Match {match_id} of {summoner_name} is already {minutes} seconds long')
                continue
        except datapipelines.common.NotFoundError:
            continue

        if already_enabled(match_id):
            logger.info(f'{match_id} Already enabled.')
            continue
        recording_worked = porofessor_extractor.request_recording(summoner_name, region)
        logger.info(f'Requesting recording for {match_id} {region}')

        if recording_worked:
            match = {
                'version': get_current_game_version(),
                'queue': current_match.queue.value,
                'took_from': summoner_name,
                'match_id': match_id,
                'region': region,
                'game_time': game_time,
                'inserted_at': datetime.datetime.now(),
                'is_populated': False
            }
            recorded_games_manager.add_game(match)
