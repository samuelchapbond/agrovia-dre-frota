import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict
import pandas as pd

# Carrega a chave de segurança do arquivo .env
load_dotenv()

# 1. Configurando o cérebro do agente com o Gemini
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

# 2. O Estado (a memória onde os dados e as análises ficam salvos)
class EstadoFinanceiro(TypedDict):
    caminho_arquivo: str
    dados: dict
    divergencias: list
    relatorio: str

# 3. As tarefas (Nós) do nosso robô financeiro em modo seguro
def coletar_dados(state: EstadoFinanceiro):
    print("📈 Lendo a planilha real da pasta dados/banco_de_dados (Modo Leitura Segura)...")
    df = pd.read_excel(state["caminho_arquivo"])
    
    # Pegamos um resumo inicial (ex: 50 linhas) para análise do agente
    df_resumo = df.head(50)
    return {"dados": df_resumo.to_dict(orient="records")}

def auditar(state: EstadoFinanceiro):
    print("🔍 Analisando os lançamentos e preparando as diretrizes para o operador...")
    prompt = (
        "Você é um controller sênior. Analise estes dados contábeis/financeiros e elabore um "
        "GUIA DE CORREÇÃO PARA O OPERADOR. O relatório deve ser focado em instruir o operador "
        "sobre quais lançamentos específicos precisam ser corrigidos, ajustados ou estornados "
        "antes de atualizar o banco de dados oficial. Seja claro, objetivo e liste as ações passo a passo: "
        f"{state['dados']}"
    )
    resposta = llm.invoke(prompt)
    return {"divergencias": [resposta.content]}

def gerar_relatorio_e_salvar(state: EstadoFinanceiro):
    print("📝 Formatando o relatório para impressão e salvando na pasta saidas/relatorios_auditoria...")
    prompt = f"Com base na auditoria, formate um relatório limpo e pronto para impressão (em formato de texto estruturado) para o operador corrigir os lançamentos: {state['divergencias']}"
    relatorio = llm.invoke(prompt)
    
    # Tratamento para garantir texto puro
    conteudo = relatorio.content
    if isinstance(conteudo, list):
        texto_final = "".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in conteudo])
    else:
        texto_final = str(conteudo)
        
    # Salvando automaticamente na pasta correta com o nome exato saidas/relatorios_auditoria
    caminho_saida = "saidas/relatorios_auditoria/relatorio_correcao_operador.txt"
    os.makedirs("saidas/relatorios_auditoria", exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(texto_final)
        
    print(f"📁 Guia do operador salvo com sucesso em: {caminho_saida}")
    return {"relatorio": texto_final}

# 4. Desenhando o Fluxo Seguro (LangGraph)
workflow = StateGraph(EstadoFinanceiro)

workflow.add_node("coletar", coletar_dados)
workflow.add_node("auditar", auditar)
workflow.add_node("relatar", gerar_relatorio_e_salvar)

workflow.set_entry_point("coletar")
workflow.add_edge("coletar", "auditar")
workflow.add_edge("auditar", "relatar")
workflow.add_edge("relatar", END)

app = workflow.compile()

if __name__ == "__main__":
    arquivo_teste = "dados/banco_de_dados/mes01-2026.xlsx"
    
    if os.path.exists(arquivo_teste):
        print("🚀 Rodando o agente em modo de auditoria de apoio...\n")
        resultado = app.invoke({"caminho_arquivo": arquivo_teste})
        print("\n--- PROCESSO CONCLUÍDO COM SUCESSO ---")
        print("O arquivo de texto foi gerado dentro da pasta 'saidas/relatorios_auditoria'!")
    else:
        print(f"⚠️ Atenção: Não encontramos o arquivo no caminho '{arquivo_teste}'.")


        
          