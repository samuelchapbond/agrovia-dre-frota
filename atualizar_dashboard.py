import pandas as pd
import datetime
import unicodedata
import os
import shutil
import glob
import json
import sys
import re

VERSAO_ATUAL = "v8.32-CorrecaoRoscaDefinitiva"
print("="*80)
print(f" 🚀 AGROVIA - MOTOR DE GESTÃO DE CUSTO DE FROTA [{VERSAO_ATUAL}]")
print("    Correção definitiva da renderização do Gráfico de Rosca e KPIs...")
print("="*80)

os.makedirs("Banco_de_Dados", exist_ok=True)
os.makedirs("versoes_codigo", exist_ok=True)
os.makedirs("backup_relatorios", exist_ok=True)
os.makedirs("relatorios_auditoria", exist_ok=True)

def limpar_texto(texto):
    if pd.isna(texto):
        return ""
    texto_str = str(texto).strip().lower()
    nfkd = unicodedata.normalize('NFKD', texto_str)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def carregar_excel_inteligente(caminho_arquivo):
    for linha_cabecalho in range(0, 5):
        try:
            df = pd.read_excel(caminho_arquivo, header=linha_cabecalho)
            colunas_str = [str(c) for c in df.columns]
            if any('natureza' in limpar_texto(c) for c in colunas_str) or any('valor' in limpar_texto(c) for c in colunas_str) or any('historico' in limpar_texto(c) for c in colunas_str):
                return df
        except Exception:
            continue
    return pd.read_excel(caminho_arquivo)

def encontrar_coluna(df, possiveis_nomes):
    colunas_norm = {limpar_texto(c): c for c in df.columns}
    for nome in possiveis_nomes:
        nome_limpo = limpar_texto(nome)
        if nome_limpo in colunas_norm:
            return colunas_norm[nome_limpo]
    for col_norm, col_original in colunas_norm.items():
        for nome in possiveis_nomes:
            if limpar_texto(nome) in col_norm:
                return col_original
    return None

def classificar_categoria_despesa(natureza, historico):
    texto = limpar_texto(f"{natureza} {historico}")
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

def df_row_has_col(row, col):
    try:
        return col in row.index and pd.notna(row[col])
    except:
        return False

padrao_busca = os.path.join("Banco_de_Dados", "*.*")
todos_arquivos = [f for f in glob.glob(padrao_busca) if f.lower().endswith(('.xlsx', '.xls')) and not os.path.basename(f).startswith('~$')]

if not todos_arquivos:
    sys.exit(1)

dfs_consolidados = []
for arq in todos_arquivos:
    try:
        df_temp = carregar_excel_inteligente(arq)
        if not df_temp.empty:
            dfs_consolidados.append(df_temp)
    except Exception as e:
        pass

if not dfs_consolidados:
    sys.exit(1)

df_global = pd.concat(dfs_consolidados, ignore_index=True)

