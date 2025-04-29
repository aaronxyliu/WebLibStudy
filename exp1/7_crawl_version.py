# Crawl releases and tags from GitHub for all libraries

import os
from urllib.request import Request, urlopen
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
import json
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
logger = getLogger()
conn = ConnDatabase('Libraries')
conn2 = ConnDatabase('Releases_4_26')
conn3 = ConnDatabase('Tags_4_26')

LIB_TABLE = 'libs_cdnjs_all_4_20u'

START_RANK = 1
END_RANK = 100000

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
            reset_timestamp = response.getheader('X-RateLimit-Reset')  # UTC epoch seconds
            # Convert to datetime object
            reset_time = datetime.fromtimestamp(reset_timestamp)

            # Format as readable string
            formatted_time = reset_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.warning(f"API rate limit exceeded. Limit resets at: {formatted_time}")
            exit(0)

        res = json.loads(response.read())
    except KeyboardInterrupt:
        pass
    except:
        logger.warning(f"{url} is an invalid url. Or github token is outdated.")
    return res

def crawlByRelease(libname, github_direct=None):
    table_name = github_direct[:50] # Table name cannot be too long
    if table_name in conn2.show_tables():
        logger.info(f'The table {table_name} already exists in the release database.')
        return conn2.entry_count(table_name)
    
    conn2.create_new_table(table_name, '''
        `id` int unsigned NOT NULL AUTO_INCREMENT,
        `tag_name` varchar(500) DEFAULT NULL,
        `name` varchar(500) DEFAULT NULL,
        `publish_date` date DEFAULT NULL,
        `url` varchar(500) DEFAULT NULL,
        PRIMARY KEY (`id`)
    ''')

    release_no = 0
    page_no = 1
    while(True):

        release_url = f'https://api.github.com/repos/{github_direct}/releases?page={page_no}'
        logger.info(f'Reading the data from {release_url} ...')
        release_info_list = readurl(release_url)

        if release_info_list and isinstance(release_info_list, list) and len(release_info_list) > 0:
            for release_info in release_info_list:
                if release_info:
                    conn2.insert(table_name,
                                 data={
                                     'tag_name': release_info['tag_name'],
                                     'name': release_info['name'],
                                     'publish_date': release_info['published_at'][:10],
                                     'url': release_info['url']
                                 })
                    release_no += 1
        else:
            break

        page_no += 1
    
    logger.info(f'{libname} finished. Release number: {release_no}.')
    if release_no == 0:
        conn2.drop(table_name)
    return release_no

def crawlByTag(libname, github_direct=None):
    table_name = github_direct[:50] # Table name cannot be too long
    if table_name in conn3.show_tables():
        logger.info(f'The table {table_name} already exists in the tag database.')
        return conn3.entry_count(table_name)
    
    conn3.create_new_table(table_name, '''
        `id` int unsigned NOT NULL AUTO_INCREMENT,
        `tag_name` varchar(500) DEFAULT NULL,
        `name` varchar(500) DEFAULT NULL,
        `publish_date` date DEFAULT NULL,
        `url` varchar(500) DEFAULT NULL,
        PRIMARY KEY (`id`)
    ''')

    page_no = 1
    tag_no = 0
    while(True):

        tag_url = f'https://api.github.com/repos/{github_direct}/tags?page={page_no}'
        logger.info(f'Reading the data from {tag_url} ...')

        tag_info_list = readurl(tag_url)

        if tag_info_list and isinstance(tag_info_list, list) and len(tag_info_list) > 0:
            for tag_info in tag_info_list:
                commit_url = None
                try:
                    commit_url = tag_info['commit']['url']
                except:
                    logger.warning('Github API miss element.')
                    continue

                commit_info = readurl(commit_url)
                if commit_info:
                    date = ''
                    try:
                        date = commit_info['commit']['author']['date']
                    except:
                        logger.warning('Github API miss element 2.')
                        continue
                    conn3.insert(table_name, 
                                 data={
                                    'tag_name': tag_info['name'],
                                    'name': '',
                                    'publish_date': date[:10],
                                    'url': commit_url
                    })
                    tag_no += 1
                
        else:
            break

        page_no += 1
    
    logger.info(f'{libname} finished. Tag number: {tag_no}.')
    if tag_no == 0:
        conn3.drop(table_name)
    return tag_no


def crawlAll():

    res = conn.select_all(LIB_TABLE, ['cdnjs rank', 'libname', 'github'], return_as='tuple', order_by='cdnjs rank')
    for entry in res:
        rank = entry[0]
        if rank < START_RANK:
            continue
        if rank > END_RANK:
            break
        libname = entry[1]
        github_direct = entry[2][11:]
        logger.info(f'{rank}: {libname}')
        if github_direct:
            release_no = crawlByRelease(libname, github_direct)
            if release_no < 10:
                crawlByTag(libname, github_direct)


if __name__ == '__main__':
    crawlAll()


