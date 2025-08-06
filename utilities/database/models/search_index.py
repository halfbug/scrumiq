from mongoengine import Document, StringField, ListField, DateTimeField

class SearchIndex(Document):
    final_answer = StringField(required=False)
    query = StringField(required=True)
    sources = StringField(required=False)
    thread_id = StringField(required=False)
    user_id = StringField(required=False)
    checkpointer_id = StringField(required=False)
    created_at = DateTimeField(required=False)

    meta = {'collection': 'search_index'}
