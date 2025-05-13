# Crawl the hits of the past year of all versions of all libraries through jsDelivr

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
db2 = ConnDatabase('version_npm')

LIB_TABLE = 'libs_cdnjs_all_4_20u'


def get_normalized_github_urls_from_db():
    """
    Read GitHub URLs from the database and normalize them
    """
    
    rows = db.select_all(LIB_TABLE, ['libname', 'github'], condition='`github` IS NOT NULL', return_as="tuple")
    
    normalized_urls = {}
    for libname, github_url in rows:
        if not github_url:
            continue  
        parsed = urlparse('https://'+github_url)
        if parsed.netloc == 'github.com':
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                normalized_url = f"{path_parts[0]}/{path_parts[1]}"
                normalized_urls[libname] = normalized_url
    
    return normalized_urls

NORMALIZED = get_normalized_github_urls_from_db()

def get_jsdelivr_hits(libname:str, source:str, version_tag:str=None, period:str=None):
    # API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com#get-/v1/stats/packages/gh/-user-/-repo-

    stats_url = f"https://data.jsdelivr.com/v1/stats/packages/"

    if source == 'npm':
        stats_url += f"npm/{libname}"
    else:
        if libname not in NORMALIZED:
            logger.warning(f"{libname} has no github url in table {LIB_TABLE}")
            return 0
        normalized_url = NORMALIZED[libname]
        owner, repo = normalized_url.split('/')
        stats_url += f"gh/{owner}/{repo}"
    
    if version_tag:
        stats_url += f"@{version_tag}"
    
    if period:
        stats_url += f"?period={period}"

    req = Request(
        url=stats_url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['hits']['total']
    except HTTPError as e:
        if e.code == 404:
            logger.warning(f"HTTP Error for {libname}: {e.code}")
            return 0  # Package not found
    except URLError as e:
        logger.warning(f"URL Error for {libname}: {e.reason}")
    except Exception as e:
        logger.warning(f"Error processing {libname}: {e}")
    
    return 0   
    

def getVersionList(libname:str, source:str) -> dict:
    """
    Return a version list of the library.

    source: npm or gh
    """
    ret_version_list = []

    # API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com#get-/v1/stats/packages/gh/-user-/-repo-
    stats_url = f"https://data.jsdelivr.com/v1/packages/"

    if source == 'npm':
        stats_url += f"npm/{libname}"
    else:
        if libname not in NORMALIZED:
            logger.warning(f"{libname} has no github url in table {LIB_TABLE}")
            return {}
        normalized_url = NORMALIZED[libname]
        owner, repo = normalized_url.split('/')
        stats_url += f"gh/{owner}/{repo}"

    req = Request(
        url=stats_url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    version_info_list = []
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            version_info_list = data['versions']
    except HTTPError as e:
        if e.code == 404:
            logger.warning(f"HTTP Error for {libname}: {stats_url}")
            return []  # Package not found
    except URLError as e:
        logger.warning(f"URL Error for {libname}: {stats_url}")
    except Exception as e:
        logger.warning(f"Error processing {libname}: {stats_url} ({e})")
    
    for version_info in version_info_list:
        # Check whether this version is vulnerable
       ret_version_list.append(version_info["version"])
    return ret_version_list


if __name__ == '__main__':
    libs = db.select_all(LIB_TABLE, ["libname"])
        
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['libname']
        version_list = getVersionList(libname, source='npm')
        if len(version_list) > 0:
            db2.create_if_not_exists(libname, '''
                `version` varchar(100) DEFAULT NULL,
                `jsDelivr rank` int  DEFAULT NULL,
                `year hits` bigint  DEFAULT NULL
            ''')
        
        rank = 1
        for version_tag in version_list:
            hits = get_jsdelivr_hits(libname, "npm", version_tag, "year")
            db2.upsert(libname, data={
                'version': version_tag,
                'jsDelivr rank': rank,
                'year hits': hits
            }, condition_fields="version")

            rank += 1
        
        logger.info(f"({i}/{len(libs)}) Complete {libname}. In total {rank} versions.")
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





