from mongoengine import Document, StringField, DictField, DateTimeField, IntField
from mongoengine.fields import ObjectIdField
from datetime import datetime
import uuid

class Tokenz(Document):
    # MongoDB ObjectId as primary key, but allow custom UUID if needed
    id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()), db_field="_id")
    agent_type = StringField(required=True)
    thread_id = StringField(required=True)
    user_id = StringField(required=True)
    update_time = DateTimeField(default=datetime.utcnow)
    # Store all other usage details as a dict
    usage_details = DictField()
    total_tokens = IntField()
    input_tokens = IntField()
    output_tokens = IntField()
    model_name = StringField(null=True)
    question_type = StringField(required=False)

    meta = {'collection': 'tokenz'}
