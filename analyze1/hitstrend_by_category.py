# Calculate the number of hits of each category in different years

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
db = ConnDatabase('Libraries')
logger = getLogger()

LIB_TABLE = 'libs_cdnjs_all_4_20u'

START_YEAR = 2020
END_YEAR = 2024
SPAN = (END_YEAR - START_YEAR + 1) * 4  # 4 quaters a year

def analyze(category, total=False):

    hits_list = [0] * SPAN        # the number of libraries hits of each year
    i = 0
    for year in range(START_YEAR, END_YEAR + 1):
        for quater in range (1,5):
            hits_table_name = f"HITS_{year}Q{quater}"
            if total:
                res = db.fetchall(f'''  SELECT SUM(lh.`# hits`)
                                        FROM {LIB_TABLE} lc
                                        JOIN {hits_table_name} lh ON lc.`libname` = lh.`libname`;
                                   ''')
                hits_list[i] = res[0][0]
            else:
                res = db.fetchall(f'''  SELECT SUM(lh.`# hits`)
                                        FROM {LIB_TABLE} lc
                                        JOIN {hits_table_name} lh ON lc.`libname` = lh.`libname`
                                        WHERE lc.`category` = '{category}'
                                        GROUP BY lc.`category`;
                                   ''')
                hits_list[i] = res[0][0]
            i += 1
    
    return hits_list
            

if __name__ == '__main__':
    year_list = []
    for year in range(START_YEAR, END_YEAR + 1):
        for quater in range (1,5):
            year_list.append(f"{year}Q{quater}")

    cat_num = len(CATEGORY_LIST)
    hits_cat_lists = [[]] * cat_num

    for i in range(cat_num):
        hits_cat_lists[i] = analyze(CATEGORY_LIST[i])
    hits_cat_lists.append(analyze('Total', total=True))
    
    with open(f'data/hitstrend/byCat.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(len(year_list)):
            row = [year_list[i_row]]
            for l in hits_cat_lists:
                row.append(l[i_row])
            writer.writerow(row)   
    db.close()
