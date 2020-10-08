import logging
import pymongo
import mongo_manager

MATCHES = 'matches'


def get_recorded_games():
    recorded_games_collection = mongo_manager.get_recorded_games_collection()
    games = [game for game in recorded_games_collection.find({})]
    print(f'Found {len(games)} games')
    return games


def already_enabled(match_id):
    recorded_games = get_recorded_games()
    return any(g.get('match_id') == match_id for g in recorded_games)


def add_game(game):
    recorded_games_collection = mongo_manager.get_recorded_games_collection()
    try:
        recorded_games_collection.insert_one(game)
    except pymongo.errors.DuplicateKeyError:
        logging.info('Match already recording on opgg.')
    logging.info(f'Added {game.get("match_id")}')
