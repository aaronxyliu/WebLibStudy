# Crawl the hits of the past year of all versions of all libraries through jsDelivr (gh)

from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import commonReader
logger = getLogger()
db = ConnDatabase('Libraries')
db_gh = ConnDatabase('version_gh')
reader = commonReader(logger=logger, debug=True)

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == '__main__':
    libs = db.select_all(LIB_TABLE, ["libname", "github"], condition="`npm` IS NULL")

    gh_libnames = db_gh.show_tables()
        
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname, github = entry['libname'], entry["github"]
        if not libname or libname in gh_libnames:
            # Skip libraries already crawled from GitHub source
            continue

        logger.outdent()
        logger.info(f"({i}/{len(libs)}) Start updating {libname}.")
        logger.indent()

        
        github_direct = github[11:]
        libinfo = reader.read_jsDelivr(github_direct, 'gh', stats=False)
        if not libinfo:
            logger.warning(f'Failed to read the {libname} versions from jsDelivr (gh).')
            continue

        version_list = []
        for version_info in libinfo['versions']:
        # Check whether this version is vulnerable
            version_list.append(version_info["version"])

        if len(version_list) > 0:
            db_gh.create_if_not_exists(libname, '''
                `version` varchar(100) DEFAULT NULL,
                `jsDelivr rank` int  DEFAULT NULL,
                `year hits` bigint  DEFAULT NULL
            ''')
        
        rank = 1
        for version_tag in version_list:
            hits = 0
            data = reader.read_jsDelivr(github_direct, "gh", version_tag, "year")
            if data:
                hits = data['hits']['total']
            db_gh.upsert(libname, data={
                'version': version_tag,
                'jsDelivr rank': rank,
                'year hits': hits
            }, condition_fields="version")

            rank += 1
        
        logger.info(f"Complete {libname}. In total {rank - 1} versions.")
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





