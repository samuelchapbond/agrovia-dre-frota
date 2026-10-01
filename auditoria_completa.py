import pandas as pd
import glob
import unicodedata
import os

print("="*90)
print(" 🔍 AGROVIA - AUDITORIA COMPLETA DOS DADOS DA FROTA")
print("="*90)

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
        return 'Combustível (Diesel)'
    elif any(k in texto for k in ['manut', 'peca', 'pneu', 'borracharia', 'oficina', 'mecanica']):
        return 'Manutenção'
    elif any(k in texto for k in ['pedag', 'taxa', 'pedagio']):
        return 'Pedágio'
    elif any(k in texto for k in ['segur', 'apólice', 'apolice']):
        return 'Seguros'
    elif any(k in texto for k in ['ipva', 'licenci', 'multa', 'detran', 'crlv']):
        return 'IPVA / Lic. / Multas'
    else:
        return 'Outros Custos'

# Procura ficheiros na pasta Banco_de_Dados
arquivos = glob.glob("Banco_de_Dados/*.*")
excel_files = [f for f in arquivos if f.lower().endswith(('.xlsx', '.xls'))]

if not excel_files:
    print("\n❌ [ERRO] Nenhum ficheiro Excel encontrado dentro da pasta 'Banco_de_Dados'.")
else:
    for arq in excel_files:
        print(f"\n📂 Ficheiro em análise: {arq}")
        df = carregar_excel_inteligente(arq)
        print(f"📌 Total de linhas detetadas: {len(df)}")
        
        col_valor = encontrar_coluna(df, ['Valor Líquido', 'Valor Liquido', 'VALOR', 'Valor'])
        col_nat = encontrar_coluna(df, ['Descrição (Natureza)', 'Natureza', 'Descricao (Natureza)'])
        col_hist = encontrar_coluna(df, ['Histórico', 'Historico', 'HISTORICO'])
        col_data = encontrar_coluna(df, ['Data', 'Competencia', 'Emissao', 'Vencimento', 'Data Movimento'])

        total_rec = 0.0
        total_desp = 0.0
        categorias_resumo = {
            'Combustível (Diesel)': 0.0,
            'Manutenção': 0.0,
            'Pedágio': 0.0,
            'Seguros': 0.0,
            'IPVA / Lic. / Multas': 0.0,
            'Outros Custos': 0.0
        }

        print("\n" + "-"*90)
        print(f"{'DATA':<12} | {'TIPO / CATEGORIA ALOCADA':<25} | {'VALOR (R$)':<15} | {'HISTÓRICO / NATUREZA'}")
        print("-"*90)

        for idx, row in df.iterrows():
            val_raw = row[col_valor] if col_valor and col_valor in df.columns else 0.0
            try:
                val = float(val_raw)
            except:
                val = 0.0
            
            nat = str(row[col_nat]) if col_nat and col_nat in df.columns else ""
            hist = str(row[col_hist]) if col_hist and col_hist in df.columns else ""
            data = str(row[col_data])[:10] if col_data and col_data in df.columns else "N/D"
            
            detalhe = f"{nat} - {hist}".strip("- ")
            
            if val > 0:
                total_rec += val
                tipo = "RECEITA BRUTA"
            else:
                desp_val = abs(val)
                total_desp += desp_val
                cat = classificar_categoria_despesa(nat, hist)
                categorias_resumo[cat] += desp_val
                tipo = f"DESP: {cat}"
                
            print(f"{data:<12} | {tipo:<25} | R$ {val:>12,.2f} | {detalhe}")

        print("-"*90)
        print(f"\n📊 RESUMO CONSOLIDADO QUE ALIMENTA O DASHBOARD:")
        print(f"   * Receita Bruta Total : R$ {total_rec:,.2f}")
        print(f"   * Custo Total da Frota: R$ {total_desp:,.2f}")
        print(f"   * Resultado Líquido   : R$ {total_rec - total_desp:,.2f}")
        print("\n   📋 Total por Categoria de Custo (Gráfico de Rosca & DRE):")
        for cat, valor in categorias_resumo.items():
            print(f"     - {cat}: R$ {valor:,.2f}")
        print("="*90)







        