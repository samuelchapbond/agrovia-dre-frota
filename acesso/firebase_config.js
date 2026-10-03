// Configuração web do Firebase. É pública por desenho (vai no site): quem protege os dados são as
// regras em firebase/firestore.rules. O segredo real é a chave de serviço em config_local/, nunca aqui.
// Copiar de: Consola Firebase > Definições do projeto > As suas apps > App Web > Configuração do SDK.
export const firebaseConfig = {
    apiKey: "",
    authDomain: "",
    projectId: "",
    storageBucket: "",
    messagingSenderId: "",
    appId: ""
};
