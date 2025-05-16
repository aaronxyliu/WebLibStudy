
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.stat import Distribution as Dist
from utils.globalv import CATEGORY_LIST
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_npm')

logger = getLogger()

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == "__main__":


    tables = db2.show_tables()

    for i, table in enumerate(tables):
        res = db2.select_all(table, ['version'])
        for entry in res:
            db2.update(table, data={
                'estimate date': None
            }, condition="`version`=%s", condition_values=(entry['version'],))
        logger.leftTimeEstimator(len(tables) - i)

    
    db.close()