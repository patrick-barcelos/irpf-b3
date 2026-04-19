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
        
        self.cnpj_map = {
            'PETR4': '33.000.167/0001-01', 'PETR3': '33.000.167/0001-01',
            'VALE3': '33.592.510/0001-54', 'BBDC4': '60.746.948/0001-12', 
            'BBDC3': '60.746.948/0001-12', 'ITUB4': '60.872.504/0001-23', 
            'ITUB3': '60.872.504/0001-23', 'KLBN4': '89.637.490/0001-45', 
            'TAEE11': '07.859.971/0001-30', 'BBSE3': '17.344.597/0001-94',
            'CMIG4': '17.155.730/0001-64', 'SAPR4': '76.484.013/0001-45',
            'EZTC3': '08.312.229/0001-73', 'WEGE3': '84.429.695/0001-11',
            'BBAS3': '00.000.000/0001-91', 'XPLG11': '26.502.794/0001-85'
        }

    def _clean_value(self, val):
        if isinstance(val, str):
            val = val.replace('R$', '').replace('.', '').replace(',', '.').replace('-', '0').strip()
            try: return float(val)
            except: return 0.0
        return float(val) if pd.notnull(val) else 0.0

    def _extract_ticker(self, text):
        match = re.search(r'\b([A-Z]{4}[345611]{1,2})F?\b', str(text).upper())
        return match.group(1) if match else None

    def _init_asset(self, ticker, nome=""):
        if ticker not in self.portfolio:
            self.portfolio[ticker] = {
                'nome': nome or ticker, 'v23_dec': 0.0, 'v24_dec': 0.0, 'q24_dec': 0,
                'q24_final': 0, 'v24_final': 0, 'q25_final': 0, 'v25_final': 0,
                'div_25': 0, 'jcp_25': 0, 'q_start': 0, 'c_start': 0
            }

    def parse_dec_file(self):
        if not self.dec_path or not os.path.exists(self.dec_path): return
        print(f"--- LENDO DECLARAÇÃO (.DEC) ---")
        with open(self.dec_path, 'r', encoding='latin-1') as f:
            for line in f:
                if line.startswith('16'): self.user_nome = line[13:73].strip()
                if line.startswith('27'):
                    # Posição 19 é onde o código 105 (Brasil) costuma terminar e começar o texto
                    desc = line[19:400].strip()
                    ticker = self._extract_ticker(desc)
                    # Regex mais rigorosa para capturar apenas a quantidade (número antes de ACOES/COTAS)
                    qtd_match = re.search(r'(\d+)\s+(?:ACOES|COTAS|UNIDADES|QUANTIDADE)', desc, re.IGNORECASE)
                    
                    key = ticker if ticker else f"OUTRO_{hash(desc)%1000}"
                    vals = re.findall(r'(\d{13})', line)
                    v_2023 = float(vals[-2]) / 100.0 if len(vals) >= 2 else 0.0
                    v_2024_dec = float(vals[-1]) / 100.0 if len(vals) >= 1 else 0.0
                    qtd_2024_dec = int(qtd_match.group(1)) if qtd_match else 0

                    self._init_asset(key, desc)
                    self.portfolio[key]['v23_dec'] += v_2023
                    self.portfolio[key]['v24_dec'] += v_2024_dec
                    self.portfolio[key]['q24_dec'] += qtd_2024_dec

    def process_all_files(self):
        neg_df = pd.DataFrame()
        if self.neg_path and os.path.exists(self.neg_path):
            neg_df = pd.read_excel(self.neg_path); neg_df.columns = [c.strip() for c in neg_df.columns]
            for col in ['Quantidade', 'Valor']: neg_df[col] = neg_df[col].apply(self._clean_value)
            neg_df['Data'] = pd.to_datetime(neg_df['Data do Negócio'], dayfirst=True)
            neg_df['ticker_norm'] = neg_df['Código de Negociação'].apply(self._extract_ticker)

        mov_dfs = []
        for p in [self.excel_2024, self.excel_2025]:
            if p and os.path.exists(p):
                df = pd.read_excel(p); df.columns = [c.strip() for c in df.columns]
                for col in ['Quantidade', 'Valor da Operação']: df[col] = df[col].apply(self._clean_value)
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
                df['ticker_norm'] = df['Produto'].apply(self._extract_ticker)
                mov_dfs.append(df)
        all_movs = pd.concat(mov_dfs) if mov_dfs else pd.DataFrame()

        all_tickers = set(self.portfolio.keys())
        if not neg_df.empty: all_tickers.update(neg_df['ticker_norm'].dropna().unique())
        if not all_movs.empty: all_tickers.update(all_movs['ticker_norm'].dropna().unique())
        for t in all_tickers: self._init_asset(t)

        for ticker, data in self.portfolio.items():
            net_q24, net_c24 = 0, 0
            if not neg_df.empty:
                t_neg = neg_df[(neg_df['ticker_norm'] == ticker) & (neg_df['Data'].dt.year == 2024)]
                for _, row in t_neg.iterrows():
                    if 'COMPRA' in str(row['Tipo de Movimentação']).upper(): net_q24 += row['Quantidade']; net_c24 += row['Valor']
                    else: net_q24 -= row['Quantidade']
            if not all_movs.empty:
                t_mov = all_movs[(all_movs['ticker_norm'] == ticker) & (all_movs['Data'].dt.year == 2024)]
                for _, row in t_mov.iterrows():
                    tipo = str(row['Movimentação']).upper()
                    if 'BONIFICAÇÃO' in tipo: net_q24 += row['Quantidade']
                    elif 'AMORTIZAÇÃO' in tipo: net_c24 -= row['Valor da Operação']
            data['q_start'] = data['q24_dec'] - net_q24
            data['c_start'] = data['v23_dec']

        for ticker, data in self.portfolio.items():
            curr_q, curr_c = data['q_start'], data['c_start']
            combined = []
            if not neg_df.empty:
                for _, r in neg_df[neg_df['ticker_norm'] == ticker].iterrows():
                    combined.append({'data': r['Data'], 'tipo': str(r['Tipo de Movimentação']).upper(), 'q': r['Quantidade'], 'v': r['Valor']})
            if not all_movs.empty:
                for _, r in all_movs[all_movs['ticker_norm'] == ticker].iterrows():
                    t = str(r['Movimentação']).upper()
                    if any(x in t for x in ['BONIFICAÇÃO', 'AMORTIZAÇÃO', 'DIVIDENDO', 'RENDIMENTO', 'JUROS SOBRE CAPITAL']):
                        combined.append({'data': r['Data'], 'tipo': t, 'q': r['Quantidade'], 'v': r['Valor da Operação']})
            
            combined = sorted(combined, key=lambda x: x['data'])
            for m in combined:
                if 'COMPRA' in m['tipo']: curr_q += m['q']; curr_c += m['v']
                elif 'BONIFICAÇÃO' in m['tipo']: curr_q += m['q']
                elif 'AMORTIZAÇÃO' in m['tipo']: curr_c -= m['v']
                elif 'VENDA' in m['tipo'] and curr_q > 0:
                    pm = curr_c / curr_q; curr_q -= m['q']; curr_c -= (m['q'] * pm)
                if m['data'].year == 2024: data['q24_final'], data['v24_final'] = curr_q, curr_c
                if m['data'].year == 2025:
                    if 'JUROS SOBRE CAPITAL' in m['tipo']: data['jcp_25'] += m['v']
                    elif any(x in m['tipo'] for x in ['DIVIDENDO', 'RENDIMENTO']): data['div_25'] += m['v']
            data['q25_final'], data['v25_final'] = curr_q, curr_c

    def export_json(self):
        data = {"usuario": {"nome": self.user_nome, "cpf": self.user_cpf}, "ativos": [], "proventos": []}
        for t, d in self.portfolio.items():
            q24, v24 = d.get('q24_final', d['q24_dec']), d.get('v24_final', d['v24_dec'])
            q25, v25 = d['q25_final'], v24
            if v24 > 0.01 or v25 > 0.01:
                data["ativos"].append({"ticker": t, "nome": d['nome'], "q24": int(q24), "v24": round(v24, 2), "q25": int(q25), "v25": round(v25, 2)})
            if d['div_25'] > 0 or d['jcp_25'] > 0:
                data["proventos"].append({"ticker": t, "dividendos": round(d['div_25'], 2), "jcp": round(d['jcp_25'], 2), "cnpj": self.cnpj_map.get(t, "CNPJ NÃO ENCONTRADO")})
        with open(os.path.join(self.dash_dir, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def start_server(self):
        os.chdir(self.dash_dir)
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"\n🚀 Dashboard CORRIGIDO: http://localhost:8000"); webbrowser.open("http://localhost:8000"); httpd.serve_forever()

if __name__ == "__main__":
    import sys
    e25, e24, dec, neg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    manager = IRPFManager(e25, e24, dec, neg)
    manager.parse_dec_file(); manager.process_all_files(); manager.export_json(); manager.start_server()
