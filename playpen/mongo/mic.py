"""
Quick Mongo DB Interactive Client for playing with mongo in python.
"""

import pymongo
from pymongo.collection import Collection
from pymongo.son_manipulator import AutoReference, NamespaceInjector


_connection = None
_db = None

db_name = 'test' # you can re-assign this *before* calling connect

# client api -------------------------------------------------------------------

def connect():
    global _connection, _db
    _connection = pymongo.Connection()
    _db = getattr(_connection, db_name)
    _db.add_son_manipulator(NamespaceInjector())
    _db.add_son_manipulator(AutoReference(_db))
    

def clean():
    for name in _db.collection_names():
        if name.startswith(u'system.'):
            continue
        _db.drop_collection(name)


def collection(name, unique_indices=None, search_indicies=None):
    c = Collection(_db, name)
    if unique_indices:
        c.ensure_index(unique_indices, unique=True, background=True)
    if search_indicies:
        c.ensure_index(search_indicies, unique=False, background=True)
    return c

