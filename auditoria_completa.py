import pandas as pd
import unicodedata
import os
import re
import sys
import numpy as np

from fontes_dados import escrever_inventario

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

print("="*145)
print(" 🔍 AGROVIA - AUDITORIA DE BACKEND (NOME TEXTUAL DO OPERADOR E HISTÓRICO REDUZIDO)")
print("="*145)

PLACA_FROTA_PRINCIPAL = "OOM9749"
PLACEHOLDERS_PLACA = {"", "N/D", "NAN", "NONE", "NULL", "N/A", "NA", "[XYZ]", "-", "0", "SEM PLACA"}

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

def extrair_placa_do_texto(texto):
    if not texto:
        return None
    match = PADRAO_PLACA.search(str(texto).upper())
    if match:
        return match.group(1).replace("-", "")
    return None

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

def classificar_categoria_despesa(natureza, historico):
    texto = limpar_texto(f"{natureza} {historico}").lower()
    if any(k in texto for k in ['combust', 'diesel', 'arla']):
        return 'Combustível (Diesel)'
    elif any(k in texto for k in ['manut', 'peca', 'pneu', 'borracharia', 'oficina', 'mecanica']):
        return 'Manutenção'
    elif any(k in texto for k in ['pedag', 'taxa', 'pedagio']):
        return 'Pedágio'
    elif any(k in texto for k in ['segur', 'apólice', 'apolice', 'seguro']):
        return 'Seguros'
    elif any(k in texto for k in ['ipva', 'licenci', 'multa', 'detran', 'crlv']):
        return 'IPVA / Lic. / Multas'
    else:
        return 'Outros Custos'

CAMINHO_VEREDITO = os.path.join("relatorios_auditoria", "veredito_publicacao.txt")

def mes_referencia(data_raw):
    """Ano-mês (AAAA-MM) com o mesmo parse de datas do atualizar_dashboard.py."""
    dt = pd.to_datetime(data_raw, errors='coerce')
    return None if pd.isna(dt) else dt.strftime('%Y-%m')

def descrever_periodo(meses):
    if not meses:
        return "sem lançamentos"
    return f"{min(meses)} a {max(meses)} ({len(meses)} meses com lançamentos: {', '.join(sorted(meses))})"

