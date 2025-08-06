from mongoengine import Document, StringField

class Checkpoints(Document):
    thread_id = StringField(required=True)

    meta = {'collection': 'checkpoints'}
