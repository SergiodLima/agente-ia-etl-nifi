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

def montar_pipeline_ia(nome_fluxo, url_api):
    try:
        # Autenticacao
        print("Autenticando no NiFi...")
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        
        # Pega o grupo principal
        root_id = canvas.get_root_pg_id()
        root_pg = canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: CRIAR O EXTRATOR (InvokeHTTP) ---
        print(f"Passo 1: Criando Extrator para {url_api}...")
        type_http = canvas.get_processor_type('InvokeHTTP')
        proc_http = canvas.create_processor(root_pg, type_http, (400, 200), f"EXTRAIR_{nome_fluxo}")
        
        # CONFIGURAR URL (Modo Direto: altera o objeto e envia de volta)
        # Isso evita o erro de importar 'models' ou 'ProcessorConfigDTO'
        proc_http.component.config.properties['Remote URL'] = url_api
        canvas.update_processor(proc_http, proc_http.component.config)

        # --- PASSO 2: CRIAR O LOGGER (LogAttribute) ---
        print("Passo 2: Criando Logger de Sucesso...")
        type_log = canvas.get_processor_type('LogAttribute')
        proc_log = canvas.create_processor(root_pg, type_log, (400, 500), f"LOG_SUCESSO_{nome_fluxo}")

        # --- PASSO 3: CRIAR A CONEXAO (Setinha) ---
        print("Passo 3: Criando a conexao entre os componentes...")
        canvas.create_connection(
            source=proc_http,
            target=proc_log,
            relationships=['Response']
        )

        return f"SUCESSO: Pipeline '{nome_fluxo}' criado e conectado no NiFi!"

    except Exception as e:
        return f"ERRO NO PIPELINE: {str(e)}"

# 2. IA PENSANDO (Llama 3.2)
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

print("-" * 40)
print("IA PLANEJANDO O PROJETO...")
# Prompt ultra-curto para a IA nao dar erro de texto longo
prompt = "Responda apenas uma palavra: um nome para um projeto de dados."
nome_ia = llm.invoke(prompt).content.strip()
nome_limpo = nome_ia.split()[-1].replace('"', '').replace('.', '').upper()
url_api = "https://jsonplaceholder.typicode.com/posts"

print(f"Nome sugerido pela IA: {nome_limpo}")
print("-" * 40)

# 3. EXECUCAO
if nome_limpo:
    resultado = montar_pipeline_ia(nome_limpo, url_api)
    print(resultado)
else:
    print("IA nao retornou um nome.")