import os, requests, threading
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.clock import Clock

# DİKKAT: yeni_proje.py dosyasındaki sınıfı içeri alıyoruz
from yeni_proje import YeniProje 

class ProjeDuzenleModulu:
    def __init__(self):
        self.isletme = os.environ.get("SECILI_ISLETME", "AMD")
        self.base_url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.satir_objeleri = []
        self.mevcut_filtre = "HEPSİ"
        # Yeni sütun yapısı: Seç, Dur/No/Tar, Müşteri, Proje, Bedel
        self.widths = [0.05, 0.20, 0.20, 0.40, 0.15]
        self.view = None
        self.bulut_verisi = {}

    def hucre(self, t, w, c=(1,1,1,1), bold=False):
        # markup=True metin içinde [color] ve [size] etiketlerini kullanmamızı sağlar
        l = Label(text=str(t), size_hint_x=w, size_hint_y=None, height=dp(55),
                  halign='left', valign='middle', font_size='10sp', color=c, 
                  bold=bold, padding=(dp(5), 0), markup=True)
        l.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        return l

    def buluttan_oku(self):
        def fetch():
            try:
                r = requests.get(f"{self.base_url}/{self.isletme}/projeler.json", timeout=10).json()
                self.bulut_verisi = r if r else {}
                Clock.schedule_once(lambda dt: self.listeyi_yenile(), 0)
            except: pass
        threading.Thread(target=fetch, daemon=True).start()

    def listeyi_yenile(self):
        if not self.view: return
        self.liste_layout.clear_widgets()
        self.satir_objeleri = []
        
        # Başlık Satırı (5 Sütun)
        h_row = GridLayout(cols=5, size_hint_y=None, height=dp(35), spacing=2)
        basliklar = ["SEÇ", "DUR/NO/TAR", "MÜŞTERİ", "PROJE ADI", "BEDEL"]
        for i, m in enumerate(basliklar):
            h_row.add_widget(self.hucre(m, self.widths[i], (1,.8,0,1), True))
        self.liste_layout.add_widget(h_row)

        for musteri_adi, projeler in self.bulut_verisi.items():
            for p_id, v in projeler.items():
                durum = str(v.get("durum", "BEKLEMEDE")).upper()
                if self.mevcut_filtre != "HEPSİ" and self.mevcut_filtre != durum: continue
                
                row = GridLayout(cols=5, size_hint_y=None, height=dp(58), spacing=2)
                
                # 1. Seçim (CheckBox)
                cb = CheckBox(size_hint_x=self.widths[0])
                row.add_widget(cb)
                
                # 2. Durum / No / Tarih (Alt alta ve Renkli)
                d_renk = "00FF00" if durum == "ONAYLANDI" else "FF6600"
                tarih = v.get("tarih", "-")
                # Proje No (ID) çok uzunsa ilk 10 karakterini alabilirsin: p_id[:10]
                birlesik_metin = f"[b][color={d_renk}]{durum}[/color][/b]\n[size=9sp]{p_id}[/size]\n[size=9sp]{tarih}[/size]"
                row.add_widget(self.hucre(birlesik_metin, self.widths[1]))

                # 3. Müşteri (Klasör Adı)
                row.add_widget(self.hucre(musteri_adi, self.widths[2]))

                # 4. Proje Detayı
                row.add_widget(self.hucre(v.get("proje_adi","-"), self.widths[3], bold=True))

                # 5. Bedel
                bedel_metni = f"{v.get('bedel','0')} {v.get('doviz','')}"
                row.add_widget(self.hucre(bedel_metni, self.widths[4]))
                
                self.liste_layout.add_widget(row)
                v["musteri"] = musteri_adi 
                self.satir_objeleri.append({"cb": cb, "p_id": p_id, "veri": v})

    def secileni_gor(self, *args):
        secili = [s for s in self.satir_objeleri if s["cb"].active]
        if not secili: return
        
        proje_verisi = secili[0]["veri"]
        proje_id = secili[0]["p_id"]
        
        form_katmani = YeniProje()
        icerik = form_katmani.ekrani_olustur(duzenleme_verisi=proje_verisi, p_id=proje_id)
        
        self.popup = Popup(title="PROJE DETAYI VE DÜZENLEME", content=icerik, size_hint=(0.95, 0.95))
        self.popup.open()

    def islem(self, tip):
        secili = [s for s in self.satir_objeleri if s["cb"].active]
        if not secili: return
        
        def run():
            for s in secili:
                m_adi = s['veri'].get('musteri', 'BILINMEYEN')
                url = f"{self.base_url}/{self.isletme}/projeler/{m_adi}/{s['p_id']}.json"
                
                if tip == "ONAY":
                    y = "ONAYLANDI" if s['veri'].get("durum") != "ONAYLANDI" else "BEKLEMEDE"
                    requests.patch(url, json={"durum": y})
                elif tip == "SIL":
                    requests.delete(url)
            
            Clock.schedule_once(lambda dt: self.buluttan_oku(), 0)
            
        threading.Thread(target=run, daemon=True).start()

    def ekrani_olustur(self):
        self.view = ModalView(size_hint=(1, 1), auto_dismiss=False)
        ana = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # ÜST PANEL
        ust = BoxLayout(size_hint_y=None, height=dp(55))
        ust.add_widget(Label(text=f"{self.isletme} PROJE LİSTESİ", bold=True, font_size='16sp', size_hint_x=0.7, halign='left'))
        
        f_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        f_box.add_widget(Label(text="FİLTRE", font_size='9sp', color=(.7,.7,.7,1)))
        self.sp = Spinner(text="HEPSİ", values=("HEPSİ", "ONAYLANDI", "BEKLEMEDE"), size_hint_y=None, height=dp(30))
        self.sp.bind(text=lambda s, t: setattr(self, 'mevcut_filtre', t) or self.listeyi_yenile())
        f_box.add_widget(self.sp)
        ust.add_widget(f_box)
        ana.add_widget(ust)
        
        # LİSTE ALANI
        self.scroll = ScrollView()
        self.liste_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        self.liste_layout.bind(minimum_height=self.liste_layout.setter('height'))
        self.scroll.add_widget(self.liste_layout)
        ana.add_widget(self.scroll)
        
        # ALT BUTONLAR
        alt = GridLayout(cols=2, size_hint_y=None, height=dp(95), spacing=5)
        alt.add_widget(Button(text="SEÇİLENİ GÖR", background_color=(0, .5, .7, 1), bold=True, on_release=self.secileni_gor))
        alt.add_widget(Button(text="DURUM DEĞİŞTİR", background_color=(0, .6, .2, 1), bold=True, on_release=lambda x: self.islem("ONAY")))
        alt.add_widget(Button(text="PROJEYİ SİL", background_color=(.7, 0, 0, 1), on_release=lambda x: self.islem("SIL")))
        alt.add_widget(Button(text="KAPAT", background_color=(.3, .3, .3, 1), bold=True, on_release=lambda x: self.view.dismiss()))
        
        ana.add_widget(alt)
        self.view.add_widget(ana)
        self.buluttan_oku()
        self.view.open()
        return self.view

def ekrani_olustur(): 
    return ProjeDuzenleModulu().ekrani_olustur()