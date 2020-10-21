import logging

import pymongo
from pymongo import UpdateOne

from mongo import mongo_manager

MATCHES = 'matches'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_recorded_games():
    recorded_games_collection = mongo_manager.get_recorded_games_collection()
    games = [game for game in recorded_games_collection.find({})]
    return games


def already_enabled(match_id):
    recorded_games = get_recorded_games()
    return any(g.get('match_id') == match_id for g in recorded_games)


def add_game(game):
    match_id = game.get("match_id")
    recorded_games_collection = mongo_manager.get_recorded_games_collection()
    try:
        recorded_games_collection.insert_one(game)
    except pymongo.errors.DuplicateKeyError:
        logger.info(f'Match {match_id} already recording.')
    logger.info(f'Added {match_id}')


def update_games(games):
    update_ones = []
    for game in games:
        update_one = UpdateOne({'match_id': game.get('match_id')},
                               {'$set': game})
        update_ones.append(update_one)
        recorded_games_collection = mongo_manager.get_recorded_games_collection()
        recorded_games_collection.bulk_write(update_ones)
