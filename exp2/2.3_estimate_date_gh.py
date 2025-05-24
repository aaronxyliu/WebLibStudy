# Estimate the missing (None) dates by evenly dividing the time intervals between known dates (or the library's 
# created_date/last_update_date if the missing dates are at the beginning or end).

# Approach:
#   Estimate Missing Dates:
#     If missing dates are between two known dates, evenly distribute the time interval between them.
#     If missing dates are at the beginning (before the first known date), use last_update_date as the reference.
#     If missing dates are at the end (after the last known date), use created_date as the reference.
#   Handle Edge Cases:
#     If all dates are None, distribute dates evenly between created_date and last_update_date.
#     If only one known date exists, estimate missing dates based on the created_date and last_update_date.

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import GitHubAPIReader
logger = getLogger()
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_gh')
reader = GitHubAPIReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'

def estimate_missing_dates(dates: List[Optional[str]], created_date: str, last_update_date: str) -> Dict[int, str]:
    # EXAMPLE INPUT:
    #   dates = ['2024-02-01', '2024-01-15', '2024-01-14', None, None, '2023-09-02', None]
    #   created_date = '2023-01-01'
    #   last_update_date = '2024-02-01'
    # OUTPUT:
    #   {3: '2023-12-01', 4: '2023-10-16', 6: '2023-05-01'}
    
    
    # Convert all non-None dates to datetime objects and record their positions
    known_positions = []
    known_dates = []
    for idx, date in enumerate(dates):
        if date is not None:
            known_positions.append(idx)
            known_dates.append(datetime.strptime(date, "%Y-%m-%d").date())
    
    # Convert created_date and last_update_date to datetime objects
    created_dt = datetime.strptime(created_date, "%Y-%m-%d").date()
    last_update_dt = datetime.strptime(last_update_date, "%Y-%m-%d").date()
    
    # Initialize the dictionary to store estimated dates
    estimated_dict = {}
    
    # If no known dates, distribute evenly between created_date and last_update_date in descending order
    if not known_dates:
        total_days = (last_update_dt - created_dt).days
        interval = total_days / (len(dates) - 1) if len(dates) > 1 else 0
        for i in range(len(dates)):
            estimated_date = (last_update_dt - timedelta(days=interval * i)).strftime("%Y-%m-%d")
            estimated_dict[i] = estimated_date
        return estimated_dict
    
    # Estimate missing dates before the first known date
    first_known_pos = known_positions[0]
    if first_known_pos > 0:
        last_known_dt = known_dates[0]
        total_days = (last_update_dt - last_known_dt).days
        interval = total_days / (first_known_pos + 1)
        for i in range(first_known_pos):
            estimated_date = (last_update_dt - timedelta(days=interval * (i + 1))).strftime("%Y-%m-%d")
            estimated_dict[i] = estimated_date
    
    # Estimate missing dates after the last known date
    last_known_pos = known_positions[-1]
    if last_known_pos < len(dates) - 1:
        next_known_dt = known_dates[-1]
        total_days = (next_known_dt - created_dt).days
        interval = total_days / (len(dates) - last_known_pos)
        for i in range(last_known_pos + 1, len(dates)):
            estimated_date = (next_known_dt - timedelta(days=interval * (i - last_known_pos))).strftime("%Y-%m-%d")
            estimated_dict[i] = estimated_date
    
    # Estimate missing dates between known dates
    for i in range(1, len(known_positions)):
        prev_pos = known_positions[i - 1]
        curr_pos = known_positions[i]
        if curr_pos - prev_pos > 1:
            prev_dt = known_dates[i - 1]
            curr_dt = known_dates[i]
            total_days = (prev_dt - curr_dt).days
            interval = total_days / (curr_pos - prev_pos)
            for j in range(prev_pos + 1, curr_pos):
                estimated_date = (prev_dt - timedelta(days=interval * (j - prev_pos))).strftime("%Y-%m-%d")
                estimated_dict[j] = estimated_date
    
    return estimated_dict





if __name__ == '__main__':
    libs = db.select_all(LIB_TABLE, ['libname', 'github'], condition='`npm` IS NULL')
    for i, libentry in enumerate(libs):
        libname, github_direct = libentry['libname'], libentry['github'][11:]
        if libname not in db2.show_tables():
            logger.warning(f"Failed to retrieve the version information of {libname} from database 'version_gh'.")
            continue
        if 'tag date' not in db2.show_columns(libname):
            logger.warning(f"Table {libname} does not have the column `tag date`.")
            continue
        if db2.entry_count(libname, condition="`tag date` IS NULL AND `estimate date` IS NULL") == 0:
            # Do not need to induce, skip
            continue

        github_api_url = f'https://api.github.com/repos/{github_direct}'
        repo_info, should_stop = reader.read_url(github_api_url)

        if should_stop:
            exit(0)

        if not repo_info['created_at']:
            logger.warning(f"Library created time is unkown. ({github_api_url})")
            continue
        if not repo_info['updated_at']:
            logger.warning(f"Library last updated time is unkown. ({github_api_url})")
            continue
        
        created = repo_info['created_at'][:10]
        updated = repo_info['updated_at'][:10]

        version_list = []
        date_list = []
        version_entries = db2.select_all(libname, ['version', 'tag date'])
        for version_entry in version_entries:
            version_list.append(version_entry['version'])
            date_str = str(version_entry['tag date'])
            if date_str == 'None':
                date_list.append(None)
            else:
                date_list.append(date_str)

        estimate_dict = estimate_missing_dates(date_list, created, updated)
        for index, estimate_date in estimate_dict.items():
            db2.update(libname, 
                       data={'estimate date': estimate_date}, 
                       condition='`version`=%s', 
                       condition_values=(version_list[index],))

        logger.info(f"({i}/{len(libs)}) {libname} table is updated. Estimated {len(estimate_dict)} dates.")
        logger.leftTimeEstimator(len(libs) - i)

    db.close()