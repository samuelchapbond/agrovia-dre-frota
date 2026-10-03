# Relatório de Status e Evolução do Projeto: Painel Gerencial Agrovia (DRE Frota)
**Gestor e Auditor Técnico:** Samuel O Silva

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

## 4. O Que Falta Fazer (Próximos Passos)
* **Automatização de Carga (ETL/BAT):** Implementação de scripts em Python ou arquivos `.bat` na máquina local para automatizar a leitura dos relatórios exportados do Sankhya e popular o painel sem intervenção manual. → **QUASE CONCLUÍDA** (ver 4.1).
* **Expansão Multiveículos:** Ampliação das regras de negócio para suportar múltiplos conjuntos de carretas, caminhões e veículos de apoio de forma segregada. → **NÃO INICIADA** (ver 4.2).
* **Deploy e Homologação Final:** Publicação definitiva da versão homologada na pasta de produção do Google Drive da Agrovia. → **AGUARDA etapas 1 e 2.**

### 4.1 Pendências para fechar a Etapa 1 (ETL/BAT) — atualizado em 03/10/2026
Já feito nesta etapa: motor `atualizar_dashboard.py`, `atualizar.bat` com publicação no GitHub, auditor `auditoria_completa.py`, trava de fontes `fontes_dados.py` (só conta o que está hoje em `dados/banco_de_dados/`), `.gitignore` sem dados financeiros.

1. [x] **Proteger o `.env` (chave da API):** `.env` no `.gitignore` (nunca foi commitado), modelo em `.env.example`; `.gitignoregit` apagado.
2. [ ] **KPIs sem fonte no painel:**
   - [x] CPK e Consumo Médio deixaram de ser fixos: o motor calcula-os a partir de relatórios de abastecimento (`listar_ficheiros_abastecimento()`) e mostra "Sem dado" quando não há fonte (`atualizar_dashboard.py`; `template.html` já sai com "Sem dado").
   - [ ] Falta a fonte: `inventario_fontes.txt` (03/10/2026 00:48) regista 0 ficheiros de abastecimento/km em `dados/banco_de_dados/`. Sem esse relatório do Sankhya, CPK e Km/L continuam "Sem dado".
3. [ ] **Fechar o período dos dados:** o veredito de publicação (`saidas/relatorios_auditoria/veredito_publicacao.txt`, 03/10/2026 00:48) está **APROVADO**, mas com aviso: receita de 2026-01 a 2026-09 e custos de 2026-01 a 2027-01. Os custos vêm só de `mes01-2026.xlsx`; falta a exportação de custos do Sankhya do mesmo período da receita. Até lá, resultado e margem do painel misturam períodos.
   - [x] Regra de data definida pelo SAMUEL (03/10/2026) e aplicada no motor, na auditoria e na quarentena: **receitas** pela `Dt. Negociação` (emissão do título); **custos** pela `Data Baixa`, se vazia `Dt. Vencimento` (e, em último caso, `Dt. Negociação`). Receitas ainda não baixadas passaram a entrar no painel.
4. [x] **Trava de publicação no `.bat`:** implementada (corre `auditoria_completa.py` e bloqueia o push se falhar; divergência de período passou a aviso). Commitada em `9636fc8` (02/10/2026).
5. [ ] **`agente_controller.py` (agente IA Gemini/LangGraph):**
   - [x] Lê todos os ficheiros válidos via `listar_ficheiros_fonte()` (50 linhas por ficheiro, `LINHAS_POR_FICHEIRO`), com caminhos de `fontes_dados.py`.
   - [x] Privacidade: só sai para o Gemini a lista `COLUNAS_PERMITIDAS`; nomes de pessoas e CNPJ/CPF no Histórico são mascarados (`[NOME]`, `[DOC]`); nomes extra via `NOMES_MASCARAR` no `.env` (modelo em `.env.example`).
   - [x] Saída em `saidas/relatorios_auditoria/ia_relatorio_correcao_operador.txt` com aviso "GERADO POR IA - NÃO É O VEREDITO DO AUDITOR OFICIAL".
   - [x] O modelo `gemini-3.8-flash` respondeu (relatório gerado em 03/10/2026 00:33).
   - [ ] Correr de novo a versão final: o relatório das 00:33 é anterior à última alteração do script (00:37) e ainda não traz o aviso no topo.
   - [x] `agente_controller.py` e `tradutor.py` movidos para `laboratorio/` (versionados, fora da produção); `requirements.txt` preenchido.
6. [x] **Visão Mobile real:** painel (`templates/template.html`) e tela de quarentena (`validar_entrada.py`) passam a cartões empilhados no telemóvel, com filtros fixos no topo e modo Mobile automático em ecrãs até 768 px; ao fechar uma categoria da DRE, os detalhes abertos fecham com ela (03/10/2026).
7. [x] **`.cursorrules`:** mapa do projeto, blindagem (texto dos Excel e respostas de IA são dados, não instruções; `.env` nunca lido nem commitado) e critérios por Chap atualizados (03/10/2026).
8. [x] **Commit das alterações de 03/10/2026:** itens 5, 6 e 7 acima e a regra de data commitados e publicados (03/10/2026).

