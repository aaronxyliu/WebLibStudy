# Calculate the vulnerable hits number for each library

import os
from packaging import version
from packaging.specifiers import SpecifierSet
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
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
db = ConnDatabase('Libraries')

LIB_TABLE = 'libs_cdnjs_all_4_20u'
VUL_TABLE = 'vulnerabilities'
HITS_TABLE = 'vulhits2'

SEVERITIES = ['low issue', 'medium issue', 'high issue', 'critical issue']

VERSION_DICT_NPM = {}
VERSION_DICT_GH = {}

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

def extract_version_part(version_str):
    """
    Extract the version part from a string that might have prefixes or suffixes.
    Examples:
    "zone.js-0.10.2" -> "0.10.2"
    "1.0.28-csp" -> "1.0.28"
    "v4.2.3" -> "4.2.3"
    """
    # Match version numbers in the string (including prerelease/build metadata)
    version_pattern = r"""
        v?                                      # Optional 'v' prefix
        (\d+!)?                                 # Epoch
        \d+(\.\d+)*                             # Release segment
        ([._-]?(a|b|c|rc|alpha|beta|pre|preview|dev))?  # Pre-release
        ([._-]?(post|rev|r))?                   # Post release
        (\d+)?                                  # Post release version
        ([._-]?dev)?                            # Dev release
        (\+[a-z0-9]+([._-][a-z0-9]+)*)?        # Local version
    """
    match = re.search(version_pattern, version_str, re.VERBOSE | re.IGNORECASE)
    if match:
        return match.group(0).lstrip('v')  # Remove 'v' prefix if present
    return None

def is_version_in_range(version_str, range_str):
    """
    Check if a version string is within a specified version range.
    
    Args:
        version_str (str): The version to check (e.g., "zone.js-0.10.2", "1.0.28-csp")
        range_str (str): The version range (e.g., ">=0.10.0 <1.0.0", "=0.10.2", "*")
        
    Returns:
        bool: True if the version is within the range, False otherwise
    """
    try:
        # Handle wildcard (*) which means any version
        if range_str.strip() == "*":
            return True
            
        # Normalize the range string
        normalized_range = range_str
        
        # First handle space-separated conditions
        normalized_range = re.sub(r'(?<=[^\s=<>!])\s+(?=[<>=])', ', ', normalized_range)
        
        # Then handle exact version matches (= to ==)
        normalized_range = re.sub(r'(?<![<>=!])=\s*', '==', normalized_range)
        
        # Parse the specifier set
        spec = SpecifierSet(normalized_range)
        
        # Extract the version part from the string (handles prefixes and suffixes)
        version_part = extract_version_part(version_str)
        if not version_part:
            # No number-related version tag found
            return False
        
        # Parse the version
        try:
            ver = version.parse(version_part)
        except version.InvalidVersion:
            raise ValueError(f"Invalid version format: {version_str} (extracted: {version_part})")
        
        return spec.contains(ver)
        
    except (version.InvalidVersion, ValueError) as e:
        logger.error(f"Invalid version or range: {e}")
        return False
    

def getVersionDict(libname:str, source:str) -> dict:
    """
    Return a version dictionary of the library. The format is <version: True/False>, indicating whether
    a specific version is vulnerable.

    source: npm or gh
    """
    ret_version_dict = {}

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
            return {}  # Package not found
    except URLError as e:
        logger.warning(f"URL Error for {libname}: {stats_url}")
    except Exception as e:
        logger.warning(f"Error processing {libname}: {stats_url} ({e})")
    
    for version_info in version_info_list:
        # Check whether this version is vulnerable
       ret_version_dict[version_info["version"]] = False
    return ret_version_dict


if __name__ == '__main__':
    db.create_if_not_exists(HITS_TABLE, '''
        `vgroup` varchar(100) DEFAULT NULL,
        `severity` varchar(100) DEFAULT NULL,
        `# hits (npm)` bigint  DEFAULT NULL,
        `# hits (gh)` bigint  DEFAULT NULL,
        `# hits` bigint  DEFAULT NULL
    ''')

    vgroups = db.fetchall(f"SELECT DISTINCT `vgroup` FROM {VUL_TABLE};")
    for entry1 in vgroups:
        # Iterate through vulnerable groups
        vgroup = entry1[0]
        
        for sv in SEVERITIES:
            # Iterate through severities
            hits1, hits2 = 0, 0
            libs = db.fetchall(f"SELECT DISTINCT `libname` FROM {VUL_TABLE} WHERE `vgroup`='{vgroup}' AND `severity`='{sv}';")
            
            for entry2 in libs:
                # Iterate through libraries
                libname = entry2[0]
                v_dict_npm = getVersionDict(libname, 'npm')
                v_dict_gh = getVersionDict(libname, 'gh')
                
                
                res = db.select_all(VUL_TABLE, ['version1', 'version2', 'version3', 'version4', 'version5', 'version6']
                                , return_as='tuple', condition="`libname`=%s AND `vgroup`=%s AND `severity`=%s", condition_values=(libname, vgroup, sv))
                for entry3 in res:
                    for i in range(0, 6):
                        version_range = entry3[i]
                        if not version_range:
                            break
                        for version_tag in v_dict_npm:
                            if is_version_in_range(version_tag, version_range):
                                v_dict_npm[version_tag] = True
                        for version_tag in v_dict_gh:
                            if is_version_in_range(version_tag, version_range):
                                v_dict_gh[version_tag] = True

                for version_tag in v_dict_npm:
                    if v_dict_npm[version_tag] == True:
                        # Iterate through all vulnerable versions
                        hits1 += get_jsdelivr_hits(libname, "npm", version_tag, 'year')
                for version_tag in v_dict_gh:
                    if v_dict_gh[version_tag] == True:
                        # Iterate through all vulnerable versions
                        hits2 += get_jsdelivr_hits(libname, "gh", version_tag, 'year')
         
            hits = hits1 + hits2
            db.upsert(HITS_TABLE, data={
                'vgroup': vgroup,
                'severity': sv,
                '# hits (npm)': hits1,
                '# hits (gh)': hits2,
                '# hits': hits
            }, condition_fields=["vgroup", "severity"])

            logger.info(f'Update {vgroup} ({sv}) # hits: {hits}')

    db.close()





