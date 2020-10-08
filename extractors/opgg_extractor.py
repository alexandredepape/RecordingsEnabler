import re
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from cassiopeia import Side


OBSERVER_KEY = '/match/new/batch/id='

REGION_URLS = {
    'KR': 'www.op.gg',
    'EUW': 'euw.op.gg'
}
SCHEMA = ' http://'
LADDER = '/ranking/ladder'
SPECTATE_PLAYER_PAGE = '/summoner/spectator/userName='
USERNAME_URL = '/summoner/userName='
SPECTATE_MATCH = '/match/new/batch/id='
PAGE = '/page='
SPECTATE = '/spectate'
SPECTATE_TAB = '/pro'
PRO_PLAYERS_LIST = '/list/'

REQUEST_RECORDING = '/summoner/ajax/requestRecording/gameId='



def request_recording(match_id, region):
    region_url = REGION_URLS[region]
    url = SCHEMA + region_url + REQUEST_RECORDING + str(match_id)
    response = requests.get(url, timeout=60)
    status_code = response.status_code
    print(status_code)
    return status_code == 200


def extract_match_type(html):
    soup = BeautifulSoup(html, "html.parser")

    queue = soup.find('div', {'class': 'SpectateSummoner'})
    queue = queue.find('div', {'class': 'Box'})
    queue = queue.find('div', {'class': 'Title'})
    if 'Ranked Solo' in queue.text.strip():
        return True
    return False


def spectate_tab(region):
    region_url = REGION_URLS[region]
    spectate_tab = SCHEMA + region_url + SPECTATE + SPECTATE_TAB
    print(f'[{__name__.upper()}] - Getting spectate_tab')

    r = requests.get(spectate_tab, timeout=60)
    html = r.text
    return extract_names(html)


def get_ladder(region):
    region_url = REGION_URLS[region]
    ladder_url = SCHEMA + region_url + LADDER
    r = requests.get(ladder_url, timeout=60)
    html = r.text

    return extract_names(html)


def extract_pro_player_names(html):
    soup = BeautifulSoup(html, "html.parser")
    player_tags = soup.findAll('li', {'data-summoner-name': True})
    pro_player_names = {}
    for player_tag in player_tags:
        summoner_team = player_tag.find('div', {'class': 'SummonerTeam'})
        summoner_name = player_tag.find('div', {'class': 'SummonerName'})
        pro_name = player_tag.find('span', {'class': 'SummonerExtra'})

        summoner_team = summoner_team.text.strip()
        summoner_name = summoner_name.text.strip()
        pro_name = pro_name.text.strip()
        pro_player_info = {
            'team': None,
            'name': pro_name
        }
        if summoner_team != 'Progamer':
            pro_player_info['team'] = summoner_team

        pro_player_names[summoner_name] = pro_player_info
    return pro_player_names


def get_pro_players_info(region):
    region_url = REGION_URLS[region]
    pro_players_url = SCHEMA + region_url + SPECTATE + PRO_PLAYERS_LIST
    r = requests.get(pro_players_url, timeout=60)
    html = r.text
    players_name = extract_pro_player_names(html)
    return players_name


def extract_names(html):
    soup = BeautifulSoup(html, "html.parser")
    challengers = soup.findAll('a')
    challengers = list(map(lambda link: link['href'], challengers))
    challengers = list(filter(lambda href: USERNAME_URL in href, challengers))
    challengers = list(map(lambda href: href.split('=')[1], challengers))
    challengers = list(map(lambda challenger: challenger.replace('+', ' '), challengers))
    challengers = list(map(lambda challenger: unquote(challenger), challengers))
    challengers = list(map(lambda challenger: challenger.strip(), challengers))
    return list(dict.fromkeys(challengers))


class MatchIdNotFoundException(Exception):
    def __init__(self, html):
        self.html = html


def extract_match_id(html):

    p = re.compile("\$\.OP\.GG\.matches\.openSpectate\(([0-9]*)\); return false;")
    result = p.search(html)
    if not result:
        return

    match_id = result.group(1)
    return int(match_id)


class OpggTooManyRequestException(Exception):
    pass


def get_match_data(summoner_name, region):
    region_url = REGION_URLS[region]
    url = SCHEMA + region_url + SPECTATE_PLAYER_PAGE + summoner_name

    r = requests.get(url, timeout=60)
    if r.status_code == 403:
        raise OpggTooManyRequestException
    html = r.text

    match_data = {}

    players = extract_players_data(html)
    match_data['players_data'] = players

    if not len(players):

        return

    is_ranked = extract_match_type(html)
    match_data['is_ranked'] = is_ranked

    match_id = extract_match_id(html)
    if not match_id:
        raise MatchIdNotFoundException(html)
    match_data['match_id'] = match_id
    # print(f'"{summoner_name}" : match available on opgg')

    return match_data


def get_player_page(region):
    region_url = REGION_URLS[region]
    player_page_url = SCHEMA + region_url + USERNAME_URL
    return player_page_url


def extract_players_data(html):
    soup = BeautifulSoup(html, "html.parser")

    players = {}
    players_html = soup.find_all("tr")
    players_html = list(
        filter(lambda tr: tr.get('id') is not None and 'SpectateBigListRow' in tr.get('id'), players_html))
    side = Side.blue.value
    for i in range(len(players_html)):
        # with open(f'player.html', 'w') as f:
        #     f.write(str(players_html[i]))
        player_html = players_html[i]
        player_data = {}

        player_data['champion'] = player_html.find('a').get('title')
        player_name = player_html.find('a', {'class': "SummonerName"}).text.strip()
        player_ranking_information = player_html.find('div', {'class': 'TierRank'}).text.strip()
        tier, lp = get_tier_lp_from_rank(player_ranking_information)

        player_data['tier'] = tier
        player_data['lp'] = lp
        player_data['side'] = side
        if i == 4:
            side = Side.red.value
        players[player_name] = player_data

    return players


def get_tier_lp_from_rank(rank):
    # print(f"getting tier and lp from {rank}")
    p = re.compile("([a-zA-Z]*( [1-4])?) \\(([0-9]*) LP\\)")
    result = p.search(rank)
    if not result:
        return 'Unranked', None

    tier = result.group(1)
    lp = result.group(3)
    return tier, lp


def get_match_recording_settings(match_id, region):
    region_url = REGION_URLS[region]
    url = SCHEMA + region_url + OBSERVER_KEY + str(match_id)

    r = requests.get(url, timeout=60)
    p = re.compile('@start "" "League of Legends.exe" "spectator (.*) (.*) (.*) (.*)" "-UseRads" "-Locale=!locale!" "-GameBaseDir=.."')
    bat_text = r.text
    result = p.search(bat_text)
    host = result.group(1)
    observer_key = result.group(2)
    return host, observer_key