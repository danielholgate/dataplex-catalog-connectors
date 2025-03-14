import sys
from src import bootstrap
import logging

#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)

# Allow shared files to be found when running from command line
sys.path.insert(1, '../src/shared')

if __name__ == '__main__':
    bootstrap.run()
