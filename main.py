import logging
import os

from cassiopeia import cassiopeia

import recording_enabler

import dotenv
dotenv.load_dotenv()

cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info('Starting Search')
    recording_enabler.search()


if __name__ == '__main__':
    main()
