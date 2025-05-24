# For each library, calculates the minimum number of versions needed to reach 
# the total hits thresholds (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999)

# SELECT `.50`, `.60`, `.70`, `.80`, `.90`, `.95`, `.99`, `.999` FROM Libraries.lib_version_hits_distribution WHERE `year hits`>99 AND `# versions` > 9;


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
DATA_TABLE = 'lib_version_hits_distribution'

THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999]


if __name__ == '__main__':
    db.create_if_not_exists(DATA_TABLE, '''
            `libname` varchar(100) DEFAULT NULL,
            `npm` varchar(100) DEFAULT NULL,
            `# versions` int DEFAULT NULL,
            `year hits` bigint DEFAULT NULL,
            `.50` int DEFAULT NULL,
            `.60` int DEFAULT NULL,
            `.70` int DEFAULT NULL,
            `.80` int DEFAULT NULL,
            `.90` int DEFAULT NULL,
            `.95` int DEFAULT NULL,
            `.99` int DEFAULT NULL,
            `.999` int DEFAULT NULL
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
            res = db_npm.select_all(npm_name, ['year hits'], return_as='tuple', order_by='year hits', descending=True)
            total_hits = db_npm.fetchone(f'SELECT SUM(`year hits`) FROM `{npm_name}`')[0]
        
        else:
            if libname not in db_gh.show_tables():
                logger.warning(f"Failed to retrieve the version information of {libname} from database 'version_gh'.")
                continue
            res = db_gh.select_all(libname, ['year hits'], return_as='tuple', order_by='year hits', descending=True)
            total_hits = db_gh.fetchone(f'SELECT SUM(`year hits`) FROM `{libname}`')[0]

        if total_hits == 0:
            logger.warning(f"Total hits of {libname} is 0.")
            continue

        # Calculate how many versions are needed to reach the hits thresholds
        cumulative_hits = 0
        distribution = [0] * len(THRESHOLDS)
        for j, entry in enumerate(res):
            cumulative_hits += entry[0]
            for k, threshold in enumerate(THRESHOLDS):
                if distribution[k] == 0 and cumulative_hits / total_hits >= threshold:
                    distribution[k] = j + 1

        db.upsert(DATA_TABLE, data={
            'libname': libname,
            'npm': npm_name,
            '# versions': len(res),
            'year hits': total_hits,
            '.50': distribution[0],
            '.60': distribution[1],
            '.70': distribution[2],
            '.80': distribution[3],
            '.90': distribution[4],
            '.95': distribution[5],
            '.99': distribution[6],
            '.999': distribution[7]
        }, condition_fields='libname')
        
        logger.leftTimeEstimator(len(libs) - i)
    
    db.close()
    db_npm.close()
    db_gh.close()

