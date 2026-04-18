---
name: irpf-b3
description: Processa extratos da B3 e mescla os dados (Bens, Dividendos, JCP) diretamente no arquivo XML da declaração do IRPF.
---

# IRPF B3 - Assistente de Integração Total

Esta skill automatiza o processamento de investimentos e a atualização do arquivo de declaração da Receita Federal.

## Quando usar
- Para processar arquivos Excel da B3.
- Para **atualizar um XML existente** do IRPF com novos dados de investimentos.

## Como usar (Workflow)
1. **Coleta:** O usuário fornece o Excel da B3 e o XML da declaração (opcional).
2. **Processamento:** Execute `scripts/process_b3.py <arquivo_excel> <arquivo_xml>`.
3. **Resultado:** 
   - Resumo no terminal (Compra, Venda, Proventos).
   - Arquivo `declaracao_atualizada.xml` pronto para importação no programa do IRPF.

## Regras de Negócio Inclusas
- **Custo Médio:** Calculado cronologicamente.
- **Merge Inteligente:** Se o ativo já existir no XML, ele apenas atualiza o valor. Se não existir, ele cria um novo registro.
- **Proventos:** Identifica Dividendos (Isentos) e JCP (Tributação Exclusiva).

## Importação no Programa IRPF
Após gerar o XML atualizado:
1. Abra o Programa IRPF 2026.
2. Vá em **Ferramentas** > **Importar Dados de Arquivo XML**.
3. Selecione o arquivo gerado pela skill.
