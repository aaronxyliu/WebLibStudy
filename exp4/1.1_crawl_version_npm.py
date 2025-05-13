# Crawl the hits of the past year of all versions of all libraries through jsDelivr

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
from utils.api_reader import commonReader
logger = getLogger()
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_npm')
reader = commonReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == '__main__':
    libs = db.select_all(LIB_TABLE, ["npm"])

    npm_libnames = db2.show_tables()
        
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['npm']
        if not libname or libname in npm_libnames:
            # Skip libraries already crawled from npm source
            continue

        libinfo = reader.read_jsDelivr(libname, 'npm', stats=False)
        if not libinfo:
            logger.warning(f'Failed to read the {libname} versions from jsDelivr (gh).')
            continue

        version_list = []
        for version_info in libinfo['versions']:
        # Check whether this version is vulnerable
            version_list.append(version_info["version"])

        if len(version_list) > 0:
            db2.create_if_not_exists(libname, '''
                `version` varchar(100) DEFAULT NULL,
                `jsDelivr rank` int  DEFAULT NULL,
                `year hits` bigint  DEFAULT NULL
            ''')
        
        rank = 1
        for version_tag in version_list:
            data = reader.get_stat(libname, "npm", version_tag, "year")
            hits = data['hits']['total']
            db2.upsert(libname, data={
                'version': version_tag,
                'jsDelivr rank': rank,
                'year hits': hits
            }, condition_fields="version")

            rank += 1
        
        logger.info(f"({i}/{len(libs)}) Complete {libname}. In total {len(version_list)} versions.")
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





