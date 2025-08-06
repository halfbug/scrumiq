import os
from core.config import config

def set_environment_variables():
    """Set environment variables with fallback values and validation."""
    required_vars = {
        # 'OPENAI_API_KEY': config.OPENAI_API_KEY,
        'PINECONE_API_KEY': config.PINECONE_KEY,
        'PINECONE_INDEX_NAME': config.PINECONE_INDEX_NAME,
        'API_KEY': config.API_KEY,
    }

    # Set required variables with validation
    for var_name, value in required_vars.items():
        if not value:
            raise ValueError(f"Configuration missing for {var_name}")
        os.environ[var_name] = value

    # Set optional variables
    optional_vars = {
        # 'GOOGLE_API_KEY': config.GOOGLE_API_KEY,
        'MONGO_URI': config.MONGO_URI,
        # 'HUGGINGFACEHUB_API_TOKEN': config.HUGGINGFACEHUB_API_TOKEN,
        # 'DEEPSEEK_API_KEY': config.DEEPSEEK_API_KEY,
        'MONGO_DB': config.MONGO_DB,
        'SEARCH_URL': config.SEARCH_URL,
    }

    for var_name, value in optional_vars.items():
        if value:
            os.environ[var_name] = value
