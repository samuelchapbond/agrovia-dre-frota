---
description: "Modelo de lista de tarefas para a implementação de funcionalidades"
---

# Tarefas: [NOME DA FUNCIONALIDADE]

**Entrada**: Documentos de design de `/specs/[###-nome-da-funcionalidade]/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de utilizador), research.md, data-model.md, contracts/

**Testes**: Os exemplos abaixo incluem tarefas de teste. Os testes são OPCIONAIS - inclua-os apenas se expressamente solicitados na especificação da funcionalidade.

**Organização**: As tarefas são agrupadas por história de utilizador para permitir a implementação e o teste independentes de cada história.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executado em paralelo (ficheiros diferentes, sem dependências)
- **[História]**: A que história de utilizador esta tarefa pertence (ex: US1, US2, US3)
- Inclua caminhos de ficheiro exatos nas descrições

## Convenções de Caminho

- **Projeto único**: `src/`, `tests/` na raiz do repositório
- **Aplicação Web**: `backend/src/`, `frontend/src/`
- **Móvel**: `api/src/`, `ios/src/` ou `android/src/`
- Os caminhos mostrados abaixo assumem um projeto único - ajuste com base na estrutura do plan.md

<!--
  ============================================================================
  IMPORTANTE: As tarefas abaixo são TAREFAS DE EXEMPLO apenas para fins ilustrativos.

  O comando /speckit-tasks DEVE substituir estas por tarefas reais com base em:
  - Histórias de utilizador do spec.md (com as respetivas prioridades P1, P2, P3...)
  - Requisitos da funcionalidade do plan.md
  - Entidades do data-model.md
  - Endpoints de contracts/

  As tarefas DEVEM ser organizadas por história de utilizador para que cada história possa ser:
  - Implementada de forma independente
  - Testada de forma independente
  - Entregue como um incremento de MVP

  NÃO mantenha estas tarefas de exemplo no ficheiro tasks.md gerado.
  ============================================================================
-->

## Fase 1: Configuração (Infraestrutura Partilhada)

**Objetivo**: Inicialização do projeto e estrutura básica

- [ ] T001 Criar estrutura do projeto de acordo com o plano de implementação
- [ ] T002 Inicializar projeto em [linguagem] com dependências do [framework]
- [ ] T003 [P] Configurar ferramentas de linting e formatação

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Objetivo**: Infraestrutura principal que DEVE estar concluída antes que QUALQUER história de utilizador possa ser implementada

**⚠️ CRÍTICO**: Nenhuma atividade de história de utilizador pode começar até que esta fase esteja concluída

Exemplos de tarefas fundacionais (ajuste com base no seu projeto):

- [ ] T004 Configurar esquema da base de dados e framework de migrações
- [ ] T005 [P] Implementar framework de autenticação/autorização
- [ ] T006 [P] Configurar encaminhamento de API e estrutura de middleware
- [ ] T007 Criar modelos/entidades base dos quais todas as histórias dependem
- [ ] T008 Configurar tratamento de erros e infraestrutura de registo (logs)
- [ ] T009 Configurar gestão de configuração de ambiente

**Ponto de Controlo**: Fundação pronta - a implementação da história de utilizador pode agora começar em paralelo

---

## Fase 3: História de Utilizador 1 - [Título] (Prioridade: P1) 🎯 MVP

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 1 (OPCIONAL - apenas se solicitados testes) ⚠️

> **NOTA: Escreva estes testes PRIMEIRO, certifique-se de que FALHAM antes da implementação**

- [ ] T010 [P] [US1] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T011 [P] [US1] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 1

- [ ] T012 [P] [US1] Criar modelo [Entity1] em src/models/[entity1].py
- [ ] T013 [P] [US1] Criar modelo [Entity2] em src/models/[entity2].py
- [ ] T014 [US1] Implementar [Service] em src/services/[service].py (depende de T012, T013)
- [ ] T015 [US1] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py
- [ ] T016 [US1] Adicionar validação e tratamento de erros
- [ ] T017 [US1] Adicionar registo (logging) para as operações da história de utilizador 1

**Ponto de Controlo**: A este ponto, a História de Utilizador 1 deve estar totalmente funcional e testável de forma independente

---

## Fase 4: História de Utilizador 2 - [Título] (Prioridade: P2)

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 2 (OPCIONAL - apenas se solicitados testes) ⚠️

- [ ] T018 [P] [US2] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T019 [P] [US2] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 2

- [ ] T020 [P] [US2] Criar modelo [Entity] em src/models/[entity].py
- [ ] T021 [US2] Implementar [Service] em src/services/[service].py
- [ ] T022 [US2] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py
- [ ] T023 [US2] Integrar com componentes da História de Utilizador 1 (se necessário)

**Ponto de Controlo**: A este ponto, as Histórias de Utilizador 1 E 2 devem funcionar ambas de forma independente

---

## Fase 5: História de Utilizador 3 - [Título] (Prioridade: P3)

**Objetivo**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 3 (OPCIONAL - apenas se solicitados testes) ⚠️

- [ ] T024 [P] [US3] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T025 [P] [US3] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 3

- [ ] T026 [P] [US3] Criar modelo [Entity] em src/models/[entity].py
- [ ] T027 [US3] Implementar [Service] em src/services/[service].py
- [ ] T028 [US3] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py

**Ponto de Controlo**: Todas as histórias de utilizador devem agora ser funcionalmente independentes

---

[Adicione mais fases de histórias de utilizador conforme necessário, seguindo o mesmo padrão]

---

## Fase N: Polimento & Questões Transversais

**Objetivo**: Melhorias que afetam múltiplas histórias de utilizador

- [ ] TXXX [P] Atualizações de documentação em docs/
- [ ] TXXX Limpeza de código e refatoração
- [ ] TXXX Otimização de desempenho em todas as histórias
- [ ] TXXX [P]Aqui está a tradução completa do modelo de lista de tarefas (`tasks.md`) para português, mantendo toda a estrutura de formatação e os marcadores originais para uso no seu fluxo de trabalho com o Cursor e o Spec Kit:

```markdown
---
description: "Modelo de lista de tarefas para implementação de funcionalidades"
---

