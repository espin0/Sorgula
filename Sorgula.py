import sys
import json
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QComboBox, QLabel, QFileDialog
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtCore import Qt

class BBKQueryApp(QWidget):
    def __init__(self):
        super().__init__()

        # BBK kodlarını saklamak için dosya yolu
        self.codes_file = 'bbk_codes.json'
        self.previous_bbk_codes = self.load_bbk_codes()

        # UI bileşenlerini oluştur
        self.initUI()

    def initUI(self):
        # Layout oluştur
        layout = QVBoxLayout()
        
        # Üst kısım için yatay düzen
        top_layout = QHBoxLayout()

        # "Önceki BBK Kodları" etiketi
        self.previous_bbk_label = QLabel('Önceki BBK Kodları:', self)
        top_layout.addWidget(self.previous_bbk_label)

        # BBK kodu seçim kutusu
        self.bbk_combo = QComboBox(self)
        self.bbk_combo.setPlaceholderText('Önceki BBK kodları \\')
        self.bbk_combo.addItems(self.previous_bbk_codes)  # Önceki BBK kodlarını ekle
        self.bbk_combo.currentTextChanged.connect(self.update_bbk_input)

        # Ok işaretini kırmızı yapmak için custom bir stil ekleyelim
        self.bbk_combo.setStyleSheet('QComboBox::drop-down {border: none;}'
                                     'QComboBox::down-arrow {image: url(arrow_down.png);}'
                                     'QComboBox QAbstractItemView {background-color: white; selection-background-color: lightblue;}')

        top_layout.addWidget(self.bbk_combo)

        # BBK kodu giriş kutusu
        self.bbk_input = QLineEdit(self)
        self.bbk_input.setPlaceholderText('BBK kodunu girin')
        top_layout.addWidget(self.bbk_input)

        # Sorgu butonu
        self.query_button = QPushButton('Sorgula', self)
        self.query_button.setStyleSheet('background-color: green; color: white;')
        self.query_button.clicked.connect(self.perform_query)
        top_layout.addWidget(self.query_button)

        # Kaydet butonu
        self.save_button = QPushButton('Kaydet', self)
        self.save_button.setStyleSheet('background-color: blue; color: white;')
        self.save_button.clicked.connect(self.save_to_file)
        top_layout.addWidget(self.save_button)

        layout.addLayout(top_layout)

        # Sonuçları göstermek için metin kutusu
        self.results_text = QTextEdit(self)
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)

        # Ana pencereyi ayarla
        self.setLayout(layout)
        self.setWindowTitle('BBK Altyapı Sorgulama')
        self.setGeometry(100, 100, 900, 380)  # Pencere boyutunu büyütüyoruz

    def load_bbk_codes(self):
        """ Daha önceki BBK kodlarını dosyadan yükle """
        try:
            with open(self.codes_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []  # Dosya yoksa boş liste döndür
        except json.JSONDecodeError:
            return []  # JSON hatası varsa boş liste döndür

    def save_bbk_codes(self):
        """ BBK kodlarını dosyaya kaydet """
        with open(self.codes_file, 'w') as file:
            json.dump(self.previous_bbk_codes, file)

    def update_bbk_input(self, text):
        if text:
            self.bbk_input.setText(text)

    def fetch_address_data(self, bbk_code):
        base_url = "https://user.goknet.com.tr/sistem/getTTAddressWebservice.php"
        urls = {
            "city": f"{base_url}?bbk={bbk_code}&datatype=actionBringAllAddress",
            "check": f"{base_url}?kod={bbk_code}&datatype=checkAddress"
        }
        headers = {
            "accept": "*/*",
            "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest"
        }
        results = {}
        for key, url in urls.items():
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                results[key] = response.json()
            except requests.RequestException as e:
                results[key] = f"İstek hatası: {e}"
            except ValueError:
                results[key] = "JSON formatında veri bekleniyor, ancak alınamadı."
        return results

    def perform_query(self):
        bbk_code = self.bbk_input.text().strip()
        if bbk_code:
            address_data = self.fetch_address_data(bbk_code)

            # BBK kodunu geçmiş kodlar listesine ekle
            if bbk_code not in self.previous_bbk_codes:
                self.previous_bbk_codes.append(bbk_code)
                self.bbk_combo.addItem(bbk_code)
                # BBK kodlarını dosyaya kaydet
                self.save_bbk_codes()

            # Sonuçları formatla
            output = "<h2>City Bilgileri:</h2><table border='1' style='width:100%; border-collapse: collapse;'>"
            city_info = address_data.get('city', {})
            if isinstance(city_info, dict):
                for key, value in city_info.items():
                    if isinstance(value, list):
                        if not value or (len(value) == 1 and value[0].strip() == ''):
                            continue
                        value = ', '.join(value)
                    output += f"<tr><td><strong>{key}</strong></td><td><strong><span style='color:blue;'>{value}</span></strong></td></tr>"
            output += "</table><br>"

            # Check 1 bilgilerini yatay tablo olarak göster
            output += "<table border='1' style='width:100%; border-collapse: collapse;'><tr>"
            check1_info = address_data.get('check', {}).get('1', {})
            if isinstance(check1_info, dict):
                flex_list = check1_info.get('flexList', {})
                if isinstance(flex_list, dict):
                    for flex in flex_list.get('flexList', []):
                        if isinstance(flex, dict):
                            name = flex.get('name', 'Bilinmiyor')
                            value = flex.get('value', 'Bilinmiyor')
                            if name == 'SNTRLMSF':
                                output += f"<td><strong>SANTRAL MESAFESİ:<span style='color:red;'> {value}</span></strong></td>"
                            elif name == 'FIBERX':
                                if value == '1':
                                    output += "<td><strong>FIBERX:<span style='color:red;'> FTTX-V1(GPON) VAR</span></strong></td>"
                                else:
                                    output += "<td><strong>FIBERX:<span style='color:red;'> FTTX-V1(GPON) YOK</span></strong></td>"
                            elif name == 'BSPRT':
                                if value == '1':
                                    output += "<td><strong>BOŞ PORT:<span style='color:red;'> VAR</span></td>"
                                else:
                                    output += "<td><strong>BOŞ PORT:<span style='color:red;'> YOK</span></td>"
                            elif name == 'NDSLX':
                                if value == '1':
                                    output += "<td><strong>VDSL:<span style='color:red;'> VAR</span></strong></td>"
                                else:
                                    output += "<td><strong>VDSL:<span style='color:red;'> YOK</span></strong></td>"
                            elif name in ['SNTRLIDX', 'SNTRLAD', 'SNTRLMDK', 'SNTRLMDA']:
                                output += f"<td><strong>{name}:<span style='color:red;'> {value}</span></strong></td>"
            output += "</tr></table>"

            self.results_text.setHtml(output)
        else:
            self.results_text.setPlainText("Lütfen geçerli bir BBK kodu girin.")

    def save_to_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Sonuçları Kaydet", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.results_text.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BBKQueryApp()
    window.show()
    sys.exit(app.exec_())
