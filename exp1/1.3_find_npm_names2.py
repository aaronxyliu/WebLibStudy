# Find the npm name of the library by name

import base64
from dotenv import load_dotenv
load_dotenv()
import json
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import GitHubAPIReader, commonReader
logger = getLogger()
db = ConnDatabase('Libraries')
c_reader = commonReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'

def verify_npm_name(npm_name: str) -> bool:
    '''Verify the existence of this library on the jsDelivr npm source.'''

    libinfo = c_reader.read_jsDelivr(npm_name, 'npm', stats=False)
    if not libinfo:
        return False
    if 'versions' not in libinfo:
        return False
    if not libinfo['versions'] or len(libinfo['versions']) == 0:
        return False
    return True


if __name__ == '__main__':
    db.add_column(LIB_TABLE, 'npm', 'varchar(100) DEFAULT NULL', after_column='libname')

    libs = db.select_all(LIB_TABLE, ["libname"], condition="`npm` IS NULL")
    
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['libname']

        logger.info(f"({i}/{len(libs)}) Start {libname}.")
        induced_npm_name = libname.strip().lower()
        if verify_npm_name(induced_npm_name):
            db.update(LIB_TABLE, 
                    data={'npm': induced_npm_name},
                    condition=f'`libname`=%s',
                    condition_values=(libname,))
            logger.info(f"The induced npm name is {induced_npm_name}.")
        else:
            logger.warning(f"{induced_npm_name} is incorrect.")
        
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





