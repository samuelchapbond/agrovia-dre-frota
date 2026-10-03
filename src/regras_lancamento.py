"""Leitura de extratos Sankhya e regras de validação de lançamentos.

Partilhado por auditoria_completa.py (auditoria do que já está em dados/banco_de_dados)
e validar_entrada.py (quarentena antes de entrar em dados/banco_de_dados).
"""
import os
import re
import sys
import unicodedata
from collections import defaultdict

import pandas as pd

PLACA_FROTA_PRINCIPAL = "OOM9749"
PLACEHOLDERS_PLACA = {"", "N/D", "NAN", "NONE", "NULL", "N/A", "NA", "[XYZ]", "-", "0", "SEM PLACA"}

BLOQUEANTE = "BLOQUEANTE"
AVISO = "AVISO"


def configurar_stdout_utf8() -> None:
    """Evita UnicodeEncodeError no terminal Windows (cp1252) com emoji/acentos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception as exc:
                print(f"[AVISO] Falha ao reconfigurar {stream.name}: {exc}", file=sys.stderr)

def limpar_texto(texto):
    if pd.isna(texto):
        return ""
    texto_str = str(texto).strip()
    nfkd = unicodedata.normalize('NFKD', texto_str)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def celula_texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass
    texto = str(valor).strip()
    if texto.lower() in {"nan", "nat", "none", "null"}:
        return ""
    return texto

def reduzir_historico(hist, max_len=30):
    """Reduz o texto do histórico para manter a tabela limpa e legível."""
    if not hist:
        return ""
    h_str = str(hist).strip()
    if len(h_str) > max_len:
        return h_str[:max_len] + "..."
    return h_str

PADRAO_PLACA = re.compile(
    r'(?<![A-Z0-9])([A-Z]{3}-?[0-9][A-Z0-9][0-9]{2})(?![A-Z0-9])'
)

def _padrao_variantes_placa(placa):
    """Aceita hífen ou espaço e o equivalente Mercosul (5.º carácter 0-9 -> A-J)."""
    letra_mercosul = "ABCDEFGHIJ"[int(placa[4])]
    return rf"{placa[:3]}[\s-]?{placa[3]}[{placa[4]}{letra_mercosul}]{placa[5:]}"

PADRAO_PLACA_FROTA = re.compile(
    r'(?<![A-Z0-9])' + _padrao_variantes_placa(PLACA_FROTA_PRINCIPAL) + r'(?![A-Z0-9])'
)

def extrair_placa_do_texto(texto):
    """Primeira placa do texto; variantes da frota principal (OOM 9749, OOM-9749, OOM9H49) devolvem OOM9749."""
    if not texto:
        return None
    texto = str(texto).upper()
    achados = [m for m in (PADRAO_PLACA_FROTA.search(texto), PADRAO_PLACA.search(texto)) if m]
    if not achados:
        return None
    primeiro = min(achados, key=lambda m: m.start())
    if primeiro.re is PADRAO_PLACA_FROTA:
        return PLACA_FROTA_PRINCIPAL
    return primeiro.group(1).replace("-", "")

def carregar_excel_com_cabecalho(caminho_arquivo):
    """Devolve (DataFrame, índice 0-based da linha de cabeçalho no Excel)."""
    for linha_cabecalho in range(0, 5):
        try:
            df = pd.read_excel(caminho_arquivo, header=linha_cabecalho)
            colunas_str = [str(c) for c in df.columns]
            if any('natureza' in limpar_texto(c).lower() for c in colunas_str) or any('valor' in limpar_texto(c).lower() for c in colunas_str):
                return df, linha_cabecalho
        except Exception:
            continue
    return pd.read_excel(caminho_arquivo), 0

def carregar_excel_inteligente(caminho_arquivo):
    return carregar_excel_com_cabecalho(caminho_arquivo)[0]

def encontrar_coluna(df, possiveis_nomes):
    colunas_norm = {limpar_texto(c).lower(): c for c in df.columns}
    for nome in possiveis_nomes:
        nome_limpo = limpar_texto(nome).lower()
        if nome_limpo in colunas_norm:
            return colunas_norm[nome_limpo]
    for col_norm, col_original in colunas_norm.items():
        for nome in possiveis_nomes:
            if limpar_texto(nome).lower() in col_norm:
                return col_original
    return None

def encontrar_coluna_nr_unico(df):
    possiveis = ['nufin', 'nunota', 'nu. unico', 'numero unico', 'nrunico', 'nr unico', 'id unico', 'chave', 'lancamento']
    colunas_norm = {limpar_texto(c).lower(): c for c in df.columns}
    for p in possiveis:
        if p in colunas_norm:
            return colunas_norm[p]
    for col_norm, col_original in colunas_norm.items():
        if any(p in col_norm for p in ['nufin', 'nunota', 'nrunico', 'unico', 'chave']):
            return col_original
    return None

def encontrar_coluna_parceiro(df):
    for col in df.columns:
        c_lower = limpar_texto(str(col)).lower()
        if ('nome' in c_lower or 'razao' in c_lower or 'descricao' in c_lower) and ('parceiro' in c_lower or 'cliente' in c_lower or 'fornecedor' in c_lower):
            return col
    for col in df.columns:
        c_lower = limpar_texto(str(col)).lower()
        if 'nome' in c_lower or 'razao' in c_lower:
            return col
    return encontrar_coluna(df, ['Parceiro', 'Nome Parceiro', 'Razao Social', 'Cliente', 'Fornecedor'])

def encontrar_coluna_operador(df):
    """Procura especificamente pela coluna de NOME do operador/usuário, ignorando códigos."""
    # 0. Prioridade ABSOLUTA para os nomes padrão do Sankhya com parênteses
    nomes_exatos = ['nome (usuario)', 'nome usuario', 'nome (operador)', 'nome operador']
    colunas_norm = {limpar_texto(str(c)).lower(): c for c in df.columns}
    for n in nomes_exatos:
        if n in colunas_norm:
            return colunas_norm[n]

    # 1. Prioridade máxima: Colunas que contenham "Nome" ou "Descrição" + "Usuário/Operador"
    for col in df.columns:
        c_lower = limpar_texto(str(col)).lower()
        if ('nome' in c_lower or 'descricao' in c_lower) and ('usuario' in c_lower or 'operador' in c_lower or 'responsavel' in c_lower):
            return col
            
    # 2. Prioridade média: Varredura geral bloqueando "cod" e "id"
    for col in df.columns:
        c_lower = limpar_texto(str(col)).lower()
        if any(p in c_lower for p in ['usuario', 'operador', 'responsavel', 'criado por']):
            if 'cod' not in c_lower and 'id' not in c_lower:
                return col
                
    # 3. Fallback original
    return encontrar_coluna(df, ['Usuario', 'Operador'])


# ---------------------------------------------------------------------------
# Validação de lançamentos (quarentena)
# ---------------------------------------------------------------------------

ACOES = {
    "Valor ausente ou inválido": "Preencher o Valor Líquido do título no Sankhya e reexportar.",
    "Data ausente ou inválida": "Preencher negociação/vencimento/baixa do título no Sankhya e reexportar.",
    "Nro Único ausente": "Reexportar o relatório do Sankhya com a coluna Nro Único preenchida.",
    "Nro Único repetido no ficheiro": "Conferir se o título foi exportado duas vezes; reexportar sem a repetição.",
    "Placa genérica ou ausente": "Informar a placa/veículo correto no título (campo Marca [Placa] / Código do Veículo).",
    "Placa só no histórico": "Placa encontrada no texto, mas o campo de placa está genérico: corrigir o campo no Sankhya.",
    "Valor R$ 0,00": "Confirmar se o título deve existir; se não, cancelar no Sankhya.",
    "Lançamento Tesou": "Confirmar contrapartida de tesouraria; não entra na DRE da frota.",
    "Placa de outro veículo": "Confirmar o veículo; se for da frota principal, corrigir a placa no Sankhya.",
    "Suspeita de duplicidade": "Conferir extrato: mesmo parceiro, valor e vencimento em Nro Únicos diferentes.",
}

SEVERIDADE_REGRA = {
    "Valor ausente ou inválido": BLOQUEANTE,
    "Data ausente ou inválida": BLOQUEANTE,
    "Nro Único ausente": BLOQUEANTE,
    "Nro Único repetido no ficheiro": BLOQUEANTE,
    "Placa genérica ou ausente": BLOQUEANTE,
    "Placa só no histórico": AVISO,
    "Valor R$ 0,00": AVISO,
    "Lançamento Tesou": AVISO,
    "Placa de outro veículo": AVISO,
    "Suspeita de duplicidade": AVISO,
}


def _data_valida(valor) -> str:
    """Data no formato AAAA-MM-DD ou '' se ausente/inválida."""
    if not celula_texto(valor):
        return ""
    dt = pd.to_datetime(valor, errors="coerce", dayfirst=isinstance(valor, str))
    return "" if pd.isna(dt) else dt.strftime("%Y-%m-%d")


def _valor_numerico(valor):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(v) else v


def placa_do_campo(placa_erp: str):
    """Placa contida no campo do ERP (ex.: 'M.BENZ/ACTROS[OOM9749]'), ou None se genérica."""
    texto = placa_erp.strip().upper()
    if texto in PLACEHOLDERS_PLACA or "[XYZ]" in texto:
        return None
    return extrair_placa_do_texto(texto)


def identificar_placa(placa_erp: str, texto_busca: str):
    """(placa, origem): origem 'campo', 'historico' (natureza/histórico/obs/identificação) ou None se sem placa.

    Mesmo critério na quarentena, no motor e na auditoria: sem placa = BLOQUEANTE e fora da DRE.
    """
    placa = placa_do_campo(placa_erp or "")
    if placa:
        return placa, "campo"
    placa = extrair_placa_do_texto(texto_busca)
    if placa:
        return placa, "historico"
    return None, None


def validar_ficheiro(caminho):
    """Lista de erros do ficheiro (um dict por erro).

    Linhas de rodapé/total do Sankhya (sem parceiro e sem Nro Único) não são lançamentos e são ignoradas.
    """
    df, linha_cabecalho = carregar_excel_com_cabecalho(caminho)
    nome_ficheiro = os.path.basename(caminho)

    def coluna(nomes):
        return encontrar_coluna(df, nomes)

    col_valor = coluna(['Valor Líquido', 'Valor Liquido', 'VALOR', 'Valor'])
    col_nat = coluna(['Descrição (Natureza)', 'Natureza', 'Descricao (Natureza)'])
    col_hist = coluna(['Histórico', 'Historico', 'HISTORICO'])
    col_obs = coluna(['Observação', 'Observacao', 'Observação padrão', 'Observacao padrao'])
    col_ident = coluna(['Identificação', 'Identificacao'])
    col_placa = coluna(['Placa', 'Marca [Placa]', 'Veiculo', 'Frota', 'Equipamento'])
    col_negociacao = coluna(['Dt. Negociação', 'Dt. Negociacao', 'Data Negociação'])
    col_vencimento = coluna(['Data Vencimento', 'Dt. Vencimento', 'Vencimento'])
    col_baixa = coluna(['Data Baixa', 'Baixa'])
    col_nr_unico = encontrar_coluna_nr_unico(df)
    col_parceiro = encontrar_coluna_parceiro(df)
    col_operador = encontrar_coluna_operador(df)

    def texto(row, col):
        return celula_texto(row[col]) if col and col in df.columns else ""

    erros = []
    lancamentos = []

    for idx, row in df.iterrows():
        nr_u = texto(row, col_nr_unico).split('.')[0]
        parceiro = texto(row, col_parceiro)
        nat = texto(row, col_nat)
        hist = texto(row, col_hist)
        obs = texto(row, col_obs)
        ident = texto(row, col_ident)
        texto_busca = " - ".join(p for p in (nat, hist, obs, ident) if p)

        if not nr_u and not parceiro:
            continue
        if any(t in limpar_texto(texto_busca).lower() for t in ['total geral', 'resumo', 'total da conta']):
            continue

        valor = _valor_numerico(row[col_valor]) if col_valor and col_valor in df.columns else None
        data_negociacao = _data_valida(row[col_negociacao]) if col_negociacao else ""
        if valor is not None and valor > 0:
            data = data_negociacao
        else:
            data = (
                _data_valida(row[col_baixa]) if col_baixa else ""
            ) or (
                _data_valida(row[col_vencimento]) if col_vencimento else ""
            ) or data_negociacao
        placa_erp = texto(row, col_placa)

        base = {
            "ficheiro": nome_ficheiro,
            "linha": int(idx) + linha_cabecalho + 2,
            "nr_unico": nr_u or "N/D",
            "data": data or "N/D",
            "vencimento": _data_valida(row[col_vencimento]) if col_vencimento else "",
            "parceiro": parceiro or "N/D",
            "operador": texto(row, col_operador) or "N/D",
            "valor": valor,
            "placa_erp": placa_erp or "N/D",
            "historico": reduzir_historico(hist or nat, max_len=80),
        }

        def registar(regra, detalhe=""):
            erros.append({
                **base,
                "severidade": SEVERIDADE_REGRA[regra],
                "regra": regra,
                "detalhe": detalhe,
                "acao": ACOES[regra],
            })

        if valor is None:
            registar("Valor ausente ou inválido")
        elif valor == 0:
            registar("Valor R$ 0,00")
        if not data:
            registar("Data ausente ou inválida")
        if not nr_u:
            registar("Nro Único ausente")

        if 'tesou' in limpar_texto(texto_busca).lower():
            registar("Lançamento Tesou")
        else:
            placa, origem = identificar_placa(placa_erp, texto_busca)
            if origem == "historico":
                registar("Placa só no histórico", f"Placa no texto: {placa}")
            elif not placa:
                registar("Placa genérica ou ausente")
            if placa and placa != PLACA_FROTA_PRINCIPAL:
                registar("Placa de outro veículo", f"Placa: {placa}")

        lancamentos.append(base)

    por_nr = defaultdict(list)
    for item in lancamentos:
        if item["nr_unico"] != "N/D":
            por_nr[item["nr_unico"]].append(item)
    for nr, itens in por_nr.items():
        if len(itens) > 1:
            linhas = ", ".join(str(i["linha"]) for i in itens)
            for item in itens:
                erros.append({
                    **item,
                    "severidade": SEVERIDADE_REGRA["Nro Único repetido no ficheiro"],
                    "regra": "Nro Único repetido no ficheiro",
                    "detalhe": f"Linhas {linhas}",
                    "acao": ACOES["Nro Único repetido no ficheiro"],
                })

    grupos = defaultdict(list)
    for item in lancamentos:
        if item["valor"] and item["parceiro"] != "N/D" and item["vencimento"]:
            grupos[(limpar_texto(item["parceiro"]).upper(), round(abs(item["valor"]), 2), item["vencimento"])].append(item)
    for itens in grupos.values():
        nrs = {i["nr_unico"] for i in itens}
        if len(nrs) > 1:
            outros = ", ".join(sorted(nrs))
            for item in itens:
                erros.append({
                    **item,
                    "severidade": SEVERIDADE_REGRA["Suspeita de duplicidade"],
                    "regra": "Suspeita de duplicidade",
                    "detalhe": f"Nro Únicos: {outros}",
                    "acao": ACOES["Suspeita de duplicidade"],
                })

    erros.sort(key=lambda e: (e["severidade"] != BLOQUEANTE, e["linha"], e["regra"]))
    return erros
