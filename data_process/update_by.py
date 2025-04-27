# Update the entry of one database based on the corresponding value in the another database

import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
db = ConnDatabase('Libraries')

TABLE = 'libs_cdnjs_all_4_20u'
BASED_TABLE = 'libs_cdnjs_all_4_20u_copy2'

SUB_CATEGORIES = [
    "UI Framework",
    "Framework Extension",
    "UI Component",
    "DOM Manipulation",
    "Icons & Fonts",
    "Routing",
    "Internationalization",
    "Code Utilities",
    "Module/Bundling",
    "Performance",
    "Data Storage",
    "API/Communication",
    "Document Processing",
    "Graphics & Animation",
    "Data Visualization",
    "Multimedia",
    "Game Development",
    "Testing",
    "Debugging & Profiling",
    "Authentication/Authorization",
    "Cryptography",
    "Sanitizer",
    "AI"
]

res = db.select_all(TABLE, fields=['category', 'libname'])

for lib in res:
    if lib['category'] not in SUB_CATEGORIES:
        # db.update(TABLE, {'category': NEW_VALUE}, 'category=%s', (OLD_VALUE,))
        print(f"Update library {lib['libname']}: {lib['category']}")
        res2 = db.select_one(BASED_TABLE, 
                      fields=['category'], 
                      condition='libname=%s',
                      condition_values=(lib['libname'],)) 
        new_cat = res2['category']
        print(f"New category: {new_cat}")

        db.update(TABLE, 
                  data={'category': new_cat}, 
                  condition='libname=%s', 
                  condition_values=(lib['libname'],)) 