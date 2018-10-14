'''
Remove useless category before parsing WIKI Hierarchy
'''
import pickle
from pathlib import Path

import pandas as pd
import pymysql.cursors
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

ENGINE = create_engine('mysql+pymysql://root@db/test', isolation_level='AUTOCOMMIT')
SESSION = sessionmaker(bind=ENGINE)
SESS = SESSION(autocommit=True)
with SESS.begin(): 
    SQL_STRING = Path('garbage_title.sql')
    SESS.execute(SQL_STRING.open().read())
    SQL_STRING = Path('insert_garbage_title.sql')
    SESS.execute(SQL_STRING.open().read())
    SQL_STRING = Path('hierarchy.sql')
    RESULT = SESS.execute(SQL_STRING.open().read()).fetchall()
    pickle.dump(RESULT, open('hierarchy.pkl', 'wb'))
