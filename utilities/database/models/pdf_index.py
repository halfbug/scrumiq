from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField

class PDFIndex(Document):
    title = StringField(null=True)
    description = StringField(null=True)
    media_type = StringField(default='pdf', choices=['pdf', 'audio', 'video'])
    transcript = StringField(null=True)
    pdf_url = StringField(required=True, unique=True)
    publication_id = IntField(required=True)
    type = StringField(required=True)
    source_table = StringField(required=True)
    unit_id = IntField(required=True)
    week_id = IntField(required=True)
    article_id = IntField(required=True)
    status = StringField(default='pending')
    error_message = StringField(null=True)
    uploaded = BooleanField(default=False)
    created_at = DateTimeField(required=True)
    
    meta = {'collection': 'pdf_index'}
