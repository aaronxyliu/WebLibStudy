# Check whether the versions crawled from jsDeliver have the same names in GitHub tag list, 
# if so, use the tag created date as the version publish date

import os
import re
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()
import json
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import GitHubAPIReader
logger = getLogger()
db = ConnDatabase('Libraries')
db2 = ConnDatabase('version_npm')
reader = GitHubAPIReader(logger=logger)


LIB_TABLE = 'libs_cdnjs_all_4_20u'
TAG_TABLE = 'tags_5_11'

START_LIB = 'simple-datatables'


def remove_non_numeric_prefix(input_string):
    """
    Removes all non-numeric characters from the beginning of a string,
    keeping only digits and the first decimal point encountered.
    
    Args:
        input_string (str): The input string to process
        
    Returns:
        str: The string with non-numeric prefix removed
    """
    # Use regular expression to find the first numeric part (including decimals)
    match = re.search(r'(\d+\.?\d*)', input_string)
    if match:
        return match.group(1)
    return input_string  # Return the original string


def crawl_tag_date():
    libs = db.select_all(LIB_TABLE, ["libname"])
    
    start_flag = False
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['libname']

        if libname == START_LIB:
            start_flag = True
        if not start_flag:
            continue

        logger.info(f"({i}/{len(libs)}) Start updating {libname}.")

        if libname not in db2.show_tables():
            logger.warning(f"{libname} has no records in the database 'version_npm'.")
            continue

        tags_entry = db.select_one(TAG_TABLE, ["tags"], condition="`libname`=%s", condition_values=(libname,))
        tags = json.loads(tags_entry["tags"])
        tag_name_url_dict = {}
        for tag in tags:
            clean_tag_name = remove_non_numeric_prefix(tag['name'])
            tag_name_url_dict[clean_tag_name] = tag['commit']['url']

        db2.add_column(libname, 'date', 'date DEFAULT NULL')
        res = db2.select_all(libname, ["version"], condition="`date` IS NULL")
        matched_num = 0
        for entry2 in res:
            v_name_original = entry2["version"]
            v_name = remove_non_numeric_prefix(v_name_original)
            if v_name in tag_name_url_dict:
                matched_num += 1
                commit_url = tag_name_url_dict[v_name]
                if commit_url:
                    # Read from GitHub API
                    commit_info, should_stop = reader.read_url(commit_url)
                    # commit_info, should_stop = readurl(commit_url)
                    if commit_info:
                        date = ''
                        try:
                            date = commit_info['commit']['author']['date']
                        except:
                            logger.warning('Github API miss element 2.')
                            continue
                        db2.update(libname, data={'date': date[:10]}, condition="version=%s", condition_values=(v_name_original,))
                        logger.info(f'    {v_name}: {date[:10]}')
                    if should_stop:
                        return  # Stop crawling
        
        logger.info(f"{libname} is updated. {matched_num}/{len(res)} versions are matched.")
        logger.leftTimeEstimator(len(libs) - i)


if __name__ == '__main__':
    while True:
        crawl_tag_date()
        time.sleep(180) # Wait for 3 minutes
    db.close()