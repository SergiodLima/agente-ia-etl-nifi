# -*- coding: utf-8 -*-
import os, json, re, urllib3, nipyapi
from nipyapi import canvas, security
from fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 1. SETUP E SEGURANCA
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '..', '.env'))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NIFI_USER = os.getenv('NIFI_USER')
NIFI_PASS = os.getenv('NIFI_PASS')
nipyapi.config.nifi_config.host = 'https://localhost:8443/nifi-api'
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.nifi_config.username = NIFI_USER
nipyapi.config.nifi_config.password = NIFI_PASS

mcp = FastMCP("NiFi-Smart-Builder")
llm = ChatOpenAI(model='llama3.2', base_url="http://localhost:11434/v1", api_key="ollama")

def do_login():
    try:
        security.service_login(username=NIFI_USER, password=NIFI_PASS)
        return True
    except: return False

@mcp.tool()
def clear_nifi_canvas() -> str:
    """Limpa o NiFi para a demo."""
    if not do_login(): return "Erro login."
    try:
        root_id = canvas.get_root_pg_id()
        canvas.schedule_process_group(root_id, False)
        for c in canvas.list_all_connections(): canvas.delete_connection(c, purge=True)
        for p in canvas.list_all_processors(): canvas.delete_processor(p, force=True)
        return "Canvas limpo!"
    except Exception as e: return f"Erro ao limpar: {str(e)}"

@mcp.tool()
def ai_build_pipeline(instrucao: str) -> str:
    """Cria o fluxo exato baseado na ordem, usando exemplos para guiar a IA."""
    try:
        if not do_login(): return "Erro login."
        
        MAP = {
            "arquivo": "GetFile", "api": "InvokeHTTP",
            "banco": "PutDatabaseRecord", "log": "LogAttribute",
            "filtro": "QueryRecord"
        }

        # Prompt com exemplos para evitar alucinacoes
        prompt = f"""
        Traduza a instrucao: '{instrucao}' em termos separados por virgula.
        Use apenas: arquivo, api, banco, log, filtro.
        Exemplo: 'arquivo para log' -> arquivo, log
        Resposta:"""

        resposta = llm.invoke(prompt).content.strip().lower()
        termos = [t.strip() for t in resposta.split(',') if t.strip() in MAP]
        
        if not termos: return f"IA nao entendeu os tipos. Resposta: {resposta}"

        root_pg = canvas.get_process_group(canvas.get_root_pg_id(), 'id')
        criados = []

        # IDs Reais do seu NiFi
        READER_ID = '028c3e93-019d-1000-3082-ff0a7185768e'
        WRITER_ID = '028c830f-019d-1000-8ff3-b304528a3666'
        POOL_ID   = '028d9419-019d-1000-7f53-2cdf25ed6eaa'

        for i, termo in enumerate(termos):
            tipo_nifi = MAP[termo]
            nome = f"{tipo_nifi}_{i+1}"
            t_obj = canvas.get_processor_type(tipo_nifi)
            p = canvas.create_processor(root_pg, t_obj, (400, 100 + (i*250)), nome)
            
            config = p.component.config
            if tipo_nifi == "GetFile":
                config.properties['Input Directory'] = 'C:/nifi/entrada'
            elif tipo_nifi == "InvokeHTTP":
                config.properties['Remote URL'] = 'https://jsonplaceholder.typicode.com/posts'
            elif tipo_nifi == "QueryRecord":
                config.properties['Record Reader'] = READER_ID
                config.properties['Record Writer'] = WRITER_ID
                config.properties['output_ia'] = 'SELECT * FROM FLOWFILE'
            elif tipo_nifi == "PutDatabaseRecord":
                config.properties['Record Reader'] = READER_ID
                config.properties['Database Connection Pooling Service'] = POOL_ID
                config.properties['Table Name'] = 'tb_posts_tecnologia'
                config.properties['Statement Type'] = 'INSERT'

            # Configura auto-terminate para evitar erros amarelos
            config.auto_terminated_relationships = ['failure', 'original', 'retry', 'no retry', 'success']
            canvas.update_processor(p, config)
            criados.append({"obj": p, "tipo": tipo_nifi})

        # Conectar em cadeia (1 -> 2 -> 3...)
        for i in range(len(criados) - 1):
            src, tgt = criados[i], criados[i+1]
            rel = "Response" if src['tipo'] == "InvokeHTTP" else "success"
            
            # Garante que a saida nao esta encerrada antes de conectar
            conf = src['obj'].component.config
            if rel in conf.auto_terminated_relationships:
                conf.auto_terminated_relationships.remove(rel)
                canvas.update_processor(src['obj'], conf)
            
            canvas.create_connection(src['obj'], tgt['obj'], relationships=[rel])

        return f"Sucesso! Pipeline criado: {' -> '.join(termos)}"
    except Exception as e:
        return f"Erro tecnico: {str(e)}"

@mcp.tool()
def analyze_and_suggest() -> str:
    """Analisa o fluxo e sugere melhorias."""
    try:
        if not do_login(): return "Erro login."
        procs = canvas.list_all_processors()
        state = "\n".join([f"Proc: {p.component.name}" for p in procs])
        prompt = f"Sugira 2 melhorias para este NiFi em portugues:\n{state}"
        res = llm.invoke(prompt).content.strip()
        return f"Sugestoes da IA:\n{res}"
    except Exception as e: return f"Erro: {str(e)}"

if __name__ == "__main__":
    mcp.run()