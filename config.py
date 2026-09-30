import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_URL = os.getenv('API_URL', 'https://app.apiaberta.pt')
    API_ENDPOINT = os.getenv('API_ENDPOINT', '/nif')
    API_KEY = os.getenv('API_KEY', '')

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'puxar_nifs')

    JWT_SECRET = os.getenv('JWT_SECRET', 'troque-esta-chave-em-producao')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', '3600'))

    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'troque-esta-chave-em-producao')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    @staticmethod
    def get_db_config():
        return {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME,
        }