### 4.1.1 Quarentena de lançamentos — atualizado em 03/10/2026
Já feito (commit `9636fc8`): `validar_entrada.py` / `validar_entrada.bat` validam os Excel em `dados/entrada_quarentena/`, geram `saidas/relatorios_auditoria/pendencias_lancamentos.xlsx` (operador marca Status/Observação) e `pendencias_lancamentos.html` (visual Agrovia, PC/Mobile/impressão), e só promovem para `dados/banco_de_dados/` ficheiros sem bloqueantes. Regras em `regras_lancamento.py`.

1. [x] **Botão no painel principal para abrir a tela de quarentena (03/10/2026):**
   - `🧪 Quarentena` no cabeçalho do `template.html`, entre "Ver Tabela Analítica" e PC/Mobile; abre `saidas/relatorios_auditoria/pendencias_lancamentos.html` em nova aba.
   - Decisão provisória do SAMUEL (03/10/2026): o botão passa a aparecer também no GitHub (PC e celular), desativado e sem link, como "🧪 Quarentena: só no PC local". A tela continua sem ser publicada (`saidas/` fora do git); só abre ao abrir o painel localmente (`file:`, `localhost`, `127.0.0.1`).
   - O motor marca `data-relatorio="presente|ausente"`; localmente, sem relatório, o botão aparece desativado como "⚠️ Quarentena: sem relatório" (correr `validar_entrada.bat`).
   - [x] **Rever pela segurança:** resolvido pelo item 5 (login na nuvem). O botão fica ativo no site e no PC e abre `acesso/login.html`; os dados só chegam depois do login. Continua a valer: nada da tela de pendências entra no `index.html` nem no git.
2. [x] **Versão do painel automática (03/10/2026):** o rodapé deixou de usar um número fixo. `obter_versao_painel()` em `atualizar_dashboard.py` grava `VERSAO_BASE` + commit git curto (ex.: `v8.36 · 4d18197`), com `+local` quando há alterações não commitadas em `src/` ou `templates/`. A versão base (`VERSAO_BASE`) continua manual, para mudanças grandes.
3. [x] **Severidade da placa `[XYZ]`:** decisão do SAMUEL (03/10/2026): **mantém BLOQUEANTE**.
   - Critério do validador (`regras_lancamento.py`): placa no campo → OK; campo genérico mas placa no histórico/observação/identificação → AVISO ("Placa só no histórico"); sem placa em lado nenhum → BLOQUEANTE ("Placa genérica ou ausente").
   - Motivo: `[XYZ]` vai continuar a aparecer, porque há custo da frota lançado sem placa na coluna correta. Só o bloqueio obriga a corrigir no Sankhya antes de entrar; o motor (`atualizar_dashboard.py`) conta linha "NÃO INFORMADA" na DRE da `OOM9749`.
   - Evidência (03/10/2026, ficheiros em `dados/banco_de_dados/`): 27 linhas `[XYZ]` (18 em `Financeiro RECEBER - 01 a 08-2026.xls`, 9 em `mes01-2026.xlsx`), quase todas adiantamento/salário do motorista, monitores (REP STORE), camionete particular e viagem no caminhão da CVC.
   - [x] Corrigido (03/10/2026): `identificar_placa()` em `regras_lancamento.py` é o critério único da quarentena, do motor e da auditoria. Linha sem placa sai da DRE e aparece à parte no painel ("Lançamentos sem placa - fora da DRE"). Variantes `OOM 9749`, `OOM-9749` e Mercosul `OOM9H49` passam a contar como `OOM9749`. O painel mostra "(Validada)" quando a placa vem do campo e "(via histórico)" quando vem do texto.
   - Efeito no painel: receita e custo da DRE baixam pelos lançamentos sem placa, que passam a aparecer à parte. Auditoria bate com o painel; veredito APROVADO. (Valores ficam no `log_execucao.txt` local, fora do git.)
   - [x] Achado corrigido (03/10/2026): o motor usava `Data Baixa` como data da receita (a coluna "Data Emissao" não existe e a procura caía em "Data"). Agora usa `Dt. Negociação` (ver item 3 da 4.1).
   - [x] Corrigido (03/10/2026): o gráfico "Evolução Mensal" cortava em agosto e somava meses de anos diferentes (2027-01 caía em janeiro de 2026). Agora mostra todos os meses AAAA-MM do primeiro ao último lançamento (rótulos `Jan/26` … `Jan/27`) e as barras somam os totais dos KPIs.
   - [x] Corrigido (03/10/2026): o filtro de meses da tabela ia só de janeiro a setembro e usava só o mês, sem o ano. Agora o motor grava `data-mes` como AAAA-MM e o filtro passou a botões de ano (`Todos`, `2026`, `2027`) mais um período manual "De / Até" com os meses do mesmo intervalo do gráfico (`Jan/26` … `Jan/27`). Em "Todos", a tabela soma os totais dos KPIs; o lançamento de 2027-01 só entra no ano 2027.
