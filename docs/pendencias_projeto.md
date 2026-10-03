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
   - Decisão: só aparece ao abrir localmente (`file:`, `localhost`, `127.0.0.1`); no GitHub fica escondido.
   - O motor marca `data-relatorio="presente|ausente"`; sem relatório, o botão aparece desativado como "⚠️ Quarentena: sem relatório" (correr `validar_entrada.bat`).
2. [x] **Severidade da placa `[XYZ]`:** decisão do SAMUEL (03/10/2026): **mantém BLOQUEANTE**.
   - Critério do validador (`regras_lancamento.py`): placa no campo → OK; campo genérico mas placa no histórico/observação/identificação → AVISO ("Placa só no histórico"); sem placa em lado nenhum → BLOQUEANTE ("Placa genérica ou ausente").
   - Motivo: `[XYZ]` vai continuar a aparecer, porque há custo da frota lançado sem placa na coluna correta. Só o bloqueio obriga a corrigir no Sankhya antes de entrar; o motor (`atualizar_dashboard.py`) conta linha "NÃO INFORMADA" na DRE da `OOM9749`.
   - Evidência (03/10/2026, ficheiros em `dados/banco_de_dados/`): 27 linhas `[XYZ]` (18 em `Financeiro RECEBER - 01 a 08-2026.xls`, 9 em `mes01-2026.xlsx`), quase todas adiantamento/salário do motorista, monitores (REP STORE), camionete particular e viagem no caminhão da CVC.
   - [x] Corrigido (03/10/2026): `identificar_placa()` em `regras_lancamento.py` é o critério único da quarentena, do motor e da auditoria. Linha sem placa sai da DRE e aparece à parte no painel ("Lançamentos sem placa - fora da DRE"). Variantes `OOM 9749`, `OOM-9749` e Mercosul `OOM9H49` passam a contar como `OOM9749`. O painel mostra "(Validada)" quando a placa vem do campo e "(via histórico)" quando vem do texto.
   - Efeito no painel: receita e custo da DRE baixam pelos lançamentos sem placa, que passam a aparecer à parte. Auditoria bate com o painel; veredito APROVADO. (Valores ficam no `log_execucao.txt` local, fora do git.)
   - [x] Achado corrigido (03/10/2026): o motor usava `Data Baixa` como data da receita (a coluna "Data Emissao" não existe e a procura caía em "Data"). Agora usa `Dt. Negociação` (ver item 3 da 4.1).
   - [ ] Achado: o filtro de meses da tabela vai só de janeiro a setembro. Custos com data de outubro em diante contam no KPI mas desaparecem da tabela quando o filtro recalcula.
3. [x] **`.gitignore`:** `dados/banco_de_dados/`, `dados/entrada_quarentena/`, `saidas/relatorios_auditoria/`, `saidas/backup_relatorios/` inteiros fora do git (commit `1011c00`, 02/10/2026). O repositório é público.

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

