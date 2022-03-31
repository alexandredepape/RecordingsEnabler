import logging
import os

from cassiopeia import cassiopeia
from recording import recording_enabler
from dotenv import load_dotenv

load_dotenv()

cassiopeia_logger = logging.getLogger('cassiopeia')
cassiopeia_logger.setLevel(logging.ERROR)

config = cassiopeia.get_default_config()
config['pipeline']['RiotAPI']['api_key'] = os.getenv("RIOT_KEY")
config['logging']['print_calls'] = False


cassiopeia.apply_settings(config)


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info('Starting Search')
    recording_enabler.search()


if __name__ == '__main__':
    main()
