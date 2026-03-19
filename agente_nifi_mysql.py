# -*- coding: utf-8 -*-
import nipyapi
from nipyapi import canvas, security
import urllib3
from langchain_openai import ChatOpenAI

# 1. CONFIGURACOES NIFI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
NIFI_USER = '7105582f-10a4-424f-9e1f-6b1b04393642' 
NIFI_PASS = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

def montar_pipeline_mysql(nome_projeto, query_sql, url_api):
    try:
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        root_id = canvas.get_root_pg_id()
        root_pg = canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: EXTRAIR (InvokeHTTP) ---
        print("Passo 1: Criando Extrator da API...")
        type_http = canvas.get_processor_type('InvokeHTTP')
        proc_http = canvas.create_processor(root_pg, type_http, (400, 100), f"API_{nome_projeto}")
        proc_http.component.config.properties['Remote URL'] = url_api
        proc_http.component.config.auto_terminated_relationships = ['Original', 'Failure', 'Retry', 'No Retry']
        canvas.update_processor(proc_http, proc_http.component.config)

        # --- PASSO 2: FILTRAR (QueryRecord) ---
        print("Passo 2: Criando Filtro de Tecnologia (SQL Calcite)...")
        type_query = canvas.get_processor_type('QueryRecord')
        proc_query = canvas.create_processor(root_pg, type_query, (400, 350), f"FILTRAR_TECNOLOGIA")
        
        # A IA definiu esta query para filtrar o JSON
        proc_query.component.config.properties['tech_posts'] = query_sql
        proc_query.component.config.auto_terminated_relationships = ['original', 'failure']
        canvas.update_processor(proc_query, proc_query.component.config)

        # --- PASSO 3: CARREGAR NO MYSQL (PutDatabaseRecord) ---
        print("Passo 3: Criando Gravador para MySQL...")
        type_db = canvas.get_processor_type('PutDatabaseRecord')
        proc_db = canvas.create_processor(root_pg, type_db, (400, 600), f"MYSQL_LOADER")
        
        # Configuracoes do MySQL
        proc_db.component.config.properties['Statement Type'] = 'INSERT'
        proc_db.component.config.properties['Table Name'] = 'tb_posts_tecnologia'
        proc_db.component.config.properties['Database Dialect'] = 'MySQL'
        proc_db.component.config.auto_terminated_relationships = ['success', 'failure', 'retry']
        canvas.update_processor(proc_db, proc_db.component.config)

        # --- CONEXOES ---
        print("Passo 4: Criando Linhagem de Dados...")
        canvas.create_connection(proc_http, proc_query, relationships=['Response'])
        canvas.create_connection(proc_query, proc_db, relationships=['tech_posts'])

        return f"SUCESSO: Pipeline para MySQL '{nome_projeto}' pronto!"

    except Exception as e:
        return f"ERRO: {str(e)}"

# 3. IA PENSANDO (Llama 3.2)
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

print("-" * 40)
print("IA GERANDO LÓGICA DE NEGÓCIO...")
# Query de filtragem para o NiFi (Apache Calcite)
prompt_filtro = "Crie um comando SQL para filtrar registros onde 'title' ou 'body' contenham 'technology', 'software' ou 'computer'. Use a tabela FLOWFILE."
sql_ia = llm.invoke(prompt_filtro).content.strip()

print(f"Lógica de Filtro da IA: {sql_ia}")
print("-" * 40)

# 4. EXECUCAO
resultado = montar_pipeline_mysql("PROJETO_MYSQL_TECH", sql_ia, "https://jsonplaceholder.typicode.com/posts")
print(resultado)