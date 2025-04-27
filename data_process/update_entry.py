import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
db = ConnDatabase('Libraries')

TABLE = 'libs_cdnjs_all_4_20u'
OLD_VALUE = '21. Cryptography'
NEW_VALUE = 'Cryptography'

db.update(TABLE, {'category': NEW_VALUE}, 'category=%s', (OLD_VALUE,))