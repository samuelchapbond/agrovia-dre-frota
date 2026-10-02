import pandas as pd
import unicodedata

from fontes_dados import listar_ficheiros_fonte

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

arquivos = listar_ficheiros_fonte()
for arq in arquivos:
    print(f"\n📂 A auditar o ficheiro com o Motor Inteligente: {arq}")
    df = carregar_excel_inteligente(arq)
    print(f"   -> Total de registos lidos: {len(df)}")
    
    # Encontrar coluna de valor
    for col in df.columns:
        if 'valor' in limpar_texto(str(col)):
            valores_num = pd.to_numeric(df[col], errors='coerce').fillna(0)
            print(f"   -> Coluna de Valor Identificada: '{col}'")
            print(f"      • Soma Positiva (Entradas/Receitas): R$ {valores_num[valores_num > 0].sum():,.2f}")
            print(f"      • Soma Negativa (Saídas/Despesas): R$ {valores_num[valores_num < 0].abs().sum():,.2f}")


