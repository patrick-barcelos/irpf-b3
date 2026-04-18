import pandas as pd
import xml.etree.ElementTree as ET
import os
import re

class IRPFManager:
    def __init__(self, excel_path, xml_path=None):
        self.excel_path = excel_path
        self.xml_path = xml_path
        self.portfolio = {}
        self.df_b3 = None

    def load_b3_data(self):
        try:
            self.df_b3 = pd.read_excel(self.excel_path)
            self.df_b3.columns = [c.strip() for c in self.df_b3.columns]
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

    def _get_asset_type(self, ticker):
        """Identifica grupo/código baseado no ticker"""
        if ticker.endswith('11'): 
            return ("07", "03") # FII / ETF (simplificado)
        return ("03", "01") # Ações

    def merge_with_xml(self, output_path):
        if not self.xml_path or not os.path.exists(self.xml_path): return

        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        bens_section = root.find('.//bensEDireitos')
        if bens_section is None: bens_section = ET.SubElement(root, 'bensEDireitos')

        print("\n--- ANALISANDO INTEGRAÇÃO XML ---")
        
        for ticker, data in self.portfolio.items():
            if data['quantidade'] <= 0: continue
            
            # Busca por ticker na discriminação (Regex para evitar PETR3 vs PETR4)
            found_bem = None
            for bem in bens_section.findall('bem'):
                disc = bem.find('discriminacao').text if bem.find('discriminacao') is not None else ""
                if re.search(rf'\b{ticker}\b', disc, re.IGNORECASE):
                    found_bem = bem
                    break

            if found_bem is not None:
                old_val = found_bem.find('valorAtual').text if found_bem.find('valorAtual') is not None else "0.00"
                new_val = f"{data['custo_total']:.2f}"
                if old_val != new_val:
                    print(f"[ATUALIZANDO] {ticker}: R$ {old_val} -> R$ {new_val} (Custo Médio)")
                    found_bem.find('valorAtual').text = new_val
                    # Opcional: Adicionar nota na discriminação
                    disc_elem = found_bem.find('discriminacao')
                    if "[B3-SKILL]" not in disc_elem.text:
                        disc_elem.text += f" [B3-SKILL: Custo Médio Atualizado em {datetime.now().strftime('%d/%m/%Y')}]"
                else:
                    print(f"[OK] {ticker}: Valor já está correto.")
            else:
                print(f"[NOVO ATIVO] {ticker}: Adicionando à ficha de Bens e Direitos.")
                grupo, codigo = self._get_asset_type(ticker)
                novo_bem = ET.SubElement(bens_section, 'bem')
                ET.SubElement(novo_bem, 'grupo').text = grupo
                ET.SubElement(novo_bem, 'codigo').text = codigo
                ET.SubElement(novo_bem, 'discriminacao').text = f"{data['nome_completo']} - Qtd: {data['quantidade']} [Adicionado via B3-SKILL]"
                ET.SubElement(novo_bem, 'valorAnterior').text = "0.00"
                ET.SubElement(novo_bem, 'valorAtual').text = f"{data['custo_total']:.2f}"

        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"\n✅ XML gerado: {output_path}")

if __name__ == "__main__":
    from datetime import datetime
    import sys
    if len(sys.argv) < 2:
        print("Uso: python process_b3.py <excel_b3> [xml_irpf]")
    else:
        excel, xml = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
        manager = IRPFManager(excel, xml)
        if manager.load_b3_data():
            manager.process_calculations()
            if xml: manager.merge_with_xml("declaracao_atualizada.xml")
            else: manager.print_summary()
