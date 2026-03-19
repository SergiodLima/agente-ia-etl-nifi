# -*- coding: utf-8 -*-
import nipyapi
import urllib3
import json
from langchain_openai import ChatOpenAI

# 1. CONFIGURACOES NIFI
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- COLOQUE SEU USUARIO E SENHA REAIS AQUI ---
NIFI_USER = '7105582f-10a4-424f-9e1f-6b1b04393642' 
NIFI_PASS = 'K9XuA0YhHNvCGF1xjXivUWYHXJ5zsVNU'

nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

def criar_box_nifi(nome):
    try:
        # Autentica e pega o token
        nipyapi.security.service_login(username=NIFI_USER, password=NIFI_PASS)
        
        # Pega o ID do grupo raiz
        root_id = nipyapi.canvas.get_root_pg_id()
        # Pega o objeto do grupo raiz
        root_pg = nipyapi.canvas.get_process_group(root_id, 'id')
        
        # Pega o tipo do processador InvokeHTTP
        proc_type = nipyapi.canvas.get_processor_type('InvokeHTTP')
        
        # Chamada POSICIONAL (sem nomes de parametros para evitar erro de 'type')
        # Ordem: (Grupo Pai, Tipo do Processador, Localizacao, Nome)
        new_proc = nipyapi.canvas.create_processor(
            root_pg,
            proc_type,
            (600, 400),
            nome
        )
        
        return f"SUCESSO: Processador '{nome}' criado com ID: {new_proc.id}"
    except Exception as e:
        return f"ERRO NA CRIACAO: {str(e)}"

# 2. IA PENSANDO (Usando Llama 3.2 que ja esta no seu Ollama)
llm = ChatOpenAI(
    model='llama3.2',
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

pergunta = "Preciso de um nome criativo e profissional para um processo de ETL que le dados de uma API de vendas. Responda apenas o nome."

print("-" * 30)
print("IA PENSANDO NO NOME DO PROCESSO...")
resposta_ia = llm.invoke(pergunta).content.strip()
# Limpando aspas se a IA colocar
nome_final = resposta_ia.replace('"', '').replace("'", "")

print(f"IA sugeriu o nome: {nome_final}")
print("-" * 30)

# 3. EXECUCAO
if nome_final:
    print("Enviando comando para o NiFi...")
    resultado = criar_box_nifi(nome_final)
    print(resultado)
else:
    print("IA nao conseguiu sugerir um nome.")