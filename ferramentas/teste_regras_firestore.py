"""Testa as regras do Firestore EM PRODUÇÃO com a conta teste_ai (usuário comum), pela API pública.

Uso (a conta tem de estar ativa; no fim, desativar):
    python ferramentas\\conta_teste_ai.py ativar [--primeiro-acesso]
    python ferramentas\\teste_regras_firestore.py
    python ferramentas\\conta_teste_ai.py desativar

Usa a mesma chave pública do site (acesso/firebase_config.js), por isso vale o mesmo que o browser:
as regras de firebase/firestore.rules publicadas na consola. Não usa a chave de serviço.
Também testa a auto-inscrição (conta criada por fora, sem perfil do ADM) e apaga essa conta no fim.
Nunca imprime senhas nem tokens. Sai com 0 se todos os testes passarem, 1 se algum falhar.
"""
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from fontes_dados import CAMINHO_CONTA_TESTE_AI, PASTA_PROJETO
from quarentena_online import DOMINIO_APELIDO, apelido_para_email
from regras_lancamento import configurar_stdout_utf8

CAMINHO_CONFIG_WEB = os.path.join(PASTA_PROJETO, "acesso", "firebase_config.js")
URL_AUTH = "https://identitytoolkit.googleapis.com/v1/accounts:{acao}?key={chave}"
URL_DOCS = "https://firestore.googleapis.com/v1/projects/{projeto}/databases/(default)/documents/"


def ler_config_web() -> tuple:
    with open(CAMINHO_CONFIG_WEB, encoding="utf-8") as f:
        texto = f.read()
    chave = re.search(r'apiKey:\s*"([^"]+)"', texto)
    projeto = re.search(r'projectId:\s*"([^"]+)"', texto)
    if not chave or not projeto:
        raise RuntimeError("apiKey/projectId não encontrados em acesso/firebase_config.js")
    return chave.group(1), projeto.group(1)


def pedir(metodo: str, url: str, corpo=None, token=None) -> tuple:
    """Devolve (código HTTP, JSON da resposta)."""
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    pedido = urllib.request.Request(url, data=dados, method=metodo)
    pedido.add_header("Content-Type", "application/json")
    if token:
        pedido.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read() or b"{}")
        except ValueError:
            return erro.code, {}


def campos(**valores) -> dict:
    convertidos = {}
    for nome, valor in valores.items():
        if isinstance(valor, bool):
            convertidos[nome] = {"booleanValue": valor}
        else:
            convertidos[nome] = {"stringValue": str(valor)}
    return {"fields": convertidos}


def mascara(nomes) -> str:
    return "&".join(f"updateMask.fieldPaths={n}" for n in nomes)


class Teste:
    def __init__(self, chave: str, projeto: str):
        self.chave = chave
        self.docs = URL_DOCS.format(projeto=projeto)
        self.resultados = []

    def auth(self, acao: str, corpo: dict) -> tuple:
        return pedir("POST", URL_AUTH.format(acao=acao, chave=self.chave), corpo)

    def verificar(self, descricao: str, codigo: int, esperado) -> None:
        esperados = esperado if isinstance(esperado, tuple) else (esperado,)
        ok = codigo in esperados
        self.resultados.append(ok)
        print(f"  [{'OK' if ok else 'FALHOU'}] {descricao}: HTTP {codigo} (esperado {'/'.join(map(str, esperados))})")

    def doc(self, metodo: str, caminho: str, token: str, corpo=None, query: str = "") -> int:
        url = self.docs + caminho + (f"?{query}" if query else "")
        return pedir(metodo, url, corpo, token)[0]


def testar_senha_errada(t: Teste, email: str, senha_certa: str) -> None:
    print("\n1) Login com senha errada")
    senha_errada = f"{(int(senha_certa) + 1) % 1_000_000:06d}"
    codigo, resp = t.auth("signInWithPassword", {"email": email, "password": senha_errada, "returnSecureToken": True})
    motivo = resp.get("error", {}).get("message", "")
    t.verificar(f"senha errada recusada ({motivo or 'sem motivo'})", codigo, 400)
    t.resultados[-1] = t.resultados[-1] and "idToken" not in resp


