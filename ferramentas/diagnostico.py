import os
import re

CAMINHO_TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "template.html")

try:
    with open(CAMINHO_TEMPLATE, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print("=== DIAGNÓSTICO DO TEMPLATE.HTML ===")
    # Procura por padrões de valores monetários ou percentuais no template
    valores = re.findall(r'(R\$\s*[\d\.,-]+|-?[\d\.,]+%)', html)
    print(f"Valores encontrados no template: {valores[:10]}")
    
except Exception as e:
    print(f"Erro ao ler o template: {e}")




    