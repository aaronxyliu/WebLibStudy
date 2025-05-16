
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
    total_version_num = 0
    version_with_date_num = 0
    cnt1_sum = 0
    cnt2_sum = 0
    cnt3_sum = 0
    tables = db.show_tables()
    diff_sum = 0
    diff_cnt = 0
    for table in tables:
        version_num = db.entry_count(table)
        total_version_num += version_num

        columns = db.show_columns(table)
        if 'tag date' in columns and 'npm date' in columns:
            cnt1_sum += db.entry_count(table, condition="`tag date` IS NOT NULL AND `npm date` IS NOT NULL AND `tag date` > `npm date`")
            cnt2_sum += db.entry_count(table, condition="`tag date` IS NOT NULL AND `npm date` IS NOT NULL AND `tag date` < `npm date`")
            cnt3_sum += db.entry_count(table, condition="`tag date` IS NOT NULL AND `npm date` IS NOT NULL AND `tag date` = `npm date`")

            res = db.select_all(table, ['tag date', 'npm date'], condition="`tag date` IS NOT NULL AND `npm date` IS NOT NULL")
            for entry in res:
                diff = (entry['npm date'] - entry['tag date']).days
                diff_cnt += 1
                diff_sum += diff


    logger.info(f'Number of table: {len(tables)}')
    logger.info(f'Total version: {total_version_num}')
    logger.info(cnt1_sum)
    logger.info(cnt2_sum)
    logger.info(cnt3_sum)
    logger.info(diff_sum / diff_cnt)


    # logger.info(f'Version with date: {version_with_date_num} ({version_with_date_num * 100/total_version_num:.1f}%)')
    db.close()