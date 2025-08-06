from typing import Dict, Any
from core.mongoengine_connect import init_mongoengine
from utilities.database.models.tokenz import Tokenz

class UsageTracker:
    def __init__(self):
        init_mongoengine()

    def save_usage(self, thread_id: str, usage_details: Dict[str, Any], user_id: str, agent_type: str = "rag", model_name: str = None):
        """Saves the usage details to the MongoDB collection."""
        from datetime import datetime
        doc = Tokenz(
            agent_type=agent_type,
            thread_id=thread_id,
            user_id=user_id,
            update_time=datetime.utcnow(),
            usage_details=usage_details,
            model_name=model_name
        )
        doc.save()
