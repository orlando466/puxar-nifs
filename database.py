from __future__ import annotations

import requests

from config import Config


class NIFManager:
    def __init__(self):
        self.base_url = Config.API_URL.rstrip('/')
        self.endpoint = Config.API_ENDPOINT
        self.api_key = Config.API_KEY

    def consultar_nif(self, nif: str):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        url = f'{self.base_url}{self.endpoint}/{nif}'
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return {'sucesso': True, 'dados': response.json()}
            if response.status_code == 404:
                return {'sucesso': False, 'mensagem': 'NIF não encontrado'}
            return {'sucesso': False, 'mensagem': f'Erro da API: {response.status_code}'}
        except requests.RequestException as exc:
            return {'sucesso': False, 'mensagem': f'Erro de conexão: {exc}'}

    def consultar_e_salvar_nif(self, nif, db, usuario_id):
        resultado = self.consultar_nif(nif)
        if not resultado['sucesso']:
            return resultado

        dados = resultado['dados']
        db.execute_insert_update(
            '''
            INSERT INTO nifs (usuario_id, nif, nome, email, telefone, endereco, cidade, pais)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nome=VALUES(nome), email=VALUES(email), telefone=VALUES(telefone),
                endereco=VALUES(endereco), cidade=VALUES(cidade), pais=VALUES(pais),
                ultima_atualizacao = CURRENT_TIMESTAMP
            ''',
            (
                usuario_id,
                nif,
                dados.get('nome') or '',
                dados.get('email') or '',
                dados.get('telefone') or '',
                dados.get('endereco') or '',
                dados.get('cidade') or '',
                dados.get('pais') or '',
            ),
        )
        return {'sucesso': True, 'mensagem': 'NIF consultado e salvo', 'dados': dados}

    def listar_nifs_usuario(self, db, usuario_id, pagina=1, limite=10):
        offset = (pagina - 1) * limite
        itens = db.execute_query(
            '''
            SELECT id, nif, nome, email, telefone, endereco, cidade, pais, data_consulta
            FROM nifs WHERE usuario_id = %s ORDER BY data_consulta DESC LIMIT %s OFFSET %s
            ''',
            (usuario_id, limite, offset),
        )
        total = db.execute_query('SELECT COUNT(*) as total FROM nifs WHERE usuario_id = %s', (usuario_id,))[0]['total']
        return {'nifs': itens, 'total': total, 'pagina': pagina, 'limite': limite}

