# Identify the group of each library based on category

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
from utils.globalv import LIB_CATEGORY
db = ConnDatabase('Libraries')
logger = getLogger()


TABLE = 'libs_cdnjs_all_4_20u'

def getGroup(category):
    # According to the group category relationship LIB_CATEGORY defined in the globalv
    for group_name, categories in LIB_CATEGORY.items():
        if category in categories:
            return group_name
    return "Other"

# Main processing function
def process_libraries():
    db.add_column(TABLE, "group", "varchar(100)", after_column='libname')
    libraries = db.select_all(TABLE, ['libname', 'category', 'description'])
    
    for lib in libraries:
        libname, category = lib['libname'], lib['category']
        group = getGroup(category)
        db.update(TABLE, 
                  data={'group': group}, 
                  condition='libname=%s', 
                  condition_values=(libname,)) 
        

if __name__ == "__main__":
    process_libraries()

    db.close()