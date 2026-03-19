# -*- coding: utf-8 -*-
import nipyapi
from nipyapi import canvas, security
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

def montar_pipeline_limpo(nome_fluxo, url_api):
    try:
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        root_id = canvas.get_root_pg_id()
        root_pg = canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: EXTRAIR (InvokeHTTP) ---
        print(f"Passo 1: Criando Extrator...")
        type_http = canvas.get_processor_type('InvokeHTTP')
        proc_http = canvas.create_processor(root_pg, type_http, (400, 200), f"EXTRAIR_{nome_fluxo}")
        
        # CONFIGURAR URL E AUTO-TERMINAR RELACOES SOBRANTES
        # Aqui dizemos para o NiFi encerrar 'Original', 'Failure', etc.
        proc_http.component.config.properties['Remote URL'] = url_api
        proc_http.component.config.auto_terminated_relationships = ['Original', 'Failure', 'Retry', 'No Retry']
        canvas.update_processor(proc_http, proc_http.component.config)

        # --- PASSO 2: LOGGER (LogAttribute) ---
        print("Passo 2: Criando Logger...")
        type_log = canvas.get_processor_type('LogAttribute')
        proc_log = canvas.create_processor(root_pg, type_log, (400, 500), f"LOG_SUCESSO_{nome_fluxo}")
        
        # Auto-terminar a relacao 'success' do LogAttribute (ele e o fim da linha)
        proc_log.component.config.auto_terminated_relationships = ['success']
        canvas.update_processor(proc_log, proc_log.component.config)

        # --- PASSO 3: CONECTAR ---
        print("Passo 3: Conectando componentes...")
        canvas.create_connection(proc_http, proc_log, relationships=['Response'])

        return f"SUCESSO: Pipeline '{nome_fluxo}' pronto para rodar (SEM ERROS)!"

    except Exception as e:
        return f"ERRO: {str(e)}"

# 2. IA PENSANDO
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")
nome_ia = llm.invoke("Sugira uma palavra para um projeto de dados.").content.strip().split()[-1].upper()
url_api = "https://jsonplaceholder.typicode.com/posts"

# 3. EXECUCAO
print("-" * 30)
print(f"IA Sugeriu o nome: {nome_ia}")
resultado = montar_pipeline_limpo(nome_ia, url_api)
print(resultado)
print("-" * 30)