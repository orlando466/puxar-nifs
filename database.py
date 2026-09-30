import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Gerenciador de conexão com MySQL"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Conecta ao banco de dados"""
        try:
            self.connection = mysql.connector.connect(**Config.get_db_config())
            logger.info("✅ Conexão com banco de dados estabelecida")
            return self.connection
        except Error as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise
    
    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("✅ Conexão com banco de dados fechada")
    
    def execute_query(self, query, params=None):
        """Executa uma query e retorna os resultados"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            logger.error(f"❌ Erro ao executar query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_insert_update(self, query, params=None):
        """Executa insert ou update e retorna o ID inserido"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            logger.info(f"✅ Query executada com sucesso (afetadas {cursor.rowcount} linhas)")
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            logger.error(f"❌ Erro ao executar insert/update: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def create_tables(self):
        """Cria as tabelas necessárias"""
        queries = [
            # Tabela de usuários
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                nome_completo VARCHAR(100),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE,
                data_ultimo_acesso TIMESTAMP NULL,
                INDEX idx_username (username),
                INDEX idx_email (email)
            )
            """,
            # Tabela de NIFs
            """
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
                INDEX idx_usuario_id (usuario_id),
                INDEX idx_data_consulta (data_consulta)
            )
            """,
            # Tabela de logs de acesso
            """
            CREATE TABLE IF NOT EXISTS logs_acesso (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT NOT NULL,
                acao VARCHAR(100),
                descricao TEXT,
                ip_address VARCHAR(50),
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                INDEX idx_usuario_id (usuario_id),
                INDEX idx_data_acao (data_acao)
            )
            """
        ]
        
        cursor = None
        try:
            cursor = self.connection.cursor()
            for query in queries:
                cursor.execute(query)
            self.connection.commit()
            logger.info("✅ Tabelas criadas com sucesso")
        except Error as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
