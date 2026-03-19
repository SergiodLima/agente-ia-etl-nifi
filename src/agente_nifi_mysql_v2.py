# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv # Adicione esta linha

import nipyapi
from nipyapi import canvas, security
import urllib3
import re
from langchain_openai import ChatOpenAI

# 1. CONFIGURACOES NIFI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Carrega as senhas do arquivo .env escondido
load_dotenv() 

# Pega as senhas das variaveis de ambiente
NIFI_USER = os.getenv('NIFI_USER')
NIFI_PASS = os.getenv('NIFI_PASS')

nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

def montar_pipeline_mysql(nome_projeto, sql_ia, url_api):
    try:
        # Autenticacao
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        root_id = canvas.get_root_pg_id()
        root_pg = canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: EXTRAIR (InvokeHTTP) ---
        print("Passo 1: Criando Extrator...")
        type_http = canvas.get_processor_type('InvokeHTTP')
        proc_http = canvas.create_processor(root_pg, type_http, (400, 100), f"API_{nome_projeto}")
        
        # Modo Seguro: Altera o objeto interno e envia de volta
        conf_http = proc_http.component.config
        conf_http.properties = {'Remote URL': url_api}
        conf_http.auto_terminated_relationships = ['Original', 'Failure', 'Retry', 'No Retry']
        canvas.update_processor(proc_http, conf_http)

        # --- PASSO 2: FILTRAR (QueryRecord) ---
        print("Passo 2: Criando Filtro Inteligente...")
        type_query = canvas.get_processor_type('QueryRecord')
        proc_query = canvas.create_processor(root_pg, type_query, (400, 350), "FILTRO_TECNOLOGIA")
        
        # Adiciona a query da IA e encerra o resto
        conf_query = proc_query.component.config
        conf_query.properties = {'tech_posts': sql_ia}
        conf_query.auto_terminated_relationships = ['original', 'failure']
        canvas.update_processor(proc_query, conf_query)

        # --- PASSO 3: CARREGAR NO MYSQL (PutDatabaseRecord) ---
        print("Passo 3: Criando Gravador MySQL...")
        type_db = canvas.get_processor_type('PutDatabaseRecord')
        proc_db = canvas.create_processor(root_pg, type_db, (400, 600), "MYSQL_LOADER")
        
        # Configuracoes do MySQL
        conf_db = proc_db.component.config
        conf_db.properties = {
            'Statement Type': 'INSERT',
            'Table Name': 'tb_posts_tecnologia',
            'Database Dialect': 'MySQL'
        }
        conf_db.auto_terminated_relationships = ['success', 'failure', 'retry']
        canvas.update_processor(proc_db, conf_db)

        # --- CONEXOES ---
        print("Passo 4: Criando Linhagem de Dados...")
        canvas.create_connection(proc_http, proc_query, relationships=['Response'])
        
        # Recarrega o processador para o NiFi validar o relacionamento 'tech_posts'
        proc_query_new = canvas.get_processor(proc_query.id, 'id')
        canvas.create_connection(proc_query_new, proc_db, relationships=['tech_posts'])

        return f"SUCESSO: Pipeline {nome_projeto} criado!"

    except Exception as e:
        return f"ERRO NO PIPELINE: {str(e)}"

# 3. IA PENSANDO
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

print("-" * 30)
print("IA GERANDO LOGICA DE NEGOCIO...")
prompt = "SQL SELECT FROM FLOWFILE where title like software. Only the SQL command."
sql_ia = llm.invoke(prompt).content.strip()
sql_limpo = re.sub(r'```sql|```|`', '', sql_ia).strip().replace('\n', ' ')

print(f"SQL Limpo: {sql_limpo}")
print("-" * 30)

# 4. EXECUCAO
if "SELECT" in sql_limpo.upper():
    resultado = montar_pipeline_mysql("PROJETO_MYSQL", sql_limpo, "https://jsonplaceholder.typicode.com/posts")
    print(resultado)
else:
    print("IA nao gerou SQL valido.")