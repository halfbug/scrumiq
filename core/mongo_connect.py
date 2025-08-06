from pymongo import MongoClient
import os

class MongoConnect:
    @staticmethod
    def get_collection(collection_name: str):
        try:
            client = MongoClient(os.environ["MONGO_URI"])
            db = client[os.environ['MONGO_DB']]
            return db[collection_name]
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        