try:
    col_valor = encontrar_coluna(df_global, ['Valor Líquido', 'Valor Liquido', 'VALOR', 'Valor'])
    col_rec_desp = encontrar_coluna(df_global, ['Receita/Despesa', 'Tipo Operação', 'Tipo de Operação', 'Operação'])
    col_nat = encontrar_coluna(df_global, ['Descrição (Natureza)', 'Natureza', 'Descricao (Natureza)'])
    col_hist = encontrar_coluna(df_global, ['Histórico', 'Historico', 'HISTORICO'])
    col_data = encontrar_coluna(df_global, ['Data', 'Competencia', 'Emissao', 'Vencimento', 'Data Movimento'])
    col_nr_unico = encontrar_coluna(df_global, ['Nr Único', 'Numero Unico', 'NrUnico', 'ID', 'Chave', 'Lancamento'])
    col_placa = encontrar_coluna(df_global, ['Placa', 'Marca [Placa]', 'Veiculo', 'Frota', 'Equipamento'])

    df_frota = df_global.copy()

    if col_data and col_data in df_frota.columns:
        df_frota['Data_Parsed'] = pd.to_datetime(df_frota[col_data], errors='coerce')
        df_frota['Mes'] = df_frota['Data_Parsed'].dt.month.fillna(1).astype(int)
        df_frota['Data_Str'] = df_frota['Data_Parsed'].dt.strftime('%d/%m/%Y').fillna('20/01/2026')
    else:
        df_frota['Mes'] = 1
        df_frota['Data_Str'] = '20/01/2026'

    df_frota['Valor_Numerico'] = pd.to_numeric(df_frota[col_valor], errors='coerce').fillna(0.0)

    if col_rec_desp and col_rec_desp in df_frota.columns:
        rec_desp_limpo = df_frota[col_rec_desp].astype(str).apply(limpar_texto)
        df_receitas = df_frota[rec_desp_limpo.str.contains('rec|cred|fatur', na=False) | (df_frota['Valor_Numerico'] > 0)]
        df_despesas = df_frota[rec_desp_limpo.str.contains('desp|pag|debit|cust', na=False) | (df_frota['Valor_Numerico'] < 0)]
    else:
        df_receitas = df_frota[df_frota['Valor_Numerico'] > 0]
        df_despesas = df_frota[df_frota['Valor_Numerico'] < 0]

    receitas_por_mes = [0.0] * 12
    despesas_por_mes = [0.0] * 12

    for _, row in df_receitas.iterrows():
        m = int(row['Mes'])
        if 1 <= m <= 12:
            receitas_por_mes[m - 1] += float(row['Valor_Numerico'])

    for _, row in df_despesas.iterrows():
        m = int(row['Mes'])
        val = abs(float(row['Valor_Numerico']))
        if 1 <= m <= 12:
            despesas_por_mes[m - 1] += val

    total_receita = float(df_receitas['Valor_Numerico'].sum())
    total_despesa = float(df_despesas['Valor_Numerico'].abs().sum())

    lista_detalhes_receitas = []
    for _, row in df_receitas.iterrows():
        nat = str(row[col_nat]) if col_nat and col_nat in df_receitas.columns else "Receita de Frete"
        hist = str(row[col_hist]) if col_hist and col_hist in df_receitas.columns else ""
        val = float(row['Valor_Numerico'])
        mes_num = f"{int(row['Mes']):02d}"
        data_str = row['Data_Str']
        nr_u = str(row[col_nr_unico]) if col_nr_unico and df_row_has_col(row, col_nr_unico) else "N/D"
        placa_val = str(row[col_placa]) if col_placa and df_row_has_col(row, col_placa) else "OOM9749"
        
        lista_detalhes_receitas.append({
            'data': data_str, 'mes': mes_num, 'parceiro': hist if hist else nat, 'natureza': nat, 'valor': val, 'nr_unico': nr_u, 'placa': placa_val
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
        nat = str(row[col_nat]) if col_nat and col_nat in df_despesas.columns else "Despesa Frota"
        hist = str(row[col_hist]) if col_hist and col_hist in df_despesas.columns else ""
        val = abs(float(row['Valor_Numerico']))
        mes_num = f"{int(row['Mes']):02d}"
        data_str = row['Data_Str']
        nr_u = str(row[col_nr_unico]) if col_nr_unico and df_row_has_col(row, col_nr_unico) else "N/D"
        placa_val = str(row[col_placa]) if col_placa and df_row_has_col(row, col_placa) else "OOM9749"
        
        cat_nome, cat_class, badge_sub = classificar_categoria_despesa(nat, hist)
        despesas_por_cat[cat_nome]['total'] += val
        despesas_por_cat[cat_nome]['linhas'].append({
            'data': data_str, 'mes': mes_num, 'parceiro': hist if hist else nat, 'natureza': nat, 'valor': val, 'nr_unico': nr_u, 'placa': placa_val
        })

    KM_TOTAL_PERIODO = 52000.0  
    cpk_calculado = (total_despesa / KM_TOTAL_PERIODO) if KM_TOTAL_PERIODO > 0 else 0.0

except Exception as e:
    sys.exit(1)

resultado_liquido = float(total_receita - total_despesa)
margem_liquida = float((resultado_liquido / total_receita * 100) if total_receita > 0 else 0)

arquivo_base = 'template.html' if os.path.exists('template.html') else 'index.html'
with open(arquivo_base, 'r', encoding='utf-8') as f:
    html_template = f.read()

data_hoje = datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')

def fmt_brl(val):
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

rec_fmt = fmt_brl(total_receita)
desp_fmt = fmt_brl(total_despesa)
res_abs = fmt_brl(abs(resultado_liquido))
res_fmt = f"R$ -{res_abs.replace('R$ ', '')}" if resultado_liquido < 0 else f"R$ {res_abs}"
margem_fmt = f"{margem_liquida:.2f}%"
cpk_fmt = fmt_brl(cpk_calculado)

html_final = html_template

# 1. Cabeçalho e Versão
html_final = re.sub(r'Atualizado em: \d{2}/\d{2}/\d{4} às \d{2}:\d{2}', f"Atualizado em: {data_hoje}", html_final)
html_final = re.sub(r'Agrovia DRE Master v[\d\.]+', 'Agrovia DRE Master v8.32', html_final)

# 2. Atualização dos KPIs principais por classe única
html_final = re.sub(r'class="kpi-value kpi-receita-bruta">[^<]+<', f'class="kpi-value kpi-receita-bruta">{rec_fmt}<', html_final)
html_final = re.sub(r'class="kpi-value kpi-custo-total">[^<]+<', f'class="kpi-value kpi-custo-total">{desp_fmt}<', html_final)
html_final = re.sub(r'class="kpi-value kpi-resultado-liquido">[^<]+<', f'class="kpi-value kpi-resultado-liquido">{res_fmt}<', html_final)
html_final = re.sub(r'class="kpi-value kpi-margem-liquida">[^<]+<', f'class="kpi-value kpi-margem-liquida">{margem_fmt}<', html_final)
html_final = re.sub(r'class="kpi-value kpi-cpk">[^<]+<', f'class="kpi-value kpi-cpk">{cpk_fmt}<', html_final)

# 3. Gráficos (Injeção de arrays numéricos)
str_rec_mes = json.dumps(receitas_por_mes[:8])
str_desp_mes = json.dumps(despesas_por_mes[:8])

html_final = re.sub(r'label:\s*\'Receita Bruta\',\s*data:\s*\[[^\]]+\]', f"label: 'Receita Bruta', data: {str_rec_mes}", html_final)
html_final = re.sub(r'label:\s*\'Custo Total Frota\',\s*data:\s*\[[^\]]+\]', f"label: 'Custo Total Frota', data: {str_desp_mes}", html_final)

# ORDENAÇÃO DECRESCENTE (DO MAIOR PARA O MENOR CUSTO)
cat_ordenadas = sorted(despesas_por_cat.items(), key=lambda x: x[1]['total'], reverse=True)
cat_nomes = [item[0] for item in cat_ordenadas]
lista_rosca = [item[1]['total'] for item in cat_ordenadas]

str_rosca = json.dumps(lista_rosca)
str_labels_rosca = json.dumps(cat_nomes, ensure_ascii=False)

# Injeção direta no bloco do gráfico de rosca para garantir renderização imediata
idx_doughnut = html_final.find("type: 'doughnut'")
if idx_doughnut != -1:
    bloco_doughnut = html_final[idx_doughnut:idx_doughnut+900]
    bloco_novo = re.sub(r'labels:\s*\[[^\]]*\]', f"labels: {str_labels_rosca}", bloco_doughnut)
    bloco_novo = re.sub(r'data:\s*\[[^\]]*\]', f"data: {str_rosca}", bloco_novo, count=1)
    html_final = html_final[:idx_doughnut] + bloco_novo + html_final[idx_doughnut+900:]

# 4. MONTAGEM DINÂMICA DA TABELA DRE COM NÚMERO ÚNICO & PLACA
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

html_final = re.sub(r'<tbody>.*?<\/tbody>', f"<tbody>{html_linhas_tabela}\n                    </tbody>", html_final, flags=re.DOTALL)

caminho_index = os.path.abspath("index.html")
with open(caminho_index, 'w', encoding='utf-8') as f:
    f.write(html_final)

print(f"📍 O ficheiro index.html foi ATUALIZADO com sucesso em: {caminho_index}")
print(f"🚛 Sucesso Total! Versão 8.32 executada com injeção direta na rosca.")


























