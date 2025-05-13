# Crawl version date from npm

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
db2 = ConnDatabase('version_npm')
reader = commonReader(logger=logger)

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == '__main__':
    libs = db.select_all(LIB_TABLE, ["npm"], condition="`npm` IS NOT NULL")

    npm_libnames = db2.show_tables()
        
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['npm']
        logger.outdent()
        logger.info(f"({i}/{len(libs)}) Start updating {libname}.")
        logger.indent()

        if libname not in npm_libnames:
            logger.warning(f"{libname} has no version table in database 'version_npm'.")
            continue

        libinfo = reader.read_npm(libname)
        if not libinfo:
            logger.warning(f'Failed to read the {libname} versions from npm.')
            continue

        version_time_dict = libinfo['time']
        db2.add_column(libname, 'npm date', 'date DEFAULT NULL')
        res = db2.select_all(libname, ["version"], condition="`npm date` IS NULL")
        matched_num = 0
        for entry2 in res:
            version_tag = entry2['version']
            if version_tag in version_time_dict:
                date = version_time_dict[version_tag]
                db2.update(libname, data={'npm date': date[:10]}, condition="`version`=%s", condition_values=(version_tag,))
                matched_num += 1
            else:
                logger.warning(f'{version_tag} does not have a matched one in npm.')
        
        logger.info(f"{libname} is updated. {matched_num}/{len(res)} versions are matched.")
        logger.leftTimeEstimator(len(libs) - i)