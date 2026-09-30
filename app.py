import logging

import mysql.connector
from mysql.connector import Error

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**Config.get_db_config())
            logger.info('✅ Conexão com banco de dados estabelecida')
            return self.connection
        except Error as exc:
            logger.error(f'❌ Erro ao conectar ao banco: {exc}')
            raise

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info('✅ Conexão fechada')

    def execute_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as exc:
            logger.error(f'❌ Erro ao executar query: {exc}')
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_insert_update(self, query, params=None):
        cursor = None
        try:
            cursor = self.connection.cursor()
            if params is not None:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except Error as exc:
            self.connection.rollback()
            logger.error(f'❌ Erro ao executar insert/update: {exc}')
            raise
        finally:
            if cursor:
                cursor.close()

    def create_tables(self):
        queries = [
            '''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                nome_completo VARCHAR(150),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE,
                data_ultimo_acesso TIMESTAMP NULL,
                INDEX idx_username (username),
                INDEX idx_email (email)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS nifs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                nif VARCHAR(20) NOT NULL,
                nome VARCHAR(255),
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                cidade VARCHAR(100),
                pais VARCHAR(100),
                data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'ativo',
                UNIQUE KEY unique_usuario_nif (usuario_id, nif),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                INDEX idx_nif (nif),
                INDEX idx_usuario_id (usuario_id)
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS logs_acesso (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                acao VARCHAR(100),
                descricao TEXT,
                ip_address VARCHAR(50),
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                INDEX idx_usuario_id (usuario_id)
            )
            ''',
        ]

        cursor = None
        try:
            cursor = self.connection.cursor()
            for query in queries:
                cursor.execute(query)
            self.connection.commit()
            logger.info('✅ Tabelas criadas com sucesso')
        except Error as exc:
            logger.error(f'❌ Erro ao criar tabelas: {exc}')
            raise
        finally:
            if cursor:
                cursor.close()

