import os

import requests
from cassiopeia import Region, cassiopeia, Queue

SCHEMA = 'https://'

BASE_URL = '.api.riotgames.com/lol/'
REGION_URLS = {
    Region.korea.value: 'kr',
    Region.europe_west.value: 'euw1'
}

CHALLENGER_LEAGUE_URL = 'league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
CURRENT_GAME_URL = 'spectator/v4/active-games/by-summoner/'
MATCH_URL = 'match/v4/matches/'


def get_match_duration(region, id):
    region_url = REGION_URLS.get(region)
    url = SCHEMA + region_url + BASE_URL + str(id)

    r = requests.get(url, headers={"X-Riot-Token": os.getenv("RIOT_KEY")})
    return r.json().get('gameLength')


def get_all_challenger_players(region):
    challenger_league = cassiopeia.get_challenger_league(Queue.ranked_solo_fives, region)
    return [entry.summoner.id for entry in challenger_league.entries]


def get_current_game_version():
    response = requests.get('http://ddragon.leagueoflegends.com/api/versions.json')
    latest_game_version = '.'.join(response.json()[0].split('.')[:2])
    print(f"{latest_game_version=}")
    return latest_game_version


def get_match(match_id, region):
    region_url = REGION_URLS.get(region)
    url = SCHEMA + region_url + BASE_URL + MATCH_URL + str(match_id)

    r = requests.get(url, headers={"X-Riot-Token": os.getenv("RIOT_KEY")})
    if r.status_code != 200:
        print(f'{match_id}: {r.status_code}')
        return
    return r.json()
