# Crawl jsdelivr's API to find libraries whose GitHub URLs contained in the database produced by "2_remove_redundant.py"

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import json
import time
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
db = ConnDatabase('Libraries')
logger = getLogger()


TABLE = 'libs_cdnjs_all_4_20u'
CRAWL_START = 1
CRAWL_INTERVAL = 0.1    # sleep seconds between iterations



if __name__ == "__main__":
    
    rows = db.select_all(TABLE, ['libname', '# hits (gh)', '# hits (npm)'], condition='`github` IS NOT NULL', return_as="tuple")
    
    for row in rows:
        libname, h1, h2 = row[0], row[1], row[2]
    
        h = h1 + h2
        db.update(TABLE, {'# hits': h}, 'libname=%s', (libname,))

    db.close()