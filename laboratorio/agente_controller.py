import os
import re
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from fontes_dados import PASTA_PROJETO, PASTA_RELATORIOS, listar_ficheiros_fonte
from regras_lancamento import carregar_excel_com_cabecalho, configurar_stdout_utf8, limpar_texto

configurar_stdout_utf8()

# Carrega a chave de segurança do arquivo .env
load_dotenv(os.path.join(PASTA_PROJETO, ".env"))

LINHAS_POR_FICHEIRO = 50

# Só estas colunas saem do computador para o Gemini. Nomes de parceiros, CNPJ/CPF,
# dados bancários e utilizadores ficam de fora; o Histórico sai com nomes e documentos mascarados.
COLUNAS_PERMITIDAS = [
    "historico",
    "nro unico",
    "parceiro",
    "dt. negociacao",
    "dt. vencimento",
    "data baixa",
    "valor liquido",
    "receita/despesa",
    "descricao (natureza)",
    "descricao (centro de resultado)",
    "descricao (tipo de operacao)",
    "marca [placa]",
    "veiculo",
    "provisao",
]

CAMINHO_SAIDA = os.path.join(PASTA_RELATORIOS, "ia_relatorio_correcao_operador.txt")

# 1. Configurando o cérebro do agente com o Gemini
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

# 2. O Estado (a memória onde os dados e as análises ficam salvos)
class EstadoFinanceiro(TypedDict):
    caminhos_arquivos: list
    dados: list
    divergencias: list
    relatorio: str


COLUNAS_COM_NOMES = ["nome parceiro (parceiro)", "nome (usuario)", "nome (usuario baixa)", "apelido"]
SUFIXO_EMPRESA = re.compile(r"\s+(LTDA|S\.?A\.?|ME|EPP|EIRELI)\.?$", re.IGNORECASE)
PADRAO_DOCUMENTO = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
# Pessoas citadas só no texto (ex.: "ANDERSON AUTORIZOU", "GUILHERME DA CVT RETIROU", "NF EM NOME DO GILSON").
PADRAO_PESSOA_ACAO = re.compile(
    r"\b[A-ZÀ-Ú]+(?=\s+(?:DA\s+\S+\s+)?(?:AUTORIZOU|SOLICITOU|RETIROU|APROVOU|PEDIU|LIGOU|PAGOU|LEVOU|BUSCOU|ENTREGOU)\b)"
)
PADRAO_PESSOA_CONTEXTO = re.compile(r"\b(NOME D[OA]|MOTORISTA)\s+[A-ZÀ-Ú]+")


def variantes_nome(nome: str) -> set:
    """'PEDRO HENRIQUE MORALI DE ALBUQUERQUE' também aparece no Histórico como 'PEDRO HENRIQUE MORALI'."""
    nome = SUFIXO_EMPRESA.sub("", nome.strip())
    base = nome.split(" - ")[0].strip()
    palavras = base.split()
    variantes = {nome, base}
    variantes.update(" ".join(palavras[:n]) for n in range(2, len(palavras)))
    return {v for v in variantes if len(v) >= 4}


def padrao_nomes(df: pd.DataFrame):
    colunas = {limpar_texto(c).lower(): c for c in df.columns}
    variantes = set()
    for chave in COLUNAS_COM_NOMES:
        if chave in colunas:
            for valor in df[colunas[chave]].dropna().astype(str).unique():
                if not valor.startswith("<"):
                    variantes |= variantes_nome(valor)
    variantes |= {n.strip() for n in os.getenv("NOMES_MASCARAR", "").split(",") if len(n.strip()) >= 3}
    if not variantes:
        return None
    alternativas = "|".join(re.escape(v) for v in sorted(variantes, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternativas})(?!\w)", re.IGNORECASE)


def anonimizar(texto, padrao):
    if pd.isna(texto):
        return texto
    texto = str(texto)
    # Nomes completos primeiro, para as regras de contexto não cortarem um nome ao meio.
    if padrao:
        texto = padrao.sub("[NOME]", texto)
    texto = PADRAO_PESSOA_ACAO.sub("[NOME]", texto)
    texto = PADRAO_PESSOA_CONTEXTO.sub(r"\1 [NOME]", texto)
    return PADRAO_DOCUMENTO.sub("[DOC]", texto)


def colunas_seguras(df: pd.DataFrame) -> pd.DataFrame:
    nomes = {limpar_texto(c).lower(): c for c in df.columns}
    seguro = df[[nomes[n] for n in COLUNAS_PERMITIDAS if n in nomes]].copy()
    if "historico" in nomes:
        padrao = padrao_nomes(df)
        seguro[nomes["historico"]] = seguro[nomes["historico"]].map(lambda t: anonimizar(t, padrao))
    return seguro


# 3. As tarefas (Nós) do nosso robô financeiro em modo seguro
def coletar_dados(state: EstadoFinanceiro):
    print("📈 Lendo as planilhas válidas de dados/banco_de_dados (Modo Leitura Segura)...")
    registos = []
    for caminho in state["caminhos_arquivos"]:
        df, _ = carregar_excel_com_cabecalho(caminho)
        df_resumo = colunas_seguras(df).head(LINHAS_POR_FICHEIRO).copy()
        df_resumo.insert(0, "Ficheiro", os.path.basename(caminho))
        registos += df_resumo.to_dict(orient="records")
        print(f"   - {os.path.basename(caminho)}: {len(df_resumo)} linhas, {df_resumo.shape[1] - 1} colunas enviadas")
    return {"dados": registos}

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

    aviso = "GERADO POR IA (laboratorio/agente_controller.py) - NÃO É O VEREDITO DO AUDITOR OFICIAL\n\n"
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    with open(CAMINHO_SAIDA, "w", encoding="utf-8") as f:
        f.write(aviso + texto_final)
        
    print(f"📁 Guia do operador salvo com sucesso em: {CAMINHO_SAIDA}")
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
    fontes = listar_ficheiros_fonte()

    if fontes:
        print("🚀 Rodando o agente em modo de auditoria de apoio...\n")
        resultado = app.invoke({"caminhos_arquivos": fontes})
        print("\n--- PROCESSO CONCLUÍDO COM SUCESSO ---")
        print(f"O arquivo de texto foi gerado em '{CAMINHO_SAIDA}'!")
    else:
        print("⚠️ Atenção: não há Excel válido em dados/banco_de_dados.")
