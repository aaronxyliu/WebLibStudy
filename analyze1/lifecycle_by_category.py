# Calculate the first_tag and last_tag libraries in each year, and save to csv files

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

TABLE = 'libs_cdnjs_all_4_20u'

START_YEAR = 2008
END_YEAR = 2025
SPAN = END_YEAR - START_YEAR + 1

def analyze(category, total=False):

    first_tag_year_list = [0] * SPAN        # the number of libraries that start to update of each year
    last_tag_year_list = [0] * SPAN         # the number of libraries that stop to update of each year
    stop_update_perc_list = [0] * SPAN      # the percentage of libraries that stop of update of each year
    start_update_sum_list = [0] * SPAN      # the number of cumulative libraries that start to update of each year
    keep_update_list = [0] * SPAN           # the number of libraries that keep updateing of each year
    
    if total:
        res = db.select_all(TABLE, ['created', 'first tag date', 'last tag date'])
    else:
        res = db.select_all(TABLE, ['created', 'first tag date', 'last tag date'], condition="`category`=%s", condition_values=(category,))

    for entry in res:
        created, first_tag_date, last_tag_date = entry['created'], entry['first tag date'], entry['last tag date']
        if not first_tag_date or not last_tag_date:
            # When no tag, use the repo created time as the only tag date
            first_tag_date = created
            last_tag_date = created

        first_tag_year = int(str(first_tag_date)[:4])
        last_tag_year = int(str(last_tag_date)[:4])
        
        # Calculate first_tag_year_list and last_tag_year_list
        if first_tag_year >= START_YEAR and first_tag_year <= END_YEAR :
            first_tag_year_list[first_tag_year - START_YEAR] += 1
        else:
            logger.warning(f'First tag year is out of range: {first_tag_year}')

        if last_tag_year >= START_YEAR and last_tag_year <= END_YEAR:
            last_tag_year_list[last_tag_year - START_YEAR] += 1
        else:
            logger.warning(f'Last tag year is out of range: {last_tag_year}')
        
    # Calculate stop_update_perc_list, start_update_sum_list, and keep_update_list
    start_update_sum = 0
    stop_update_sum = 0
    for i in range(0, SPAN):
        start_update_sum += first_tag_year_list[i]
        start_update_sum_list[i] = start_update_sum
        keep_update_list[i] = start_update_sum - stop_update_sum
        stop_update_sum += last_tag_year_list[i]

        if start_update_sum == 0:
            stop_update_perc_list[i] = 0
        else:
            stop_update_perc_list[i] = round(last_tag_year_list[i] / start_update_sum, 4)
    
    return first_tag_year_list, last_tag_year_list, stop_update_perc_list, start_update_sum_list, keep_update_list
            

if __name__ == '__main__':
    year_list = range(START_YEAR, END_YEAR + 1)

    cat_num = len(CATEGORY_LIST)
    first_tag_year_lists = [[]] * cat_num
    last_tag_year_lists = [[]] * cat_num
    stop_update_perc_lists = [[]] * cat_num
    start_update_sum_lists = [[]] * cat_num
    keep_update_lists = [[]] * cat_num

    for i in range(cat_num):
        first_tag_year_lists[i], last_tag_year_lists[i], stop_update_perc_lists[i], start_update_sum_lists[i], keep_update_lists[i] = analyze(CATEGORY_LIST[i])
    l1, l2, l3, l4, l5 = analyze('Total', total=True)
    first_tag_year_lists.append(l1)
    last_tag_year_lists.append(l2)
    stop_update_perc_lists.append(l3)
    start_update_sum_lists.append(l4)
    keep_update_lists.append(l5)
    
    with open(f'data/lifecycle/byCat/first_tag_year.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(SPAN):
            row = [year_list[i_row]]
            for l in first_tag_year_lists:
                row.append(l[i_row])
            writer.writerow(row)   

    with open(f'data/lifecycle/byCat/last_tag_year.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(SPAN):
            row = [year_list[i_row]]
            for l in last_tag_year_lists:
                row.append(l[i_row])
            writer.writerow(row)   

    with open(f'data/lifecycle/byCat/stop_update_perc.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(SPAN):
            row = [year_list[i_row]]
            for l in stop_update_perc_lists:
                row.append(l[i_row])
            writer.writerow(row)   
    
    with open(f'data/lifecycle/byCat/start_update_sum.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(SPAN):
            row = [year_list[i_row]]
            for l in start_update_sum_lists:
                row.append(l[i_row])
            writer.writerow(row)   

    with open(f'data/lifecycle/byCat/keep_update_year.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year'] + CATEGORY_LIST + ['Total'])  # Header row
        for i_row in range(SPAN):
            row = [year_list[i_row]]
            for l in keep_update_lists:
                row.append(l[i_row])
            writer.writerow(row)   
    db.close()
