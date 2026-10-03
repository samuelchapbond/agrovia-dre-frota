# Relatório de Status e Evolução do Projeto: Painel Gerencial Agrovia (DRE Frota)
**Gestor e Auditor Técnico:** Samuel O Silva
**Última revisão das pendências:** 03/10/2026

## Índice
1. Visão Geral e Objetivos do Projeto
2. O Papel e as Funções da Inteligência Artificial no Projeto
3. O Que Já Foi Feito (Status Atual)
4. **Pendências por grau de urgência** ← começar por aqui
5. Riscos aceites e cuidados permanentes
6. Decisões do SAMUEL (registo)
7. Etapas do projeto
8. Histórico de entregas (concluído)

## 1. Visão Geral e Objetivos do Projeto
O projeto **Agrovia - Gestão de Custo de Frota** tem como finalidade centralizar, auditar e exibir os indicadores financeiros e operacionais (DRE Gerencial) de frotas de transporte (foco inicial em conjunto carreta/rodocaçamba), utilizando dados brutos extraídos do **ERP Sankhya**. 

A principal intenção é garantir transparência analítica por meio de um painel web intuitivo, de alta performance, equipado com visual moderno e responsivo (visões PC e Mobile).

## 2. O Papel e as Funções da Inteligência Artificial no Projeto
A IA atua como **Arquiteta de Software, Engenheira de Front-End e Auditora de Dados**, exercendo as seguintes funções:
* **Validação de Consistência (Auditoria IA):** Cruzamento e verificação de dados financeiros e operacionais para evitar divergências nos lançamentos de receitas, custos com diesel, manutenção, pedágios, seguros e encargos.
* **Refinamento de Layout e UX/UI:** Tradução dos direcionamentos de design do gestor em código estruturado (HTML5, CSS3, JavaScript e Chart.js), aplicando a paleta de cores oficial da empresa.
* **Geração Automatizada de Código:** Criação iterativa de versões estáveis para unificar componentes visuais (como o rodapé de assinatura técnica e a tabela analítica oculta/expansível).

## 3. O Que Já Foi Feito (Status Atual)
* **Estrutura Base e Identidade Visual:** Implementação bem-sucedida da nova paleta de cores corporativa da Agrovia (tons de verde profundo, verde-limão e ciano nos gráficos e cartões KPI).
* **Painel de Indicadores (KPIs Executivos):** Exibição consolidada de Receita Bruta Total, Custo Total da Frota, Resultado Líquido, Margem Líquida, CPK (Custo por KM) e Consumo Médio (Km/L).
* **Gráficos Dinâmicos (Chart.js):** Gráfico principal de evolução mensal (Receita vs. Custo vs. Resultado Líquido) e gráfico de rosca de composição de custos por categoria.
* **Auditoria Detalhada (Tabela Analítica Ocultável):** Inclusão da tabela interativa contendo o histórico detalhado dos lançamentos do ERP Sankhya, com botões para alternar entre as visões de PC e Mobile.
* **Assinatura e Credenciamento Técnico:** Inserção oficial do rodapé e cabeçalho identificando a Gestão e Auditoria Técnica de Samuel O Silva.

---

## 4. Pendências por grau de urgência

### 4.0 Como classificar e manter esta lista

| Grau | Quando usar | Quando resolver |
|------|-------------|-----------------|
| 🔴 **Urgente** | O número publicado está errado ou engana; risco de segurança ou de dados financeiros saírem para o git ou para a internet; publicação travada. | Antes da próxima publicação (`atualizar.bat`). |
| 🟠 **Alta** | Falta um dado ou uma função e uma parte do painel fica sem informação (ex.: KPI "Sem dado"); risco operacional que se repete. | Nos próximos dias. |
| 🟡 **Média** | Robustez, manutenção, decisões em aberto que não mudam o número de hoje. | Quando houver folga. |
| 🟢 **Baixa** | Melhoria, conforto, ideia para o futuro. | Sem prazo. |

Regras da lista:
- Cada item tem: o que é e porquê, **quem age** (SAMUEL ou IA), **onde** (ficheiro/pasta) e **desde** (data em que entrou).
- Ao concluir: marcar `[x]`, pôr a data e passar o item para a secção 8 (Histórico). Decisões novas do SAMUEL vão também para a secção 6.
- Se o grau mudar (ex.: uma Baixa passa a travar a publicação), mover o item e dizer porquê.
- Repositório público: **nenhum valor em R$ nem dado de lançamento** neste ficheiro. Contagens e nomes de ficheiros podem; valores ficam no `log_execucao.txt` local.

