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
            'PETR4': '33.000.167/0001-01', 'VALE3': '33.592.510/0001-54',
            'BBDC4': '60.746.948/0001-12', 'ITUB4': '60.872.504/0001-23',
            'KLBN4': '89.637.490/0001-45', 'TAEE11': '07.859.971/0001-30',
            'BBSE3': '17.344.597/0001-94', 'CMIG4': '17.155.730/0001-64',
            'SAPR4': '76.484.013/0001-45', 'BBAS3': '00.000.000/0001-91',
            'CXSE3': '22.543.331/0001-00', 'TVRI11': '14.410.722/0001-29'
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

    def _extract_unit_pm(self, text):
        match = re.search(r'PRECO\s+MEDIO\s+DE\s+R\$\s*(\d+,\d+)', str(text).upper())
        if match: return float(match.group(1).replace(',', '.'))
        return None

    def parse_dec_file(self):
        if not self.dec_path or not os.path.exists(self.dec_path): return
        with open(self.dec_path, 'r', encoding='latin-1') as f:
            for line in f:
                if line.startswith('27'):
                    desc = line[19:400].strip()
                    ticker = self._extract_ticker(desc)
                    if not ticker: continue
                    q_match = re.search(r'(\d+)\s+(?:ACOES|COTAS|UNIDADES)', desc, re.IGNORECASE)
                    q24 = int(q_match.group(1)) if q_match else 0
                    pm_unit = self._extract_unit_pm(desc)
                    vals = re.findall(r'(\d{13})', line)
                    v24 = float(vals[-1]) / 100.0 if vals else 0.0
                    if pm_unit and v24 == 0: v24 = q24 * pm_unit
                    self.portfolio[ticker] = {'nome': desc, 'q24': q24, 'v24': v24, 'pm_fix': pm_unit, 'q25': q24, 'v25': v24, 'div': 0, 'jcp': 0, 'fii': 0}

    def process_2025(self):
        # Primeiro, atualizar as quantidades de 2025 lendo as planilhas
        all_dfs = []
        if self.neg_path:
            df = pd.read_excel(self.neg_path); df.columns = [c.strip() for c in df.columns]
            df['Data'] = pd.to_datetime(df['Data do Negócio'], dayfirst=True)
            all_dfs.append(df[df['Data'].dt.year == 2025].rename(columns={'Código de Negociação': 'ticker_norm', 'Tipo de Movimentação': 'tipo_mov'}))
        
        # Processa Proventos e Bonificações (Quantidade)
        df_mov = pd.read_excel(self.excel_2025); df_mov.columns = [c.strip() for c in df_mov.columns]
        df_mov['Data'] = pd.to_datetime(df_mov['Data'], dayfirst=True)
        
        for _, r in df_mov[df_mov['Data'].dt.year == 2025].iterrows():
            t = self._extract_ticker(r['Produto'])
            if not t: continue
            if t not in self.portfolio: self.portfolio[t] = {'nome': r['Produto'], 'q24':0, 'v24':0, 'pm_fix':None, 'q25':0, 'v25':0, 'div':0, 'jcp':0, 'fii':0}
            
            asset = self.portfolio[t]
            tipo = str(r['Movimentação']).upper()
            q, v = self._clean_value(r['Quantidade']), self._clean_value(r['Valor da Operação'])
            
            if 'COMPRA' in tipo or 'LIQUIDAÇÃO' in tipo or 'BONIFICAÇÃO' in tipo: asset['q25'] += q
            elif 'VENDA' in tipo: asset['q25'] -= q
            elif 'JUROS SOBRE CAPITAL' in tipo: asset['jcp'] += v
            elif 'RENDIMENTO' in tipo: asset['fii'] += v
            elif 'DIVIDENDO' in tipo: asset['div'] += v

        # REGRA SOBERANA: Saldo Final = Quantidade Final * PM do Texto
        for t, d in self.portfolio.items():
            if d['pm_fix']:
                d['v24'] = d['q24'] * d['pm_fix']
                d['v25'] = d['q25'] * d['pm_fix']
            elif d['q24'] > 0:
                pm_auto = d['v24'] / d['q24']
                d['v25'] = d['q25'] * pm_auto

    def export_json(self):
        data = {"usuario": {"nome": self.user_nome, "cpf": self.user_cpf}, "ativos": [], "proventos": []}
        for t, d in self.portfolio.items():
            if d['q24'] > 0 or d['q25'] > 0:
                data["ativos"].append({"ticker": t, "nome": d['nome'], "q24": d['q24'], "v24": round(d['v24'], 2), "q25": int(d['q25']), "v25": round(d['v25'], 2)})
            if d['div'] > 0: data["proventos"].append({"ticker": t, "tipo": "DIVIDENDO", "valor": round(d['div'], 2), "cnpj": self.cnpj_map.get(t, "")})
            if d['fii'] > 0: data["proventos"].append({"ticker": t, "tipo": "FII", "valor": round(d['fii'], 2), "cnpj": self.cnpj_map.get(t, "")})
            if d['jcp'] > 0: data["proventos"].append({"ticker": t, "tipo": "JCP", "valor": round(d['jcp'], 2), "cnpj": self.cnpj_map.get(t, "")})
        with open(os.path.join(self.dash_dir, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    import sys
    e25, e24, dec, neg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    manager = IRPFManager(e25, e24, dec, neg)
    manager.parse_dec_file(); manager.process_2025(); manager.export_json()
    os.chdir(manager.dash_dir)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
        webbrowser.open("http://localhost:8000"); httpd.serve_forever()
