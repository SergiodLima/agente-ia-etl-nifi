# -*- coding: utf-8 -*-
import os
import nipyapi
from crewai import Agent, Task, Crew, LLM
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
os.environ["OPENAI_API_KEY"] = "ollama"

# 2. IA (Llama 3.2)
llm_local = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# 3. DEFINIR O AGENTE ESPECIALISTA (O Cérebro)
# Ele vai "pensar" sobre o estado do NiFi que o MCP reportar
agente_mcp = Agent(
    role='Arquiteto de Dados Autônomo',
    goal='Auditar o NiFi e criar componentes faltantes via MCP',
    backstory='Você é um engenheiro sênior que gerencia o NiFi remotamente.',
    llm=llm_local,
    verbose=True
)

# 4. TAREFA DE AUDITORIA E AÇÃO
# Vamos passar a lista que você acabou de pegar como "contexto" para a IA
canvas_atual = """
Nome: MYSQL_LOADER | ID: 02884484...
Nome: FILTRO_TECNOLOGIA | ID: 02884404...
Nome: API_PROJETO_MYSQL | ID: 028843c6...
"""

tarefa_final = Task(
    description=f'''
    O estado atual do meu NiFi é: {canvas_atual}
    
    Sua tarefa:
    1. Verifique se existe algum processador de LOG de ERRO (LogAttribute).
    2. Se não existir, use o seu conhecimento para sugerir a criação de um 
       chamado 'LOG_ERRO_AUTOMATICO'.
    ''',
    expected_output='Um relatório confirmando se o Log já existe ou se deve ser criado.',
    agent=agente_mcp
)

# 5. EXECUÇÃO
equipe = Crew(agents=[agente_mcp], tasks=[tarefa_final])
print("-" * 30)
print("INICIANDO AUDITORIA DE IA...")
resultado = equipe.kickoff()
print("\n--- RELATÓRIO DO AGENTE ---")
print(resultado)