"""Fonte única de verdade sobre quais ficheiros de dados existem para análise.

Só contam os Excel presentes AGORA em Banco_de_Dados/. Logs, relatórios antigos,
backups e histórico git não são fonte de dados.
"""
import datetime
import os
import unicodedata

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(PASTA_PROJETO, "Banco_de_Dados")
PASTA_QUARENTENA = os.path.join(PASTA_PROJETO, "Entrada_Quarentena")
PASTA_RELATORIOS = os.path.join(PASTA_PROJETO, "relatorios_auditoria")
PASTA_BACKUP = os.path.join(PASTA_PROJETO, "backup_relatorios")
CAMINHO_TEMPLATE = os.path.join(PASTA_PROJETO, "templates", "template.html")
CAMINHO_INDEX = os.path.join(PASTA_PROJETO, "index.html")
CAMINHO_INVENTARIO = os.path.join(PASTA_RELATORIOS, "inventario_fontes.txt")


def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def eh_abastecimento(nome: str) -> bool:
    """Relatórios de abastecimento (km/litros) têm 'abastec' no nome e não entram na DRE financeira."""
    return "abastec" in _normalizar(nome)


def motivo_exclusao(nome: str):
    """Devolve o motivo pelo qual o ficheiro é ignorado, ou None se for fonte válida."""
    nome_l = nome.lower()
    if not nome_l.endswith((".xlsx", ".xls")):
        return "não é Excel"
    if nome.startswith("~"):
        return "ficheiro temporário/lock do Excel"
    if "copia" in _normalizar(nome):
        return "cópia ('Copia' no nome)"
    return None


def _ficheiros_na_pasta(pasta: str = PASTA_DADOS) -> list:
    if not os.path.isdir(pasta):
        return []
    return sorted(
        n for n in os.listdir(pasta)
        if os.path.isfile(os.path.join(pasta, n)) and n.lower() != "desktop.ini"
    )


def listar_ficheiros_fonte() -> list:
    """Caminhos absolutos dos Excel válidos em Banco_de_Dados.

    Os extratos "Financeiro" (período completo) vêm primeiro para prevalecerem
    na deduplicação por Nro Único.
    """
    validos = [
        n for n in _ficheiros_na_pasta()
        if motivo_exclusao(n) is None and not eh_abastecimento(n)
    ]
    validos.sort(key=lambda n: ("financeiro" not in _normalizar(n), n.lower()))
    return [os.path.join(PASTA_DADOS, n) for n in validos]


def listar_ficheiros_abastecimento() -> list:
    """Caminhos absolutos dos relatórios de abastecimento válidos em Banco_de_Dados."""
    validos = [
        n for n in _ficheiros_na_pasta()
        if motivo_exclusao(n) is None and eh_abastecimento(n)
    ]
    return [os.path.join(PASTA_DADOS, n) for n in validos]


def listar_ficheiros_quarentena() -> list:
    """Caminhos absolutos dos Excel à espera de validação em Entrada_Quarentena.

    Não são fonte de análise: só passam a contar depois de promovidos para Banco_de_Dados.
    """
    validos = [n for n in _ficheiros_na_pasta(PASTA_QUARENTENA) if motivo_exclusao(n) is None]
    return [os.path.join(PASTA_QUARENTENA, n) for n in validos]


def escrever_inventario(script: str) -> list:
    """Regrava o inventário com o conteúdo atual de Banco_de_Dados e devolve as fontes válidas."""
    fontes = listar_ficheiros_fonte()
    abastecimento = listar_ficheiros_abastecimento()
    ignorados = [
        (n, motivo_exclusao(n)) for n in _ficheiros_na_pasta() if motivo_exclusao(n) is not None
    ]

    linhas = [
        "INVENTÁRIO DE FONTES - Banco_de_Dados (estado atual da pasta)",
        f"Gerado em: {datetime.datetime.now():%Y-%m-%d %H:%M:%S} por {script}",
        "Só os ficheiros listados em 'FONTES VÁLIDAS' existem para efeito de análise.",
        "=" * 70,
        "",
        f"FONTES VÁLIDAS ({len(fontes)}):",
    ]
    for caminho in fontes:
        st = os.stat(caminho)
        modificado = datetime.datetime.fromtimestamp(st.st_mtime)
        linhas.append(f"  - {os.path.basename(caminho)} | {st.st_size} bytes | modificado {modificado:%Y-%m-%d %H:%M:%S}")
    if not fontes:
        linhas.append("  (nenhuma)")

    linhas += ["", f"FONTES OPERACIONAIS - ABASTECIMENTO / KM ({len(abastecimento)}):"]
    linhas += [f"  - {os.path.basename(c)}" for c in abastecimento] or ["  (nenhuma: CPK e Km/L ficam 'Sem dado')"]

    linhas += ["", f"IGNORADOS ({len(ignorados)}):"]
    linhas += [f"  - {n} | {motivo}" for n, motivo in ignorados] or ["  (nenhum)"]

    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    with open(CAMINHO_INVENTARIO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return fontes