def testar_usuario_comum(t: Teste, uid: str, token: str, primeiro_acesso: bool) -> None:
    print(f"\n2) Usuário comum ({'1.º acesso, ainda sem trocar a senha' if primeiro_acesso else 'liberado'}) tenta escrever")
    t.verificar("ler o próprio perfil (permitido)", t.doc("GET", f"perfis/{uid}", token), 200)
    t.verificar("promover-se a ADM", t.doc("PATCH", f"perfis/{uid}", token, campos(papel="ADM"), mascara(["papel"])), 403)
    t.verificar("mudar o próprio nome/celular", t.doc(
        "PATCH", f"perfis/{uid}", token, campos(nome="Alterado", celular="11999999999"), mascara(["nome", "celular"])), 403)
    t.verificar("apagar o próprio perfil", t.doc("DELETE", f"perfis/{uid}", token), 403)
    uid_falso = "teste_regras_" + secrets.token_hex(6)
    t.verificar("cadastrar outro usuário como ADM", t.doc("PATCH", f"perfis/{uid_falso}", token, campos(
        apelido="intruso", nome="Intruso", celular="11999999999", papel="ADM", ativo=True, deve_trocar_senha=False)), 403)
    t.verificar("listar todos os perfis", t.doc("GET", "perfis", token), 403)
    t.verificar("gravar no resumo da quarentena", t.doc(
        "PATCH", "quarentena/atual", token, campos(gerado_em="adulterado"), mascara(["gerado_em"])), 403)
    t.verificar("gravar um lote na quarentena", t.doc(
        "PATCH", "quarentena/atual/lotes/999", token, campos(execucao_id="adulterado")), 403)
    t.verificar("apagar a quarentena", t.doc("DELETE", "quarentena/atual", token), 403)
    t.verificar("gravar noutra coleção", t.doc("PATCH", "outra_colecao/teste", token, campos(x="1")), 403)
    if primeiro_acesso:
        t.verificar("ler a quarentena antes de trocar a senha", t.doc("GET", "quarentena/atual", token), 403)
        t.verificar("sair da troca obrigatória e virar ADM no mesmo pedido", t.doc(
            "PATCH", f"perfis/{uid}", token, campos(deve_trocar_senha=False, papel="ADM"),
            mascara(["deve_trocar_senha", "papel"])), 403)
    else:
        # 404 = permitido mas ainda sem dados enviados pelo validar_entrada.
        t.verificar("ler a quarentena (permitido)", t.doc("GET", "quarentena/atual", token), (200, 404))
        t.verificar("voltar a ligar a troca de senha", t.doc(
            "PATCH", f"perfis/{uid}", token, campos(deve_trocar_senha=True), mascara(["deve_trocar_senha"])), 403)


def testar_auto_inscricao(t: Teste) -> None:
    print("\n3) Conta criada por fora (auto-inscrição com a chave pública, sem perfil do ADM)")
    email = f"intruso_{secrets.token_hex(4)}@{DOMINIO_APELIDO}"
    codigo, resp = t.auth("signUp", {"email": email, "password": f"{secrets.randbelow(1_000_000):06d}",
                                     "returnSecureToken": True})
    if "idToken" not in resp:
        motivo = resp.get("error", {}).get("message", "")
        print(f"  [OK] auto-inscrição recusada pelo Firebase: HTTP {codigo} ({motivo})")
        t.resultados.append(True)
        return
    token, uid = resp["idToken"], resp["localId"]
    try:
        t.verificar("criar o próprio perfil como ADM", t.doc("PATCH", f"perfis/{uid}", token, campos(
            apelido="intruso", nome="Intruso", celular="11999999999", papel="ADM", ativo=True,
            deve_trocar_senha=False)), 403)
        t.verificar("ler a quarentena", t.doc("GET", "quarentena/atual", token), 403)
        t.verificar("gravar na quarentena", t.doc(
            "PATCH", "quarentena/atual", token, campos(gerado_em="adulterado"), mascara(["gerado_em"])), 403)
        t.verificar("listar os perfis", t.doc("GET", "perfis", token), 403)
    finally:
        codigo_del, _ = t.auth("delete", {"idToken": token})
        print(f"  [{'OK' if codigo_del == 200 else 'ATENÇÃO'}] conta de teste da auto-inscrição apagada: HTTP {codigo_del}")


def main() -> int:
    configurar_stdout_utf8()
    if not os.path.isfile(CAMINHO_CONTA_TESTE_AI):
        print("[X] Conta teste_ai não está ativa. Correr: python ferramentas\\conta_teste_ai.py ativar")
        return 1
    with open(CAMINHO_CONTA_TESTE_AI, encoding="utf-8") as f:
        conta = json.load(f)
    chave, projeto = ler_config_web()
    t = Teste(chave, projeto)
    email = apelido_para_email(conta["apelido"])

    print("=" * 90)
    print(f" TESTE DAS REGRAS DO FIRESTORE EM PRODUÇÃO ({projeto}) - conta {conta['apelido']}")
    print("=" * 90)

    testar_senha_errada(t, email, conta["senha"])

    codigo, resp = t.auth("signInWithPassword", {"email": email, "password": conta["senha"], "returnSecureToken": True})
    if "idToken" not in resp:
        print(f"[X] Login com a senha certa falhou: HTTP {codigo} ({resp.get('error', {}).get('message', '')})")
        return 1
    print("  [OK] login com a senha certa aceite")
    testar_usuario_comum(t, resp["localId"], resp["idToken"], bool(conta.get("primeiro_acesso")))
    testar_auto_inscricao(t)

    falhas = t.resultados.count(False)
    print("-" * 90)
    print(f" {len(t.resultados) - falhas}/{len(t.resultados)} testes OK" + (f" | {falhas} FALHARAM" if falhas else ""))
    print(" Lembrete: python ferramentas\\conta_teste_ai.py desativar")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
