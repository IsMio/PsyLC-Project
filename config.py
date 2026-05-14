import os
import yaml
from dotenv import load_dotenv
from typing import Optional
load_dotenv()

class Config:
    """配置类"""
    # 加载配置文件
    with open('./data/config.yaml', 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    # 模型配置
    DASHSCOPE_API_KEY = config_data['dashscope']['api_key']
    DASHSCOPE_API_BASE_URL = config_data['dashscope']['api_base_url']
    ASSIST_DASHSCOPE_API_BASE_URL = config_data['dashscope']['assist_api_base_url']
    ASSIST_API_KEY = config_data['dashscope']['assist_api_key']
    MODEL_NAME = config_data['dashscope']['model_name']
    MODEL_MAX_TOKENS = config_data['dashscope']['model_max_tokens']
    EMBEDDINGS_MODEL_NAME = config_data['dashscope']['embeddings_model_name']
    DB_PATH = config_data['db']['path']
    # 模型参数
    TEMPERATURE = config_data['model']['temperature']
    TOP_P = config_data['model']['top_p']
    ENABLE_SEARCH = config_data['model']['enable_search']

    # 应用配置
    MEMORY_KEY = config_data['app']['memory_key']
    SYSTEM_PROMPT = config_data['app']['system_prompt']
    CHROMA_COLLECTION_NAME = config_data['app']['chroma_collection_name']
    CHROMA_PERSIST_DIR = config_data['app']['chroma_persist_dir']
    PROMPT_TEMPLATE_PATH= config_data['app']['prompt_template_path']
    MAX_HISTORY_MESSAGES = config_data['app']['max_history_messages']
    MAX_HISTORY_CHARS = config_data['app']['max_history_chars']
    MAX_SINGLE_MESSAGE_CHARS = config_data['app']['max_single_message_chars']
    KNOWLEDGE_UPLOAD_DIR = config_data['app'].get('knowledge_upload_dir', 'data/knowledge_uploads')
    KNOWLEDGE_ALLOWED_EXTENSIONS = config_data['app'].get('knowledge_allowed_extensions', ['.txt', '.md', '.pdf', '.docx', '.html', '.htm'])
    OUTPUT_FILTER_ENABLED = config_data['app'].get('output_filter_enabled', True)
    OUTPUT_FILTER_REVIEW_ENABLED = config_data['app'].get('output_filter_review_enabled', True)
    REDIS_HOST = config_data['redis']['redis_host']
    REDIS_PORT = config_data['redis']['redis_port']
    REDIS_DB = config_data['redis']['redis_db']
    SECRET_KEY = config_data['jwt']['secret_key']
    ALGORITHM = config_data['jwt']['algorithm']
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    @classmethod
    def get_base_url(cls)-> Optional[str]:
        """获取API基础URL，优先使用环境变量"""
        base_url = (
            os.getenv("DASHSCOPE_API_BASE_URL") or
            os.getenv("ALIYUN_API_BASE_URL") or
            getattr(cls, 'DASHSCOPE_API_BASE_URL', None)
        )
        return base_url;
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """安全获取API密钥"""
        api_key = (
                os.getenv("DASHSCOPE_API_KEY") or
                os.getenv("ALIYUN_API_KEY") or
                getattr(cls, 'DASHSCOPE_API_KEY', None)
        )
        return api_key

    @classmethod
    def get_assist_api_key(cls) -> Optional[str]:
        """安全获取Assist API密钥"""
        assist_api_key = (
                os.getenv("ASSIST_API_KEY") or
                getattr(cls, 'ASSIST_API_KEY', None)
        )
        return assist_api_key
    @classmethod
    def validate_config(cls):
        """验证配置是否完整"""
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY未找到"
            )
        return True