# Tarefas: [NOME DA FUNCIONALIDADE]

**Entrada**: Documentos de design de `/specs/[###-feature-name]/`

**Pré-requisitos**: plan.md (obrigatório), spec.md (obrigatório para histórias de utilizador), research.md, data-model.md, contracts/

**Testes**: Os exemplos abaixo incluem tarefas de testes. Os testes são OPCIONAIS - inclua-os apenas se solicitado explicitamente na especificação da funcionalidade.

**Organização**: As tarefas são agrupadas por história de utilizador para permitir a implementação e teste independentes de cada história.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: Pode ser executado em paralelo (ficheiros diferentes, sem dependências)
- **[História]**: A que história de utilizador esta tarefa pertence (ex: US1, US2, US3)
- Inclua caminhos exatos de ficheiros nas descrições

## Convenções de Caminho

- **Projeto único**: `src/`, `tests/` na raiz do repositório
- **Aplicação web**: `backend/src/`, `frontend/src/`
- **Móvel**: `api/src/`, `ios/src/` ou `android/src/`
- Os caminhos mostrados abaixo assumem projeto único - ajuste com base na estrutura do plan.md

<!--
  ============================================================================
  IMPORTANTE: As tarefas abaixo são TAREFAS DE EXEMPLO apenas para fins ilustrativos.

  O comando /speckit-tasks DEVE substituí-las por tarefas reais com base em:
  - Histórias de utilizador de spec.md (com suas prioridades P1, P2, P3...)
  - Requisitos de funcionalidade de plan.md
  - Entidades de data-model.md
  - Endpoints de contracts/

  As tarefas DEVEM ser organizadas por história de utilizador para que cada história possa ser:
  - Implementada de forma independente
  - Testada de forma independente
  - Entregue como um incremento de MVP

  NÃO mantenha estas tarefas de exemplo no ficheiro tasks.md gerado.
  ============================================================================
-->

## Fase 1: Configuração (Infraestrutura Partilhada)

**Objetivo**: Inicialização do projeto e estrutura básica

- [ ] T001 Criar estrutura do projeto conforme o plano de implementação
- [ ] T002 Inicializar projeto [linguagem] com dependências do [framework]
- [ ] T003 [P] Configurar ferramentas de linting e formatação

---

## Fase 2: Fundacional (Pré-requisitos Bloqueantes)

**Objetivo**: Infraestrutura principal que DEVE estar completa ANTES que qualquer história de utilizador possa ser implementada

**⚠️ CRÍTICO**: Nenhum trabalho de história de utilizador pode começar até que esta fase esteja concluída

Exemplos de tarefas fundacionais (ajuste com base no seu projeto):

- [ ] T004 Configurar esquema da base de dados e framework de migrações
- [ ] T005 [P] Implementar framework de autenticação/autorização
- [ ] T006 [P] Configurar roteamento de API e estrutura de middleware
- [ ] T007 Criar modelos/entidades base de que todas as histórias dependem
- [ ] T008 Configurar tratamento de erros e infraestrutura de logs
- [ ] T009 Configurar gestão de configuração de ambiente

**Ponto de Controlo**: Fundação pronta - a implementação da história de utilizador pode agora começar em paralelo

---

## Fase 3: História de Utilizador 1 - [Título] (Prioridade: P1) 🎯 MVP

**Meta**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 1 (OPCIONAL - apenas se solicitados) ⚠️

> **NOTA: Escreva estes testes PRIMEIRO, certifique-se de que FALHAM antes da implementação**

- [ ] T010 [P] [US1] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T011 [P] [US1] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 1

- [ ] T012 [P] [US1] Criar modelo [Entity1] em src/models/[entity1].py
- [ ] T013 [P] [US1] Criar modelo [Entity2] em src/models/[entity2].py
- [ ] T014 [US1] Implementar [Service] em src/services/[service].py (depende de T012, T013)
- [ ] T015 [US1] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py
- [ ] T016 [US1] Adicionar validação e tratamento de erros
- [ ] T017 [US1] Adicionar logs para as operações da história de utilizador 1

