"""Envio da quarentena de lançamentos para o Firestore (Firebase, plano Spark gratuito).

A tela online (acesso/quarentena.html, no GitHub Pages) só mostra estes dados depois do login,
conforme firebase/firestore.rules. A chave de serviço fica em config_local/ (fora do git).

Estrutura no Firestore:
    quarentena/atual                 resumo (KPIs, ficheiros, gerado em, modo, execucao_id, n_lotes)
    quarentena/atual/lotes/{000..}   erros em lotes de TAMANHO_LOTE (limite de 1 MB por documento)
"""
import json
import os
import re
import unicodedata
import uuid

from fontes_dados import CAMINHO_CHAVE_FIREBASE

DOMINIO_APELIDO = "agrovia-dre.invalid"
PADRAO_APELIDO = re.compile(r"^[a-z0-9._-]{3,30}$")
PADRAO_SENHA = re.compile(r"^\d{6}$")
PADRAO_CELULAR = re.compile(r"^\d{11}$")
TAMANHO_LOTE = 300
NOME_APP = "agrovia_quarentena"


def normalizar_apelido(apelido: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(apelido).strip().lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def apelido_para_email(apelido: str) -> str:
    return f"{normalizar_apelido(apelido)}@{DOMINIO_APELIDO}"


def ligar_firestore():
    """Devolve (firebase_admin, cliente Firestore) ou levanta RuntimeError com o motivo legível."""
    if not os.path.isfile(CAMINHO_CHAVE_FIREBASE):
        raise RuntimeError("chave de serviço não encontrada em config_local/firebase_servico.json")
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise RuntimeError(f"biblioteca firebase-admin não instalada ({exc}); correr: pip install -r requirements.txt")
    try:
        app = firebase_admin.get_app(NOME_APP)
    except ValueError:
        app = firebase_admin.initialize_app(credentials.Certificate(CAMINHO_CHAVE_FIREBASE), name=NOME_APP)
    return firebase_admin, firestore.client(app=app)


def calcular_resumo(erros: list, resumo_ficheiros: list, gerado_em: str, modo: str) -> dict:
    bloqueantes = [e for e in erros if e["severidade"] == "BLOQUEANTE"]
    linhas_bloqueadas = {(e["ficheiro"], e["linha"]): abs(e["valor"] or 0) for e in bloqueantes}
    return {
        "gerado_em": gerado_em,
        "modo": modo,
        "total_erros": len(erros),
        "bloqueantes": len(bloqueantes),
        "avisos": len(erros) - len(bloqueantes),
        "valor_risco": round(sum(linhas_bloqueadas.values()), 2),
        "lancamentos_bloqueados": len(linhas_bloqueadas),
        "promovidos": sum(1 for r in resumo_ficheiros if r["decisao"].startswith("PROMOVIDO")),
        "retidos": sum(1 for r in resumo_ficheiros if r["decisao"].startswith("RETIDO")),
        "ficheiros": resumo_ficheiros,
    }


CAMPOS_ERRO = ("severidade", "regra", "ficheiro", "linha", "nr_unico", "data", "parceiro",
               "operador", "valor", "placa_erp", "historico", "detalhe", "acao", "status")


def publicar_quarentena(erros: list, resumo: dict) -> str:
    """Grava resumo + erros no Firestore. Devolve mensagem de sucesso; levanta RuntimeError se falhar."""
    _, db = ligar_firestore()
    erros_limpos = json.loads(json.dumps([{k: e.get(k) for k in CAMPOS_ERRO} for e in erros],
                                         ensure_ascii=False, default=str))
    resumo_limpo = json.loads(json.dumps(resumo, ensure_ascii=False, default=str))

    execucao_id = uuid.uuid4().hex
    lotes = [erros_limpos[i:i + TAMANHO_LOTE] for i in range(0, len(erros_limpos), TAMANHO_LOTE)]
    doc_atual = db.collection("quarentena").document("atual")
    col_lotes = doc_atual.collection("lotes")

    try:
        # Lotes primeiro e resumo depois: a tela só aceita lotes com o execucao_id do resumo.
        for i, lote in enumerate(lotes):
            col_lotes.document(f"{i:03d}").set({"execucao_id": execucao_id, "indice": i, "erros": lote})
        doc_atual.set({**resumo_limpo, "execucao_id": execucao_id, "n_lotes": len(lotes)})
        for antigo in col_lotes.stream():
            if antigo.id >= f"{len(lotes):03d}":
                antigo.reference.delete()
    except Exception as exc:
        raise RuntimeError(f"falha ao gravar no Firestore ({exc.__class__.__name__}: {exc})")
    return f"quarentena online atualizada ({len(erros_limpos)} pendência(s) em {len(lotes)} lote(s))"
