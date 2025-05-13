# Crawl GitHub tags of each library

import os
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
logger = getLogger()
db = ConnDatabase('Libraries')

LIB_TABLE = 'libs_cdnjs_all_4_20u'
TAG_TABLE = 'tags_5_11'

START_LIB = 'FastActive'

def readurl(url:str) -> object:
    # Github API rate limit: 5000/hr
    # Token generation: https://github.com/settings/tokens
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    req = Request(url)
    req.add_header('Authorization', f'token {GITHUB_TOKEN}')
    res = None
    try:
        response = urlopen(req)
        # Get rate limit info from headers
        rate_limit_remaining = response.getheader('X-RateLimit-Remaining')
        rate_limit = response.getheader('X-RateLimit-Limit')
        

        logger.info(f"Requests remaining: {rate_limit_remaining}/{rate_limit}")

        if int(rate_limit_remaining) <= 0:
            logger.warning('1')
            reset_timestamp = response.getheader('X-RateLimit-Reset')  # UTC epoch seconds
            logger.warning('2')
            # Convert to datetime object
            reset_time = datetime.fromtimestamp(reset_timestamp)
            logger.warning('3')

            # Format as readable string
            formatted_time = reset_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.warning('4')
            logger.warning(f"API rate limit exceeded. Limit resets at: {formatted_time}")
            logger.warning('5')
            exit(0)
            logger.warning('6')

        res = json.loads(response.read())
    except KeyboardInterrupt:
        pass
    except:
        logger.warning(f"{url} is an invalid url. Or github token is outdated.")
    return res

if __name__ == '__main__':
    db.create_if_not_exists(TAG_TABLE, '''
                                `libname` varchar(100) DEFAULT NULL,
                                `# tags` varchar(100) DEFAULT NULL,
                                `tags` json DEFAULT NULL
                            ''')
    libs = db.select_all(LIB_TABLE, ["libname", "github"])
    
    start_flag = False
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname, github_url = entry['libname'], entry['github']
        github_direct = github_url[11:]

        if libname == START_LIB:
            start_flag = True
        if not start_flag:
            continue

        logger.info(f"({i}/{len(libs)}) Start updating {libname}.")

        tag_num = 0
        page_no = 0
        tag_content = []
        while(True):
            page_no += 1
            tag_url = f'https://api.github.com/repos/{github_direct}/tags?page={page_no}'
            tag_info_list = readurl(tag_url)
            if tag_info_list and isinstance(tag_info_list, list) and len(tag_info_list) > 0:
                tag_num += len(tag_info_list)
                tag_content += tag_info_list
            else:
                break
        
        db.upsert(TAG_TABLE, data={
            'libname': libname,
            '# tags': tag_num,
            'tags': json.dumps(tag_content)
        }, condition_fields="libname")

        logger.info(f"{libname} is updated with {tag_num} tags.")
 
        logger.leftTimeEstimator(len(libs) - i)
        

    db.close() 