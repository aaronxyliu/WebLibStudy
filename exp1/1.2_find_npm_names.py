# Find the npm name of the library

import base64
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()
import json
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import GitHubAPIReader
logger = getLogger()
db = ConnDatabase('Libraries')
reader = GitHubAPIReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'

START_LIB = 'egg.js'


if __name__ == '__main__':
    db.add_column(LIB_TABLE, 'npm', 'varchar(100) DEFAULT NULL', after_column='libname')

    libs = db.select_all(LIB_TABLE, ["libname", "github"])
    
    start = False
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname, github = entry['libname'], entry['github']

        if libname == START_LIB:
            start = True
        if not start:
            continue
        logger.info(f"({i}/{len(libs)}) Start {libname}.")
        
        print(github)
        url = f"https://api.github.com/repos/{github[11:]}/contents/package.json"

        data, should_stop = reader.read_url(url)
        if data:
            content = base64.b64decode(data['content']).decode('utf-8')
        
            # Parse the JSON content
            try:
                package_json = json.loads(content)
            except Exception as e:
                logger.info(f"JSON decoding error: {e}")
                continue
            if 'name' in package_json:
                db.update(LIB_TABLE, 
                          data={'npm': package_json['name']},
                          condition=f'`libname`=%s',
                          condition_values=(libname,))
                logger.info(f"The npm name is {package_json['name']}.")
            else:
                logger.warning(f"No name is found in the {libname}'s package.json file.")
        
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





