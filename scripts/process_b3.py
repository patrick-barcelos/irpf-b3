import pandas as pd
import xml.etree.ElementTree as ET
import os
from datetime import datetime

class IRPFManager:
    def __init__(self, excel_path, xml_path=None):
        self.excel_path = excel_path
        self.xml_path = xml_path
        self.portfolio = {}
        self.df_b3 = None

    def load_b3_data(self):
        """Carrega e processa o Excel da B3"""
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
        """Calcula as posições consolidadas"""
        for _, row in self.df_b3.iterrows():
            produto = row['Produto']
            ticker = produto.split('-')[-1].strip() if '-' in produto else produto
            tipo = row['Movimentação'].upper()
            qtd = row['Quantidade']
            valor_total = row['Valor da Operação']

            if ticker not in self.portfolio:
                self.portfolio[ticker] = {
                    'quantidade': 0,
                    'custo_total': 0.0,
                    'dividendos': 0.0,
                    'jcp': 0.0,
                    'nome_completo': produto
                }

            if 'COMPRA' in tipo or 'TRANSFERÊNCIA - LIQUIDAÇÃO' in tipo or 'BONIFICAÇÃO' in tipo:
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

    def merge_with_xml(self, output_path):
        """Mescla os dados calculados no XML do IRPF"""
        if not self.xml_path or not os.path.exists(self.xml_path):
            print("XML de base não fornecido ou não encontrado.")
            return

        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Localiza ou cria as seções principais do IRPF
        bens_section = root.find('.//bensEDireitos')
        if bens_section is None:
            bens_section = ET.SubElement(root, 'bensEDireitos')

        for ticker, data in self.portfolio.items():
            if data['quantidade'] <= 0: continue

            # Tenta encontrar se o ativo já existe no XML (simplificado pelo ticker na descrição)
            found = False
            for bem in bens_section.findall('bem'):
                disc = bem.find('discriminacao').text if bem.find('discriminacao') is not None else ""
                if ticker in disc:
                    # Atualiza valor atual
                    val_atual = bem.find('valorAtual')
                    if val_atual is not None:
                        val_atual.text = f"{data['custo_total']:.2f}"
                    found = True
                    break
            
            if not found:
                # Adiciona novo bem
                novo_bem = ET.SubElement(bens_section, 'bem')
                ET.SubElement(novo_bem, 'grupo').text = "03" # Padrão Ações, pode ser refinado
                ET.SubElement(novo_bem, 'codigo').text = "01"
                ET.SubElement(novo_bem, 'discriminacao').text = f"{data['nome_completo']} - Qtd: {data['quantidade']} (Atualizado via Skill B3)"
                ET.SubElement(novo_bem, 'valorAnterior').text = "0.00"
                ET.SubElement(novo_bem, 'valorAtual').text = f"{data['custo_total']:.2f}"

        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"Sucesso! XML atualizado gerado em: {output_path}")

    def print_summary(self):
        print("\n=== RESUMO CONSOLIDADO B3 ===")
        for t, d in self.portfolio.items():
            if d['quantidade'] > 0:
                print(f"{t}: Qtd {d['quantidade']} | Custo Total: R${d['custo_total']:.2f} | Div: R${d['dividendos']:.2f} | JCP: R${d['jcp']:.2f}")

if __name__ == "__main__":
    # Exemplo de uso via CLI
    import sys
    if len(sys.argv) < 2:
        print("Uso: python process_b3.py <excel_b3> [xml_irpf]")
    else:
        excel = sys.argv[1]
        xml = sys.argv[2] if len(sys.argv) > 2 else None
        manager = IRPFManager(excel, xml)
        if manager.load_b3_data():
            manager.process_calculations()
            manager.print_summary()
            if xml:
                manager.merge_with_xml("declaracao_atualizada.xml")
