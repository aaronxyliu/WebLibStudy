# Plot the lifecycle distribution of all libraries

from typing import Type
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.stat import Distribution as Dist
db = ConnDatabase('Libraries')
logger = getLogger()

TABLE = 'libs_cdnjs_all_4_20u'

def analyze(table_name):
    res = db.select_all(table_name, ['cdnjs rank', 'star', 'updated', 'created'], return_as='tuple', condition="`group`=%s", condition_values=('Security',))
    begin_date_dist = Dist()
    begin_date_dist2 = Dist()
    latest_date_dist = Dist()
    latest_date_dist2 = Dist()
    has_github_cnt = 0
    lifetime_dist = Dist()

    for entry in res:
        star = entry[1]
        if star and star > 0:
            has_github_cnt += 1
        if entry[2]:
            if str(entry[3]) == 'None':
                logger.error(f'Date Empty: {entry[0]}')
            if entry[2] < entry[3]:
                logger.error(f'Date Error: {entry[0]}')
            begin_date_dist.add(entry[0], str(entry[3]))
            begin_date_dist2.add(int(str(entry[3])[:4]))
            latest_date_dist.add(entry[0], str(entry[2]))
            latest_date_dist2.add(int(str(entry[2])[:4]))
            lifetime_dist.add(entry[0], ((entry[2] - entry[3]).days)/365)
        
    logger.info(f'Containing Github Repo: {has_github_cnt} / {len(res)}')    

    lifetime_dist.showplot('Life Time Histogram of Libraries on Each Web Rank', ylabel='frequence', xlabel='years', processFunc=lambda x:x[0],hist=True)
    # latest_date_dist.showplot('Latest Date Histogram of Libraries on Each Web Rank', ylabel='frequence', xlabel='date', dateY=True, processFunc=lambda x:x[0],hist=True)
    printByYear(begin_date_dist2)
    printByYear(latest_date_dist2)
    

def printByYear(input_dict: Type[Dist]):
    freq_dict = input_dict.freqDict()
    freq_dict = dict(sorted(freq_dict.items(), key=lambda x:x[0]))
    x = list(freq_dict.keys())
    y = list(freq_dict.values())
    print(x)
    print(y)
        





if __name__ == '__main__':
    analyze(TABLE)
    db.close()
