from mongoengine import Document, StringField

class CheckpointWrites(Document):
    thread_id = StringField(required=True)

    meta = {'collection': 'checkpoint_writes'}
