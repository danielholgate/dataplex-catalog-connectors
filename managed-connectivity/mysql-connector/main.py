import sys
from src.common import bootstrap
from src import mysql_connector
from src.common import cmd_reader

if __name__ == '__main__':
    bootstrap.run(cmd_reader.read_args())
