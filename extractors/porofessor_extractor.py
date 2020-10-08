import re
from datetime import timedelta
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from cassiopeia import Region
from unidecode import unidecode

TRY_AGAIN_LATER = 'An Error has occured, please try again later'

REGION_URLS = {
    Region.korea.value: 'kr/',
    Region.europe_west.value: 'euw/'
}
BASE_URL = ' http://porofessor.gg/'
SPECTATE_PLAYER_PAGE = 'partial/live-partial/'
NOT_IN_GAME = 'The summoner is not in-game, please retry later. The game must be on the loading screen or it must have started.'


class PorofessorNoResponseException(Exception):
    pass


def extract_recording_url(html):
    p = re.compile("recordUrl: '(.*)',")
    result = p.search(html)
    return result.group(1)


def get_request_recording_url(summoner_name, region):
    region_url = REGION_URLS[region]
    url = BASE_URL + SPECTATE_PLAYER_PAGE + region_url + summoner_name.replace(' ', '%20')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
    }
    r = requests.get(url, headers=headers, timeout=60)
    html = r.text
    return extract_recording_url(html)


def request_recording(summoner_name, region):
    print(f'Requesting recording for {summoner_name} in {region}')

    url = get_request_recording_url(summoner_name, region)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=60)
    status_code = response.status_code
    return status_code == 200


def get_match_data(summoner_name, region):
    region_url = REGION_URLS[region]
    full_url = BASE_URL + SPECTATE_PLAYER_PAGE + region_url + summoner_name.replace(' ', '%20')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
    }
    r = requests.get(full_url, headers=headers, timeout=60)
    html = r.text
    if NOT_IN_GAME in html:
        print("Not in game")
        return

    if TRY_AGAIN_LATER in html:
        print('PorofessorNoResponseException')
        raise PorofessorNoResponseException
    soup = BeautifulSoup(html, "html.parser")
    match_data = {}

    players_html = soup.findAll("div", {'class': 'card card-5'})
    players = extract_players_order(players_html)
    duration_tag = soup.find('span', id='gameDuration')
    duration = get_match_duration(duration_tag)
    # print(duration)

    # print(f'[{__name__.upper()}] - Players Order: {players}')
    match_data['players'] = players
    match_data['duration'] = duration
    # print(f'{datetime.now()} [{__name__.upper()}] - Getting player match data for "{summoner_name}"')
    # print(f'"{summoner_name}" : match available on porofessor')

    return match_data


def get_match_duration(duration_tag):
    if duration_tag is None:
        return timedelta()
    duration_string = duration_tag.text
    duration = get_duration(duration_string)
    if duration is None:
        return timedelta()

    return duration


def get_duration(duration_string):
    p = re.compile('^\(([0-9]{2}):([0-9]{2})\)$')
    result = p.search(duration_string)
    minutes = result.group(1)
    seconds = result.group(2)
    if not minutes:
        return
    duration = timedelta(minutes=int(minutes), seconds=int(seconds))
    return duration


def get_summoners_name_from_html(soup):
    challengers = soup.findAll("div", class_="card card-5")
    challengers = list(map(lambda div: div['data-summonername'], challengers))
    challengers = list(map(lambda challenger: challenger.replace('+', ' '), challengers))
    challengers = list(map(lambda challenger: unidecode(unquote(challenger)), challengers))
    return challengers


def extract_players_order(players_html):
    # players_html = soup.findAll("div", {'class': 'card card-5'})
    players = list(map(lambda player_html: player_html.attrs['data-summonername'].strip(), players_html))
    return players

