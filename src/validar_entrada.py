"""Quarentena de lançamentos: valida os Excel em dados/entrada_quarentena/ antes de entrarem em dados/banco_de_dados/.

Uso:
    python validar_entrada.py                 # valida, gera pendências e promove ficheiros sem bloqueantes
    python validar_entrada.py --sem-promover  # só valida e gera pendências (não move nada)

Saídas em saidas/relatorios_auditoria/: pendencias_lancamentos.xlsx, pendencias_lancamentos.html, log_quarentena.txt.
A tela com as pendências é online e exige login (acesso/quarentena.html); os dados vão para o Firestore
(src/quarentena_online.py). O pendencias_lancamentos.html local é só um atalho, sem dados.
A correção é sempre feita no Sankhya, com nova exportação; o Excel exportado não é editado à mão.
"""
import argparse
import datetime
import html
import os
import shutil
import sys

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from fontes_dados import PASTA_DADOS, PASTA_QUARENTENA, PASTA_RELATORIOS, URL_LOGIN_QUARENTENA, listar_ficheiros_quarentena
from quarentena_online import calcular_resumo, publicar_quarentena
from regras_lancamento import AVISO, BLOQUEANTE, configurar_stdout_utf8, validar_ficheiro

CAMINHO_XLSX = os.path.join(PASTA_RELATORIOS, "pendencias_lancamentos.xlsx")
CAMINHO_HTML = os.path.join(PASTA_RELATORIOS, "pendencias_lancamentos.html")
CAMINHO_LOG = os.path.join(PASTA_RELATORIOS, "log_quarentena.txt")
PASTA_SUBSTITUIDOS = os.path.join(PASTA_QUARENTENA, "substituidos")

STATUS_OPCOES = ["Pendente", "Corrigido no Sankhya", "Justificado"]

COLUNAS = [
    ("Severidade", "severidade", 13),
    ("Regra", "regra", 28),
    ("Ficheiro", "ficheiro", 30),
    ("Linha Excel", "linha", 8),
    ("Nro Único", "nr_unico", 12),
    ("Data", "data", 11),
    ("Parceiro", "parceiro", 30),
    ("Operador", "operador", 20),
    ("Valor (R$)", "valor", 14),
    ("Placa ERP", "placa_erp", 26),
    ("Histórico", "historico", 45),
    ("Detalhe", "detalhe", 28),
    ("Ação esperada", "acao", 55),
    ("Status", "status", 20),
    ("Observação do operador", "observacao", 40),
]

PREENCHIMENTO = {
    BLOQUEANTE: PatternFill("solid", fgColor="FDE2E2"),
    AVISO: PatternFill("solid", fgColor="FFF4D6"),
}


def chave_pendencia(erro: dict) -> tuple:
    if erro["nr_unico"] != "N/D":
        return (erro["nr_unico"], erro["regra"])
    return (erro["ficheiro"], str(erro["linha"]), erro["regra"])


def ler_status_anteriores() -> dict:
    """Status e Observação já preenchidos pelo operador na planilha anterior."""
    if not os.path.isfile(CAMINHO_XLSX):
        return {}
    try:
        ws = load_workbook(CAMINHO_XLSX, read_only=True)["Pendências"]
    except Exception as exc:
        print(f"[AVISO] Não foi possível ler a planilha anterior ({exc}); Status/Observação recomeçam.")
        return {}
    linhas = ws.iter_rows(values_only=True)
    cabecalho = [str(c) if c is not None else "" for c in next(linhas, [])]
    idx = {nome: i for i, nome in enumerate(cabecalho)}
    necessarias = ["Nro Único", "Regra", "Ficheiro", "Linha Excel", "Status", "Observação do operador"]
    if any(n not in idx for n in necessarias):
        return {}
    anteriores = {}
    for linha in linhas:
        def campo(nome):
            v = linha[idx[nome]]
            return "" if v is None else str(v)
        erro = {"nr_unico": campo("Nro Único") or "N/D", "regra": campo("Regra"),
                "ficheiro": campo("Ficheiro"), "linha": campo("Linha Excel")}
        anteriores[chave_pendencia(erro)] = (campo("Status"), campo("Observação do operador"))
    return anteriores


