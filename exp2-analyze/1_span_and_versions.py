# Calculate the `# versions`, `span`, and `span per version` for each library

from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.api_reader import commonReader
from datetime import date

current_time = date.today()
logger = getLogger()
db = ConnDatabase('Libraries')
db_npm = ConnDatabase('version_npm')
db_gh = ConnDatabase('version_gh')
reader = commonReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'
DATA_TABLE = 'lib_version_time'


if __name__ == '__main__':
    db.create_if_not_exists(DATA_TABLE, '''
            `libname` varchar(100) DEFAULT NULL,
            `npm` varchar(100) DEFAULT NULL,
            `# versions` int DEFAULT NULL,
            `first version` varchar(100) DEFAULT NULL,
            `first version date` date DEFAULT NULL,
            `latest version` varchar(100) DEFAULT NULL,
            `latest version date` date DEFAULT NULL,
            `span` int DEFAULT NULL,
            `avg. hits distance to current` int DEFAULT NULL,
            `avg. hits distance to latest` int DEFAULT NULL,
            `year hits` bigint DEFAULT NULL
        ''')
    
    libs = db.select_all(LIB_TABLE, ["libname", "npm"])

    npm_libnames = db_npm.show_tables()
    gh_libnames = db_gh.show_tables()
        
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname, npm_name = entry['libname'], entry['npm']
        if npm_name:
            # npm library
            if npm_name not in db_npm.show_tables():
                logger.warning(f"Failed to retrieve the version information of {libname} ({npm_name}) from database 'version_npm'.")
                continue
            res = db_npm.select_all(npm_name, ['version', 'year hits', 'tag date', 'estimate date'], return_as='tuple')
        
        else:
            if libname not in db_gh.show_tables():
                logger.warning(f"Failed to retrieve the version information of {libname} from database 'version_gh'.")
                continue
            res = db_gh.select_all(libname, ['version', 'year hits', 'tag date', 'estimate date'], return_as='tuple')
        first_version, first_version_date, latest_version, latest_version_date = None, None, None, None
        total_hits = 0
        distance_to_latest = 0
        distance_to_current = 0
        
        for j, entry in enumerate(res):
            version, hits, tag_date, e_date = entry[0], entry[1], entry[2], entry[3]
            vdate = tag_date or e_date
            if not vdate:
                logger.error(f"{libname} {version} does not have date info.")
                exit(0)
            if j == 0:
                latest_version = version
                latest_version_date = vdate
                first_version = version
                first_version_date = vdate

            if latest_version_date < vdate:
                latest_version = version
                latest_version_date = vdate

            if first_version_date > vdate:
                first_version = version
                first_version_date = vdate

        for j, entry in enumerate(res):
            version, hits, tag_date, e_date = entry[0], entry[1], entry[2], entry[3]
            vdate = tag_date or e_date

            total_hits += hits
            distance_to_current += (current_time - vdate).days * hits
            distance_to_latest += (latest_version_date - vdate).days * hits
            
        span = 0
        if first_version_date and latest_version_date:
            span = (latest_version_date - first_version_date).days

        db.upsert(DATA_TABLE, data={
            'libname': libname,
            'npm': npm_name,
            '# versions': len(res),
            'first version': first_version,
            'first version date': first_version_date,
            'latest version': latest_version,
            'latest version date': latest_version_date,
            'span': span,
            'avg. hits distance to current': None if total_hits == 0 else int(distance_to_current / total_hits),
            'avg. hits distance to latest': None if total_hits == 0 else int(distance_to_latest / total_hits),
            'year hits': total_hits
        }, condition_fields='libname')
        
        logger.leftTimeEstimator(len(libs) - i)
    
    db.close()
    db_npm.close()
    db_gh.close()