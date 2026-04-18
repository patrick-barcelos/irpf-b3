import pandas as pd
import xml.etree.ElementTree as ET
import os
import re
import json

class IRPFManager:
    def __init__(self, excel_path, xml_path=None):
        self.excel_path = excel_path
        self.xml_path = xml_path
        self.portfolio = {}
        self.df_b3 = None
        self.user_case_style = "upper"

    def _clean_value(self, val):
        if isinstance(val, str):
            val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(val)
            except: return 0.0
        return float(val) if pd.notnull(val) else 0.0

    def load_b3_data(self):
        try:
            self.df_b3 = pd.read_excel(self.excel_path)
            self.df_b3.columns = [c.strip() for c in self.df_b3.columns]
            cols_to_clean = ['Quantidade', 'Preço unitário', 'Valor da Operação']
            for col in cols_to_clean:
                if col in self.df_b3.columns:
                    self.df_b3[col] = self.df_b3[col].apply(self._clean_value)
            self.df_b3['Data'] = pd.to_datetime(self.df_b3['Data'], dayfirst=True)
            self.df_b3 = self.df_b3.sort_values('Data')
            return True
        except Exception as e:
            print(f"Erro ao carregar Excel: {e}")
            return False

    def process_calculations(self):
        for _, row in self.df_b3.iterrows():
            produto = row['Produto']
            ticker = produto.split('-')[-1].strip() if '-' in produto else produto
            tipo = row['Movimentação'].upper()
            qtd = row['Quantidade']
            valor_total = row['Valor da Operação']

            if ticker not in self.portfolio:
                self.portfolio[ticker] = {
                    'quantidade': 0, 'custo_total': 0.0, 
                    'dividendos': 0.0, 'jcp': 0.0, 'nome_completo': produto
                }

            if any(x in tipo for x in ['COMPRA', 'LIQUIDAÇÃO', 'BONIFICAÇÃO']):
                self.portfolio[ticker]['quantidade'] += qtd
                self.portfolio[ticker]['custo_total'] += valor_total
            elif 'VENDA' in tipo:
                if self.portfolio[ticker]['quantidade'] > 0:
                    pm = self.portfolio[ticker]['custo_total'] / self.portfolio[ticker]['quantidade']
                    self.portfolio[ticker]['quantidade'] -= qtd
                    self.portfolio[ticker]['custo_total'] -= (qtd * pm)
            elif 'DIVIDENDO' in tipo:
                self.portfolio[ticker]['dividendos'] += valor_total
            elif 'JUROS SOBRE CAPITAL' in tipo:
                self.portfolio[ticker]['jcp'] += valor_total

    def generate_html_dashboard(self, output_path="dashboard_investimentos.html"):
        """Gera um Dashboard visual em HTML com Chart.js"""
        labels = []
        custos = []
        proventos = []
        detalhes = []

        total_investido = 0
        total_div = 0
        total_jcp = 0

        for ticker, data in self.portfolio.items():
            if data['quantidade'] > 0 or data['dividendos'] > 0 or data['jcp'] > 0:
                labels.append(ticker)
                custos.append(round(data['custo_total'], 2))
                proventos.append(round(data['dividendos'] + data['jcp'], 2))
                total_investido += data['custo_total']
                total_div += data['dividendos']
                total_jcp += data['jcp']
                detalhes.append({
                    "ticker": ticker,
                    "nome": data['nome_completo'],
                    "qtd": data['quantidade'],
                    "custo": data['custo_total'],
                    "dividendos": data['dividendos'],
                    "jcp": data['jcp']
                })

        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <title>Dashboard IRPF - B3</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }}
                .container {{ max-width: 1200px; margin: auto; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
                .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
                .card h3 {{ margin: 0; color: #777; font-size: 0.9em; }}
                .card p {{ margin: 10px 0 0; font-size: 1.5em; font-weight: bold; color: #2c3e50; }}
                .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
                .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
                th {{ background: #2c3e50; color: white; }}
                tr:hover {{ background: #f9f9f9; }}
                .positive {{ color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Resumo de Investimentos 2025/2026</h1>
                    <span style="color: #95a5a6;">Gerado via Skill IRPF-B3</span>
                </div>
                
                <div class="cards">
                    <div class="card"><h3>Total Investido (Custo)</h3><p>R$ {total_investido:,.2f}</p></div>
                    <div class="card"><h3>Total Dividendos</h3><p class="positive">R$ {total_div:,.2f}</p></div>
                    <div class="card"><h3>Total JCP (Bruto)</h3><p class="positive">R$ {total_jcp:,.2f}</p></div>
                </div>

                <div class="charts">
                    <div class="chart-container">
                        <h3>Distribuição da Carteira (%)</h3>
                        <canvas id="portfolioChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>Ranking de Proventos (Top 10)</h3>
                        <canvas id="proventosChart"></canvas>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Quantidade</th>
                            <th>Custo Médio Total</th>
                            <th>Dividendos</th>
                            <th>JCP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {" ".join([f"<tr><td>{d['ticker']}</td><td>{d['qtd']:.0f}</td><td>R$ {d['custo']:,.2f}</td><td class='positive'>R$ {d['dividendos']:,.2f}</td><td class='positive'>R$ {d['jcp']:,.2f}</td></tr>" for d in detalhes])}
                    </tbody>
                </table>
            </div>

            <script>
                const labels = {json.dumps(labels)};
                const custos = {json.dumps(custos)};
                const proventos = {json.dumps(proventos)};

                new Chart(document.getElementById('portfolioChart'), {{
                    type: 'doughnut',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            data: custos,
                            backgroundColor: ['#1abc9c', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c', '#2c3e50', '#95a5a6']
                        }}]
                    }}
                }});

                new Chart(document.getElementById('proventosChart'), {{
                    type: 'bar',
                    data: {{
                        labels: labels.slice(0, 10),
                        datasets: [{{
                            label: 'Total Proventos (R$)',
                            data: proventos.slice(0, 10),
                            backgroundColor: '#27ae60'
                        }}]
                    }},
                    options: {{ indexAxis: 'y' }}
                }});
            </script>
        </body>
        </html>
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"\n📊 Dashboard visual gerado com sucesso: {os.path.abspath(output_path)}")

    def print_summary(self):
        print("\n=== RESUMO CONSOLIDADO PARA IRPF (EXCEL B3) ===")
        for ticker, data in self.portfolio.items():
            if data['quantidade'] > 0 or data['dividendos'] > 0 or data['jcp'] > 0:
                print(f"{ticker:<10} | Qtd: {data['quantidade']:>5.0f} | Custo: R$ {data['custo_total']:>10.2f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 process_b3.py <excel_b3> [xml_irpf]")
    else:
        excel, xml = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
        manager = IRPFManager(excel, xml)
        if manager.load_b3_data():
            manager.process_calculations()
            manager.print_summary()
            manager.generate_html_dashboard() # Sempre gera o visual agora
            if xml:
                manager.merge_with_xml("declaracao_atualizada.xml")