def gravar_xlsx(erros: list, resumo_ficheiros: list, gerado_em: str) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Pendências"
    ws.append([c[0] for c in COLUNAS])
    for celula in ws[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor="1B4D3E")
        celula.alignment = Alignment(vertical="center", wrap_text=True)

    col_valor = [c[1] for c in COLUNAS].index("valor") + 1
    for erro in erros:
        ws.append([erro.get(campo, "") if campo != "valor" else erro.get("valor") for _, campo, _ in COLUNAS])
        linha = ws.max_row
        for celula in ws[linha]:
            celula.fill = PREENCHIMENTO[erro["severidade"]]
            celula.alignment = Alignment(vertical="top", wrap_text=True)
        ws.cell(row=linha, column=col_valor).number_format = '#,##0.00;[Red]-#,##0.00'

    for i, (_, _, largura) in enumerate(COLUNAS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura
    ws.freeze_panes = "A2"
    ultima_col = get_column_letter(len(COLUNAS))
    ws.auto_filter.ref = f"A1:{ultima_col}{max(ws.max_row, 2)}"

    col_status = get_column_letter([c[1] for c in COLUNAS].index("status") + 1)
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUS_OPCOES) + '"', allow_blank=False)
    dv.error = "Escolha um status da lista."
    dv.prompt = "Pendente / Corrigido no Sankhya / Justificado"
    ws.add_data_validation(dv)
    dv.add(f"{col_status}2:{col_status}{max(ws.max_row, 2) + 200}")

    wr = wb.create_sheet("Resumo")
    wr.append(["Quarentena de lançamentos - gerado em", gerado_em])
    wr.append([])
    wr.append(["Ficheiro", "Bloqueantes", "Avisos", "Decisão"])
    for celula in wr[3]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill("solid", fgColor="1B4D3E")
    for r in resumo_ficheiros:
        wr.append([r["ficheiro"], r["bloqueantes"], r["avisos"], r["decisao"]])
    wr.append([])
    wr.append(["Bloqueante: impede a entrada em dados/banco_de_dados até corrigir no Sankhya e reexportar."])
    wr.append(["Aviso: não impede; confirmar e marcar Status (Corrigido no Sankhya / Justificado)."])
    for col, largura in zip("ABCD", (45, 12, 10, 60)):
        wr.column_dimensions[col].width = largura

    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    try:
        wb.save(CAMINHO_XLSX)
        return CAMINHO_XLSX
    except PermissionError:
        alternativo = CAMINHO_XLSX.replace(".xlsx", f"_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx")
        wb.save(alternativo)
        print(f"[AVISO] {os.path.basename(CAMINHO_XLSX)} está aberto no Excel; gravado em {os.path.basename(alternativo)}.")
        return alternativo


def promover(caminho: str) -> str:
    """Move o ficheiro para dados/banco_de_dados; um homónimo existente vai para substituidos/."""
    nome = os.path.basename(caminho)
    destino = os.path.join(PASTA_DADOS, nome)
    detalhe = ""
    if os.path.exists(destino):
        os.makedirs(PASTA_SUBSTITUIDOS, exist_ok=True)
        antigo = os.path.join(PASTA_SUBSTITUIDOS, f"{datetime.datetime.now():%Y%m%d_%H%M%S}_{nome}")
        shutil.move(destino, antigo)
        detalhe = f" (versão anterior movida para substituidos/{os.path.basename(antigo)})"
    shutil.move(caminho, destino)
    return f"PROMOVIDO para dados/banco_de_dados{detalhe}"


