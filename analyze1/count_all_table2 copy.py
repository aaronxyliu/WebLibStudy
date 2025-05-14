
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import commonReader
from utils.globalv import CATEGORY_LIST
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_npm')

logger = getLogger()
reader = commonReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'


def verify_npm_name(npm_name: str) -> bool:
    '''Verify the existence of this library on the jsDelivr npm source.'''

    libinfo = reader.read_jsDelivr(npm_name, 'npm', stats=False)
    if not libinfo:
        return False
    if 'versions' not in libinfo:
        return False
    if not libinfo['versions'] or len(libinfo['versions']) == 0:
        return False
    return True

if __name__ == "__main__":
    res = db.select_all(LIB_TABLE, ['libname', 'npm'], condition='`npm` IS NOT NULL')
    npm_list = []
    cnt = 0
    for entry in res:
        libname, npm = entry['libname'], entry['npm']
        if not verify_npm_name(npm):
            logger.info(npm)
            db.update(LIB_TABLE, data={
                'npm': None
            }, condition="`libname`=%s", condition_values=(libname,))
            cnt += 1

    logger.info(f'{cnt} tables.')
    db.close()