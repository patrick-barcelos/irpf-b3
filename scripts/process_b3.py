import pandas as pd
import os
import re
import json
import http.server
import socketserver
import webbrowser

class IRPFManager:
    def __init__(self, excel_2025, excel_2024, dec_path=None, neg_path=None):
        self.excel_2025 = excel_2025
        self.excel_2024 = excel_2024
        self.dec_path = dec_path
        self.neg_path = neg_path
        self.portfolio = {}
        self.user_cpf = "39229903809"
        self.user_nome = "PATRICK CRISTIAN BARCELOS"
        self.dash_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")

    def _clean_value(self, val):
        if isinstance(val, str):
            val = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return float(val)
            except: return 0.0
        return float(val) if pd.notnull(val) else 0.0

    def _extract_ticker(self, text):
        match = re.search(r'\b([A-Z]{4}[345611]{1,2})\b', str(text).upper())
        return match.group(1) if match else None

    def parse_dec_file(self):
        if not self.dec_path or not os.path.exists(self.dec_path): return
        print(f"--- LENDO DECLARAÇÃO (.DEC) ---")
        with open(self.dec_path, 'r', encoding='latin-1') as f:
            for line in f:
                if line.startswith('16'): self.user_nome = line[13:73].strip()
                if line.startswith('27'):
                    desc = line[17:400].strip()
                    ticker = self._extract_ticker(desc)
                    qtd_match = re.search(r'(\d+)\s+(?:ACOES|COTAS|UNIDADES|QUANTIDADE)', desc, re.IGNORECASE)
                    key = ticker if ticker else f"OUTRO_{hash(desc)%1000}"
                    vals = re.findall(r'(\d{13})', line)
                    v_2023 = float(vals[-2]) / 100.0 if len(vals) >= 2 else 0.0
                    v_2024_dec = float(vals[-1]) / 100.0 if len(vals) >= 1 else 0.0
                    qtd_ini = int(qtd_match.group(1)) if qtd_match else 0
                    if key not in self.portfolio:
                        self.portfolio[key] = {'qtd': qtd_ini, 'custo': v_2023, 'nome': desc, 'v24_dec': v_2024_dec, 'v24': 0, 'q24': 0, 'v25': 0, 'q25': 0, 'dividendos': 0, 'jcp': 0}
                    else:
                        self.portfolio[key]['qtd'] += qtd_ini; self.portfolio[key]['custo'] += v_2023; self.portfolio[key]['v24_dec'] += v_2024_dec

    def process_negotiations(self):
        if not self.neg_path or not os.path.exists(self.neg_path): return
        df = pd.read_excel(self.neg_path)
        df.columns = [c.strip() for c in df.columns]
        for col in ['Quantidade', 'Preço', 'Valor']:
            if col in df.columns: df[col] = df[col].apply(self._clean_value)
        df['Data do Negócio'] = pd.to_datetime(df['Data do Negócio'], dayfirst=True)
        df = df.sort_values('Data do Negócio')
        for _, row in df.iterrows():
            ticker = row['Código de Negociação']
            if ticker not in self.portfolio:
                self.portfolio[ticker] = {'qtd':0, 'custo':0, 'nome':ticker, 'v24_dec':0, 'v24':0, 'q24':0, 'v25':0, 'q25':0, 'dividendos': 0, 'jcp': 0}
            asset = self.portfolio[ticker]
            tipo = str(row['Tipo de Movimentação']).upper()
            if 'COMPRA' in tipo:
                asset['qtd'] += row['Quantidade']; asset['custo'] += row['Valor']
            elif 'VENDA' in tipo and asset['qtd'] > 0:
                pm = asset['custo'] / asset['qtd']
                asset['qtd'] -= row['Quantidade']; asset['custo'] -= (row['Quantidade'] * pm)
            if row['Data do Negócio'].year == 2024: asset['q24'], asset['v24'] = asset['qtd'], asset['custo']
            elif row['Data do Negócio'].year == 2025: asset['q25'], asset['v25'] = asset['qtd'], asset['custo']

    def process_dividends(self):
        paths = [self.excel_2024, self.excel_2025]
        for path in paths:
            if not path or not os.path.exists(path): continue
            df = pd.read_excel(path)
            df.columns = [c.strip() for c in df.columns]
            for _, row in df.iterrows():
                tipo = str(row['Movimentação']).upper()
                ticker = self._extract_ticker(row['Produto'])
                if ticker and ticker in self.portfolio:
                    val = self._clean_value(row['Valor da Operação'])
                    if pd.to_datetime(row['Data'], dayfirst=True).year == 2025:
                        if 'JUROS SOBRE CAPITAL' in tipo: self.portfolio[ticker]['jcp'] += val
                        elif 'DIVIDENDO' in tipo or 'RENDIMENTO' in tipo: self.portfolio[ticker]['dividendos'] += val

    def export_json(self):
        data = {"usuario": {"nome": self.user_nome, "cpf": self.user_cpf}, "ativos": [], "proventos": []}
        for t, d in self.portfolio.items():
            v24 = d['v24'] if d['v24'] > 0 or d['q24'] > 0 else d['v24_dec']
            q24 = d['q24'] if d['v24'] > 0 or d['q24'] > 0 else 0
            v25 = d['v25'] if d['v25'] > 0 or d['q25'] > 0 else v24
            q25 = d['q25'] if d['v25'] > 0 or d['q25'] > 0 else q24
            
            # Preço Médio Unitário 2025
            pm25 = (v25 / q25) if q25 > 0 else 0

            if v24 > 0.01 or v25 > 0.01:
                data["ativos"].append({
                    "ticker": t, "nome": d['nome'], 
                    "q24": q24, "v24": round(v24, 2), 
                    "q25": q25, "v25": round(v25, 2),
                    "pm25": round(pm25, 4)
                })
            if d['dividendos'] > 0 or d['jcp'] > 0:
                data["proventos"].append({"ticker": t, "dividendos": round(d['dividendos'], 2), "jcp": round(d['jcp'], 2)})
        with open(os.path.join(self.dash_dir, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def start_server(self):
        os.chdir(self.dash_dir)
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            webbrowser.open("http://localhost:8000"); httpd.serve_forever()

if __name__ == "__main__":
    import sys
    e25, e24, dec, neg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    manager = IRPFManager(e25, e24, dec, neg)
    manager.parse_dec_file(); manager.process_negotiations(); manager.process_dividends(); manager.export_json(); manager.start_server()
