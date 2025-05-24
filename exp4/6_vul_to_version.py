# Read versions with vulnerabilities from VUL_TABLE, and write to the version_npm database.

from packaging import version
from packaging.specifiers import SpecifierSet
import re
import json
from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
logger = getLogger()
db = ConnDatabase('Libraries')
db_npm = ConnDatabase('version_npm')

LIB_TABLE = 'libs_cdnjs_all_4_20u'
VUL_TABLE = 'vulnerabilities'

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
    

if __name__ == "__main__":
    # Get all vulnerable libraries
    vul_libnames = db.fetchall(f"SELECT DISTINCT `libname` FROM {VUL_TABLE}")

    for i, entry in enumerate(vul_libnames):
        # Iterate through libraries
        libname = entry[0]
        npm_name = db.fetchone(f"SELECT `npm` FROM {LIB_TABLE} WHERE `libname`='{libname}'")[0]
        if not npm_name:
            logger.warning(f"Library {libname} does not have an npm name.")
            continue

        # Check if the library exists in the npm database
        if npm_name not in db_npm.show_tables():
            logger.warning(f"Library {libname} does not exist in the npm database.")
            continue

        logger.info(f"({i}/{len(vul_libnames)}) Start {libname} ({npm_name}).")
        
        db_npm.add_column(npm_name, 'vuls', 'json DEFAULT NULL')
        # Select all rows from the library table
        
        vul_rows = db.select_all(VUL_TABLE, 
                                 ['synk', 'version1', 'version2', 'version3', 'version4', 'version5', 'version6'], 
                                 return_as='tuple',
                                 condition="`libname`=%s",
                                 condition_values=(libname,))

        vul_list = []
        version_rows = db_npm.select_all(npm_name, ['version'])
        for version_row in version_rows:
            version_tag = version_row['version']
            for vul_row in vul_rows:
                # Check if the version is in the range
                for i in range(1, 7):
                    version_range = vul_row[i]
                    if not version_range:
                        break
                    if is_version_in_range(version_tag, version_range):
                        vul_list.append(vul_row[0])
                        break
        
            if len(vul_list) > 0:
                # Update the library table with the vulnerabilities
                db_npm.update(npm_name, data={'vuls': json.dumps(vul_list)}, condition='version=%s', condition_values=(version_tag,)) 
            
        logger.leftTimeEstimator(len(vul_libnames) - i)

    db_npm.close()
    db.close()
    logger.info("All done.")
    logger.close()           