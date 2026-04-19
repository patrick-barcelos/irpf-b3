# IRPF B3 Dashboard 📊

Uma ferramenta automatizada para consolidar investimentos da B3, calcular Preço Médio (Custo Médio) e organizar proventos (Dividendos/JCP) para a declaração de Imposto de Renda 2026 (Ano-Calendário 2025).

## 🚀 Funcionalidades

- **Cálculo de Preço Médio Real:** Algoritmo cronológico que desconta vendas pelo custo médio proporcional.
- **Dashboard Interativo:** Interface em React com busca, ordenação e divisão por fichas da Receita Federal.
- **Privacidade:** Seus dados financeiros não saem da sua máquina.

---

## 📂 Como obter os arquivos (Passo a Passo)

Para a precisão total dos cálculos, você precisará de **4 arquivos**. Siga as instruções abaixo para cada um:

### 1. Extratos de Movimentação (B3)
Este arquivo contém o histórico de entradas de Dividendos, JCP e Rendimentos.
1. Acesse o portal [Área do Investidor B3](https://investidor.b3.com.br/).
2. No menu superior, clique em **Extratos** > **Movimentação**.
3. No campo de período, selecione: **01/01/2024** a **31/12/2024**.
4. Clique no ícone de **Excel** (Download) no canto superior direito.
5. **Repita o processo** selecionando o período: **01/01/2025** a **31/12/2025**.

### 2. Extrato de Negociação (B3)
Este arquivo é o mais importante para o cálculo do Preço Médio das compras e vendas.
1. No portal [Área do Investidor B3](https://investidor.b3.com.br/), vá em **Extratos** > **Negociação**.
2. Selecione o período completo: **01/01/2024** a **31/12/2025**.
3. Clique no ícone de **Excel** (Download).

### 3. Arquivo da Declaração Anterior (.DEC)
Este arquivo contém os saldos que você já declarou e ativos fora da B3 (como seu carro ou contas bancárias).
1. Abra o **Programa IRPF 2025** no seu computador.
2. Na lista de declarações, identifique a que foi entregue.
3. No seu computador (Windows ou Mac), navegue até a pasta onde o programa salva os dados.
   - **No Mac:** Geralmente em `Documents/IRPF/2025/transmitidas`.
   - **No Windows:** Geralmente em `C:\Arquivos de Programas RFB\IRPF2025\aplicacao\dados`.
4. Procure o arquivo que começa com o seu CPF e termina com a extensão **.DEC** (Ex: `12345678900-IRPF-A-2025-2024-ORIGI.DEC`).

---

## 🛠️ Como Utilizar

### 1. Instalação
Clone o repositório e instale as dependências:
```bash
git clone https://github.com/patrick-barcelos/irpf-b3.git
cd irpf-b3
pip install pandas openpyxl
```

### 2. Execução
Rode o script passando os arquivos na seguinte ordem:
```bash
python3 scripts/process_b3.py \
  "caminho/movimentacao_2025.xlsx" \
  "caminho/movimentacao_2024.xlsx" \
  "caminho/sua_declaracao.DEC" \
  "caminho/negociacao_2024_2025.xlsx"
```

### 3. Visualização
O Dashboard abrirá automaticamente no seu navegador em `http://localhost:8000`. Use as tabelas para preencher as fichas:
- **Bens e Direitos**
- **Rendimentos Isentos**
- **Rendimentos Sujeitos à Tributação Exclusiva**

---
## 🛡️ Segurança
Os dados financeiros são processados localmente. O arquivo `.gitignore` já está configurado para não permitir que você suba acidentalmente seus dados (`.json`, `.xlsx`, `.DEC`) para o GitHub.
