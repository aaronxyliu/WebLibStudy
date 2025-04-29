# Calculate the abandonment-related information for libraries
# Get the average span of each category:
#     SELECT `category`, AVG(`span`) FROM Libraries.libs_cdnjs_all_4_20u WHERE `span`>=0 GROUP BY `category`;
# Get the number of adandoned libraries of each category:
#     SELECT `category`, COUNT(*) FROM Libraries.libs_cdnjs_all_4_20u WHERE `abandoned`=1 GROUP BY `category`;

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.globalv import LIB_CATEGORY
db = ConnDatabase('Libraries')
from datetime import datetime


TABLE = 'libs_cdnjs_all_4_20u'
# Current date
TODAY = datetime.now().date()
ABANDON_THRES_DAYS = 716        # 99% libraries' span per tag is less or equal than 716

def getGroup(category):
    for group_name, categories in LIB_CATEGORY.items():
        if category in categories:
            return group_name
    return "Other"

# Main processing function
def process_libraries():
    db.add_column(TABLE, "span", "int", after_column='updated') # days
    db.add_column(TABLE, "span per tag", "int", after_column='span') # days
    db.add_column(TABLE, "abandoned", "bool", after_column='span') # True or False
    

    libraries = db.select_all(TABLE, ['created', 'updated', 'libname', 'first tag date', 'last tag date', '# versions', "# tag"])
    
    for lib in libraries:
        libname, created, updated, first_tag_date, last_tag_date, v_num, tag_num = lib['libname'], lib['created'], lib['updated'], lib['first tag date'], lib['last tag date'], lib['# versions'], lib['# tag']
        
        span_days = 0
        from_today = -1
        span_per_tag = 0
        if tag_num == 0:
            from_today = (TODAY - updated).days
        if tag_num > 0:
            from_today = (TODAY - last_tag_date).days
        if tag_num > 1:
            # Span is only meaningful when # tag > 1
            if last_tag_date >= first_tag_date:
                span_days = (last_tag_date - first_tag_date).days
                span_per_tag = round(span_days / (tag_num - 1), 1)
        
        # Marked as "abandoned" if the last update is 2 years ago
        abaondoned = from_today > ABANDON_THRES_DAYS

        # span_per_tag = span_days
        

        db.update(TABLE, 
                  data={'span': span_days, "abandoned": abaondoned, "span per tag": span_per_tag}, 
                  condition='libname=%s', 
                  condition_values=(libname,)) 
        

if __name__ == "__main__":
    process_libraries()

    db.close()