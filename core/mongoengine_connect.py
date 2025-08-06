import os
from mongoengine import connect

def init_mongoengine():
    connect(
        db=os.environ['MONGO_DB'],
        host=os.environ['MONGO_URI']
    )
