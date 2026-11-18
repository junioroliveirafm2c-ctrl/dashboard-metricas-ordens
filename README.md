# Dashboard Elite PCM — Medidor de Atendimento por Área

Dashboard gerencial interativo desenvolvido a partir dos dados reais de **METRICAS DE ORDENS.XLSX** (fonte: `C:\Users\exjoli16\Downloads\METRICAS DE ORDENS.XLSX`).

## Entregáveis incluídos

1. **Painel executivo geral** — KPIs, atendimentos por área/mês, evolução, participação, empilhado área×status, medidor vs meta, ranking TOP 10, matriz área×mês e inteligência analítica.
2. **Painel de atendimento por área** — área/mês/ano selecionados, quantidade total, participação, comparativos com mês anterior e mesmo mês do ano anterior, evolução e distribuição por status.
3. **Painel de evolução mensal e anual** — gráficos mensal/anual, tendência por área e tabela mês×ano.
4. **Painel de status das ordens** — KPIs e gráficos por situação/status, com dicionário de classificação editável na sessão.
5. **Tabela detalhada com possibilidade de filtragem** — filtros globais combináveis + busca textual.
6. **Dicionário de classificação das áreas** — mapeamento editável (código derivado do Local de instalação → nome da área), com exportação JSON.
7. **Estrutura preparada para atualização da base** — script `build_data.py`, configs preserváveis e dados reprocessáveis.

## Como usar

- Abra `index.html` no navegador (dashboard interativo, com dados embutidos em `data/dados_embutidos.js`).
- Use os filtros globais (Ano, Mês, Área, Centro de trabalho, Tipo de ordem, Status do usuário, Status do sistema). Todos os indicadores e gráficos atualizam automaticamente.
- No painel **Dicionário de Classificação**, ajuste nomes de áreas e cadastre metas mensais (não informadas na base). É possível exportar os JSONs atualizados.
- No painel **Status das Ordens**, ajuste a situação de cada *Status do sistema* (Concluída/Pendente/Em Execução/Não Informada) para validação; os KPIs são recalculados conforme o dicionário.

## Regras aplicadas (dados reais)

- **Ordem**: identificador do atendimento; ordens duplicadas não são contadas mais de uma vez (na base atual não há duplicidades).
- **Data-base do início**: origem de mês e ano.
- **Local de instalação**: origem da identificação/classificação da área (código derivado do dado real). Registros sem classificação permanecem como **NÃO CLASSIFICADO**.
- **Status**: ordens **não** são consideradas concluídas automaticamente; indicadores de Concluídas/Pendentes/Em Execução são calculados conforme o dicionário de classificação de status (proposta inicial gerada a partir dos códigos SAP observados, **validar/ajustar**).
- **Metas**: não existem na base original; quando não cadastradas, exibidas como **Não informada**.
- Nenhuma área, meta, classificação ou quantidade foi inventada; informações ausentes são identificadas como não informadas.

## Atualização da base (preservando histórico/configurações)

1. Atualize a planilha original: `C:\Users\exjoli16\Downloads\METRICAS DE ORDENS.XLSX` (ou ajuste `SOURCE_XLSX` em `build_data.py`).
2. Na pasta do dashboard, execute:
   ```bash
   python build_data.py
   ```
3. O script reimporta os registros, remove duplicidades de Ordem, atualiza `data/ordens.json`, `data/metadata.json` e `data/dados_embutidos.js`, e **preserva/mescla** `config/classificacao_areas.json`, `config/classificacao_status.json` e `config/metas.json` (mantém ajustes e adiciona novas áreas/status encontrados).
4. Reabra/recarregue `index.html`.

## Estrutura

- `index.html` — dashboard interativo (painéis, filtros, gráficos, tabelas, dicionários).
- `build_data.py` — processamento da planilha e geração/atualização dos dados.
- `data/ordens.json`, `data/metadata.json` — dados processados.
- `data/dados_embutidos.js` — dados/configs embutidos para abertura local do dashboard.
- `config/classificacao_areas.json` — dicionário de áreas (editável).
- `config/classificacao_status.json` — dicionário de status/situação (editável, validar).
- `config/metas.json` — metas mensais cadastradas.

## Observações analíticas

- Variação percentual, aumento/redução de demanda, concentração e alertas são calculados sobre os dados filtrados.
- "Ranking por volume de ordens registradas" indica volume registrado, **não** produtividade individual nem eficiência operacional.
