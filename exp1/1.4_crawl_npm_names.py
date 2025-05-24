# Find the npm name of the library by name

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
c_reader = commonReader(logger=logger, debug=True)

LIB_TABLE = 'libs_cdnjs_all_4_20u'


if __name__ == '__main__':
    db.add_column(LIB_TABLE, 'npm from cdnjs', 'varchar(100) DEFAULT NULL', after_column='libname')

    libs = db.select_all(LIB_TABLE, ["libname"], condition="`npm from cdnjs` IS NULL")
    
    for i, entry in enumerate(libs):
        # Iterate through libraries
        libname = entry['libname']

        logger.info(f"({i}/{len(libs)}) Start {libname}.")
        data = c_reader.read_cdnjs(libname)
        if data and 'autoupdate' in data:
            autoupdate = data['autoupdate']
            logger.info(f"autoupdate source: {autoupdate['source']}")
            if autoupdate['source'] == 'npm':
                db.update(LIB_TABLE, 
                        data={'npm from cdnjs': autoupdate['target']},
                        condition=f'`libname`=%s',
                        condition_values=(libname,))
                # logger.info(f"The npm name of {libname} is {autoupdate['target']}.")
        else:
            logger.warning(f"{libname} does not have the 'autoupdate' field.")
        
        logger.leftTimeEstimator(len(libs) - i)

    db.close()