def emitir_veredito(falhas, meses_receita, meses_custos):
    linhas = [
        "VEREDITO DE PUBLICAÇÃO - auditoria_completa.py",
        f"Gerado em: {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}",
        f"Frota principal: {PLACA_FROTA_PRINCIPAL}",
        f"Período da receita: {descrever_periodo(meses_receita)}",
        f"Período dos custos: {descrever_periodo(meses_custos)}",
    ]
    if falhas:
        linhas.append("RESULTADO: BLOQUEADO")
        linhas += [f"  - {f}" for f in falhas]
    else:
        linhas.append("RESULTADO: APROVADO")

    print("\n" + "="*145)
    print(" 🛡️  VEREDITO DE PUBLICAÇÃO")
    print("="*145)
    for linha in linhas[2:]:
        print(f" {linha}")
    print("="*145)

    os.makedirs(os.path.dirname(CAMINHO_VEREDITO), exist_ok=True)
    with open(CAMINHO_VEREDITO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")

arquivos = escrever_inventario("auditoria_completa.py")
excel_files = arquivos

falhas_auditoria = []
meses_receita = set()
meses_custos = set()

if not excel_files:
    print("\n❌ [ERRO] Nenhum ficheiro Excel encontrado dentro da pasta 'Banco_de_Dados'.")
    falhas_auditoria.append("Nenhum ficheiro Excel válido em Banco_de_Dados.")
else:
    for arq in excel_files:
        print(f"\n📂 Ficheiro em análise: {arq}")
        df = carregar_excel_inteligente(arq)
        print(f"📌 Total de linhas brutas detetadas: {len(df)}")
        
        col_valor = encontrar_coluna(df, ['Valor Líquido', 'Valor Liquido', 'VALOR', 'Valor'])
        col_nat = encontrar_coluna(df, ['Descrição (Natureza)', 'Natureza', 'Descricao (Natureza)'])
        col_hist = encontrar_coluna(df, ['Histórico', 'Historico', 'HISTORICO'])
        col_obs = encontrar_coluna(df, ['Observação', 'Observacao', 'Observação padrão', 'Observacao padrao'])
        col_ident = encontrar_coluna(df, ['Identificação', 'Identificacao'])
        col_nr_unico = encontrar_coluna_nr_unico(df)
        col_placa = encontrar_coluna(df, ['Placa', 'Marca [Placa]', 'Veiculo', 'Frota', 'Equipamento'])
        col_parceiro = encontrar_coluna_parceiro(df)
        col_operador = encontrar_coluna_operador(df)
        
        col_emissao = encontrar_coluna(df, ['Data Emissao', 'Emissao', 'Data Movimento', 'Data'])
        col_baixa = encontrar_coluna(df, ['Data Baixa', 'Baixa'])
        col_vencimento = encontrar_coluna(df, ['Data Vencimento', 'Vencimento'])

        transacoes_por_categoria = {
            'Receita Bruta': [],
            'Combustível (Diesel)': [],
            'Manutenção': [],
            'Pedágio': [],
            'Seguros': [],
            'IPVA / Lic. / Multas': [],
            'Outros Custos': []
        }
        
        lancamentos_tesou = []
        lancamentos_outros_veiculos = []
        linhas_ignoradas_lixo = 0
        placas_ocultas_recuperadas = 0
        placas_hifen_normalizadas = 0

        for idx, row in df.iterrows():
            val_raw = row[col_valor] if col_valor and col_valor in df.columns else None
            if pd.isna(val_raw):
                linhas_ignoradas_lixo += 1
                continue
                
            try:
                val = float(val_raw)
                if np.isnan(val):
                    linhas_ignoradas_lixo += 1
                    continue
            except (TypeError, ValueError):
                linhas_ignoradas_lixo += 1
                continue
            
            if val == 0.0:
                linhas_ignoradas_lixo += 1
                continue

            # Regra de Datas Inteligente
            if val > 0:
                data_raw = row[col_emissao] if col_emissao and col_emissao in df.columns else None
            else:
                b_val = row[col_baixa] if col_baixa and col_baixa in df.columns else None
                v_val = row[col_vencimento] if col_vencimento and col_vencimento in df.columns else None
                e_val = row[col_emissao] if col_emissao and col_emissao in df.columns else None
                
                if pd.notna(b_val) and str(b_val).strip() not in ["", "NaT", "nan", "None"]:
                    data_raw = b_val
                elif pd.notna(v_val) and str(v_val).strip() not in ["", "NaT", "nan", "None"]:
                    data_raw = v_val
                else:
                    data_raw = e_val

            if pd.isna(data_raw):
                linhas_ignoradas_lixo += 1
                continue
                
            data_str = str(data_raw)[:10]
            if data_str == "NaT" or len(data_str) < 8:
                linhas_ignoradas_lixo += 1
                continue

            nat = celula_texto(row[col_nat]) if col_nat and col_nat in df.columns else "N/D"
            hist_raw = celula_texto(row[col_hist]) if col_hist and col_hist in df.columns else ""
            obs = celula_texto(row[col_obs]) if col_obs and col_obs in df.columns else ""
            ident = celula_texto(row[col_ident]) if col_ident and col_ident in df.columns else ""
            parceiro = celula_texto(row[col_parceiro]) if col_parceiro and col_parceiro in df.columns else "N/D"
            operador = celula_texto(row[col_operador]) if col_operador and col_operador in df.columns else "N/D"
            if not parceiro:
                parceiro = "N/D"
            if not operador:
                operador = "N/D"
            
            texto_completo_para_busca = " - ".join([p for p in (nat, hist_raw, obs, ident) if p])
            hist_reduzido = reduzir_historico(hist_raw if hist_raw else nat, max_len=28)
            
            texto_limpo_verificacao = limpar_texto(texto_completo_para_busca).lower()
            if any(termo in texto_limpo_verificacao for termo in ['total geral', 'resumo', 'total da conta']):
                linhas_ignoradas_lixo += 1
                continue

            nr_u = str(row[col_nr_unico]).split('.')[0] if col_nr_unico and col_nr_unico in df.columns and pd.notna(row[col_nr_unico]) else "N/D"

            # Critério Tesou
            if 'tesou' in texto_limpo_verificacao:
                lancamentos_tesou.append({
                    'nr_unico': nr_u, 'data': data_str, 'placa': "N/A", 'valor': val, 'parceiro': parceiro, 'operador': operador, 'historico': hist_reduzido
                })
                continue

            # Análise da Placa
            placa_erp = str(row[col_placa]) if col_placa and col_placa in df.columns and pd.notna(row[col_placa]) else ""
            placa_erp_limpa = placa_erp.strip().upper()
            
            erp_sem_placa = placa_erp_limpa in ["", "N/D", "NAN", "NONE", "[XYZ]"] or "[" in placa_erp_limpa
            
            placa_final = placa_erp
            if erp_sem_placa:
                placa_extraida = extrair_placa_do_texto(texto_completo_para_busca)
                if placa_extraida:
                    placa_final = placa_extraida
                else:
                    placa_final = "NÃO INFORMADA"

            placa_upper_check = placa_final.upper()
            if placa_upper_check not in ["NÃO INFORMADA", "N/A", "N/D"] and PLACA_FROTA_PRINCIPAL not in placa_upper_check:
                lancamentos_outros_veiculos.append({
                    'nr_unico': nr_u, 'data': data_str, 'placa': placa_final, 'valor': val, 'parceiro': parceiro, 'operador': operador, 'historico': hist_reduzido
                })
                continue

            if PLACA_FROTA_PRINCIPAL in placa_upper_check:
                placa_exibicao = f"{PLACA_FROTA_PRINCIPAL} (Validada)"
            else:
                placa_exibicao = placa_final

            item = {
                'nr_unico': nr_u, 'data': data_str, 'placa': placa_exibicao, 'valor': val, 'parceiro': parceiro, 'operador': operador, 'historico': hist_reduzido
            }

            mes_ref = mes_referencia(data_raw)
            if val > 0:
                transacoes_por_categoria['Receita Bruta'].append(item)
                if mes_ref:
                    meses_receita.add(mes_ref)
            else:
                cat = classificar_categoria_despesa(nat, hist_raw)
                transacoes_por_categoria[cat].append(item)
                if mes_ref:
                    meses_custos.add(mes_ref)

        print(f"\n📊 [1] RESUMO FINANCEIRO E CONSOLIDAÇÃO (FROTA PRINCIPAL: {PLACA_FROTA_PRINCIPAL})")
        print(f"   * Linhas de lixo/rodapé/zero ignoradas: {linhas_ignoradas_lixo}")
        print(f"   * Lançamentos 'Tesou' isolados: {len(lancamentos_tesou)}")
        print(f"   * Lançamentos de Outros Veículos (Excluídos da Frota): {len(lancamentos_outros_veiculos)}")
        
        total_geral_rec = sum(i['valor'] for i in transacoes_por_categoria['Receita Bruta'])
        total_geral_desp = sum(abs(i['valor']) for cat, lista in transacoes_por_categoria.items() if cat != 'Receita Bruta' for i in lista)
        
        print(f"   * Receita Bruta Total : R$ {total_geral_rec:,.2f}")
        print(f"   * Custo Total Frota   : R$ {total_geral_desp:,.2f}")
        print(f"   * Resultado Líquido   : R$ {total_geral_rec - total_geral_desp:,.2f}")

        for cat_nome, itens in transacoes_por_categoria.items():
            if not itens:
                continue
            subtotal = sum(i['valor'] for i in itens)
            print("\n" + "="*145)
            print(f" 📂 GRUPO: {cat_nome.upper()} ({len(itens)} lançamentos | Total: R$ {subtotal:,.2f})")
            print("="*145)
            print(f"{'NR ÚNICO':<12} | {'DATA':<12} | {'PLACA':<22} | {'VALOR (R$)':<14} | {'PARCEIRO':<20} | {'OPERADOR':<15} | {'HISTÓRICO'}")
            print("-"*145)
            for i in itens:
                print(f"{i['nr_unico']:<12} | {i['data']:<12} | {i['placa']:<22} | R$ {i['valor']:>11,.2f} | {i['parceiro']:<20} | {i['operador']:<15} | {i['historico']}")

        if lancamentos_tesou:
            print("\n" + "="*145)
            print(f" 🟡 LANÇAMENTOS 'TESOU' DETETADOS ({len(lancamentos_tesou)} itens - Requerem Contrapartida / Exclusão)")
            print("="*145)
            print(f"{'NR ÚNICO':<12} | {'DATA':<12} | {'PLACA':<22} | {'VALOR (R$)':<14} | {'PARCEIRO':<20} | {'OPERADOR':<15} | {'HISTÓRICO'}")
            print("-"*145)
            for i in lancamentos_tesou:
                print(f"{i['nr_unico']:<12} | {i['data']:<12} | {i['placa']:<22} | R$ {i['valor']:>11,.2f} | {i['parceiro']:<20} | {i['operador']:<15} | {i['historico']}")

        if lancamentos_outros_veiculos:
            print("\n" + "="*145)
            print(f" 🚨 ALERTAS CRÍTICOS: LANÇAMENTOS DE OUTROS VEÍCULOS ({len(lancamentos_outros_veiculos)} itens - Excluídos dos Custos da Frota)")
            print("="*145)
            print(" 💡 Estes registos contêm placas de terceiros e devem ser corrigidos pelos operadores no ERP Sankhya:")
            print(f"{'NR ÚNICO':<12} | {'DATA':<12} | {'PLACA DETETADA':<22} | {'VALOR (R$)':<14} | {'PARCEIRO':<20} | {'OPERADOR':<15} | {'HISTÓRICO'}")
            print("-"*145)
            for i in lancamentos_outros_veiculos:
                print(f"{i['nr_unico']:<12} | {i['data']:<12} | {i['placa']:<22} | R$ {i['valor']:>11,.2f} | {i['parceiro']:<20} | {i['operador']:<15} | {i['historico']}")
        else:
            print("\n" + "="*145)
            print(" ✅ [OK] Nenhum lançamento de outro veículo detetado fora da frota principal.")
            print("="*145)

if excel_files:
    if not meses_receita:
        falhas_auditoria.append("Nenhuma receita da frota principal com data válida.")
    if not meses_custos:
        falhas_auditoria.append("Nenhum custo da frota principal com data válida.")
    if meses_receita and meses_custos:
        periodo_receita = (min(meses_receita), max(meses_receita))
        periodo_custos = (min(meses_custos), max(meses_custos))
        if periodo_receita != periodo_custos:
            falhas_auditoria.append(
                f"Período da receita ({periodo_receita[0]} a {periodo_receita[1]}) diferente do período dos custos "
                f"({periodo_custos[0]} a {periodo_custos[1]})."
            )

emitir_veredito(falhas_auditoria, meses_receita, meses_custos)
sys.exit(1 if falhas_auditoria else 0)
