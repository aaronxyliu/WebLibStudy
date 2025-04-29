# Some libraries' first tag date is larger than the last tag date due to the incorrect order of tags given by GitHub API
# This script will fix this problem and update the correct tag date to the database

from urllib.request import Request, urlopen
import json
import time
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from datetime import datetime

db = ConnDatabase('Libraries')
logger = getLogger()


# Github API rate limit: 5000/hr
# Token generation: https://github.com/settings/tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
logger.info(f'The Github token is: {GITHUB_TOKEN}')

TABLE = 'libs_cdnjs_all_4_20u'
CRAWL_START = 0
CRAWL_END = 100000
CRAWL_INTERVAL = 0.2    # sleep seconds between iterations


def readurl(url:str) -> object:
    # Github API rate limit: 5000/hr
    # Token generation: https://github.com/settings/tokens
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    req = Request(url)
    req.add_header('Authorization', f'token {GITHUB_TOKEN}')
    res = None
    try:
        res = json.loads(urlopen(req).read())
    except KeyboardInterrupt:
        pass
    except:
        logger.warning(f"{url} is an invalid url. Or github token is outdated.")
    return res


def update_tag_info(libname, github_direct):
    page_no = 1
    oldest_tag_name = None
    oldest_tag_date = None
    latest_tag_name = None
    latest_tag_date = None
    tag_num = 0
    while(True):

        tag_url = f'https://api.github.com/repos/{github_direct}/tags?page={page_no}'
        tag_info_list = readurl(tag_url)
        logger.info(f'Reading the data from {tag_url} ...')

        if tag_info_list and isinstance(tag_info_list, list) and len(tag_info_list) > 0:
            for tag_info in tag_info_list:
                tag_num += 1
                # Get the name and date of the tag
                tag_name = tag_info['name']
                tag_commit_info = readurl(tag_info['commit']['url'])
                tag_date = None
                if tag_commit_info:
                    tag_date_str = tag_commit_info['commit']['author']['date'][:10]
                    tag_date = datetime.strptime(tag_date_str, "%Y-%m-%d").date()

                if not oldest_tag_name:
                    # Initilialize the oldest and the latest tags
                    oldest_tag_name = tag_name
                    oldest_tag_date = tag_date
                    latest_tag_name = tag_name
                    latest_tag_date = tag_date
                else:
                    # Update when current tag is older than oldest or newer than latest
                    if (not oldest_tag_date) or (tag_date and tag_date < oldest_tag_date):
                        oldest_tag_name = tag_name
                        oldest_tag_date = tag_date
                    if (not latest_tag_date) or (tag_date and tag_date > latest_tag_date):
                        latest_tag_name = tag_name
                        latest_tag_date = tag_date                 
        else:
            break
        page_no += 1

    db.upsert(
        table_name=TABLE,
        data={ 'libname': libname,
               '# tag': tag_num,
               'first tag name': oldest_tag_name, 
               'first tag date': oldest_tag_date, 
               'last tag name': latest_tag_name, 
               'last tag date': latest_tag_date},
        condition_fields="libname"
    )
    

if __name__ == '__main__':
    cnt = 0

    res = db.fetchall(f"SELECT libname, github FROM {TABLE} WHERE `first tag date` > `last tag date`;")
    for lib_entry in res:
        cnt += 1
        if cnt < CRAWL_START:
            continue
        if cnt > CRAWL_END:
            break
        
        libname = lib_entry[0]
        github_url = lib_entry[1]


        update_tag_info(lib_entry[0], lib_entry[1][11:])    

        logger.info(f'{libname} finished. ({cnt} / {len(res)})')
        time.sleep(CRAWL_INTERVAL)


    db.close()
    logger.close()