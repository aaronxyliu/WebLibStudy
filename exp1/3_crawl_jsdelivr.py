# Crawl jsdelivr's API to find libraries whose GitHub URLs contained in the database produced by "2_remove_redundant.py"

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


TABLE = 'libs_cdnjs_all_4_20u'
CRAWL_START = 111
CRAWL_INTERVAL = 0.2    # sleep seconds between iterations

def get_normalized_github_urls_from_db():
    """
    Read GitHub URLs from the database and normalize them
    """
    
    rows = db.select_all(TABLE, ['libname', 'github'], condition='`github` IS NOT NULL', return_as="list")
    
    normalized_urls = {}
    for libname, github_url in rows:
        if not github_url:
            continue  
        parsed = urlparse('https://'+github_url)
        if parsed.netloc == 'github.com':
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                normalized_url = f"{path_parts[0]}/{path_parts[1]}"
                normalized_urls[normalized_url] = libname
    
    return normalized_urls

def get_jsdelivr_hits(normalized_url):
    """
    Get the total hits for a package on jsDelivr over the past year
    
    Args:
        normalized_url (str): GitHub URL in 'owner/repo' format
        
    Returns:
        int: Total hits in the past year or None if not found
    """
    owner, repo = normalized_url.split('/')

    # API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com#get-/v1/stats/packages/gh/-user-/-repo-
    stats_url = f"https://data.jsdelivr.com/v1/stats/packages/gh/{owner}/{repo}?period=year"
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
            return None  # Package not found
        logger.warning(f"HTTP Error for {normalized_url}: {e.code}")
    except URLError as e:
        logger.warning(f"URL Error for {normalized_url}: {e.reason}")
    except Exception as e:
        logger.warning(f"Error processing {normalized_url}: {e}")
    
    return None

def crawl_jsdelivr_hits():
    """
    Main function to crawl jsDelivr hits and update database
    """
    normalized_urls = get_normalized_github_urls_from_db()
    
    cnt = 1
    for normalized_url, libname in normalized_urls.items():
        if cnt < CRAWL_START:
            cnt += 1
            continue

        hits = get_jsdelivr_hits(normalized_url)
        
        if hits is not None:
            db.update(TABLE, 
                      data={'# hits': hits}, 
                      condition="`libname`=%s", 
                      condition_values=(libname,))
            logger.info(f"{cnt}: Updated {normalized_url}: {hits} hits")
        else:
            logger.warning(f"{cnt}: Package not found on jsDelivr: {normalized_url}")
        
        # Be polite with rate limiting
        time.sleep(CRAWL_INTERVAL)

        cnt += 1

        logger.leftTimeEstimator(len(normalized_urls) - cnt)

if __name__ == "__main__":
    
    # Start crawling
    crawl_jsdelivr_hits()

    db.close()