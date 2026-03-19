# -*- coding: utf-8 -*-
import nipyapi
import urllib3

# Desativa avisos de seguranca do SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- COLOQUE AQUI OS DADOS DO LOG ---
NIFI_URL = 'https://localhost:8443/nifi-api'
NIFI_USER = '7105582f-10a4-424f-9e1f-6b1b04393642'
NIFI_PASS = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

def testar_conexao():
    # 1. Configura o host e SSL
    nipyapi.config.nifi_config.host = NIFI_URL
    nipyapi.config.nifi_config.verify_ssl = False
    
    print(f"Tentando autenticar no NiFi: {NIFI_URL}...")

    try:
        # 2. Tenta fazer o login explicitamente para pegar o Token
        # Na versao 1.5.0 a funcao eh service_login
        nipyapi.security.service_login(
            username=NIFI_USER,
            password=NIFI_PASS
        )
        
        # 3. Se o login funcionar, agora buscamos o ID da raiz
        root_id = nipyapi.canvas.get_root_pg_id()
        
        print("-" * 40)
        print("CONEXAO REALIZADA COM SUCESSO!")
        print(f"ID do Grupo Principal: {root_id}")
        print("-" * 40)
        
    except Exception as e:
        print("-" * 40)
        print(f"ERRO DE AUTENTICACAO (401): {str(e)}")
        print("Causa provavel: O usuario ou a senha estao incorretos.")
        print("Va em C:\\nifi\\logs\\nifi-app.log e busque as ultimas credenciais geradas.")
        print("-" * 40)

if __name__ == "__main__":
    testar_conexao()