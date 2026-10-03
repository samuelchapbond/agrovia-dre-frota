"""Relatório de abastecimento FICTÍCIO para testar CPK e Km/L por ano no painel.

Uso:
    python laboratorio\\abastecimento_teste.py instalar   -> grava o Excel de teste em dados/banco_de_dados
    python laboratorio\\abastecimento_teste.py remover    -> apaga o Excel de teste

Os valores são inventados. Remover antes de correr atualizar.bat, senão o painel publicado
mostra CPK e Km/L falsos.
"""
import datetime
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from fontes_dados import PASTA_DADOS  # noqa: E402
from regras_lancamento import PLACA_FROTA_PRINCIPAL  # noqa: E402

NOME_FICHEIRO = "abastecimento_TESTE_FICTICIO.xlsx"
CAMINHO = os.path.join(PASTA_DADOS, NOME_FICHEIRO)


def gerar_registos() -> pd.DataFrame:
    """Abastecimentos a cada 14 dias de jan/2026 a jan/2027, com hodómetro sempre a subir."""
    data = datetime.date(2026, 1, 3)
    hodometro = 152_300
    km_trechos = [1180, 1320, 1250, 1410, 1090, 1360, 1220]
    km_por_litro = [2.45, 2.60, 2.38, 2.52, 2.70, 2.41, 2.55]
    registos = [{"Placa": PLACA_FROTA_PRINCIPAL, "Data Abastecimento": data, "Hodômetro": hodometro, "Litros": 480.0}]
    i = 0
    while data < datetime.date(2027, 1, 25):
        data += datetime.timedelta(days=14)
        km = km_trechos[i % len(km_trechos)]
        hodometro += km
        litros = round(km / km_por_litro[i % len(km_por_litro)], 2)
        registos.append({"Placa": PLACA_FROTA_PRINCIPAL, "Data Abastecimento": data, "Hodômetro": hodometro, "Litros": litros})
        i += 1
    return pd.DataFrame(registos)


def instalar() -> None:
    df = gerar_registos()
    os.makedirs(PASTA_DADOS, exist_ok=True)
    df.to_excel(CAMINHO, index=False)
    print(f"Instalado: {CAMINHO}")
    print(f"{len(df)} registos | {df['Data Abastecimento'].min()} a {df['Data Abastecimento'].max()} | "
          f"hodómetro {df['Hodômetro'].min()} a {df['Hodômetro'].max()}")


def remover() -> None:
    if os.path.exists(CAMINHO):
        os.remove(CAMINHO)
        print(f"Removido: {CAMINHO}")
    else:
        print("Nada a remover: o ficheiro de teste não existe.")


if __name__ == "__main__":
    acoes = {"instalar": instalar, "remover": remover}
    if len(sys.argv) != 2 or sys.argv[1] not in acoes:
        print(__doc__)
        sys.exit(1)
    acoes[sys.argv[1]]()
