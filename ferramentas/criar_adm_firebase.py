"""Cria (ou repõe) um ADM do login da quarentena no Firebase.

Uso:
    python ferramentas\\criar_adm_firebase.py

Pede apelido, nome, celular e senha de 6 dígitos (a senha não aparece no ecrã).
Se o apelido já existir, a senha é redefinida e o perfil passa a ADM ativo.
Precisa da chave de serviço em config_local/firebase_servico.json.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from quarentena_online import (NOME_APP, PADRAO_APELIDO, PADRAO_CELULAR, PADRAO_SENHA, apelido_para_email,
                               ligar_firestore, normalizar_apelido)
from regras_lancamento import configurar_stdout_utf8


def perguntar(texto: str, padrao, erro: str, normalizar=lambda v: v.strip()) -> str:
    while True:
        valor = normalizar(input(texto))
        if padrao.match(valor):
            return valor
        print(f"  [X] {erro}")


def perguntar_senha() -> str:
    while True:
        senha = getpass.getpass("Senha (6 dígitos): ").strip()
        if not PADRAO_SENHA.match(senha):
            print("  [X] A senha tem de ter exatamente 6 dígitos.")
            continue
        if getpass.getpass("Confirmar senha: ").strip() != senha:
            print("  [X] As senhas não coincidem.")
            continue
        return senha


def main() -> int:
    configurar_stdout_utf8()
    try:
        firebase_admin, db = ligar_firestore()
    except RuntimeError as exc:
        print(f"[X] {exc}")
        return 1
    from firebase_admin import auth, firestore

    print("=" * 70)
    print(" AGROVIA - CRIAR ADM DO LOGIN DA QUARENTENA (Firebase)")
    print("=" * 70)
    apelido = perguntar("Apelido (3-30: letras, números, . _ -): ", PADRAO_APELIDO,
                        "Apelido inválido.", normalizar_apelido)
    nome = input("Nome: ").strip() or apelido
    celular = perguntar("Celular com DDD (11 dígitos, ex.: 11987654321): ", PADRAO_CELULAR,
                        "Celular inválido.", lambda v: "".join(c for c in v if c.isdigit()))
    senha = perguntar_senha()

    app = firebase_admin.get_app(NOME_APP)
    email = apelido_para_email(apelido)
    try:
        usuario = auth.get_user_by_email(email, app=app)
        auth.update_user(usuario.uid, password=senha, disabled=False, app=app)
        acao = "senha redefinida e promovido a ADM"
    except auth.UserNotFoundError:
        usuario = auth.create_user(email=email, password=senha, display_name=nome, app=app)
        acao = "criado"

    db.collection("perfis").document(usuario.uid).set({
        "apelido": apelido,
        "nome": nome,
        "celular": celular,
        "papel": "ADM",
        "ativo": True,
        "deve_trocar_senha": False,
        "criado_por": "ferramentas/criar_adm_firebase.py",
        "criado_em": firestore.SERVER_TIMESTAMP,
    }, merge=True)
    print(f"[OK] ADM '{apelido}' {acao}. Entrar em acesso/login.html com este apelido e a senha.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
