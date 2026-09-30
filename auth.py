#!/usr/bin/env python3
"""
Sistema de autenticação e registro de usuários
"""

from database import Database
from auth_manager import AuthManager
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def menu_auth():
    """Menu de autenticação"""
    print("\n" + "="*50)
    print("🔐 AUTENTICAÇÃO")
    print("="*50)
    print("1. Registrar novo usuário")
    print("2. Fazer login")
    print("3. Voltar")
    print("="*50)
    return input("Escolha uma opção: ").strip()

def menu_usuario(auth, usuario_info):
    """Menu de usuário autenticado"""
    print("\n" + "="*50)
    print(f"👤 Bem-vindo, {usuario_info['username']}!")
    print("="*50)
    print("1. Ver meu perfil")
    print("2. Atualizar perfil")
    print("3. Mudar senha")
    print("4. Ver logs de acesso")
    print("5. Voltar ao menu anterior")
    print("6. Sair")
    print("="*50)
    return input("Escolha uma opção: ").strip()

def registrar_usuario(auth):
    """Registra um novo usuário"""
    print("\n" + "-"*50)
    print("📝 REGISTRAR NOVO USUÁRIO")
    print("-"*50)
    
    username = input("Nome de usuário (3-50 caracteres): ").strip()
    email = input("Email: ").strip()
    nome_completo = input("Nome completo (opcional): ").strip()
    
    print("\nRequirimentos da senha:")
    print("  • Mínimo 8 caracteres")
    print("  • Pelo menos 1 letra maiúscula")
    print("  • Pelo menos 1 letra minúscula")
    print("  • Pelo menos 1 número")
    
    senha = input("\nSenha: ").strip()
    confirmacao = input("Confirme a senha: ").strip()
    
    if senha != confirmacao:
        print("❌ As senhas não conferem")
        return
    
    resultado = auth.registrar_usuario(username, email, senha, nome_completo)
    
    if resultado['sucesso']:
        print(f"\n✅ {resultado['mensagem']}")
        print(f"   Username: {resultado['username']}")
        print(f"   Email: {resultado['email']}")
    else:
        print(f"\n❌ Erro: {resultado['mensagem']}")

def fazer_login(auth):
    """Realiza login do usuário"""
    print("\n" + "-"*50)
    print("🔑 FAZER LOGIN")
    print("-"*50)
    
    username = input("Username: ").strip()
    senha = input("Senha: ").strip()
    
    resultado = auth.login(username, senha)
    
    if resultado['sucesso']:
        print(f"\n✅ {resultado['mensagem']}")
        print(f"   Token: {resultado['token'][:50]}...")
        
        # Menu do usuário autenticado
        menu_usuario_autenticado(auth, resultado['usuario'], resultado['token'])
    else:
        print(f"\n❌ {resultado['mensagem']}")

def ver_perfil(auth, usuario_id):
    """Mostra perfil do usuário"""
    resultado = auth.obter_usuario(usuario_id)
    
    if resultado['sucesso']:
        usuario = resultado['usuario']
        print("\n" + "-"*50)
        print("👤 MEU PERFIL")
        print("-"*50)
        print(f"Username: {usuario['username']}")
        print(f"Email: {usuario['email']}")
        print(f"Nome completo: {usuario['nome_completo'] or 'Não informado'}")
        print(f"Cadastrado em: {usuario['data_criacao']}")
        print(f"Último acesso: {usuario['data_ultimo_acesso'] or 'Nunca'}")
        print(f"Status: {'✅ Ativo' if usuario['ativo'] else '❌ Inativo'}")
    else:
        print(f"❌ Erro: {resultado['mensagem']}")

def atualizar_perfil(auth, usuario_id):
    """Atualiza perfil do usuário"""
    print("\n" + "-"*50)
    print("✏️ ATUALIZAR PERFIL")
    print("-"*50)
    
    nome_completo = input("Novo nome completo (ou deixe em branco para não alterar): ").strip()
    email = input("Novo email (ou deixe em branco para não alterar): ").strip()
    
    kwargs = {}
    if nome_completo:
        kwargs['nome_completo'] = nome_completo
    if email:
        kwargs['email'] = email
    
    if not kwargs:
        print("⚠️ Nenhum campo para atualizar")
        return
    
    resultado = auth.atualizar_usuario(usuario_id, **kwargs)
    
    if resultado['sucesso']:
        print(f"\n✅ {resultado['mensagem']}")
    else:
        print(f"\n❌ Erro: {resultado['mensagem']}")

def mudar_senha(auth, usuario_id):
    """Muda a senha do usuário"""
    print("\n" + "-"*50)
    print("🔐 MUDAR SENHA")
    print("-"*50)
    
    senha_atual = input("Senha atual: ").strip()
    senha_nova = input("Nova senha: ").strip()
    confirmacao = input("Confirme a nova senha: ").strip()
    
    if senha_nova != confirmacao:
        print("❌ As novas senhas não conferem")
        return
    
    resultado = auth.mudar_senha(usuario_id, senha_atual, senha_nova)
    
    if resultado['sucesso']:
        print(f"\n✅ {resultado['mensagem']}")
    else:
        print(f"\n❌ {resultado['mensagem']}")

def menu_usuario_autenticado(auth, usuario_info, token):
    """Menu do usuário autenticado"""
    while True:
        opcao = menu_usuario(auth, usuario_info)
        
        if opcao == '1':
            ver_perfil(auth, usuario_info['id'])
        elif opcao == '2':
            atualizar_perfil(auth, usuario_info['id'])
        elif opcao == '3':
            mudar_senha(auth, usuario_info['id'])
        elif opcao == '4':
            print("\n⚠️ Funcionalidade em desenvolvimento")
        elif opcao == '5':
            break
        elif opcao == '6':
            print("\n👋 Encerrando...")
            sys.exit(0)
        else:
            print("❌ Opção inválida")

def menu_principal_auth():
    """Menu principal do sistema de autenticação"""
    db = Database()
    db.connect()
    db.create_tables()
    
    auth = AuthManager(db)
    
    try:
        while True:
            opcao = menu_auth()
            
            if opcao == '1':
                registrar_usuario(auth)
            elif opcao == '2':
                fazer_login(auth)
            elif opcao == '3':
                print("\n👋 Encerrando...")
                break
            else:
                print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
    finally:
        db.disconnect()

if __name__ == '__main__':
    print("🚀 Sistema de Autenticação")
    menu_principal_auth()