### 🔴 Urgente

- [ ] **U1. Período dos custos diferente do período da receita** — resultado e margem do painel misturam períodos e não são comparáveis.
  - Evidência: `saidas/relatorios_auditoria/veredito_publicacao.txt` (03/10/2026 18:33): APROVADO com aviso; receita de 2026-01 a 2026-09, custos de 2026-01 a 2027-01. Em `dados/banco_de_dados/` só há `Financeiro RECEBER - 01 a 08-2026.xls` (receita) e `mes01-2026.xlsx` (de onde vêm os custos).
  - Ação: exportar do Sankhya os custos do mesmo período da receita e passá-los pelo `validar_entrada.bat`.
  - Quem age: SAMUEL. Desde: 02/10/2026.

### 🟠 Alta

- [ ] **A1. Relatório de abastecimento (km e litros)** — sem ele, CPK e Consumo Médio (Km/L) ficam "Sem dado".
  - Evidência: `inventario_fontes.txt` (03/10/2026) regista 0 ficheiros de abastecimento em `dados/banco_de_dados/`. O motor já sabe calcular (`apurar_km_litros_por_ano()` em `src/atualizar_dashboard.py`).
  - Ação: exportar o relatório de abastecimento do Sankhya com "abastec" no nome e colocá-lo em `dados/banco_de_dados/`.
  - Quem age: SAMUEL. Desde: 02/10/2026.

### 🟡 Média

- [ ] **M1. Commit das alterações locais** — há trabalho pronto e testado ainda fora do git (o rodapé do painel mostra `+local`).
  - Em 03/10/2026 18:42: `src/atualizar_dashboard.py` (motor para com erro se faltar um campo no template), `atualizar.bat`, `atualizar_local.bat`, `docs/pendencias_projeto.md`, `ferramentas/limpar_desktop_ini_git.bat` e `ferramentas/teste_regras_firestore.py` (novos).
  - Quem age: SAMUEL (pedir o commit). Desde: 03/10/2026.
- [ ] **M2. Motor usa o `index.html` antigo quando falta o template** — se `templates/template.html` for apagado ou movido, o motor gera o painel a partir do `index.html` anterior, sem avisar. Proposta: falhar com mensagem clara.
  - Onde: `src/atualizar_dashboard.py` (`arquivo_base = CAMINHO_TEMPLATE if ... else CAMINHO_INDEX`).
  - Quem age: IA, com autorização. Desde: 03/10/2026.
- [ ] **M3. Gestão de usuários do login sem browser** — "nova senha provisória" para usuário já cadastrado e apagar usuário. O plano gratuito do Firebase não deixa fazer pelo browser; precisa de script local com a chave de serviço (o `criar_adm_firebase.py` já redefine a senha de um ADM).
  - Onde: `ferramentas/`. Quem age: IA. Desde: 03/10/2026.
- [ ] **M4. Repositório dentro do Google Drive (solução de fundo)** — o Drive cria `desktop.ini` dentro de `.git` e estraga o `fetch`/`pull`/`push`. A limpeza automática já existe (ver secção 5); a solução de fundo é cada máquina ter o seu clone do GitHub fora do Drive (ex.: `C:\agrovia-dre-frota`), com `dados/`, `saidas/` e `config_local/` a continuarem no Drive. Exige que `src/fontes_dados.py` aceite a pasta dos dados por configuração de cada máquina.
  - Quem age: SAMUEL decide; IA implementa. Desde: 03/10/2026 (sem data).
- [ ] **M5. Etapa 2 — Multiveículos** — hoje o motor só conhece `OOM9749` (`PLACA_FROTA_PRINCIPAL`); as outras placas são excluídas como "outros veículos". Ver secção 7.
  - Falta o SAMUEL definir: lista de conjuntos (cavalo + carretas) e como ratear custos sem placa.
  - Quem age: SAMUEL decide; IA implementa. Desde: 02/10/2026.

### 🟢 Baixa

