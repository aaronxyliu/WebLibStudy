
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.stat import Distribution as Dist
from utils.globalv import CATEGORY_LIST
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_npm2')

logger = getLogger()

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == "__main__":
    res = db.select_all(LIB_TABLE, ['npm'])
    npm_list = []
    for entry in res:
        npm_list.append(entry['npm'])

    tables = db2.show_tables()
    drop_cnt = 0
    for table in tables:
        if table in npm_list:
            db2.drop(table)
            drop_cnt += 1

    logger.info(f'{drop_cnt} tables droped. {len(tables) - drop_cnt} tables left.')
    db.close()