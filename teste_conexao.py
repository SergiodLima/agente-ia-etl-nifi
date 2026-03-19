import nipyapi

# Configurações de acesso
nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False # Para evitar erro de certificado local
nipyapi.config.nifi_config.username = '7105582f-10a4-424f-9e1f-6b1b04393642'
nipyapi.config.nifi_config.password = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

try:
    # Tenta fazer o login e pegar o ID do grupo raiz
    nipyapi.security.login()
    root_id = nipyapi.canvas.get_root_pg_id()
    print(f"Sucesso! Conectado ao NiFi. ID da Raiz: {root_id}")
except Exception as e:
    print(f"Erro ao conectar: {e}")