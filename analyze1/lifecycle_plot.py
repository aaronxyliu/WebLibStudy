# Calculate the created and updated libraries in each year, and save to csv files

from typing import Type
import sys
import csv
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.stat import Distribution as Dist
from utils.globalv import LIB_CATEGORY
db = ConnDatabase('Libraries')
logger = getLogger()

TABLE = 'libs_cdnjs_all_4_20u'

START_YEAR = 2008
END_YEAR = 2025
SPAN = END_YEAR - START_YEAR + 1

def analyze(group, total=False):

    year_list = range(START_YEAR, END_YEAR + 1)
    created_year_list = [0] * SPAN
    updated_year_list = [0] * SPAN
    live_list = [0] * SPAN
    
    if total:
        res = db.select_all(TABLE, ['updated', 'created'])
    else:
        res = db.select_all(TABLE, ['updated', 'created'], condition="`group`=%s", condition_values=(group,))

    for entry in res:
        updated, created = entry['updated'], entry['created']
        if updated and created:
            updated_year = int(str(updated)[:4])
            created_year = int(str(created)[:4])

            if updated_year >= START_YEAR and updated_year <= END_YEAR :
                updated_year_list[updated_year - START_YEAR] += 1
            else:
                logger.warning(f'Updated year is out of range: {updated_year}')

            if created_year >= START_YEAR and created_year <= END_YEAR :
                created_year_list[created_year - START_YEAR] += 1
            else:
                logger.warning(f'Created year is out of range: {created_year}')
    
    created_sum = 0
    stop_update_sum = 0
    for i in range(0, len(live_list)):
        created_sum += created_year_list[i]
        if i >= 1:
            stop_update_sum += updated_year_list[i - 1]
        live_list[i] = created_sum - stop_update_sum
            

    with open(f'data/lifecycle_{group}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year', 'Created', 'Updated', 'live'])  # Header row
        for row in zip(year_list, created_year_list, updated_year_list, live_list):
            writer.writerow(row)


if __name__ == '__main__':
    analyze('Total', total=True)
    for group_name, _ in LIB_CATEGORY.items():
        analyze(group_name)
    db.close()