Manutenção do código:
- [ ] **B1. Molde com cara de molde** — `templates/template.html` traz data (01/10/2026), versão (`v8.32`) e valores que parecem reais mas são só marcadores que o motor substitui. Trocar por marcadores neutros no mesmo formato (ex.: `00/00/0000 às 00:00`, `v0.0`) e um aviso no topo. Quem age: IA. Desde: 03/10/2026.
- [ ] **B2. `ferramentas/diagnostico.py` monta o caminho do template à mão** — deve importar `CAMINHO_TEMPLATE` de `src/fontes_dados.py` (regra do projeto: caminhos só desse módulo). Quem age: IA. Desde: 03/10/2026.
- [ ] **B3. Título do `atualizar.bat` desatualizado** — mostra `v8.32 Cloud Auto`; o painel está em `v8.36`. Só texto da janela. Quem age: IA. Desde: 03/10/2026.
- [ ] **B4. Correr de novo o `laboratorio/agente_controller.py`** — o relatório de 03/10/2026 00:33 é anterior à última alteração do script (00:37) e não traz o aviso "GERADO POR IA" no topo. Quem age: SAMUEL ou IA. Desde: 03/10/2026.

Login da quarentena (melhorias):
- [ ] **B5. Autenticação pelo celular** (app autenticador gratuito, ex.: Google Authenticator). Desde: 03/10/2026.
- [ ] **B6. Envio da senha provisória por WhatsApp** (link `wa.me`, gratuito). Desde: 03/10/2026.
- [ ] **B7. Histórico de acessos** (quem entrou e quando). Desde: 03/10/2026.
- [ ] **B8. Bloquear a auto-inscrição no Firebase** (opcional) — quem tem o link e a chave pública consegue criar conta, mas sem perfil criado pelo ADM não lê nada (testado). Exige o upgrade gratuito para Identity Platform. Desde: 03/10/2026.

Painel e análise (ideias):
- [ ] **B9. Filtro único de período no cabeçalho** — a tabela já filtra por ano e "De / Até", e o gráfico mensal por ano (atualiza KPIs e rosca). Falta um filtro só que fatie o painel inteiro. Desde: 03/10/2026.
- [ ] **B10. Métricas preditivas de manutenção** — prever vida útil de pneus e peças a partir da quilometragem (depende de A1).
- [ ] **B11. Alertas automáticos** — avisos de vencimento de seguros, AET, IPVA e manutenções preventivas.

---

## 5. Riscos aceites e cuidados permanentes

Riscos aceites pelo SAMUEL (sem ação prevista):
- `saidas/relatorios_auditoria/pendencias_lancamentos.xlsx` fica com os dados em texto aberto na pasta do Drive; protegido pela partilha do Drive (decisão de 03/10/2026).

Cuidados permanentes (não são pendências, são regras de uso):
- **Teste de abastecimento fictício:** `laboratorio/abastecimento_teste.py remover` antes de qualquer `atualizar.bat`, senão o painel publicado mostra CPK e Km/L falsos. Em 03/10/2026 18:42 o ficheiro de teste não está em `dados/banco_de_dados/`.
- **Git dentro do Drive:** antes de usar o git à mão, correr `ferramentas\limpar_desktop_ini_git.bat` (os `.bat` de atualização já o chamam). Se avisar de cópias em conflito em `.git` (nomes com " (1)"), duas máquinas mexeram no git ao mesmo tempo.
- **Publicação:** o `atualizar.bat` só faz `git add index.html`. Alterações em `acesso/`, `firebase/`, `src/` ou `templates/` precisam de commit próprio.
- **Template:** as frases que o motor procura (`Atualizado em: dd/mm/aaaa às hh:mm`, `Agrovia DRE Master v…`, classes `kpi-value kpi-…`, `const MESES_GRAFICO`, `<tbody>`, etc.) têm de manter o formato. Desde 03/10/2026 o motor para com `ERRO_CRITICO` se faltar alguma, e o `atualizar.bat` não publica.
- **Conta `teste_ai`:** fica sempre bloqueada fora dos testes; não desbloquear à mão na tela do ADM (usar `ferramentas\conta_teste_ai.py`).

---

## 6. Decisões do SAMUEL (registo)

