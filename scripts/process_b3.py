import pandas as pd
import os

class IRPFCalculator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.portfolio = {}

    def load_data(self):
        """Carrega o Excel de Movimentação da B3"""
        try:
            # A B3 costuma ter cabeçalhos nas primeiras linhas, o pandas lida bem se pularmos o que não é tabela
            self.df = pd.read_excel(self.file_path)
            # Limpeza básica de nomes de colunas (remover espaços e acentos se necessário)
            self.df.columns = [c.strip() for c in self.df.columns]
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def process_movements(self):
        """Calcula Preço Médio e Saldos"""
        # Ordenar por data para garantir o cálculo cronológico do preço médio
        self.df['Data'] = pd.to_datetime(self.df['Data'], dayfirst=True)
        self.df = self.df.sort_values('Data')

        for _, row in self.df.iterrows():
            produto = row['Produto']
            # Extrair ticker (ex: PETR4 de 'PETROBRAS PN - PETR4')
            ticker = produto.split('-')[-1].strip() if '-' in produto else produto
            
            tipo = row['Movimentação'].upper()
            qtd = row['Quantidade']
            preco_unit = row['Preço unitário']
            valor_total = row['Valor da Operação']

            if ticker not in self.portfolio:
                self.portfolio[ticker] = {
                    'quantidade': 0,
                    'custo_total': 0.0,
                    'dividendos': 0.0,
                    'jcp': 0.0,
                    'bonificacoes': 0
                }

            # Lógica de Preço Médio
            if 'COMPRA' in tipo or 'TRANSFERÊNCIA - LIQUIDAÇÃO' in tipo:
                if qtd > 0:
                    self.portfolio[ticker]['quantidade'] += qtd
                    self.portfolio[ticker]['custo_total'] += valor_total
            
            elif 'VENDA' in tipo:
                if self.portfolio[ticker]['quantidade'] > 0:
                    # Na venda, o custo total diminui proporcionalmente ao custo médio atual
                    preco_medio_atual = self.portfolio[ticker]['custo_total'] / self.portfolio[ticker]['quantidade']
                    self.portfolio[ticker]['quantidade'] -= qtd
                    self.portfolio[ticker]['custo_total'] -= (qtd * preco_medio_atual)

            # Lógica de Proventos
            elif 'DIVIDENDO' in tipo:
                self.portfolio[ticker]['dividendos'] += valor_total
            
            elif 'JUROS SOBRE CAPITAL' in tipo:
                self.portfolio[ticker]['jcp'] += valor_total

            elif 'BONIFICAÇÃO' in tipo:
                self.portfolio[ticker]['quantidade'] += qtd
                # Bonificações no IR tem um valor atribuído pela empresa, 
                # mas no extrato B3 costuma vir o valor da incorporação.
                self.portfolio[ticker]['custo_total'] += valor_total

    def generate_report(self):
        """Exibe o relatório para o IRPF"""
        print("\n=== RELATÓRIO PARA IRPF 2026 (Base 2025) ===")
        for ticker, data in self.portfolio.items():
            if data['quantidade'] > 0:
                pm = data['custo_total'] / data['quantidade']
                print(f"\nATIVO: {ticker}")
                print(f"  - Quantidade em 31/12/2025: {data['quantidade']}")
                print(f"  - Custo Médio Unitário: R$ {pm:.2f}")
                print(f"  - Valor Total em Bens e Direitos: R$ {data['custo_total']:.2f}")
                print(f"  - Total Dividendos (Isentos): R$ {data['dividendos']:.2f}")
                print(f"  - Total JCP (Tributação Exclusiva): R$ {data['jcp']:.2f}")

if __name__ == "__main__":
    print("Iniciando Calculadora IRPF MVP...")
    # Aqui você substituiria pelo caminho do seu arquivo baixado da B3
    # calc = IRPFCalculator('data/movimentacao_b3.xlsx')
    # if calc.load_data():
    #     calc.process_movements()
    #     calc.generate_report()