def registar_log(linhas: list) -> None:
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    with open(CAMINHO_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n\n")


def gerar_atalho_html(gerado_em: str, envio_ok: bool, mensagem_envio: str) -> None:
    """Grava o HTML local sem nenhum dado financeiro: só o atalho para a tela online com login."""
    if envio_ok:
        estado = f'<p class="ok">Tela online atualizada em {html.escape(gerado_em)}.</p>'
    else:
        estado = (f'<p class="falha">A tela online NÃO foi atualizada em {html.escape(gerado_em)}: '
                  f'{html.escape(mensagem_envio)}.<br>Enquanto isso, as pendências estão em '
                  f'<code>pendencias_lancamentos.xlsx</code>, nesta mesma pasta.</p>')
    pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agrovia - Quarentena de Lançamentos</title>
<style>
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f1e17; color: #f8fafc;
           margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 15px; box-sizing: border-box; }}
    .card {{ background: #162c22; border: 1px solid rgba(46, 204, 113, 0.25); border-radius: 12px; padding: 24px; max-width: 520px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
    h1 {{ margin: 0 0 10px; font-size: 20px; color: #a3e635; }}
    p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
    .ok {{ color: #34d399; }}
    .falha {{ color: #fbbf24; }}
    code {{ color: #fbbf24; }}
    a.btn {{ display: inline-block; margin-top: 8px; background: #a3e635; color: #0f1e17; padding: 12px 18px; border-radius: 8px;
            font-weight: 700; text-decoration: none; }}
</style>
</head>
<body>
<div class="card">
    <h1>Agrovia - Quarentena de Lançamentos</h1>
    <p>A tela de pendências passou a ser online e só abre com login de usuário cadastrado pelo ADM.</p>
    {estado}
    <a class="btn" href="{html.escape(URL_LOGIN_QUARENTENA)}">Abrir a quarentena (login)</a>
</div>
</body>
</html>
"""
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    with open(CAMINHO_HTML, "w", encoding="utf-8") as f:
        f.write(pagina)


def main() -> int:
    configurar_stdout_utf8()
    parser = argparse.ArgumentParser(description="Valida os Excel em dados/entrada_quarentena antes de entrarem em dados/banco_de_dados.")
    parser.add_argument("--sem-promover", action="store_true", help="só valida e gera pendências; não move ficheiros")
    args = parser.parse_args()

    os.makedirs(PASTA_QUARENTENA, exist_ok=True)
    agora = datetime.datetime.now()
    gerado_em = f"{agora:%d/%m/%Y às %H:%M}"

    print("=" * 100)
    print(" AGROVIA - QUARENTENA DE LANÇAMENTOS" + (" (SIMULAÇÃO: --sem-promover)" if args.sem_promover else ""))
    print("=" * 100)

    ficheiros = listar_ficheiros_quarentena()
    if not ficheiros:
        print(" Nenhum ficheiro Excel em dados/entrada_quarentena/. Nada a validar.")
        return 0

    anteriores = ler_status_anteriores()
    erros_todos = []
    resumo_ficheiros = []
    log = [f"[{agora:%Y-%m-%d %H:%M:%S}] validar_entrada.py" + (" --sem-promover" if args.sem_promover else "")]

    for caminho in ficheiros:
        nome = os.path.basename(caminho)
        try:
            erros = validar_ficheiro(caminho)
        except Exception as exc:
            print(f" [X] {nome}: não foi possível ler ({exc}).")
            resumo_ficheiros.append({"ficheiro": nome, "bloqueantes": 1, "avisos": 0, "decisao": f"RETIDO: ficheiro ilegível ({exc})"})
            log.append(f"  - {nome} | RETIDO | ficheiro ilegível: {exc}")
            continue

        for erro in erros:
            status, observacao = anteriores.get(chave_pendencia(erro), ("", ""))
            erro["status"] = status or "Pendente"
            erro["observacao"] = observacao
        erros_todos.extend(erros)

        n_bloq = sum(1 for e in erros if e["severidade"] == BLOQUEANTE)
        n_aviso = len(erros) - n_bloq
        if n_bloq:
            decisao = f"RETIDO: {n_bloq} bloqueante(s) - corrigir no Sankhya e reexportar"
        elif args.sem_promover:
            decisao = "APTO (simulação: não movido)"
        else:
            try:
                decisao = promover(caminho)
            except OSError as exc:
                decisao = f"RETIDO: falha ao mover ({exc})"
        resumo_ficheiros.append({"ficheiro": nome, "bloqueantes": n_bloq, "avisos": n_aviso, "decisao": decisao})
        log.append(f"  - {nome} | bloqueantes={n_bloq} avisos={n_aviso} | {decisao}")
        print(f" {nome}: {n_bloq} bloqueante(s), {n_aviso} aviso(s) -> {decisao}")

    caminho_xlsx = gravar_xlsx(erros_todos, resumo_ficheiros, gerado_em)

    modo = "Simulação (--sem-promover): nada foi movido" if args.sem_promover else "Execução real"
    try:
        mensagem_envio = publicar_quarentena(erros_todos, calcular_resumo(erros_todos, resumo_ficheiros, gerado_em, modo))
        envio_ok = True
    except RuntimeError as exc:
        mensagem_envio, envio_ok = str(exc), False
    gerar_atalho_html(gerado_em, envio_ok, mensagem_envio)
    log.append(f"  Tela online: {mensagem_envio}" if envio_ok else f"  [AVISO] Quarentena online não atualizada: {mensagem_envio}")
    registar_log(log)

    print("-" * 100)
    print(f" Planilha do operador : saidas\\relatorios_auditoria\\{os.path.basename(caminho_xlsx)}")
    if envio_ok:
        print(f" Tela online (login)  : {URL_LOGIN_QUARENTENA} - {mensagem_envio}")
    else:
        print(f" [AVISO] Tela online NÃO atualizada: {mensagem_envio}")
    print(f" Log                  : saidas\\relatorios_auditoria\\{os.path.basename(CAMINHO_LOG)}")
    print("=" * 100)

    return 2 if any(r["decisao"].startswith("RETIDO") for r in resumo_ficheiros) else 0


if __name__ == "__main__":
    sys.exit(main())
