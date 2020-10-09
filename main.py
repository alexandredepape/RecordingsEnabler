import logging
import os

from cassiopeia import cassiopeia

from recording import recording_enabler

from dotenv import load_dotenv
load_dotenv()
def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))
cassiopeia_logger = logging.getLogger('cassiopeia')
cassiopeia_logger.setLevel(logging.ERROR)

settings = cassiopeia.get_default_config()
# settings['logging']['print_calls'] = False
cassiopeia.apply_settings(settings)
cassiopeia.set_riot_api_key(os.getenv("RIOT_KEY"))


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info('Starting Search')
    recording_enabler.search()


if __name__ == '__main__':
    main()
