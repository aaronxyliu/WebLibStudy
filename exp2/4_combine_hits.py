# Identify the vulnerable versions on jsDelivr, and calculate the hits

import os
from packaging import version
from packaging.specifiers import SpecifierSet
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
import json
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
logger = getLogger()
db = ConnDatabase('Libraries')

VUL_TABLE = 'vulnerabilities'


if __name__ == '__main__':


    res = db.select_all(VUL_TABLE, ['synk', '# hits (npm)', '# hits (gh)'], return_as='tuple')

    for entry in res:
        hits = 0
        if entry[1]:
            hits += entry[1]
        if entry[2]:
            hits += entry[2]
        db.update(VUL_TABLE, {'# hits': hits}, "`synk`=%s", (entry[0],))
    

    
    db.close()





