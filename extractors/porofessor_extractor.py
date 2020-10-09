import re
import requests
from cassiopeia import Region

REGION_URLS = {
    Region.korea.value: 'kr/',
    Region.europe_west.value: 'euw/'
}
BASE_URL = ' http://porofessor.gg/'
SPECTATE_PLAYER_PAGE = 'partial/live-partial/'


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
    url = get_request_recording_url(summoner_name, region)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=60)
    status_code = response.status_code
    return status_code == 200
