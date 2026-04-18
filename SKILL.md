---
name: irpf-b3
description: Processa extratos de movimentação da B3 (Excel) para gerar relatórios mastigados para o IRPF (Bens e Direitos, Dividendos e JCP).
---

# IRPF B3 - Assistente de Declaração

Esta skill ajuda a transformar o extrato de movimentação oficial da B3 em dados prontos para o programa do IRPF.

## Quando usar
- Quando o usuário fornecer um arquivo Excel (.xlsx) baixado da Área do Investidor B3.
- Quando for necessário calcular Preço Médio ou consolidar Proventos (Dividendos/JCP) do ano-calendário.

## Fluxo de Trabalho
1. **Identificar o Arquivo:** Verifique se o arquivo contém colunas como 'Produto', 'Movimentação', 'Quantidade' e 'Valor da Operação'.
2. **Executar Processamento:** Utilize o script `scripts/process_b3.py` para processar os dados.
3. **Gerar Relatório:** Formate a saída seguindo os códigos da Receita Federal:
    - **Ações:** Grupo 03, Código 01.
    - **FIIs:** Grupo 07, Código 03.
    - **ETFs:** Grupo 07, Código 09.
    - **BDRs:** Grupo 04, Código 04.

## Scripts Inclusos
- `process_b3.py`: Recebe o caminho do Excel e imprime o resumo de Bens e Direitos e Proventos.

## Códigos de Proventos no IRPF
- **Dividendos / Rendimentos FII:** Ficha "Rendimentos Isentos e Não Tributáveis".
- **JCP:** Ficha "Rendimentos Sujeitos à Tributação Exclusiva/Definitiva" (Código 10).
