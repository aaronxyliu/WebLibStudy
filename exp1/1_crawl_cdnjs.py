# Crawl all libraries and their Github star number from Cdnjs
# Remember to set the CRAWER_LIMIT and the Github token

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

db = ConnDatabase('Libraries')
logger = getLogger()


# Github API rate limit: 5000/hr
# Token generation: https://github.com/settings/tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
logger.info(f'The Github token is: {GITHUB_TOKEN}')

OUTPUT_TABLE = 'libs_cdnjs_all_4_20'
CRAWL_START = 0
CRAWL_END = 100000
CRAWL_INTERVAL = 0.2    # sleep seconds between iterations

MEMORY_DICT = {}

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


def update_github_info(libname, lib_info):
    try:
        raw_url = lib_info['repository']['url']
    except:
        logger.warning(f'{libname} doesn\'t have repository information.')
        return 

    # Get star from Github API
    ptr = raw_url.find('github.com')
    if ptr == -1:
        logger.warning('Not a github domain.')
        return 

    # Remove ".git" suffix
    if raw_url[-4:] == '.git':
        raw_url = raw_url[:-4]
    if raw_url[-1] == '/':
        raw_url = raw_url[:-1]

    github_direct = raw_url[ptr+11:]
    github_api_url = f'https://api.github.com/repos/{github_direct}'
    github_url = f'github.com/{github_direct}'
    
    repo_info = readurl(github_api_url)
    if not repo_info:
        return
    
    # Update star information
    star = 0
    created = None
    updated = None
    if repo_info['stargazers_count']:
        star = repo_info['stargazers_count']
    if repo_info['created_at']:
        created = repo_info['created_at'][:10]
    if repo_info['updated_at']:
        updated = repo_info['updated_at'][:10]
    db.upsert(
            table_name=OUTPUT_TABLE,
            data={'libname': libname,
                'star': star,
                'github': github_url, 
                'created': created, 
                'updated': updated},
            condition_fields="libname"
        )
    
    # Update tag information
    if github_url in MEMORY_DICT:
        # Prevent duplicate query on the same github url
        lib_entry = MEMORY_DICT[github_url]
        db.upsert(
            table_name=OUTPUT_TABLE,
            data={'libname': libname,
                '# tag': lib_entry[0],
                'first tag name': lib_entry[1], 
                'first tag date': lib_entry[2], 
                'last tag name': lib_entry[3], 
                'last tag date': lib_entry[4]},
            condition_fields="libname"
        )
        return
    
    page_no = 1
    tag_no = 0
    first_tag = None
    last_tag = None
    while(True):

        tag_url = f'https://api.github.com/repos/{github_direct}/tags?page={page_no}'
        tag_info_list = readurl(tag_url)
        logger.info(f'Reading the data from {tag_url} ...')

        if tag_info_list and isinstance(tag_info_list, list) and len(tag_info_list) > 0:
            tag_no += len(tag_info_list)
            if not last_tag:
                last_tag = tag_info_list[0]
            first_tag = tag_info_list[-1]
        else:
            break

        page_no += 1

    first_tag_date = None
    first_tag_name = None
    if first_tag:
        first_tag_name = first_tag['name']
        first_commit_info = readurl(first_tag['commit']['url'])
        if first_commit_info:
            first_tag_date = first_commit_info['commit']['author']['date'][:10]
    last_tag_date = None
    last_tag_name = None
    if last_tag:
        last_tag_name = last_tag['name']
        last_commit_info = readurl(last_tag['commit']['url'])
        if last_commit_info:
            last_tag_date = last_commit_info['commit']['author']['date'][:10]
    db.upsert(
        table_name=OUTPUT_TABLE,
        data={'libname': libname,
               '# tag': tag_no,
               'first tag name': first_tag_name, 
               'first tag date': first_tag_date, 
               'last tag name': last_tag_name, 
               'last tag date': last_tag_date},
        condition_fields="libname"
    )
    MEMORY_DICT[github_url] = [tag_no, first_tag_name, first_tag_date, last_tag_name, last_tag_date]
    
def update_basic_info(libname, lib_info):
    url = lib_info['homepage'] if 'homepage' in lib_info else None
    dscp = lib_info['description'] if 'description' in lib_info else None
    version_list = lib_info['versions']
    version_num = 0
    latest_version = None
    if version_list and len(version_list) > 1:
        version_num = len(lib_info['versions'])
        latest_version = lib_info['versions'][-1] 
    db.upsert(
        table_name=OUTPUT_TABLE,
        data={'libname': libname,
               'url': url, 
               'cdnjs': cdnjs, 
               'cdnjs rank': cnt, 
               'description': dscp, 
               '# versions': version_num, 
               'latest version': latest_version},
        condition_fields="libname"
    )

if __name__ == '__main__':
    # Create databse table
    db.create_if_not_exists(OUTPUT_TABLE, '''
        `libname` varchar(100) DEFAULT NULL,
        `url` varchar(500) DEFAULT NULL,
        `cdnjs` varchar(100) DEFAULT NULL,
        `cdnjs rank` int DEFAULT NULL,
        `star` int DEFAULT NULL,
        `description` varchar(10000) DEFAULT NULL,
        `# versions` int DEFAULT NULL,
        `latest version` varchar(100) DEFAULT NULL,
        `github` varchar(500) DEFAULT NULL,
        `created` date DEFAULT NULL,
        `updated` date DEFAULT NULL,
        `# tag` int DEFAULT NULL,
        `first tag name` varchar(100) DEFAULT NULL,
        `first tag date` date DEFAULT NULL,
        `last tag name` varchar(100) DEFAULT NULL,
        `last tag date` date DEFAULT NULL
    ''')
    res = urlopen(f'https://api.cdnjs.com/libraries')
    lib_list = json.loads(res.read())['results']
    lib_num = len(lib_list)
    cnt = 0

    for lib_entry in lib_list:
        cnt += 1
        if cnt < CRAWL_START:
            continue
        if cnt > CRAWL_END:
            break
        libname = lib_entry['name']
        cdnjs = f'https://cdnjs.com/libraries/{libname}'
        res = urlopen(f'https://api.cdnjs.com/libraries/{libname}')
        lib_info = json.loads(res.read())

        update_github_info(libname, lib_info)    
        update_basic_info(libname, lib_info)

        logger.info(f'{libname} finished. ({cnt} / {lib_num})')
        time.sleep(CRAWL_INTERVAL)


    db.close()
    logger.close()