# Calculate the update distance to a safe version for a vulnerable version

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

if __name__ == "__main__":
    # Get all vulnerable libraries
    vul_libnames = db.fetchall(f"SELECT DISTINCT `libname` FROM {VUL_TABLE}")

    vul_hits_sum = 0
    updatable_hits_sum = 0
    safe_distance_sum = 0
    cross_major_hits_sum = 0

    for i, entry in enumerate(vul_libnames):
        # Iterate through libraries
        libname = entry[0]
        res = db.fetchone(f"SELECT `npm` FROM {LIB_TABLE} WHERE `libname`='{libname}'")
        npm_name = res[0]
        if not npm_name:
            logger.warning(f"Library {libname} does not have an npm name.")
            continue

        # Check if the library exists in the npm database
        if npm_name not in db_npm.show_tables():
            logger.warning(f"Library {libname} does not exist in the npm database.")
            continue

        # logger.info(f"({i}/{len(vul_libnames)}) Start {libname} ({npm_name}).")

        # Select all rows from the npm table
        version_rows = db_npm.select_all(npm_name, ['version', 'vuls', 'year hits'])
        # Get the latest version
        
        cloest_safe_version = None
        cloest_safe_distance = -1
        for version_row in version_rows:
            version_tag, vuls, hits = version_row['version'], version_row['vuls'], version_row['year hits']
            if vuls:
                vul_hits_sum += hits
                if cloest_safe_distance != -1:
                    # Safe version exists
                    cloest_safe_distance += 1
                    updatable_hits_sum += hits
                    safe_distance_sum += cloest_safe_distance * hits

                    # Check whether the update cross a major version
                    clean_version_tag = re.sub(r'[^0-9.]+', '', version_tag)
                    clean_cloest_safe_version = re.sub(r'[^0-9.]+', '', cloest_safe_version)
                    if version.parse(clean_version_tag).major != version.parse(clean_cloest_safe_version).major:
                        cross_major_hits_sum += hits
                        # logger.info(f"Library {libname} version {version_tag} is vulnerable. It can be updated to {cloest_safe_version} with a distance of {cloest_safe_distance}.")
                        # logger.info(f"Cross major version update: {version_tag} -> {cloest_safe_version}")
                    # else:
                    #     logger.info(f"Library {libname} version {version_tag} is vulnerable. It can be updated to {cloest_safe_version} with a distance of {cloest_safe_distance}.")

            else:
                # Current version is safe
                cloest_safe_distance = 0
                cloest_safe_version = version_tag




    logger.info(f"{(updatable_hits_sum / vul_hits_sum) * 100}% hits are updatable to a safe version.")
    logger.info(f"For these hits, the average update distance is {safe_distance_sum / updatable_hits_sum},")
    logger.info(f"and {(cross_major_hits_sum / updatable_hits_sum)* 100}% of them need to update cross major version.")