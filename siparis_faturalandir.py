import os
import requests
import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.clock import Clock

class SiparisFaturalandirModulu:
    def __init__(self, ana_pencere_referansi=None):
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.base_url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.satir_objeleri = []
        self.view = None
        self.bulut_verisi = {}

        # --- TELEFON İÇİN GENİŞLİK AYARLARI (Toplam 1.0) ---
        # Bu değerleri değiştirerek sütun genişliklerini mobilde ayarlayabilirsin.
        self.W = {
            "sec": 0.08,    # Seçim Kutusu
            "kunye": 0.18,  # Sipariş No / Tarih
            "urun": 0.20,   # Ürün Adı
            "mik": 0.12,    # Miktar + Birim
            "fiyat": 0.10,  # Fiyat
            "tutar": 0.24,  # Toplam Tutar
            "pak": 0.08     # Paket
        }

    def hucre_olustur(self, metin, genislik, renk=(1, 1, 1, 1), bold=False, yukseklik=dp(45), fs='9sp'):
        """ Yazıları dikeyde orta eksene çakılı, yatayda sol sütun çizgisine yaslı yapar. """
        l = Label(
            text=str(metin),
            size_hint_x=genislik,
            size_hint_y=None,
            height=yukseklik,
            font_size=fs,
            color=renk,
            bold=bold,
            halign='left',      # Sola yasla
            valign='middle',    # Dikeyde ortala
            padding=(dp(5), 0)  # Hücrenin solundan 5dp boşluk bırak (Görsel hiza)
        )
        l.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        return l

    def buluttan_oku(self):
        def fetch():
            try:
                url = f"{self.base_url}/{self.isletme}/siparisler.json"
                res = requests.get(url, timeout=10).json()
                self.bulut_verisi = res if res else {}
                Clock.schedule_once(lambda dt: self.listeyi_yenile(), 0)
            except Exception as e:
                print(f"Veri Çekme Hatası: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def listeyi_yenile(self):
        if not self.view: return
        self.liste_layout.clear_widgets()
        self.satir_objeleri = []
        genel_tutar, genel_miktar = 0.0, 0.0

        for firma, siparisler in self.bulut_verisi.items():
            if not isinstance(siparisler, dict): continue

            kalemler = []
            for sid, veri in siparisler.items():
                # --- KRİTİK DÜZELTME: 'onaylandi' (i ile) kontrolü eklendi ---
                durum = veri.get("durum", "").lower()
                if durum not in ["onaylandı", "onaylandi"]: 
                    continue
                
                for urun in veri.get("urunler", []):
                    u = urun.copy()
                    u["_sid"] = sid
                    u["_tarih"] = veri.get("tarih", "-")
                    u["_firma"] = firma
                    kalemler.append(u)

            if not kalemler: continue

            # Müşteri Başlığı (Mavi şerit)
            self.liste_layout.add_widget(
                self.hucre_olustur(f" MÜŞTERİ: {firma.upper()}", 1.0, renk=(0.2, 0.7, 1, 1), bold=True, yukseklik=dp(35), fs='11sp')
            )

            # Sütun Başlıkları (Sarı başlıklar)
            baslik_row = GridLayout(cols=7, size_hint_y=None, height=dp(30), spacing=dp(1))
            b_list = [("SEÇ", self.W["sec"]), ("DURUM/NO/TAR", self.W["kunye"]), ("ÜRÜN", self.W["urun"]),
                      ("MİK", self.W["mik"]), ("FİYAT", self.W["fiyat"]), ("TOPLAM", self.W["tutar"]), ("PAK", self.W["pak"])]
            for m, g in b_list:
                baslik_row.add_widget(self.hucre_olustur(m, g, renk=(1, 0.8, 0, 1), bold=True, fs='8sp'))
            self.liste_layout.add_widget(baslik_row)

            # Ürün Satırları
            for urun in kalemler:
                try:
                    f = float(str(urun.get("fiyat", 0)).replace(",", "."))
                    m = float(str(urun.get("miktar", 0)).replace(",", "."))
                    t = f * m
                    genel_tutar += t; genel_miktar += m
                except: f, m, t = 0, 0, 0

                row_h = dp(55) # Mobilde rahat seçim için ideal yükseklik
                satir = GridLayout(cols=7, size_hint_y=None, height=row_h, spacing=dp(1))

                # Checkbox
                cb_kutusu = BoxLayout(size_hint_x=self.W["sec"], size_hint_y=None, height=row_h, padding=[dp(5), dp(15)])
                cb = CheckBox(active=False); cb.bind(active=self.toplamlar_ara_hesap)
                cb_kutusu.add_widget(cb)
                
                satir.add_widget(cb_kutusu)
                satir.add_widget(self.hucre_olustur(f"ONAY\n{urun['_sid']}\n{urun['_tarih']}", self.W["kunye"], renk=(0,1,0,1), fs='7sp', yukseklik=row_h))
                satir.add_widget(self.hucre_olustur(urun.get("ad"), self.W["urun"], bold=True, fs='10sp', yukseklik=row_h))
                satir.add_widget(self.hucre_olustur(f"{m:g} {urun.get('birim','kg')}", self.W["mik"], yukseklik=row_h))
                satir.add_widget(self.hucre_olustur(f"{f:g} TL", self.W["fiyat"], yukseklik=row_h))
                satir.add_widget(self.hucre_olustur(f"{t:,.2f} TL", self.W["tutar"], renk=(1, 1, 0, 1), bold=True, yukseklik=row_h))
                satir.add_widget(self.hucre_olustur(str(urun.get('paket','-')), self.W["pak"], fs='8sp', yukseklik=row_h))
                self.liste_layout.add_widget(satir)
                self.satir_objeleri.append({
                    "cb": cb, "sip_id": urun["_sid"], "tutar": t, "mik": m, 
                    "urun_adi": urun.get("ad"), "firma": urun["_firma"], "fiyat": f
                })

        self.lbl_tum_val.text = f"{genel_tutar:,.2f} TL | {genel_miktar:,.0f} kg"
        self.toplamlar_ara_hesap()

    def toplamlar_ara_hesap(self, *args):
        st, sm = 0.0, 0.0
        for s in self.satir_objeleri:
            if s["cb"].active: st += s["tutar"]; sm += s["mik"]
        self.lbl_secili_val.text = f"{st:,.2f} TL | {sm:,.0f} kg"

    def fatura_modulune_aktar(self, *args):
        secilenler = [s for s in self.satir_objeleri if s["cb"].active]
        if not secilenler: return
        
        # Sadece verileri paketliyoruz. Firebase PATCH işlemi burada SİLİNDİ.
        secili_siparisler = list(set([(s["sip_id"], s["firma"]) for s in secilenler]))

        try:
            import satis_fatura_modulu
            # Fatura modülüne listeyi gönder
            f_pop = satis_fatura_modulu.fatura_penceresi(aktarilan_siparisler=secili_siparisler)
            icerik = f_pop.content
            
            # --- Fatura Ekranını Otomatik Doldur ---
            all_text_inputs = [w for w in icerik.walk() if isinstance(w, TextInput)]
            for inp in all_text_inputs:
                if inp.hint_text == "Müşteri Seç/Yaz...":
                    inp.text = secilenler[0]["firma"]
                    break
            
            for child in icerik.walk():
                if isinstance(child, Button) and child.text == "SATIR EKLE":
                    for _ in range(len(secilenler) - 1):
                        child.dispatch('on_release')
                    break

            u_k = [w for w in icerik.walk() if isinstance(w, TextInput) and w.hint_text == "Ürün..."]
            m_k = [w for w in icerik.walk() if isinstance(w, TextInput) and w.hint_text == "0"]
            f_k = [w for w in icerik.walk() if isinstance(w, TextInput) and w.hint_text == "0.00"]

            for i, s in enumerate(secilenler):
                if i < len(u_k):
                    u_k[i].text = str(s["urun_adi"])
                    m_k[i].text = str(s["mik"])
                    f_k[i].text = str(s["fiyat"])

            f_pop.open()
            # Kapanınca listeyi yenile (Firebase'deki durum fatura kaydedildiyse değişmiş olacak)
            f_pop.bind(on_dismiss=lambda x: self.buluttan_oku())

        except Exception as e:
            print(f"Aktarım Hatası: {e}")

    def ekrani_olustur(self):
        self.view = ModalView(size_hint=(1, 1), auto_dismiss=False)
        layout = BoxLayout(orientation='vertical', padding=dp(5), spacing=dp(5))
        
        layout.add_widget(Label(text=f"{self.isletme.upper()} ONAYLI SİPARİŞLER", size_hint_y=None, height=dp(40), bold=True, color=(0,1,0,1)))
        
        # Üst Özet Alanı
        ozet = GridLayout(cols=2, size_hint_y=None, height=dp(60), padding=dp(5))
        ozet.add_widget(Label(text="Onaylı Toplam:", font_size='11sp', halign='right'))
        self.lbl_tum_val = Label(font_size='12sp', bold=True)
        ozet.add_widget(self.lbl_tum_val)
        
        ozet.add_widget(Label(text="Faturaya Seçilen:", color=(1,1,0,1), font_size='11sp', halign='right'))
        self.lbl_secili_val = Label(color=(1,1,0,1), font_size='12sp', bold=True)
        ozet.add_widget(self.lbl_secili_val)
        layout.add_widget(ozet)
        
        # Scroll Liste
        self.scroll = ScrollView()
        self.liste_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(3))
        self.liste_layout.bind(minimum_height=self.liste_layout.setter('height'))
        self.scroll.add_widget(self.liste_layout)
        layout.add_widget(self.scroll)
        
        # Butonlar
        alt = GridLayout(cols=3, size_hint_y=None, height=dp(55), spacing=dp(5))
        btn_f = Button(text="FATURA OLUŞTUR", background_color=(0, 0.4, 0, 1), bold=True)
        btn_f.bind(on_release=self.fatura_modulune_aktar)
        
        btn_y = Button(text="YENİLE", background_color=(0.1, 0.1, 0.4, 1))
        btn_y.bind(on_release=lambda x: self.buluttan_oku())
        
        btn_k = Button(text="KAPAT", background_color=(0.3, 0.3, 0.3, 1))
        btn_k.bind(on_release=lambda x: self.view.dismiss())
        
        for b in [btn_f, btn_y, btn_k]: alt.add_widget(b)
        layout.add_widget(alt)
        
        self.view.add_widget(layout)
        self.buluttan_oku()
        return self.view

def ekrani_olustur():
    return SiparisFaturalandirModulu().ekrani_olustur()