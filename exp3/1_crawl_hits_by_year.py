

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import json
import time
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
db = ConnDatabase('Libraries')
logger = getLogger()


LIB_TABLE = 'libs_cdnjs_all_4_20u'
CRAWL_START = 1
CRAWL_INTERVAL = 0.1    # sleep seconds between iterations
START_FLAG = "Update table HITS_2024Q3 entry jqvmap"

START_YEAR = 2025
END_YEAR = 2025

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

if __name__ == "__main__":
    res = db.select_all(LIB_TABLE, ['libname'])

    start = True
    for year in range(START_YEAR, END_YEAR + 1):
        for quater in range (1,5):
            hits_table_name = f"HITS_{year}Q{quater}"
            db.create_if_not_exists(table_name=hits_table_name,
                                    schema='''
                                    `libname` varchar(100) DEFAULT NULL,
                                    `# hits (npm)` bigint DEFAULT NULL,
                                    `# hits (gh)` bigint DEFAULT NULL,
                                    `# hits` bigint DEFAULT NULL
                                    ''')
            for i, entry in enumerate(res):
                libname = entry['libname']

                flag = f"Update table {hits_table_name} entry {libname}"
                if flag == START_FLAG:
                    start = True
                if not start:
                    continue

                h1 = get_jsdelivr_hits(libname, 'npm', period=f'{year}-Q{quater}')
                h2 = get_jsdelivr_hits(libname, 'gh', period=f'{year}-Q{quater}')
                h = h1 + h2
                db.upsert(table_name=hits_table_name,
                          data={
                              "libname": libname,
                              "# hits (npm)": h1,
                              "# hits (gh)": h2,
                              "# hits": h
                          },
                          condition_fields="libname")
                logger.info(f"{flag} (hits: {h}).")
                logger.leftTimeEstimator((END_YEAR - year) * 4 * len(res) + (4 - quater) * len(res) + (len(res) - i))

    db.close()