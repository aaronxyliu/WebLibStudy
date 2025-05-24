
from typing import Type
import sys
import csv
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.stat import Distribution as Dist
from utils.globalv import CATEGORY_LIST
db = ConnDatabase('version_npm')
logger = getLogger()


if __name__ == "__main__":

    table_cnt = 0
    version_cnt = 0
    total_version_num = 0
    for table in  db.show_tables():
        columns = db.show_columns(table)
        if 'tag date' not in columns or 'estimate date' not in columns or 'npm date' not in columns:
            continue
        old_date = None
        
        wrong_order = False
        res = db.select_all(table, ['tag date', 'estimate date', 'npm date', 'version'], return_as='tuple')
        for entry in res:
            npm_date = entry[2]
            v_date = entry[0]
            # if npm_date and v_date:
            #     v_date = v_date + (npm_date - v_date) / 2
            # if npm_date and v_date and npm_date < v_date:
            #     v_date = npm_date
            # v_date = v_date or entry[1]
            if v_date and old_date and v_date > old_date:
                wrong_order = True
                version_cnt +=  1
                # print(table ,entry[3], v_date, old_date)
            if v_date:
                total_version_num += 1
                old_date = v_date
            
        
        if wrong_order:
            table_cnt += 1
            

    # logger.info(f'Version with date: {version_with_date_num} ({version_with_date_num * 100/total_version_num:.1f}%)')
    print('table:', table_cnt)
    print('version:', version_cnt)
    print('total version:', total_version_num)
    db.close()