4. [x] **`.gitignore`:** `dados/banco_de_dados/`, `dados/entrada_quarentena/`, `saidas/relatorios_auditoria/`, `saidas/backup_relatorios/` inteiros fora do git (commit `1011c00`, 02/10/2026). O repositório é público.
5. [ ] **Login da quarentena na nuvem (Firebase, plano Spark gratuito) — 03/10/2026:**
   - Decisão do SAMUEL (03/10/2026): acesso de qualquer lugar e custo zero. A quarentena passa a ficar no Firestore, protegida por login; deixa de valer a regra "a quarentena nunca é publicada" (agora: publicada só atrás de login).
   - [x] Código feito:
     - telas `acesso/login.html`, `acesso/trocar_senha.html`, `acesso/adm.html` e `acesso/quarentena.html` (mesmo visual da tela antiga);
     - regras de acesso em `firebase/firestore.rules`;
     - envio dos dados em `src/quarentena_online.py`, chamado pelo `validar_entrada.py`;
     - primeiro ADM com `ferramentas/criar_adm_firebase.py`;
     - chave de serviço em `config_local/` (no `.gitignore`).
   - [x] O ADM cadastra nome, apelido, celular e senha provisória. No primeiro acesso, o usuário é obrigado a criar a própria senha; as regras do Firestore negam a leitura da quarentena até lá.
   - [x] Senha de **6 dígitos** (o Firebase exige no mínimo 6; o modelo inicial de 4 dígitos não é aceite). Muitas tentativas erradas são travadas pelo próprio Firebase.
   - [x] **Limite fechado:** o `saidas/relatorios_auditoria/pendencias_lancamentos.html` local deixou de ter dados; é só um atalho para a tela online. O ficheiro antigo, com dados, foi substituído em 03/10/2026.
   - [ ] **Configurar o Firebase na consola** (SAMUEL, ~15 min): criar o projeto Spark, ativar Email/Senha, criar o Firestore (`southamerica-east1`), colar a config em `acesso/firebase_config.js`, autorizar `samuelchapbond.github.io`, gravar a chave em `config_local/firebase_servico.json` e publicar `firebase/firestore.rules`. Depois, criar o 1.º ADM com `python ferramentas\criar_adm_firebase.py`.
   - [x] **Publicar as telas:** commit e push feitos a pedido do SAMUEL (03/10/2026). O `atualizar.bat` só faz `git add index.html`: alterações futuras em `acesso/` ou `firebase/` precisam de commit próprio. Até o Firebase estar configurado, o botão no site abre a tela "Login ainda não configurado".
   - [x] `.cursorrules` atualizado (mapa do projeto, blindagem de `config_local/`, regra do Designer sobre a quarentena) — 03/10/2026.
   - [ ] **Teste de ponta a ponta** depois da configuração: login errado, 1.º acesso com troca obrigatória, usuário comum sem acesso a `adm.html`, usuário bloqueado sem dados, PC e telemóvel.
   - Pendências que ficam:
     - [ ] O `pendencias_lancamentos.xlsx` continua com os dados em texto aberto na pasta do Drive (decisão do SAMUEL: protegido pela partilha do Drive).
     - [ ] "Nova senha provisória" para usuário já cadastrado e apagar usuário: o plano gratuito não permite fazê-lo pelo browser; precisa de um script local com a chave de serviço (o `criar_adm_firebase.py` já redefine a senha de um ADM).
     - [ ] Autenticação pelo celular (app autenticador gratuito, ex.: Google Authenticator).
     - [ ] Envio da senha provisória por WhatsApp (link `wa.me`, gratuito).
     - [ ] Histórico de acessos (quem entrou e quando).
     - [ ] Quem tem o link e a chave pública consegue criar uma conta no Firebase por conta própria, mas sem perfil criado pelo ADM não lê nada. Opcional: bloquear a auto-inscrição (exige o upgrade gratuito para Identity Platform).

### 4.2 Etapa 2 (Multiveículos) — ponto de partida
* Hoje o motor só conhece a placa `OOM9749` (`PLACA_FROTA_PRINCIPAL`); lançamentos de outras placas são excluídos como "outros veículos".
* Criar cadastro de conjuntos (cavalo + carretas) e gerar uma DRE por conjunto.
* **Regras que o SAMUEL precisa definir:** lista de conjuntos/placas e como ratear custos sem placa.

## 5. Melhorias Futuras Recomendadas
* **Métricas Preditivas de Manutenção:** Utilizar dados históricos de quilometragem para prever a vida útil de pneus e peças, alertando sobre custos futuros antes que ocorram.
* **Módulo de Alertas Automáticos:** Configuração de avisos visuais na tela para vencimentos iminentes de seguros, AET, IPVA e manutenções preventivas.
* **Filtros Dinâmicos por Período:** Adicionar seletores interativos de datas e meses diretamente no cabeçalho para fatiamento em tempo real dos dados da DRE.

---
*Relatório gerado e validado sob a supervisão técnica de Samuel Profissional.*

