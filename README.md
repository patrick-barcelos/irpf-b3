# IRPF B3 Dashboard 📊

Uma ferramenta automatizada para consolidar investimentos da B3, calcular Preço Médio (Custo Médio) e organizar proventos (Dividendos/JCP) para a declaração de Imposto de Renda 2026 (Ano-Calendário 2025).

## 🚀 Funcionalidades

- **Processamento Multi-Arquivo:** Lê arquivos `.DEC` (Receita Federal), Extratos de Movimentação e Relatórios de Negociação da B3.
- **Cálculo de Preço Médio Real:** Algoritmo cronológico que desconta vendas pelo custo médio, seguindo a norma da Receita.
- **Dashboard Interativo:** Interface em React com busca, ordenação e divisão por fichas:
    - **Bens e Direitos** (Patrimônio e Quantidades).
    - **Rendimentos Isentos** (Dividendos e FIIs).
    - **Tributação Exclusiva** (JCP).
- **Servidor Local:** Abre automaticamente no seu navegador em `http://localhost:8000`.

## 📂 Como baixar os arquivos necessários

Para que a ferramenta funcione com precisão total, você deve baixar os seguintes arquivos:

1. **Área do Investidor B3 (Extratos > Movimentação):**
   - Baixe o Excel do período **01/01/2024 a 31/12/2024**.
   - Baixe o Excel do período **01/01/2025 a 31/12/2025**.
2. **Área do Investidor B3 (Extratos > Negociação):**
   - Baixe o Excel do período completo (**01/01/2024 a 31/12/2025**).
3. **Programa IRPF 2025:**
   - Localize o arquivo `.DEC` da sua última declaração entregue (base 2024).

## 🛠️ Como Utilizar

### 1. Instalação
Clone o repositório e instale as dependências:
```bash
git clone https://github.com/patrick-barcelos/irpf-b3.git
cd irpf-b3
pip install pandas openpyxl
```

### 2. Execução
Execute o script passando os caminhos dos arquivos na ordem correta:
```bash
python3 scripts/process_b3.py \
  "movimentacao_2025.xlsx" \
  "movimentacao_2024.xlsx" \
  "sua_declaracao_2025.DEC" \
  "negociacao_2024_2025.xlsx"
```

### 3. Visualização
O script abrirá automaticamente o navegador em `http://localhost:8000`. Use os dados da tabela para preencher as fichas do seu IRPF 2026.

## 🛡️ Segurança e Privacidade
Os dados são processados localmente na sua máquina. O servidor web roda apenas em `localhost` e nenhuma informação é enviada para servidores externos.

---
Desenvolvido para facilitar a vida do investidor. 📈
