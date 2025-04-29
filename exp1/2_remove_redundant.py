# Remove entries with duplicate github url, or that do not have git url

import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger

db = ConnDatabase('Libraries')
logger = getLogger()

OLD_TABLE = 'libs_cdnjs_all_4_20'
NEW_TABLE = OLD_TABLE + 'u'

db.clone_table_structure(OLD_TABLE , NEW_TABLE)
db.add_column(NEW_TABLE, "# hits", "INT")   # Record the library hits in the last one year on jsDelivr

# Get the columns from source table (excluding 'id')
columns = db.show_columns(OLD_TABLE)
if 'id' in columns:
    columns.remove('id')
if 'github' not in columns:
    raise ValueError("Source table has no 'github' column")

unique_count = 0


# Get records with non-empty github values
query = f"""
    SELECT `{'`, `'.join(columns)}` 
    FROM `{OLD_TABLE}` 
    WHERE `github` IS NOT NULL AND `github` != ''
"""
res = db.fetchall(query)

for record in res:
    github_value = record[columns.index('github')]
    
    # Check if this github value already exists in new table
    exists = db.fetchone(
        f"SELECT 1 FROM `{NEW_TABLE}` WHERE `github` = %s LIMIT 1",
        (github_value,)
    )
    
    if not exists:
        # Insert into new table
        columns_str = "`, `".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_query = f"""
            INSERT INTO `{NEW_TABLE}` (`{columns_str}`)
            VALUES ({placeholders})
        """
        db.execute(insert_query, record)
        unique_count += 1

print(f"Found {unique_count} unique GitHub entries so far")