| Data | Decisão |
|------|---------|
| 03/10/2026 | **Regra de data:** receitas pela `Dt. Negociação` (emissão do título); custos pela `Data Baixa`, se vazia `Dt. Vencimento` e, em último caso, `Dt. Negociação`. Aplicada no motor, na auditoria e na quarentena. |
| 03/10/2026 | **Placa `[XYZ]` mantém BLOQUEANTE** na quarentena. Placa no campo → OK; placa só no histórico/observação → AVISO; sem placa → BLOQUEANTE. |
| 03/10/2026 | **Quarentena online** no Firebase (plano Spark, custo zero), atrás de login; deixa de valer "a quarentena nunca é publicada". Senha de 6 dígitos (mínimo do Firebase). |
| 03/10/2026 | `pendencias_lancamentos.xlsx` no Drive em texto aberto é aceite (protegido pela partilha). |
| 03/10/2026 | Repositório fora do Drive: aceite como direção, sem data (ver M4). |

---

## 7. Etapas do projeto

| Etapa | Estado | Pendências ligadas |
|-------|--------|--------------------|
| 1. Automatização de carga (ETL/BAT) | **Quase concluída** | U1, A1 |
| 2. Expansão Multiveículos | **Não iniciada** | M5 |
| 3. Deploy e homologação final (pasta de produção da Agrovia no Drive) | **Aguarda etapas 1 e 2** | — |

---

## 8. Histórico de entregas (concluído)

### 8.1 Etapa 1 (ETL/BAT)
Base: motor `atualizar_dashboard.py`, `atualizar.bat` com publicação no GitHub, auditor `auditoria_completa.py`, trava de fontes `fontes_dados.py` (só conta o que está hoje em `dados/banco_de_dados/`), `.gitignore` sem dados financeiros.

1. [x] **Proteger o `.env` (chave da API):** `.env` no `.gitignore` (nunca foi commitado), modelo em `.env.example`; `.gitignoregit` apagado.
2. **KPIs sem fonte no painel** (pendência aberta: A1):
   - [x] CPK e Consumo Médio deixaram de ser fixos: o motor calcula-os a partir de relatórios de abastecimento (`listar_ficheiros_abastecimento()`) e mostra "Sem dado" quando não há fonte (`atualizar_dashboard.py`; `template.html` já sai com "Sem dado").
   - [x] CPK e Km/L por ano: `apurar_km_litros_por_ano()` em `atualizar_dashboard.py` reparte km e litros pelo ano civil de cada abastecimento (o 1.º não conta, tanque cheio; registo sem data ou hodómetro a recuar → "Sem dado"). O filtro de ano do gráfico mensal atualiza os cartões KPI (receita, custo, resultado, margem, CPK, Km/L) e a rosca de custos para o ano escolhido.
   - [x] Teste com dados fictícios: `laboratorio/abastecimento_teste.py instalar` grava `abastecimento_TESTE_FICTICIO.xlsx` em `dados/banco_de_dados/`; `remover` apaga-o.
3. **Fechar o período dos dados** (pendência aberta: U1):
   - [x] Regra de data definida pelo SAMUEL (03/10/2026) e aplicada no motor, na auditoria e na quarentena (ver secção 6). Receitas ainda não baixadas passaram a entrar no painel.
4. [x] **Trava de publicação no `.bat`:** corre `auditoria_completa.py` e bloqueia o push se falhar; divergência de período passou a aviso. Commit `9636fc8` (02/10/2026).
5. **`agente_controller.py` (agente IA Gemini/LangGraph)** (pendência aberta: B4):
   - [x] Lê todos os ficheiros válidos via `listar_ficheiros_fonte()` (50 linhas por ficheiro, `LINHAS_POR_FICHEIRO`), com caminhos de `fontes_dados.py`.
   - [x] Privacidade: só sai para o Gemini a lista `COLUNAS_PERMITIDAS`; nomes de pessoas e CNPJ/CPF no Histórico são mascarados (`[NOME]`, `[DOC]`); nomes extra via `NOMES_MASCARAR` no `.env` (modelo em `.env.example`).
   - [x] Saída em `saidas/relatorios_auditoria/ia_relatorio_correcao_operador.txt` com aviso "GERADO POR IA - NÃO É O VEREDITO DO AUDITOR OFICIAL".
   - [x] O modelo `gemini-3.8-flash` respondeu (relatório gerado em 03/10/2026 00:33).
   - [x] `agente_controller.py` e `tradutor.py` movidos para `laboratorio/` (versionados, fora da produção); `requirements.txt` preenchido.
