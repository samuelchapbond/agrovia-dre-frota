import pandas as pd
import datetime
import html
import unicodedata
import os
import json
import sys
import re

from fontes_dados import (
    CAMINHO_INDEX,
    CAMINHO_TEMPLATE,
    PASTA_BACKUP,
    PASTA_DADOS,
    PASTA_RELATORIOS,
    escrever_inventario,
    listar_ficheiros_abastecimento,
)
from regras_lancamento import PLACA_FROTA_PRINCIPAL, extrair_placa_do_texto, identificar_placa

VERSAO_ATUAL = "v8.36-RobustAuditEngine"

def configurar_stdout_utf8() -> None:
    """Evita UnicodeEncodeError no terminal Windows (cp1252) com emoji/acentos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception as exc:
                print(f"[AVISO] Falha ao reconfigurar {stream.name}: {exc}", file=sys.stderr)

configurar_stdout_utf8()

os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_BACKUP, exist_ok=True)
os.makedirs(PASTA_RELATORIOS, exist_ok=True)

CAMINHO_LOG = os.path.join(PASTA_RELATORIOS, "log_execucao.txt")
CAMINHO_LOG_HISTORICO = os.path.join(PASTA_BACKUP, "log_execucao_historico.txt")

def iniciar_log_execucao():
    """log_execucao.txt guarda só a execução atual; as anteriores vão para o histórico."""
    if not os.path.exists(CAMINHO_LOG):
        return
    try:
        with open(CAMINHO_LOG, "r", encoding="utf-8") as origem:
            conteudo_anterior = origem.read()
        if conteudo_anterior:
            with open(CAMINHO_LOG_HISTORICO, "a", encoding="utf-8") as historico:
                historico.write(conteudo_anterior)
        open(CAMINHO_LOG, "w", encoding="utf-8").close()
    except Exception as exc:
        print(f"[AVISO] Falha ao arquivar o log anterior: {exc}", file=sys.stderr)

def registar_log(status, mensagem):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linha_log = f"[{timestamp}] [{status}] {mensagem}\n"
    try:
        with open(CAMINHO_LOG, "a", encoding="utf-8") as f:
            f.write(linha_log)
    except Exception:
        pass
    print(linha_log.strip())

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

def remover_duplicados_entre_ficheiros(df: pd.DataFrame, col_nr_unico) -> pd.DataFrame:
    if not col_nr_unico or col_nr_unico not in df.columns:
        return df
    chave = df[col_nr_unico].map(celula_texto).str.split('.').str[0]
    tem_chave = chave != ""
    origem_ref = df.loc[tem_chave, '__origem'].groupby(chave[tem_chave]).transform('first')
    duplicado = tem_chave & (df['__origem'] != origem_ref.reindex(df.index))
    if duplicado.any():
        resumo = df.loc[duplicado, '__origem'].value_counts().to_dict()
        registar_log("INFO", f"Removidos {int(duplicado.sum())} lançamentos repetidos entre ficheiros (Nro Único): {resumo}")
    return df.loc[~duplicado]

def carregar_excel_inteligente(caminho_arquivo):
    for linha_cabecalho in range(0, 5):
        try:
            df = pd.read_excel(caminho_arquivo, header=linha_cabecalho)
            colunas_str = [str(c) for c in df.columns]
            if any('natureza' in limpar_texto(c).lower() for c in colunas_str) or any('valor' in limpar_texto(c).lower() for c in colunas_str):
                return df
        except Exception:
            continue
    return pd.read_excel(caminho_arquivo)

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

def classificar_categoria_despesa(natureza, historico):
    texto = limpar_texto(f"{natureza} {historico}").lower()
    if any(k in texto for k in ['combust', 'diesel', 'arla']):
        return ('Combustível (Diesel)', 'detail-diesel', 'Combustível Diesel S10')
    elif any(k in texto for k in ['manut', 'peca', 'pneu', 'borracharia', 'oficina', 'mecanica']):
        return ('Manutenção', 'detail-manut', 'Manutenção Frota')
    elif any(k in texto for k in ['pedag', 'taxa', 'pedagio']):
        return ('Pedágio', 'detail-pedagio', 'Tarifa de Pedágio')
    elif any(k in texto for k in ['segur', 'apólice', 'apolice']):
        return ('Seguros', 'detail-seguros', 'Apólice de Seguro')
    elif any(k in texto for k in ['ipva', 'licenci', 'multa', 'detran', 'crlv']):
        return ('IPVA / Lic. / Multas', 'detail-encargos', 'Encargos e Licenciamento')
    else:
        return ('Outros Custos', 'detail-outros', 'Outros Custos Operacionais')

COLUNAS_HODOMETRO = ['Hodômetro', 'Hodometro', 'Odômetro', 'Odometro', 'KM Atual', 'Km Atual', 'Quilometragem', 'KM']
COLUNAS_LITROS = ['Litros', 'Qtd. Litros', 'Quantidade', 'Qtde', 'Qtd', 'Volume']

def carregar_abastecimento(caminho_arquivo):
    """Lê um relatório de abastecimento; devolve (df, col_placa, col_data, col_hodometro, col_litros) ou None."""
    for linha_cabecalho in range(0, 6):
        try:
            df = pd.read_excel(caminho_arquivo, header=linha_cabecalho)
        except Exception:
            continue
        col_hod = encontrar_coluna(df, COLUNAS_HODOMETRO)
        col_lit = encontrar_coluna(df, COLUNAS_LITROS)
        if col_hod and col_lit:
            col_placa = encontrar_coluna(df, ['Placa', 'Marca [Placa]', 'Veículo', 'Veiculo', 'Frota'])
            col_data = encontrar_coluna(df, ['Data Abastecimento', 'Dt. Abastecimento', 'Data', 'Dt.'])
            return df, col_placa, col_data, col_hod, col_lit
    return None

def apurar_km_litros(placa):
    """Km rodado e litros da placa a partir dos relatórios de abastecimento.

    Km rodado = hodómetro máximo - hodómetro mínimo no período.
    Litros para Km/L = soma dos litros sem o 1.º abastecimento (método tanque cheio:
    esse combustível foi gasto antes do primeiro hodómetro registado).
    Devolve (km_rodado, litros_total, litros_consumo) ou (None, None, None) sem fonte válida.
    """
    arquivos = listar_ficheiros_abastecimento()
    if not arquivos:
        registar_log("PENDENTE", "Sem relatório de abastecimento em dados/banco_de_dados: CPK e Km/L = 'Sem dado'.")
        return None, None, None

    partes = []
    for arq in arquivos:
        nome = os.path.basename(arq)
        lido = carregar_abastecimento(arq)
        if lido is None:
            registar_log("AVISO", f"Abastecimento {nome}: colunas de hodómetro/litros não encontradas; ignorado.")
            continue
        df, col_placa, col_data, col_hod, col_lit = lido
        if not col_placa:
            registar_log("AVISO", f"Abastecimento {nome}: sem coluna de placa; ignorado para não misturar veículos.")
            continue
        registar_log("INFO", f"Abastecimento {nome}: placa='{col_placa}', data='{col_data}', hodómetro='{col_hod}', litros='{col_lit}'.")
        placas = df[col_placa].map(celula_texto).map(lambda t: extrair_placa_do_texto(t) or t.upper())
        sub = pd.DataFrame({
            'origem': nome,
            'data': pd.to_datetime(df[col_data], errors='coerce', dayfirst=True) if col_data else pd.NaT,
            'hodometro': pd.to_numeric(df[col_hod], errors='coerce'),
            'litros': pd.to_numeric(df[col_lit], errors='coerce'),
        })[placas.str.contains(placa, na=False)]
        partes.append(sub)

    if not partes:
        registar_log("PENDENTE", "Nenhum relatório de abastecimento utilizável: CPK e Km/L = 'Sem dado'.")
        return None, None, None

    abast = pd.concat(partes, ignore_index=True)
    invalidas = abast['hodometro'].isna() | (abast['hodometro'] <= 0) | abast['litros'].isna() | (abast['litros'] <= 0)
    if invalidas.any():
        registar_log("AVISO", f"Abastecimento {placa}: {int(invalidas.sum())} linhas sem hodómetro/litros válidos descartadas.")
    abast = abast[~invalidas].drop_duplicates(subset=['data', 'hodometro', 'litros'])

    if len(abast) < 2:
        registar_log("PENDENTE", f"Abastecimento {placa}: menos de 2 registos válidos; CPK e Km/L = 'Sem dado'.")
        return None, None, None

    ordem = ['data', 'hodometro'] if abast['data'].notna().all() else ['hodometro']
    abast = abast.sort_values(ordem).reset_index(drop=True)
    recuos = int((abast['hodometro'].diff() < 0).sum())
    if recuos:
        registar_log("AVISO", f"Abastecimento {placa}: hodómetro recua {recuos} vez(es) na ordem cronológica; validar a fonte.")

    km_rodado = float(abast['hodometro'].max() - abast['hodometro'].min())
    litros_total = float(abast['litros'].sum())
    litros_consumo = float(abast.sort_values('hodometro')['litros'].iloc[1:].sum())
    periodo = ""
    if abast['data'].notna().any():
        periodo = f" | período {abast['data'].min():%d/%m/%Y} a {abast['data'].max():%d/%m/%Y}"
    registar_log(
        "INFO",
        f"Abastecimento {placa}: {len(abast)} registos | hodómetro {abast['hodometro'].min():.0f} a "
        f"{abast['hodometro'].max():.0f} | km rodado {km_rodado:.0f} | litros {litros_total:.2f} "
        f"(consumo {litros_consumo:.2f}){periodo}"
    )
    if km_rodado <= 0:
        return None, None, None
    return km_rodado, litros_total, litros_consumo

def main():
    print("="*80)
    print(f" 🚀 AGROVIA - MOTOR DE GESTÃO DE CUSTO DE FROTA [{VERSAO_ATUAL}]")
    print("="*80)
    
    iniciar_log_execucao()
    registar_log("INFO", f"Início da execução do motor [{VERSAO_ATUAL}].")

    todos_arquivos = escrever_inventario("atualizar_dashboard.py")
    registar_log("INFO", f"Fontes atuais em dados/banco_de_dados: {[os.path.basename(f) for f in todos_arquivos]}")

    if not todos_arquivos:
        registar_log("ERRO_CRITICO", "Nenhum ficheiro Excel válido encontrado na pasta dados/banco_de_dados.")
        sys.exit(1)

    dfs_consolidados = []
    origens = []
    for arq in todos_arquivos:
        try:
            df_temp = carregar_excel_inteligente(arq)
            if not df_temp.empty:
                dfs_consolidados.append(df_temp)
                origens.append(os.path.basename(arq))
                registar_log("INFO", f"Ficheiro carregado com sucesso: {os.path.basename(arq)}")
        except Exception as e:
            registar_log("AVISO", f"Falha ao ler o ficheiro {os.path.basename(arq)}: {str(e)}")

    if not dfs_consolidados:
        registar_log("ERRO_CRITICO", "Todos os ficheiros Excel falharam ao ser processados.")
        sys.exit(1)

    df_global = (
        pd.concat(dfs_consolidados, keys=origens, names=['__origem', None])
        .copy()
        .reset_index(level=0)
        .reset_index(drop=True)
    )
    df_global = remover_duplicados_entre_ficheiros(df_global, encontrar_coluna_nr_unico(df_global))
    registar_log("INFO", f"Consolidação concluída. Total de registos combinados: {len(df_global)}")

    try:
        col_valor = encontrar_coluna(df_global, ['Valor Líquido', 'Valor Liquido', 'VALOR', 'Valor'])
        col_nat = encontrar_coluna(df_global, ['Descrição (Natureza)', 'Natureza', 'Descricao (Natureza)'])
        col_hist = encontrar_coluna(df_global, ['Histórico', 'Historico', 'HISTORICO'])
        col_obs = encontrar_coluna(df_global, ['Observação', 'Observacao', 'Observação padrão', 'Observacao padrao'])
        col_ident = encontrar_coluna(df_global, ['Identificação', 'Identificacao'])
        col_nr_unico = encontrar_coluna_nr_unico(df_global)
        col_placa = encontrar_coluna(df_global, ['Placa', 'Marca [Placa]', 'Veiculo', 'Frota', 'Equipamento'])
        col_parceiro = encontrar_coluna_parceiro(df_global)

        # Receita: Dt. Negociação (emissão do título). Sem o genérico 'Data', que apanhava 'Data Baixa'.
        col_emissao = encontrar_coluna(df_global, ['Dt. Negociação', 'Dt. Negociacao', 'Data Negociação', 'Data Emissao', 'Emissao'])
        col_baixa = encontrar_coluna(df_global, ['Data Baixa', 'Baixa'])
        col_vencimento = encontrar_coluna(df_global, ['Data Vencimento', 'Vencimento'])

        df_frota = df_global.copy()
        df_frota['Valor_Numerico'] = pd.to_numeric(df_frota[col_valor], errors='coerce').fillna(0.0)

        dados_filtrados = []
        lancamentos_sem_placa = []

        for _, row in df_frota.iterrows():
            val = row['Valor_Numerico']
            if val == 0.0:
                continue

            nat = celula_texto(row[col_nat]) if col_nat and col_nat in df_frota.columns else "N/D"
            hist = celula_texto(row[col_hist]) if col_hist and col_hist in df_frota.columns else ""
            obs = celula_texto(row[col_obs]) if col_obs and col_obs in df_frota.columns else ""
            ident = celula_texto(row[col_ident]) if col_ident and col_ident in df_frota.columns else ""
            texto_completo = " - ".join([p for p in (nat, hist, obs, ident) if p])
            texto_limpo_verificacao = limpar_texto(texto_completo).lower()

            # Ignora lixo e lançamentos Tesou
            if any(termo in texto_limpo_verificacao for termo in ['total geral', 'resumo', 'total da conta']) or 'tesou' in texto_limpo_verificacao:
                continue

            # Regra de Datas Inteligente
            if val > 0:
                data_raw = row[col_emissao] if col_emissao and col_emissao in df_frota.columns else None
            else:
                b_val = row[col_baixa] if col_baixa and col_baixa in df_frota.columns else None
                v_val = row[col_vencimento] if col_vencimento and col_vencimento in df_frota.columns else None
                e_val = row[col_emissao] if col_emissao and col_emissao in df_frota.columns else None
                
                if pd.notna(b_val) and str(b_val).strip() not in ["", "NaT", "nan", "None"]:
                    data_raw = b_val
                elif pd.notna(v_val) and str(v_val).strip() not in ["", "NaT", "nan", "None"]:
                    data_raw = v_val
                else:
                    data_raw = e_val

            dt_parsed = pd.to_datetime(data_raw, errors='coerce')
            if pd.isna(dt_parsed):
                continue

            placa_erp = celula_texto(row[col_placa]) if col_placa and col_placa in df_frota.columns else ""
            placa, origem_placa = identificar_placa(placa_erp, texto_completo)
            nr_u = str(row[col_nr_unico]).split('.')[0] if col_nr_unico and col_nr_unico in df_frota.columns and pd.notna(row[col_nr_unico]) else "N/D"
            parceiro_val = str(row[col_parceiro]) if col_parceiro and col_parceiro in df_frota.columns and pd.notna(row[col_parceiro]) else (hist if hist else nat)

            # Sem placa = BLOQUEANTE na quarentena: fica fora da DRE até corrigir no Sankhya
            if not placa:
                lancamentos_sem_placa.append({
                    'data': dt_parsed.strftime('%d/%m/%Y'), 'mes': f"{int(dt_parsed.month):02d}", 'valor': val,
                    'nr_unico': nr_u, 'parceiro': parceiro_val, 'historico': hist or nat,
                })
                continue
            if placa != PLACA_FROTA_PRINCIPAL:
                continue

            placa_exibicao = f"{PLACA_FROTA_PRINCIPAL} (Validada)" if origem_placa == "campo" else f"{PLACA_FROTA_PRINCIPAL} (via histórico)"

            dados_filtrados.append({
                'data_str': dt_parsed.strftime('%d/%m/%Y'),
                'mes': int(dt_parsed.month),
                'valor': val,
                'natureza': nat,
                'historico': hist,
                'parceiro': parceiro_val,
                'nr_unico': nr_u,
                'placa': placa_exibicao
            })

        df_processado = pd.DataFrame(dados_filtrados)

        if lancamentos_sem_placa:
            positivos = sum(l['valor'] for l in lancamentos_sem_placa if l['valor'] > 0)
            negativos = sum(l['valor'] for l in lancamentos_sem_placa if l['valor'] < 0)
            registar_log(
                "PENDENTE",
                f"{len(lancamentos_sem_placa)} lançamentos sem placa fora da DRE (valores positivos R$ {positivos:,.2f}, "
                f"negativos R$ {negativos:,.2f}): corrigir a placa no Sankhya e reexportar."
            )

        if df_processado.empty:
            registar_log("AVISO", "Nenhum registo válido encontrado após aplicar os filtros da frota.")
            sys.exit(0)

        df_receitas = df_processado[df_processado['valor'] > 0]
        df_despesas = df_processado[df_processado['valor'] < 0]

        receitas_por_mes = [0.0] * 12
        despesas_por_mes = [0.0] * 12

        for _, row in df_receitas.iterrows():
            m = row['mes']
            if 1 <= m <= 12:
                receitas_por_mes[m - 1] += float(row['valor'])

        for _, row in df_despesas.iterrows():
            m = row['mes']
            val = abs(float(row['valor']))
            if 1 <= m <= 12:
                despesas_por_mes[m - 1] += val

        total_receita = float(df_receitas['valor'].sum())
        total_despesa = float(df_despesas['valor'].abs().sum())

        lista_detalhes_receitas = []
        for _, row in df_receitas.iterrows():
            lista_detalhes_receitas.append({
                'data': row['data_str'], 'mes': f"{row['mes']:02d}", 'parceiro': row['parceiro'], 'natureza': row['natureza'], 'valor': row['valor'], 'nr_unico': row['nr_unico'], 'placa': row['placa']
            })

        despesas_por_cat = {
            'Combustível (Diesel)': {'total': 0.0, 'linhas': []},
            'Manutenção': {'total': 0.0, 'linhas': []},
            'Pedágio': {'total': 0.0, 'linhas': []},
            'Seguros': {'total': 0.0, 'linhas': []},
            'IPVA / Lic. / Multas': {'total': 0.0, 'linhas': []},
            'Outros Custos': {'total': 0.0, 'linhas': []}
        }

        for _, row in df_despesas.iterrows():
            val = abs(float(row['valor']))
            cat_nome, cat_class, badge_sub = classificar_categoria_despesa(row['natureza'], row['historico'])
            despesas_por_cat[cat_nome]['total'] += val
            despesas_por_cat[cat_nome]['linhas'].append({
                'data': row['data_str'], 'mes': f"{row['mes']:02d}", 'parceiro': row['parceiro'], 'natureza': row['natureza'], 'valor': val, 'nr_unico': row['nr_unico'], 'placa': row['placa']
            })

        km_rodado, _, litros_consumo = apurar_km_litros(PLACA_FROTA_PRINCIPAL)
        cpk_calculado = (total_despesa / km_rodado) if km_rodado else None
        km_por_litro = (km_rodado / litros_consumo) if km_rodado and litros_consumo else None

    except Exception as e:
        registar_log("ERRO_CRITICO", f"Erro crítico no processamento dos dados financeiros: {str(e)}")
        sys.exit(1)

    resultado_liquido = float(total_receita - total_despesa)
    margem_liquida = float((resultado_liquido / total_receita * 100) if total_receita > 0 else 0)

    arquivo_base = CAMINHO_TEMPLATE if os.path.exists(CAMINHO_TEMPLATE) else CAMINHO_INDEX
    try:
        with open(arquivo_base, 'r', encoding='utf-8') as f:
            html_template = f.read()
    except Exception as e:
        registar_log("ERRO_CRITICO", f"Não foi possível ler o template HTML base: {str(e)}")
        sys.exit(1)

    data_hoje = datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')

    def fmt_brl(val):
        return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    rec_fmt = fmt_brl(total_receita)
    desp_fmt = fmt_brl(total_despesa)
    res_abs = fmt_brl(abs(resultado_liquido))
    res_fmt = f"R$ -{res_abs.replace('R$ ', '')}" if resultado_liquido < 0 else res_abs
    margem_fmt = f"{margem_liquida:.2f}%"
    cpk_fmt = fmt_brl(cpk_calculado) if cpk_calculado is not None else "Sem dado"
    consumo_fmt = f"{km_por_litro:.2f} Km/L".replace('.', ',') if km_por_litro is not None else "Sem dado"

    html_final = html_template

    html_final = re.sub(r'Atualizado em: \d{2}/\d{2}/\d{4} às \d{2}:\d{2}', f"Atualizado em: {data_hoje}", html_final)
    html_final = re.sub(r'Agrovia DRE Master v[\d\.]+', f'Agrovia DRE Master {VERSAO_ATUAL}', html_final)

    estado_quarentena = "presente" if os.path.exists(os.path.join(PASTA_RELATORIOS, "pendencias_lancamentos.html")) else "ausente"
    html_final = re.sub(r'(id="btnQuarentena"[^>]*data-relatorio=")\w+"', rf'\g<1>{estado_quarentena}"', html_final)

    html_final = re.sub(r'class="kpi-value kpi-receita-bruta">[^<]+<', f'class="kpi-value kpi-receita-bruta">{rec_fmt}<', html_final)
    html_final = re.sub(r'class="kpi-value kpi-custo-total">[^<]+<', f'class="kpi-value kpi-custo-total">{desp_fmt}<', html_final)
    html_final = re.sub(r'class="kpi-value kpi-resultado-liquido">[^<]+<', f'class="kpi-value kpi-resultado-liquido">{res_fmt}<', html_final)
    html_final = re.sub(r'class="kpi-value kpi-margem-liquida">[^<]+<', f'class="kpi-value kpi-margem-liquida">{margem_fmt}<', html_final)
    html_final = re.sub(r'class="kpi-value kpi-cpk">[^<]+<', f'class="kpi-value kpi-cpk">{cpk_fmt}<', html_final)
    html_final = re.sub(r'class="kpi-value kpi-consumo">[^<]+<', f'class="kpi-value kpi-consumo">{consumo_fmt}<', html_final)

    str_rec_mes = json.dumps(receitas_por_mes[:8])
    str_desp_mes = json.dumps(despesas_por_mes[:8])

    html_final = re.sub(r'label:\s*\'Receita Bruta\',\s*data:\s*\[[^\]]+\]', f"label: 'Receita Bruta', data: {str_rec_mes}", html_final)
    html_final = re.sub(r'label:\s*\'Custo Total Frota\',\s*data:\s*\[[^\]]+\]', f"label: 'Custo Total Frota', data: {str_desp_mes}", html_final)

    cat_ordenadas = sorted(despesas_por_cat.items(), key=lambda x: x[1]['total'], reverse=True)
    cat_nomes = [item[0] for item in cat_ordenadas]
    lista_rosca = [item[1]['total'] for item in cat_ordenadas]

    str_rosca = json.dumps(lista_rosca)
    str_labels_rosca = json.dumps(cat_nomes, ensure_ascii=False)

    idx_doughnut = html_final.find("type: 'doughnut'")
    if idx_doughnut != -1:
        bloco_doughnut = html_final[idx_doughnut:idx_doughnut+900]
        bloco_novo = re.sub(r'labels:\s*\[[^\]]*\]', f"labels: {str_labels_rosca}", bloco_doughnut)
        bloco_novo = re.sub(r'data:\s*\[[^\]]*\]', f"data: {str_rosca}", bloco_novo, count=1)
        html_final = html_final[:idx_doughnut] + bloco_novo + html_final[idx_doughnut+900:]

    html_linhas_tabela = f"""
                            <!-- BLOCO 1: RECEITA -->
                            <tr class="row-group" onclick="toggleRow('sub-receita')">
                                <td><i class="fa-solid fa-chevron-right" id="icon-sub-receita"></i> (+) RECEITA OPERACIONAL BRUTA</td>
                                <td><span class="badge-cat">Faturamento</span></td>
                                <td class="text-right val-receita-total" style="color: var(--accent-blue);">{rec_fmt}</td>
                            </tr>
                            <tr class="row-sub sub-receita" onclick="toggleRow('detail-frete')">
                                <td style="padding-left: 30px;"><i class="fa-solid fa-caret-right"></i> • Prestação de Serviços de Transporte</td>
                                <td><span class="badge-sub">Receita de Frete</span></td>
                                <td class="text-right val-receita-sub">{rec_fmt}</td>
                            </tr>"""

    if lista_detalhes_receitas:
        for item in lista_detalhes_receitas:
            html_linhas_tabela += f"""
                            <tr class="row-detail detail-frete" data-mes="{item['mes']}" data-valor="{item['valor']}">
                                <td style="padding-left: 50px;">
                                    <i class="fa-regular fa-calendar-days" style="color: var(--accent-purple);"></i> <strong>{item['data']}</strong> • N° {item['nr_unico']} • Placa: <strong>{item['placa']}</strong> • <strong>{item['parceiro']}</strong>
                                </td>
                                <td><span class="badge-sub">Frete / Operação</span></td>
                                <td class="text-right" style="color: var(--text-primary); font-weight: 600;">{fmt_brl(item['valor'])}</td>
                            </tr>"""
    else:
        html_linhas_tabela += f"""
                            <tr class="row-detail detail-frete" data-mes="01" data-valor="0">
                                <td style="padding-left: 50px;" colspan="3">Nenhuma receita registada no período.</td>
                            </tr>"""

    html_linhas_tabela += f"""
                            <!-- BLOCO 2: DEDUÇÕES -->
                            <tr class="row-group" onclick="toggleRow('sub-deducoes')">
                                <td><i class="fa-solid fa-chevron-right"></i> (-) DEDUÇÕES DA RECEITA BRUTA</td>
                                <td><span class="badge-cat">Impostos / Retenções</span></td>
                                <td class="text-right" style="color: var(--accent-orange);">-R$ 0,00</td>
                            </tr>
                            <tr class="row-sub sub-deducoes">
                                <td style="padding-left: 30px;">• Sem deduções registradas no período</td>
                                <td><span class="badge-sub">Impostos</span></td>
                                <td class="text-right">R$ 0,00</td>
                            </tr>

                            <!-- BLOCO 3: RECEITA LÍQUIDA -->
                            <tr class="row-total">
                                <td>(=) RECEITA OPERACIONAL LÍQUIDA</td>
                                <td>Receita Efetiva</td>
                                <td class="text-right val-rec-liquida">{rec_fmt}</td>
                            </tr>

                            <!-- BLOCO 4: CUSTOS OPERACIONAIS -->
                            <tr class="row-group" onclick="toggleRow('sub-custos')">
                                <td><i class="fa-solid fa-chevron-right"></i> (-) CUSTOS OPERACIONAIS DA FROTA</td>
                                <td><span class="badge-cat">Custos Diretos</span></td>
                                <td class="text-right val-custos-total" style="color: #f87171;">-{desp_fmt}</td>
                            </tr>"""

    sub_mapping = [
        ('Combustível (Diesel)', 'detail-diesel', 'val-sub-diesel', 'Combustível'),
        ('Manutenção', 'detail-manut', 'val-sub-manut', 'Manutenção'),
        ('Pedágio', 'detail-pedagio', 'val-sub-pedagio', 'Pedágio'),
        ('Seguros', 'detail-seguros', 'val-sub-seguros', 'Seguros'),
        ('IPVA / Lic. / Multas', 'detail-encargos', 'val-sub-encargos', 'Encargos / Leis'),
        ('Outros Custos', 'detail-outros', 'val-sub-outros', 'Outros')
    ]

    for cat_nome, class_detalhe, class_subval, badge_nome in sub_mapping:
        dados_cat = despesas_por_cat[cat_nome]
        sub_tot_fmt = fmt_brl(dados_cat['total'])
        
        html_linhas_tabela += f"""
                            <tr class="row-sub sub-custos" onclick="toggleRow('{class_detalhe}')">
                                <td style="padding-left: 30px;"><i class="fa-solid fa-caret-right"></i> • {cat_nome}</td>
                                <td><span class="badge-sub">{badge_nome}</span></td>
                                <td class="text-right {class_subval}">{sub_tot_fmt}</td>
                            </tr>"""
        
        if dados_cat['linhas']:
            for l in dados_cat['linhas']:
                html_linhas_tabela += f"""
                            <tr class="row-detail {class_detalhe}" data-mes="{l['mes']}" data-valor="{l['valor']}">
                                <td style="padding-left: 50px;">
                                    <i class="fa-regular fa-calendar-days" style="color: var(--accent-purple);"></i> <strong>{l['data']}</strong> • N° {l['nr_unico']} • Placa: <strong>{l['placa']}</strong> • <strong>{l['parceiro']}</strong>
                                </td>
                                <td><span class="badge-sub">{l['natureza']}</span></td>
                                <td class="text-right" style="color: #f87171; font-weight: 600;">{fmt_brl(l['valor'])}</td>
                            </tr>"""
        else:
            html_linhas_tabela += f"""
                            <tr class="row-detail {class_detalhe}" data-mes="01" data-valor="0">
                                <td style="padding-left: 50px;" colspan="3">Nenhum registo nesta categoria.</td>
                            </tr>"""

    html_linhas_tabela += f"""
                            <!-- BLOCO 5: RESULTADO -->
                            <tr class="row-total">
                                <td>(=) RESULTADO / LUCRO LÍQUIDO DO EXERCÍCIO</td>
                                <td>Resultado Final DRE</td>
                                <td class="text-right val-resultado-liquido" style="color: {'#f87171' if resultado_liquido < 0 else 'var(--accent-purple);'};">{res_fmt}</td>
                            </tr>"""

    if lancamentos_sem_placa:
        html_linhas_tabela += f"""
                            <!-- FORA DA DRE: SEM PLACA -->
                            <tr class="row-group" onclick="toggleRow('detail-sem-placa')">
                                <td><i class="fa-solid fa-chevron-right"></i> (!) LANÇAMENTOS SEM PLACA - FORA DA DRE</td>
                                <td><span class="badge-cat">Corrigir no Sankhya</span></td>
                                <td class="text-right" style="color: var(--accent-yellow);">{len(lancamentos_sem_placa)} lançamentos</td>
                            </tr>"""
        for l in lancamentos_sem_placa:
            cor = 'var(--accent-blue)' if l['valor'] > 0 else '#f87171'
            html_linhas_tabela += f"""
                            <tr class="row-detail detail-sem-placa" data-mes="{l['mes']}">
                                <td style="padding-left: 50px;">
                                    <i class="fa-regular fa-calendar-days" style="color: var(--accent-purple);"></i> <strong>{l['data']}</strong> • N° {l['nr_unico']} • Placa: <strong>NÃO INFORMADA</strong> • <strong>{html.escape(l['parceiro'])}</strong> • {html.escape(l['historico'][:60])}
                                </td>
                                <td><span class="badge-sub">Sem placa</span></td>
                                <td class="text-right" style="color: {cor}; font-weight: 600;">{fmt_brl(l['valor'])}</td>
                            </tr>"""

    html_final = re.sub(r'<tbody>.*?<\/tbody>', f"<tbody>{html_linhas_tabela}\n                    </tbody>", html_final, flags=re.DOTALL)

    caminho_index = CAMINHO_INDEX
    try:
        with open(caminho_index, 'w', encoding='utf-8') as f:
            f.write(html_final)
        registar_log("SUCESSO", f"Dashboard gerado com exito em: {caminho_index}")
    except Exception as e:
        registar_log("ERRO_CRITICO", f"Falha ao gravar o ficheiro index.html: {str(e)}")
        sys.exit(1)

    print(f"📍 O ficheiro index.html foi ATUALIZADO com sucesso!")

if __name__ == "__main__":
    main()

    



















