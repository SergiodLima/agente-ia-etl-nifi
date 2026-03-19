# -*- coding: utf-8 -*-
import nipyapi
import urllib3
from langchain_openai import ChatOpenAI

# 1. CONFIGURACOES NIFI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- COLOQUE SEU USUARIO E SENHA REAIS ---
NIFI_USER = '7105582f-10a4-424f-9e1f-6b1b04393642' 
NIFI_PASS = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

def montar_pipeline_ia(nome_fluxo, url_api):
    try:
        # Autenticacao
        nipyapi.security.service_login(username=NIFI_USER, password=NIFI_PASS)
        root_id = nipyapi.canvas.get_root_pg_id()
        root_pg = nipyapi.canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: CRIAR O EXTRATOR (InvokeHTTP) ---
        print(f"Passo 1: Criando Extrator ({url_api})...")
        type_http = nipyapi.canvas.get_processor_type('InvokeHTTP')
        proc_http = nipyapi.canvas.create_processor(root_pg, type_http, (400, 200), f"EXTRAIR_{nome_fluxo}")
        
        # ATUALIZAR URL (Usando dicionario para evitar erro de 'models')
        nipyapi.canvas.update_processor(
            proc_http,
            {'config': {'properties': {'Remote URL': url_api}}}
        )

        # --- PASSO 2: CRIAR O LOGGER (LogAttribute) ---
        print("Passo 2: Criando Logger de Sucesso...")
        type_log = nipyapi.canvas.get_processor_type('LogAttribute')
        proc_log = nipyapi.canvas.create_processor(root_pg, type_log, (400, 500), f"LOG_SUCESSO_{nome_fluxo}")

        # --- PASSO 3: CRIAR A CONEXAO (A "Setinha") ---
        print("Passo 3: Conectando componentes...")
        # Conectamos a saida 'Response' do HTTP para a entrada do Log
        nipyapi.canvas.create_connection(
            source=proc_http,
            target=proc_log,
            relationships=['Response']
        )

        return f"Pipeline '{nome_fluxo}' finalizado com sucesso no NiFi!"

    except Exception as e:
        return f"ERRO NO PIPELINE: {str(e)}"

# 2. IA PENSANDO
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

print("-" * 40)
print("IA PLANEJANDO O PROJETO...")
# Pedindo apenas o nome para evitar que a IA divague muito
nome_ia = llm.invoke("Sugira um nome tecnico curto em uma palavra para um projeto de dados.").content.strip()
nome_limpo = "".join(filter(str.isalnum, nome_ia)) # Remove pontos e espacos
url_api = "https://jsonplaceholder.typicode.com/posts" # API estável para teste

print(f"Nome sugerido pela IA: {nome_limpo}")
print("-" * 40)

# 3. EXECUCAO
if nome_limpo:
    resultado = montar_pipeline_ia(nome_limpo, url_api)
    print(resultado)
else:
    print("Falha ao obter nome da IA.")