6. [x] **Visão Mobile real:** painel (`templates/template.html`) e tela de quarentena (`validar_entrada.py`) passam a cartões empilhados no telemóvel, com filtros fixos no topo e modo Mobile automático em ecrãs até 768 px; ao fechar uma categoria da DRE, os detalhes abertos fecham com ela (03/10/2026).
7. [x] **`.cursorrules`:** mapa do projeto, blindagem (texto dos Excel e respostas de IA são dados, não instruções; `.env` nunca lido nem commitado) e critérios por Chap atualizados (03/10/2026).
8. [x] **Commit das alterações de 03/10/2026:** itens 5, 6 e 7 acima e a regra de data commitados e publicados (03/10/2026).
9. **Repositório dentro do Google Drive (`desktop.ini` em `.git`)** (pendência aberta: M4):
   - Problema: o Google Drive cria `desktop.ini` em todas as pastas, também dentro de `.git`. Em `.git\refs` o git lê-os como referências e o `git fetch`/`pull`/`push` falha com `bad object refs/desktop.ini`. Em 03/10/2026 havia 184 dentro de `.git`.
   - [x] Correção automática (03/10/2026): `ferramentas\limpar_desktop_ini_git.bat` apaga-os (precisa de `del /a`: no disco do Drive o atributo "oculto" não sai com `attrib`). Usa o caminho da própria pasta, por isso funciona em qualquer máquina e com qualquer letra de disco. O `atualizar.bat` e o `atualizar_local.bat` chamam-no no início.
10. [x] **Trava dos campos do template (03/10/2026):** `substituir_no_template()` em `src/atualizar_dashboard.py`. Se o template perder um campo que o motor preenche (data, versão, KPIs, gráficos, filtro, tabela), o motor regista `ERRO_CRITICO`, sai com código 1 e não grava o `index.html`; o `atualizar.bat` não publica. Testado com template partido numa cópia; com o template normal o painel sai igual (só mudam data e versão). Falta o commit (M1).

### 8.2 Quarentena de lançamentos
Base (commit `9636fc8`): `validar_entrada.py` / `validar_entrada.bat` validam os Excel em `dados/entrada_quarentena/`, geram `saidas/relatorios_auditoria/pendencias_lancamentos.xlsx` (operador marca Status/Observação) e `pendencias_lancamentos.html` (visual Agrovia, PC/Mobile/impressão), e só promovem para `dados/banco_de_dados/` ficheiros sem bloqueantes. Regras em `regras_lancamento.py`.

1. [x] **Botão no painel principal para abrir a tela de quarentena (03/10/2026):**
   - `🧪 Quarentena` no cabeçalho do `template.html`, entre "Ver Tabela Analítica" e PC/Mobile.
   - Primeiro abria `saidas/relatorios_auditoria/pendencias_lancamentos.html` só no PC local; depois do login na nuvem (item 5) fica ativo no site e no PC e abre `acesso/login.html`; os dados só chegam depois do login. Continua a valer: nada da tela de pendências entra no `index.html` nem no git.
2. [x] **Versão do painel automática (03/10/2026):** `obter_versao_painel()` em `atualizar_dashboard.py` grava `VERSAO_BASE` + commit git curto (ex.: `v8.36 · 4d18197`), com `+local` quando há alterações não commitadas em `src/` ou `templates/`. A versão base (`VERSAO_BASE`) continua manual, para mudanças grandes.
3. [x] **Placa `[XYZ]` e critério único de placa (03/10/2026):**
   - Decisão do SAMUEL: mantém BLOQUEANTE (ver secção 6). Motivo: `[XYZ]` vai continuar a aparecer, porque há custo da frota lançado sem placa na coluna correta; só o bloqueio obriga a corrigir no Sankhya antes de entrar.
   - Evidência (03/10/2026, ficheiros em `dados/banco_de_dados/`): 27 linhas `[XYZ]` (18 em `Financeiro RECEBER - 01 a 08-2026.xls`, 9 em `mes01-2026.xlsx`), quase todas adiantamento/salário do motorista, monitores (REP STORE), camionete particular e viagem no caminhão da CVC.
   - [x] `identificar_placa()` em `regras_lancamento.py` é o critério único da quarentena, do motor e da auditoria. Linha sem placa sai da DRE e aparece à parte no painel ("Lançamentos sem placa - fora da DRE"). Variantes `OOM 9749`, `OOM-9749` e Mercosul `OOM9H49` contam como `OOM9749`. O painel mostra "(Validada)" quando a placa vem do campo e "(via histórico)" quando vem do texto. Auditoria bate com o painel; veredito APROVADO.
   - [x] O motor usava `Data Baixa` como data da receita (a coluna "Data Emissao" não existe e a procura caía em "Data"). Agora usa `Dt. Negociação`.
   - [x] O gráfico "Evolução Mensal" cortava em agosto e somava meses de anos diferentes. Agora mostra todos os meses AAAA-MM do primeiro ao último lançamento (`Jan/26` … `Jan/27`) e as barras somam os totais dos KPIs.
   - [x] O filtro de meses da tabela usava só o mês, sem o ano. Agora o motor grava `data-mes` como AAAA-MM e o filtro tem botões de ano (`Todos`, `2026`, `2027`) e período "De / Até".
