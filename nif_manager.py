import re
from datetime import datetime, timedelta

import bcrypt
import jwt

from config import Config


class AuthManager:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def hash_senha(senha: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verificar_senha(senha: str, senha_hash: str) -> bool:
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

    @staticmethod
    def validar_email(email: str) -> bool:
        return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email or ''))

    @staticmethod
    def validar_username(username: str) -> bool:
        if not username:
            return False
        if len(username) < 3 or len(username) > 50:
            return False
        return bool(re.match(r'^[A-Za-z0-9_]+$', username))

    @staticmethod
    def validar_senha(senha: str):
        if len(senha) < 8:
            return False, 'Senha deve ter no mínimo 8 caracteres'
        if not re.search(r'[A-Z]', senha):
            return False, 'Senha deve conter pelo menos 1 letra maiúscula'
        if not re.search(r'[a-z]', senha):
            return False, 'Senha deve conter pelo menos 1 letra minúscula'
        if not re.search(r'\d', senha):
            return False, 'Senha deve conter pelo menos 1 número'
        return True, 'Senha válida'

    def registrar_usuario(self, username, email, senha, nome_completo=''):
        if not self.validar_username(username):
            return {'sucesso': False, 'mensagem': 'Username inválido'}
        if not self.validar_email(email):
            return {'sucesso': False, 'mensagem': 'Email inválido'}
        ok, msg = self.validar_senha(senha)
        if not ok:
            return {'sucesso': False, 'mensagem': msg}

        existente = self.db.execute_query(
            'SELECT id FROM usuarios WHERE username = %s OR email = %s',
            (username, email),
        )
        if existente:
            return {'sucesso': False, 'mensagem': 'Username ou email já cadastrados'}

        senha_hash = self.hash_senha(senha)
        user_id = self.db.execute_insert_update(
            'INSERT INTO usuarios (username, email, senha_hash, nome_completo) VALUES (%s, %s, %s, %s)',
            (username, email, senha_hash, nome_completo)
        )
        return {
            'sucesso': True,
            'mensagem': 'Usuário registrado com sucesso',
            'usuario_id': user_id,
            'username': username,
            'email': email,
        }

    def login(self, username, senha):
        usuario = self.db.execute_query(
            'SELECT id, username, email, senha_hash, ativo FROM usuarios WHERE username = %s',
            (username,),
        )
        if not usuario:
            return {'sucesso': False, 'mensagem': 'Username ou senha incorretos'}

        usuario = usuario[0]
        if not usuario['ativo']:
            return {'sucesso': False, 'mensagem': 'Usuário inativo'}

        if not self.verificar_senha(senha, usuario['senha_hash']):
            return {'sucesso': False, 'mensagem': 'Username ou senha incorretos'}

        token = self.gerar_token(usuario['id'], usuario['username'], usuario['email'])
        self.db.execute_insert_update(
            'UPDATE usuarios SET data_ultimo_acesso = NOW() WHERE id = %s',
            (usuario['id'],),
        )
        self.registrar_log(usuario['id'], 'LOGIN', 'Login realizado com sucesso')
        return {
            'sucesso': True,
            'mensagem': 'Login realizado com sucesso',
            'token': token,
            'usuario': {
                'id': usuario['id'],
                'username': usuario['username'],
                'email': usuario['email'],
            }
        }

    def gerar_token(self, usuario_id, username, email):
        payload = {
            'usuario_id': usuario_id,
            'username': username,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_EXPIRATION),
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

    def verificar_token(self, token):
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
            return {
                'valido': True,
                'usuario_id': payload['usuario_id'],
                'username': payload['username'],
                'email': payload['email'],
            }
        except jwt.ExpiredSignatureError:
            return {'valido': False, 'erro': 'Token expirado'}
        except jwt.InvalidTokenError:
            return {'valido': False, 'erro': 'Token inválido'}

    def obter_usuario(self, usuario_id):
        usuario = self.db.execute_query(
            'SELECT id, username, email, nome_completo, data_criacao, ativo, data_ultimo_acesso FROM usuarios WHERE id = %s',
            (usuario_id,),
        )
        if not usuario:
            return {'sucesso': False, 'mensagem': 'Usuário não encontrado'}
        return {'sucesso': True, 'usuario': usuario[0]}

    def atualizar_usuario(self, usuario_id, nome_completo=None, email=None):
        campos = []
        params = []
        if nome_completo is not None:
            campos.append('nome_completo = %s')
            params.append(nome_completo)
        if email is not None:
            if not self.validar_email(email):
                return {'sucesso': False, 'mensagem': 'Email inválido'}
            campos.append('email = %s')
            params.append(email)
        if not campos:
            return {'sucesso': False, 'mensagem': 'Nenhum campo para atualizar'}
        params.append(usuario_id)
        self.db.execute_insert_update(
            'UPDATE usuarios SET ' + ', '.join(campos) + ' WHERE id = %s',
            params,
        )
        return {'sucesso': True, 'mensagem': 'Usuário atualizado com sucesso'}

    def mudar_senha(self, usuario_id, senha_atual, senha_nova):
        user = self.db.execute_query('SELECT senha_hash FROM usuarios WHERE id = %s', (usuario_id,))
        if not user:
            return {'sucesso': False, 'mensagem': 'Usuário não encontrado'}
        if not self.verificar_senha(senha_atual, user[0]['senha_hash']):
            return {'sucesso': False, 'mensagem': 'Senha atual incorreta'}

        ok, msg = self.validar_senha(senha_nova)
        if not ok:
            return {'sucesso': False, 'mensagem': msg}

        senha_hash = self.hash_senha(senha_nova)
        self.db.execute_insert_update(
            'UPDATE usuarios SET senha_hash = %s WHERE id = %s',
            (senha_hash, usuario_id),
        )
        self.registrar_log(usuario_id, 'MUDAR_SENHA', 'Senha alterada com sucesso')
        return {'sucesso': True, 'mensagem': 'Senha alterada com sucesso'}

    def registrar_log(self, usuario_id, acao, descricao, ip_address='127.0.0.1'):
        try:
            self.db.execute_insert_update(
                'INSERT INTO logs_acesso (usuario_id, acao, descricao, ip_address) VALUES (%s, %s, %s, %s)',
                (usuario_id, acao, descricao, ip_address),
            )
        except Exception:
            pass

