---
name: irpf-b3
description: Processa extratos da B3, mescla dados no XML do IRPF e gera dashboards visuais, seguindo as normas oficiais da Receita Federal 2026.
---

# IRPF B3 - Assistente de Integração e Conformidade 2026

Esta skill automatiza o processamento de investimentos e a atualização do arquivo de declaração da Receita Federal, mantendo o estilo de preenchimento do usuário e as normas oficiais.

## Quando usar
- Para processar arquivos Excel da B3 e gerar Dashboards visuais.
- Para **atualizar um XML existente** do IRPF com novos dados de investimentos.

## Como usar (Workflow)
1. **Coleta:** O usuário fornece o Excel da B3 e o XML da declaração (opcional).
2. **Consultar Normas:** Sempre verifique `references/normas_receita_2026.md` para garantir que os limites e códigos estão corretos antes de sugerir ações.
3. **Executar Processamento:** Execute `scripts/process_b3.py <arquivo_excel> <arquivo_xml>`.
4. **Resultado:** 
   - Dashboard HTML Interativo.
   - Arquivo `declaracao_atualizada.xml` pronto para importação.

## Recursos Offline
- **Normas Receita 2026:** Guia completo de limites, códigos e prazos em `references/normas_receita_2026.md`.

## Regras de Inteligência
- **Estilo:** O script detecta automaticamente se o usuário usa UPPERCASE ou Title Case e mimetiza esse comportamento.
- **Merge:** Se o ativo já existir no XML, apenas o valor é atualizado; a descrição original é preservada.
- **FIIs:** Rendimentos de FIIs são somados automaticamente aos proventos isentos.
