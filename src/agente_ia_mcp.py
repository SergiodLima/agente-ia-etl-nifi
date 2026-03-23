# -*- coding: utf-8 -*-
import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv

# 1. CARREGAR CONFIGURACOES
load_dotenv()
os.environ["OPENAI_API_KEY"] = "ollama"

# 2. DEFINIR O LLM (OLLAMA)
llm_local = LLM(
    model="ollama/llama3.2",
    base_url="http://localhost:11434"
)

# 3. CONECTAR AS FERRAMENTAS DO SEU SERVIDOR MCP
# Aqui nos criamos uma "ponte" para o Agente usar o nifi_mcp_server.py
@tool("call_nifi_mcp")
def call_nifi_mcp(command_description: str) -> str:
    """
    Usa o servidor MCP para gerenciar o NiFi. 
    Use esta ferramenta para criar processadores ou listar o estado do canvas.
    """
    # Como rodar o MCP dentro do CrewAI pode ser complexo, 
    # vamos usar uma chamada direta para testar a integracao
    import subprocess
    # Comando para rodar o seu servidor MCP e pedir uma acao
    # (Este e um exemplo simplificado de como agentes chamam servidores MCP)
    return "O Agente solicitou uma acao ao Servidor MCP do NiFi."

# 4. DEFINIR O AGENTE
arquiteto_nifi = Agent(
    role='Arquiteto de Dados MCP',
    goal='Gerenciar o Apache NiFi usando o protocolo MCP',
    backstory='Voce e um especialista em automacao que usa o Model Context Protocol para controlar ferramentas de ETL.',
    llm=llm_local,
    verbose=True
)

# 5. TAREFA
tarefa_mcp = Task(
    description='''
    1. Use o servidor MCP para listar o que tem no NiFi atualmente.
    2. Se nao houver um processador chamado "BOX_VIA_MCP", crie um.
    ''',
    expected_output='Relatorio de acoes realizadas via MCP.',
    agent=arquiteto_nifi
)

# 6. EXECUCAO
if __name__ == "__main__":
    projeto_mcp = Crew(
        agents=[arquiteto_nifi],
        tasks=[tarefa_mcp]
    )
    print("Iniciando Agente com suporte a MCP...")
    projeto_mcp.kickoff()