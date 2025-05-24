# Check whether the latest version of the libraries is vulnerable

from packaging import version
from packaging.specifiers import SpecifierSet
import re
import json
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
logger = getLogger()
db = ConnDatabase('Libraries')
db_npm = ConnDatabase('version_npm')

LIB_TABLE = 'libs_cdnjs_all_4_20u'
VUL_TABLE = 'vulnerabilities'

if __name__ == "__main__":
    # Get all vulnerable libraries
    vul_libnames = db.fetchall(f"SELECT DISTINCT `libname` FROM {VUL_TABLE}")

    cnt = 0
    cnt_abandoned = 0
    for i, entry in enumerate(vul_libnames):
        # Iterate through libraries
        libname = entry[0]
        res = db.fetchone(f"SELECT `npm`, `abandoned` FROM {LIB_TABLE} WHERE `libname`='{libname}'")
        npm_name, abandoned = res[0], res[1]
        if not npm_name:
            logger.warning(f"Library {libname} does not have an npm name.")
            continue

        # Check if the library exists in the npm database
        if npm_name not in db_npm.show_tables():
            logger.warning(f"Library {libname} does not exist in the npm database.")
            continue

        # logger.info(f"({i}/{len(vul_libnames)}) Start {libname} ({npm_name}).")

        # Select all rows from the npm table
        version_rows = db_npm.select_all(npm_name, ['version', 'vuls'])
        # Get the latest version
        
        if version_rows[0]['vuls']:
            logger.info(f"Library {libname} version {version_rows[0]['version']} has vulnerability.")
            cnt += 1
            if abandoned:
                cnt_abandoned += 1
    logger.info(f"{cnt} libraries have vulnerabilities in the latest version.")
    logger.info(f"Among them, {cnt_abandoned} libraries are abandoned.")