4. [x] **`.gitignore`:** `dados/banco_de_dados/`, `dados/entrada_quarentena/`, `saidas/relatorios_auditoria/`, `saidas/backup_relatorios/` inteiros fora do git (commit `1011c00`, 02/10/2026). O repositório é público.
5. [x] **Login da quarentena na nuvem (Firebase, plano Spark gratuito) — em produção desde 03/10/2026:**
   - [x] Telas `acesso/login.html`, `acesso/trocar_senha.html`, `acesso/adm.html` e `acesso/quarentena.html`; regras em `firebase/firestore.rules`; envio dos dados em `src/quarentena_online.py` (chamado pelo `validar_entrada.py`); 1.º ADM com `ferramentas/criar_adm_firebase.py`; chave de serviço em `config_local/` (no `.gitignore`).
   - [x] O ADM cadastra nome, apelido, celular e senha provisória. No 1.º acesso o usuário é obrigado a criar a própria senha; as regras do Firestore negam a leitura da quarentena até lá. Muitas tentativas erradas são travadas pelo próprio Firebase.
   - [x] O `pendencias_lancamentos.html` local deixou de ter dados; é só um atalho para a tela online.
   - [x] Firebase configurado: projeto `agrovia-dre-frota` (Spark), config em `acesso/firebase_config.js` (commit `29ab00e`), chave de serviço em `config_local/firebase_servico.json`, cópia de segurança em `chave_firebase/` (no `.gitignore`). Só uma chave ativa na conta de serviço; a extra foi apagada no Google Cloud.
   - [x] Telas publicadas (commit e push a pedido do SAMUEL).
   - [x] **Teste de ponta a ponta** (03/10/2026, no site publicado): login do ADM; cadastro; 1.º acesso redireciona para `trocar_senha.html` (também pelo endereço direto da quarentena); troca de senha libera a quarentena; usuário comum sem botão Administração e devolvido ao abrir `adm.html`; Firestore nega ao usuário comum a leitura de `perfis`; usuário bloqueado perde a sessão e o login é recusado.
     - [x] Senha errada recusada (`INVALID_LOGIN_CREDENTIALS`; a tela mostra "Usuário ou senha inválidos.").
     - [x] Escrita bloqueada: `python ferramentas\teste_regras_firestore.py` (com a chave pública do site) deu 17/17 OK em 1.º acesso e 17/17 OK liberado. O usuário comum não consegue: promover-se a ADM, mudar nome/celular, apagar o perfil, cadastrar outro usuário, listar perfis, gravar ou apagar na quarentena, gravar noutra coleção, voltar a ligar a troca de senha, nem sair da troca obrigatória e virar ADM no mesmo pedido; antes de trocar a senha não lê a quarentena. Conta criada por fora (sem perfil do ADM) não lê nem grava nada; o script apaga-a no fim.
     - [x] Quarentena com dados: cópias dos Excel validadas com `python src\validar_entrada.py --sem-promover` (nada movido; banco igual pelo hash SHA-256). Enviadas 68 pendências (29 bloqueantes, 39 avisos); a tela mostra a etiqueta "Simulação (--sem-promover)". A próxima execução real do `validar_entrada.bat` substitui estes dados.
     - [x] Telemóvel (390 px) e PC (1366 px) verificados.
   - [x] **Conta de teste do agente IA** (commit `ff66c6e`): `teste_ai`, sempre usuário comum e bloqueada fora dos testes. `python ferramentas\conta_teste_ai.py ativar [--primeiro-acesso]` / `desativar` / `estado`; a senha fica só em `config_local/teste_ai.json`.

---
*Relatório gerado e validado sob a supervisão técnica de Samuel Profissional.*
