# Identify the vulnerable versions on jsDelivr, and calculate the hits

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

START_SYNK = '/vuln/npm:js-xss:20150812'

# Prevent duplicate crawling
# Dict format: "<github_url>:<version>": <hits>
MEMORY_DICT = {}        

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

def range2version(libname:str, version_range:str) -> list:
    """
    Get the versions for a package within a specified version range on jsDelivr over the past year
    
    Args:
        normalized_url: The GitHub normalized url of the library
        version_range: The library version range provided by Synk database
        
    Returns:
        version_list: A list of versions inside the range
    """

    # API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com#get-/v1/stats/packages/gh/-user-/-repo-
    stats_url = f"https://data.jsdelivr.com/v1/packages/npm/{libname}"
    req = Request(
        url=stats_url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    version_list, version_info_list = [], []
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            version_info_list = data['versions']
    except HTTPError as e:
        if e.code == 404:
            return []  # Package not found
        logger.warning(f"HTTP Error for {libname}: {e.code}")
    except URLError as e:
        logger.warning(f"URL Error for {libname}: {e.reason}")
    except Exception as e:
        logger.warning(f"Error processing {libname}: {e}")
    
    for version_info in version_info_list:
        # Check whether this version is vulnerable
        version_str = version_info["version"]
        if is_version_in_range(version_str, version_range):
            version_list.append(version_str)
    return version_list

def get_jsdelivr_version_hits(libname, version_str):
    """
    Get the total hits for a library of given version on jsDelivr over the past year
    
    Args:
        normalized_url (str): GitHub URL in 'owner/repo' format
        version_str: The version string
        
    Returns:
        int: Total hits of this library version in the past year or None if not found
    """
    memory_key = f"{libname}:{version_str}"
    if memory_key in MEMORY_DICT:
        # Save time, no bother to crawl
        return MEMORY_DICT[memory_key]

    # API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com#get-/v1/stats/packages/gh/-user-/-repo-
    stats_url = f"https://data.jsdelivr.com/v1/stats/packages/npm/{libname}@{version_str}?period=year"
    req = Request(
        url=stats_url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            hits = data['hits']['total']
            MEMORY_DICT[memory_key] = hits
            return hits
    except HTTPError as e:
        if e.code == 404:
            logger.warning(f"HTTP Error for {libname}: {e.code}")
            return 0  # Package not found
    except URLError as e:
        logger.warning(f"URL Error for {libname}: {e.reason}")
    except Exception as e:
        logger.warning(f"Error processing {libname}: {e}")
    
    return 0

if __name__ == '__main__':
    db.add_column(VUL_TABLE, '# hits (npm)', 'BIGINT')   # One year hits of vulnerable versions

    res = db.select_all(VUL_TABLE, ['libname', 'synk', 'version1', 'version2', 'version3', 'version4', 'version5', 'version6'], return_as='tuple')
    
    start = False
    for entry in res:

        libname, synk_link = entry[0], entry[1]
        if synk_link == START_SYNK:
            start = True
        if not start:
            continue

        logger.info(f"{libname} ( {synk_link} )")
        logger.indent()
        hits = 0
        for i in range(2, 8):
            version_range = entry[i]
            if not version_range:
                break

            versions = range2version(libname, version_range)
            for version_str in versions:
                hit = get_jsdelivr_version_hits(libname, version_str)
                hits += hit
                logger.info(f"{version_str}: {hit}")
        
        db.update(VUL_TABLE, data={'# hits (npm)': hits}, condition='synk=%s', condition_values=(synk_link,))
        logger.outdent()
    
    db.close()





