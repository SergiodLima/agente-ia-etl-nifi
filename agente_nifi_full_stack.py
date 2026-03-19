# -*- coding: utf-8 -*-
import nipyapi
from nipyapi import canvas, security
import urllib3
import re # Para limpar o SQL da IA
from langchain_openai import ChatOpenAI

# 1. CONFIGURACOES NIFI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
NIFI_USER = '7105582f-10a4-424f-9e1f-6b1b04393642' 
NIFI_PASS = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

def montar_pipeline_mysql(nome_projeto, sql_limpo, url_api):
    try:
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        root_id = canvas.get_root_pg_id()
        root_pg = canvas.get_process_group(root_id, 'id')

        # --- PASSO 1: EXTRAIR (InvokeHTTP) ---
        print("Passo 1: Criando Extrator...")
        type_http = canvas.get_processor_type('InvokeHTTP')
        proc_http = canvas.create_processor(root_pg, type_http, (400, 100), f"API_{nome_projeto}")
        canvas.update_processor(proc_http, {'config': {'properties': {'Remote URL': url_api}}})
        # Auto-terminar as outras saidas
        proc_http.component.config.auto_terminated_relationships = ['Original', 'Failure', 'Retry', 'No Retry']
        canvas.update_processor(proc_http, proc_http.component.config)

        # --- PASSO 2: FILTRAR (QueryRecord) ---
        print("Passo 2: Criando Filtro (QueryRecord)...")
        type_query = canvas.get_processor_type('QueryRecord')
        proc_query = canvas.create_processor(root_pg, type_query, (400, 350), "FILTRO_IA_TECH")
        
        # Adicionamos a propriedade que criara o relacionamento 'tech_posts'
        canvas.update_processor(proc_query, {'config': {'properties': {'tech_posts': sql_limpo}}})
        # Auto-terminar o que sobrar
        proc_query.component.config.auto_terminated_relationships = ['original', 'failure']
        canvas.update_processor(proc_query, proc_query.component.config)

        # --- PASSO 3: CARREGAR NO MYSQL (PutDatabaseRecord) ---
        print("Passo 3: Criando Gravador para MySQL...")
        type_db = canvas.get_processor_type('PutDatabaseRecord')
        proc_db = canvas.create_processor(root_pg, type_db, (400, 600), "MYSQL_LOADER")
        
        # Configuracoes do MySQL
        canvas.update_processor(proc_db, {'config': {'properties': {
            'Statement Type': 'INSERT',
            'Table Name': 'tb_posts_tecnologia',
            'Database Dialect': 'MySQL'
        }}})
        proc_db.component.config.auto_terminated_relationships = ['success', 'failure', 'retry']
        canvas.update_processor(proc_db, proc_db.component.config)

        # --- CONEXOES ---
        print("Passo 4: Conectando os componentes...")
        # Conexao 1: Extrair -> Filtrar
        canvas.create_connection(proc_http, proc_query, relationships=['Response'])
        
        # Conexao 2: Filtrar -> MySQL (Usando o nome que a IA criou)
        # Forcamos a busca do processador atualizado para o NiFi "ver" o novo relacionamento
        proc_query_refreshed = canvas.get_processor(proc_query.id, 'id')
        canvas.create_connection(proc_query_refreshed, proc_db, relationships=['tech_posts'])

        return f"SUCESSO: Pipeline '{nome_projeto}' pronto no NiFi!"

    except Exception as e:
        return f"ERRO: {str(e)}"

# 3. IA PENSANDO (Llama 3.2)
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

print("-" * 40)
print("IA GERANDO LÓGICA DE NEGÓCIO...")
prompt = "Crie apenas o comando SQL (sem texto explicativo) para selecionar tudo da tabela FLOWFILE onde title ou body contenham 'technology' ou 'software'. Responda apenas o SQL."
resposta_suja = llm.invoke(prompt).content.strip()

# LIMPEZA DO SQL: Remove blocos de codigo markdown e quebras de linha
sql_ia = re.sub(r'```sql|```', '', resposta_suja).strip()
sql_ia = sql_ia.replace('\n', ' ')

print(f"SQL Limpo para o NiFi: {sql_ia}")
print("-" * 40)

# 4. EXECUCAO
if "SELECT" in sql_ia.upper():
    resultado = montar_pipeline_mysql("PROJETO_MYSQL", sql_ia, "https://jsonplaceholder.typicode.com/posts")
    print(resultado)
else:
    print("A IA nao gerou um SQL valido. Tente rodar novamente.")