**Ponto de Controlo**: A este ponto, a História de Utilizador 1 deve estar totalmente funcional e testável de forma independente

---

## Fase 4: História de Utilizador 2 - [Título] (Prioridade: P2)

**Meta**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 2 (OPCIONAL - apenas se solicitados) ⚠️

- [ ] T018 [P] [US2] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T019 [P] [US2] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 2

- [ ] T020 [P] [US2] Criar modelo [Entity] em src/models/[entity].py
- [ ] T021 [US2] Implementar [Service] em src/services/[service].py
- [ ] T022 [US2] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py
- [ ] T023 [US2] Integrar com os componentes da História de Utilizador 1 (se necessário)

**Ponto de Controlo**: A este ponto, as Histórias de Utilizador 1 E 2 devem ambas funcionar de forma independente

---

## Fase 5: História de Utilizador 3 - [Título] (Prioridade: P3)

**Meta**: [Breve descrição do que esta história entrega]

**Teste Independente**: [Como verificar se esta história funciona por si só]

### Testes para a História de Utilizador 3 (OPCIONAL - apenas se solicitados) ⚠️

- [ ] T024 [P] [US3] Teste de contrato para [endpoint] em tests/contract/test_[nome].py
- [ ] T025 [P] [US3] Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py

### Implementação para a História de Utilizador 3

- [ ] T026 [P] [US3] Criar modelo [Entity] em src/models/[entity].py
- [ ] T027 [US3] Implementar [Service] em src/services/[service].py
- [ ] T028 [US3] Implementar [endpoint/funcionalidade] em src/[localizacao]/[ficheiro].py

**Ponto de Controlo**: Todas as histórias de utilizador devem agora estar funcionalmente independentes

---

[Adicione mais fases de histórias de utilizador conforme necessário, seguindo o mesmo padrão]

---

## Fase N: Polimento e Preocupações Transversais

**Objetivo**: Melhorias que afetam múltiplas histórias de utilizador

- [ ] TXXX [P] Atualizações de documentação em docs/
- [ ] TXXX Limpeza e refatoração de código
- [ ] TXXX Otimização de desempenho em todas as histórias
- [ ] TXXX [P] Testes unitários adicionais (se solicitados) em tests/unit/
- [ ] TXXX Reforço de segurança
- [ ] TXXX Executar validação de quickstart.md

---

## Dependências e Ordem de Execução

### Dependências de Fase

- **Configuração (Fase 1)**: Sem dependências - pode começar imediatamente
- **Fundacional (Fase 2)**: Depende da conclusão da Configuração - BLOQUEIA todas as histórias de utilizador
- **Histórias de Utilizador (Fase 3+)**: Todas dependem da conclusão da fase Fundacional
  - As histórias de utilizador podem prosseguir em paralelo (se houver equipa)
  - Ou sequencialmente por ordem de prioridade (P1 → P2 → P3)
- **Polimento (Fase Final)**: Depende de todas as histórias de utilizador desejadas estarem concluídas

### Dependências entre Histórias de Utilizador

- **História de Utilizador 1 (P1)**: Pode começar após a Fundacional (Fase 2) - Sem dependências de outras histórias
- **História de Utilizador 2 (P2)**: Pode começar após a Fundacional (Fase 2) - Pode integrar com US1, mas deve ser testável de forma independente
- **História de Utilizador 3 (P3)**: Pode começar após a Fundacional (Fase 2) - Pode integrar com US1/US2, mas deve ser testável de forma independente

### Dentro de Cada História de Utilizador

- Os testes (se incluídos) DEVEM ser escritos e FALHAR antes da implementação
- Modelos antes de serviços
- Serviços antes de endpoints
- Implementação principal antes da integração
- História concluída antes de passar para a prioridade seguinte

### Oportunidades em Paralelo

- Todas as tarefas de Configuração marcadas com [P] podem correr em paralelo
- Todas as tarefas Fundacionais marcadas com [P] podem correr em paralelo (dentro da Fase 2)
- Uma vez concluída a fase Fundacional, todas as histórias de utilizador podem começar em paralelo (se a capacidade da equipa o permitir)
- Todos os testes para uma história de utilizador marcados com [P] podem correr em paralelo
- Modelos dentro de uma história marcados com [P] podem correr em paralelo
- Diferentes histórias de utilizador podem ser desenvolvidas em paralelo por diferentes membros da equipa

---

## Exemplo Paralelo: História de Utilizador 1

```bash
# Executar todos os testes para a História de Utilizador 1 em conjunto (se os testes forem solicitados):
Tarefa: "Teste de contrato para [endpoint] em tests/contract/test_[nome].py"
Tarefa: "Teste de integração para [jornada do utilizador] em tests/integration/test_[nome].py"

# Executar todos os modelos para a História de Utilizador 1 em conjunto:
Tarefa: "Criar modelo [Entity1] em src/models/[entity1].py"
Tarefa: "Criar modelo [Entity2] em src/models/[entity2].py"


