// Configuração web do Firebase. É pública por desenho (vai no site): quem protege os dados são as
// regras em firebase/firestore.rules. O segredo real é a chave de serviço em config_local/, nunca aqui.
// Copiar de: Consola Firebase > Definições do projeto > As suas apps > App Web > Configuração do SDK.
export const firebaseConfig = {
    apiKey: "AIzaSyCBRX7fzZHm6QYF5ZKd_rohqrSr0boPbKY",
    authDomain: "agrovia-dre-frota.firebaseapp.com",
    projectId: "agrovia-dre-frota",
    storageBucket: "agrovia-dre-frota.firebasestorage.app",
    messagingSenderId: "913562123769",
    appId: "1:913562123769:web:4d5993e73affc4ad49d128"
};
