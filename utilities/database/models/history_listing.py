from mongoengine import Document, StringField, DateTimeField

class HistoryListing(Document):
    thread_id = StringField(required=True, unique=True)
    user_id = StringField(required=True)
    title = StringField(required=False)
    created_at = DateTimeField(required=True)

    meta = {'collection': 'history_listing'}
