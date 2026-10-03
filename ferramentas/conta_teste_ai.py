"""Conta teste_ai: usuário comum que o agente IA usa para testar o login da quarentena.

Uso:
    python ferramentas\\conta_teste_ai.py ativar                    # senha nova, entra direto na quarentena
    python ferramentas\\conta_teste_ai.py ativar --primeiro-acesso  # senha nova, obriga a trocar a senha
    python ferramentas\\conta_teste_ai.py desativar                 # bloqueia, corta sessões, apaga a senha local
    python ferramentas\\conta_teste_ai.py estado

Fica bloqueada fora dos testes e nunca é ADM. A senha de cada ativação vai só para
config_local/teste_ai.json (fora do git) e nunca é impressa no ecrã.
"""
import argparse
import datetime
import json
import os
import secrets
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from fontes_dados import CAMINHO_CONTA_TESTE_AI, URL_LOGIN_QUARENTENA
from quarentena_online import NOME_APP, apelido_para_email, ligar_firestore
from regras_lancamento import configurar_stdout_utf8

APELIDO = "teste_ai"
NOME = "Teste AI (agente)"
CELULAR = "00000000000"


def gerar_senha() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def obter_usuario(auth, app):
    try:
        return auth.get_user_by_email(apelido_para_email(APELIDO), app=app)
    except auth.UserNotFoundError:
        return None


def ativar(auth, firestore, db, app, primeiro_acesso: bool) -> None:
    senha = gerar_senha()
    usuario = obter_usuario(auth, app)
    if usuario is None:
        usuario = auth.create_user(email=apelido_para_email(APELIDO), password=senha, display_name=NOME, app=app)
        acao = "criada e ativada"
    else:
        auth.update_user(usuario.uid, password=senha, disabled=False, app=app)
        acao = "ativada"

    db.collection("perfis").document(usuario.uid).set({
        "apelido": APELIDO,
        "nome": NOME,
        "celular": CELULAR,
        "papel": "USUARIO",
        "ativo": True,
        "deve_trocar_senha": primeiro_acesso,
        "atualizado_por": "ferramentas/conta_teste_ai.py",
        "atualizado_em": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    os.makedirs(os.path.dirname(CAMINHO_CONTA_TESTE_AI), exist_ok=True)
    with open(CAMINHO_CONTA_TESTE_AI, "w", encoding="utf-8") as f:
        json.dump({
            "apelido": APELIDO,
            "senha": senha,
            "url_login": URL_LOGIN_QUARENTENA,
            "primeiro_acesso": primeiro_acesso,
            "ativado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        }, f, ensure_ascii=False, indent=2)

    modo = "com troca de senha obrigatória" if primeiro_acesso else "sem troca de senha"
    print(f"[OK] Conta '{APELIDO}' {acao} ({modo}). Senha nova em config_local/teste_ai.json.")
    print("     No fim do teste: python ferramentas\\conta_teste_ai.py desativar")


def desativar(auth, firestore, db, app) -> None:
    usuario = obter_usuario(auth, app)
    if usuario is not None:
        auth.update_user(usuario.uid, password=gerar_senha(), disabled=True, app=app)
        auth.revoke_refresh_tokens(usuario.uid, app=app)
        db.collection("perfis").document(usuario.uid).set({
            "papel": "USUARIO",
            "ativo": False,
            "atualizado_por": "ferramentas/conta_teste_ai.py",
            "atualizado_em": firestore.SERVER_TIMESTAMP,
        }, merge=True)
    if os.path.isfile(CAMINHO_CONTA_TESTE_AI):
        os.remove(CAMINHO_CONTA_TESTE_AI)
    print(f"[OK] Conta '{APELIDO}' bloqueada; sessões cortadas e senha local apagada."
          if usuario else f"[OK] Conta '{APELIDO}' não existe; nada a bloquear.")


def estado(auth, db, app) -> None:
    usuario = obter_usuario(auth, app)
    if usuario is None:
        print(f"Conta '{APELIDO}': não existe (é criada no 1.º 'ativar').")
        return
    perfil = (db.collection("perfis").document(usuario.uid).get().to_dict()) or {}
    print(f"Conta '{APELIDO}': login {'BLOQUEADO' if usuario.disabled else 'ATIVO'} | "
          f"perfil ativo={perfil.get('ativo')} papel={perfil.get('papel')} "
          f"deve_trocar_senha={perfil.get('deve_trocar_senha')} | "
          f"senha local {'presente' if os.path.isfile(CAMINHO_CONTA_TESTE_AI) else 'ausente'}")


def main() -> int:
    configurar_stdout_utf8()
    parser = argparse.ArgumentParser(description="Conta teste_ai do login da quarentena.")
    parser.add_argument("comando", choices=["ativar", "desativar", "estado"])
    parser.add_argument("--primeiro-acesso", action="store_true",
                        help="obriga a trocar a senha no login (testa trocar_senha.html)")
    args = parser.parse_args()

    try:
        firebase_admin, db = ligar_firestore()
    except RuntimeError as exc:
        print(f"[X] {exc}")
        return 1
    from firebase_admin import auth, firestore
    app = firebase_admin.get_app(NOME_APP)

    if args.comando == "ativar":
        ativar(auth, firestore, db, app, args.primeiro_acesso)
    elif args.comando == "desativar":
        desativar(auth, firestore, db, app)
    else:
        estado(auth, db, app)
    return 0


if __name__ == "__main__":
    sys.exit(main())
