# Agrovia - DRE Gerencial de Frota

Painel gerencial auditável (DRE por veículo/conjunto) gerado a partir das exportações do ERP Sankhya.
Gestão e Auditoria Técnica: Samuel O Silva.

## Como usar

| Ação | Comando |
|------|---------|
| Validar Excel novo antes de entrar na base | `validar_entrada.bat` |
| Atualizar o painel só no computador | `atualizar_local.bat` |
| Atualizar, auditar e publicar no GitHub Pages | `atualizar.bat` |

Fluxo dos dados: Excel do Sankhya → `dados/entrada_quarentena/` → `validar_entrada.bat` → `dados/banco_de_dados/` → motor → auditor → `index.html`.
A publicação é bloqueada se o auditor reprovar (`saidas/relatorios_auditoria/veredito_publicacao.txt`).

## Instalação

```
pip install -r requirements.txt
copy .env.example .env   (só para o laboratório)
```

## Estrutura

```
├── atualizar.bat, atualizar_local.bat, validar_entrada.bat   pontos de entrada
├── index.html            painel gerado (publicado no GitHub Pages; não editar à mão)
├── src/                  código de produção
│   ├── fontes_dados.py        caminhos do projeto e trava de fontes (única fonte de verdade)
│   ├── regras_lancamento.py   regras de validação partilhadas
│   ├── atualizar_dashboard.py motor: Excel → index.html
│   ├── auditoria_completa.py  auditor: veredito de publicação
│   └── validar_entrada.py     quarentena de lançamentos
├── templates/            template.html (base do index.html)
├── ferramentas/          diagnósticos pontuais
├── laboratorio/          experiências (agente IA, tradutor); fora do fluxo de produção
├── docs/                 pendências do projeto e referências
├── assets/               logotipo oficial
├── DRE-Caminhao/         especificação (spec-kit)
│
│   ── fora do git (dados e saídas locais) ──
├── dados/
│   ├── banco_de_dados/       única fonte de dados válida
│   └── entrada_quarentena/   Excel à espera de validação
└── saidas/
    ├── relatorios_auditoria/ logs, inventário, veredito, pendências
    └── backup_relatorios/    histórico de logs e versões antigas do painel
```

## Regras do padrão

- Nomes novos em `snake_case`, minúsculos, sem acentos nem espaços.
- O repositório é público: dados, relatórios e backups nunca entram no git (`.gitignore`).
- Histórico de código é o git; não criar cópias com data no nome.
- Scripts novos que leem dados usam `listar_ficheiros_fonte()` e os caminhos de `src/fontes_dados.py`.
