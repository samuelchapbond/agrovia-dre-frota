// Funções partilhadas pelas telas de acesso (login, troca de senha, ADM e quarentena).
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js";
import { firebaseConfig } from "./firebase_config.js";

// Mesmo domínio de src/quarentena_online.py. ".invalid" é reservado e nunca recebe e-mail.
export const DOMINIO_APELIDO = "agrovia-dre.invalid";
export const PADRAO_APELIDO = /^[a-z0-9._-]{3,30}$/;
export const PADRAO_SENHA = /^\d{6}$/;
export const PADRAO_CELULAR = /^\d{11}$/;

export const configurado = Boolean(firebaseConfig.apiKey && firebaseConfig.projectId);
export const app = configurado ? initializeApp(firebaseConfig) : null;
export const auth = configurado ? getAuth(app) : null;
export const db = configurado ? getFirestore(app) : null;

export function normalizarApelido(valor) {
    return String(valor).trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

export function apelidoParaEmail(apelido) {
    return `${normalizarApelido(apelido)}@${DOMINIO_APELIDO}`;
}

export function soDigitos(valor) {
    return String(valor).replace(/\D/g, "");
}

export function formatarCelular(c) {
    return c && c.length === 11 ? `(${c.slice(0, 2)}) ${c.slice(2, 7)}-${c.slice(7)}` : (c || "");
}

const MENSAGENS = {
    "auth/invalid-credential": "Usuário ou senha inválidos.",
    "auth/invalid-login-credentials": "Usuário ou senha inválidos.",
    "auth/wrong-password": "Usuário ou senha inválidos.",
    "auth/user-not-found": "Usuário ou senha inválidos.",
    "auth/invalid-email": "Usuário ou senha inválidos.",
    "auth/user-disabled": "Este acesso foi desativado. Fale com o ADM.",
    "auth/too-many-requests": "Muitas tentativas. Aguarde alguns minutos e tente de novo.",
    "auth/network-request-failed": "Sem ligação à internet.",
    "auth/email-already-in-use": "Esse apelido já está cadastrado.",
    "auth/weak-password": "Senha fraca: use 6 dígitos.",
    "auth/requires-recent-login": "Por segurança, entre de novo antes de trocar a senha.",
    "auth/unauthorized-domain": "Este endereço não está autorizado no Firebase (Authentication > Domínios autorizados).",
    "permission-denied": "Sem permissão para esta ação.",
    "unavailable": "Serviço indisponível ou sem internet. Tente de novo.",
};

export function mensagemErro(erro) {
    return MENSAGENS[erro && erro.code] || `Erro inesperado (${(erro && (erro.code || erro.message)) || erro}).`;
}

export function mostrarMensagem(el, texto, tipo = "erro") {
    el.textContent = texto;
    el.className = `mensagem ${tipo}`;
    el.hidden = !texto;
}

export function avisoNaoConfigurado(el) {
    el.innerHTML = '<div class="card aviso-config"><h2>Login ainda não configurado</h2>' +
        "<p>Falta preencher <code>acesso/firebase_config.js</code> com a configuração da app web do Firebase.</p></div>";
}

function esperarUsuario() {
    return new Promise(resolve => {
        const parar = onAuthStateChanged(auth, usuario => { parar(); resolve(usuario); });
    });
}

export async function lerPerfil(uid) {
    const snap = await getDoc(doc(db, "perfis", uid));
    return snap.exists() ? snap.data() : null;
}

// Devolve { usuario, perfil } ou redireciona e devolve null. pagina: "quarentena" | "adm" | "trocar".
export async function exigirSessao(pagina) {
    const usuario = await esperarUsuario();
    if (!usuario) { location.replace("login.html"); return null; }
    let perfil = null;
    try { perfil = await lerPerfil(usuario.uid); } catch (e) { perfil = null; }
    if (!perfil || perfil.ativo !== true) {
        await signOut(auth);
        location.replace("login.html?motivo=sem_acesso");
        return null;
    }
    if (perfil.deve_trocar_senha && pagina !== "trocar") { location.replace("trocar_senha.html"); return null; }
    if (!perfil.deve_trocar_senha && pagina === "trocar") { location.replace("quarentena.html"); return null; }
    if (pagina === "adm" && perfil.papel !== "ADM") { location.replace("quarentena.html?motivo=so_adm"); return null; }
    return { usuario, perfil };
}

export async function sair() {
    await signOut(auth);
    location.replace("login.html");
}
