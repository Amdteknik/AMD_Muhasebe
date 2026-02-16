import os
import json
import requests
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.spinner import SpinnerOption
from kivy.uix.widget import Widget
from kivy.metrics import dp

class KucukSpinnerSecenegi(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = '9sp'  # Açılan listedeki yazı boyutu
        self.height = '30dp'    # Satır yüksekliğini de biraz daraltabilirsin

# --- MERKEZİ BULUT AYARI ---
FIREBASE_URL = os.environ.get("FIREBASE_URL", "")

class TeklifModulu(BoxLayout):
    def __init__(self, duzenleme_verisi=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 0   # <--- 0 YAPARAK BEYAZIN BUTONLARA DEĞMESİNİ SAĞLIYORUZ
        self.spacing = 0   # Butonlar ve kağıt arasındaki boşluğu da kapatır        
        self.isletme = os.environ.get("SECILI_ISLETME", "AMD") 
        self.musteri_verileri = self.musterileri_buluttan_cek()
        self.firma_isimleri = sorted(list(self.musteri_verileri.keys())) if self.musteri_verileri else []

        # --- KAĞIT GÖRÜNÜMÜ (Artık butonlar burada değil) ---
        self.kagit_dis_kutu = ScrollView(do_scroll_x=False, size_hint_y=1)        
        self.kagit = BoxLayout(orientation='vertical', size_hint=(1, None), padding=[25, 30, 25, 30], spacing=10)
        self.kagit.height = dp(1300) # Bu değer kağıdı butonların altına kadar uzatır (A4 boyu).        
        with self.kagit.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.kagit.size, pos=self.kagit.pos)
        self.kagit.bind(size=self._update_rect, pos=self._update_rect)

        # 1. LOGO
        logo_box = BoxLayout(size_hint_y=None, height=100)
        logo_path = f"{self.isletme} LOGO.jpg"
        try:
            img = Image(source=logo_path, size_hint_x=None, width=180)
            img.fit_mode = "contain"
            logo_box.add_widget(img)
        except:
            logo_box.add_widget(Label(text=f"{self.isletme} LOGO", color=(0,0,0,1), size_hint_x=None, width=180))
        logo_box.add_widget(Label()) 
        self.kagit.add_widget(logo_box)

        # 2. ÜST BİLGİLER
        ust_tablo = GridLayout(cols=4, size_hint_y=None, height=200, spacing=10)
        def create_label(txt):
            return Label(text=txt, color=(0,0,0,1), bold=True, size_hint_x=0.15, font_size='12sp', halign='left', valign='middle')

        ust_tablo.add_widget(create_label("FİRMA"))
        firma_box = BoxLayout(size_hint_x=0.35, spacing=5)
        self.firma_manuel = TextInput(hint_text="Müşteri ismi", multiline=False, font_size='11sp', size_hint_x=0.4)
        self.firma_spinner = Spinner(text="Seçiniz", values=self.firma_isimleri, font_size='11sp', size_hint_x=0.6)
        self.firma_manuel.bind(text=self.firma_filtrele)
        self.firma_spinner.bind(text=self.spinner_secildi)
        firma_box.add_widget(self.firma_manuel); firma_box.add_widget(self.firma_spinner)
        ust_tablo.add_widget(firma_box)
        
        ust_tablo.add_widget(create_label("Tarih: "))
        self.tarih_input = TextInput(text=datetime.now().strftime("%d.%m.%Y"), multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.tarih_input)

        ust_tablo.add_widget(create_label("Ilgili: "))
        self.ilgili = TextInput(multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.ilgili)
        
        ust_tablo.add_widget(create_label("No: "))
        self.teklif_no = TextInput(multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.teklif_no)

        ust_tablo.add_widget(create_label("Konu: "))
        self.konu = TextInput(multiline=False, size_hint_x=1, font_size='12sp')
        ust_tablo.add_widget(self.konu)
        ust_tablo.add_widget(Label(size_hint_x=0.001)); ust_tablo.add_widget(Label(size_hint_x=0.001))
        self.kagit.add_widget(ust_tablo)

        # 3. HİTAP VE GİRİŞ
        self.hitap = TextInput(hint_text="Sayin ...", multiline=False, size_hint_y=None, height=50, font_size='12sp')
        self.giris_metni = TextInput(hint_text="Teklif giris metni...", size_hint_y=None, height=200, font_size='12sp', multiline=True)
        self.kagit.add_widget(self.hitap); self.kagit.add_widget(self.giris_metni)

        # 4. ÜRÜN TABLOSU - BAŞLIKLAR
        baslik_box = BoxLayout(size_hint_y=None, height=50, spacing=2)
        # Toplam 1.0 olacak şekilde satır oranlarıyla BİREBİR AYNI yapıyoruz:
        self.cols_config = [
            ("Açıklama", 0.40), 
            ("Miktar", 0.13),
            ("Birim", 0.07), # Birim başlığını ekledik
            ("B. Fiyat", 0.15), 
            ("Toplam", 0.25) # Toplam kısmını biraz genişlettik
        ]
        for text, hint in self.cols_config:
            baslik_box.add_widget(Button(text=text, background_normal='', background_color=(0.85,0.85,0.85,1), 
                                         color=(0,0,0,1), font_size='11sp', bold=True, size_hint_x=hint))
        self.kagit.add_widget(baslik_box)


        self.urun_satirlari_listesi = []
        self.urun_alani = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.urun_alani.bind(minimum_height=self.urun_alani.setter('height'))
        self.kagit.add_widget(self.urun_alani)

        # TOPLAM
        toplam_bar = BoxLayout(size_hint_y=None, height=40, spacing=2)
        toplam_bar.add_widget(Label(size_hint_x=0.4)) # Sol tarafı boş bırakmak için geniş bir boşluk

        # Etiketi oluştururken halign ve valign ekliyoruz
        self.genel_toplam_label = Label(
            text="GENEL TOPLAM: 0.00 TL", 
            color=(0,0,0,1), 
            bold=True, 
            font_size='11sp', 
            size_hint_x=0.6, # Daha geniş bir alan verdik ki sağa yaslandığı belli olsun
            halign='right',  # Metni sağa yasla
            valign='middle'
        )
        
        # Kritik nokta: Metin alanını (text_size) etiketin boyutuna bağla
        self.genel_toplam_label.bind(size=lambda l, s: setattr(l, 'text_size', s)) 

        toplam_bar.add_widget(self.genel_toplam_label)
        self.kagit.add_widget(toplam_bar)
        # 5. ALT BİLGİLER (KDV ve Termin Satırları)
        
        # --- KDV Satırı ---
        kdv_box = BoxLayout(size_hint_y=None, height='30dp', spacing='5dp')
        self.chk_kdv = CheckBox(active=True, color=(0,0,0,1), size_hint=(None, 1), width='40dp')
        kdv_metni = Label(
            text="Fiyatlarimiza KDV dahil degildir.", 
            color=(0,0,0,1), 
            font_size='12sp', 
            size_hint_x=None, 
            width='200dp', 
            halign='left', 
            valign='middle'
        )
        kdv_metni.bind(size=kdv_metni.setter('text_size')) # Metni kutu içinde sola yaslamak için
        
        kdv_box.add_widget(self.chk_kdv)
        kdv_box.add_widget(kdv_metni)
        kdv_box.add_widget(Label()) # Kalan boşluğu doldurmak için
        self.kagit.add_widget(kdv_box)

        # --- Termin Satırı ---
        term_box = BoxLayout(size_hint_y=None, height='30dp', spacing='5dp')
        self.chk_termin = CheckBox(active=True, color=(0,0,0,1), size_hint=(None, 1), width='40dp')
        
        term_etiket = Label(text="Termin:", color=(0,0,0,1), size_hint=(None, 1), width='50dp', font_size='12sp')
        
        self.termin_rakam = TextInput(
            text="5", 
            multiline=False, 
            size_hint=(None, 1), 
            width='40dp', 
            font_size='11sp', 
            halign='center', 
            padding_y=[5, 5]
        )
        
        self.termin_birim = Spinner(
            text="Is Gunu", 
            values=("Is Gunu", "Hafta", "Ay"), 
            size_hint=(None, 1), 
            width='80dp', 
            font_size='10sp', 
            option_cls=KucukSpinnerSecenegi
        )
        
        term_box.add_widget(self.chk_termin)
        term_box.add_widget(term_etiket)
        term_box.add_widget(self.termin_rakam)
        term_box.add_widget(self.termin_birim)
        term_box.add_widget(Label()) # Sağa yaslı durmaları için sona boşluk
        self.kagit.add_widget(term_box)

        itici_bosluk = Widget(size_hint_y=1) 
        self.kagit.add_widget(itici_bosluk)

        # 6. İMZA BÖLÜMÜ
        imza_dis_kutu = BoxLayout(size_hint_y=None, height=100, padding=[0, 20, 0, 0])
        imza_icerik = BoxLayout(orientation='vertical', size_hint_x=None, width=300)
        self.yetkili_ad = Label(text="Hulya Sonmez", color=(0,0,0,1), bold=True, font_size='13sp', halign='right', text_size=(300, None))
        self.yetkili_unvan = Label(text="Sirket Yetkilisi", color=(0,0,0,1), font_size='11sp', halign='right', text_size=(300, None))
        self.yetkili_tel = Label(text="0533 165 29 92", color=(0,0,0,1), font_size='11sp', halign='right', text_size=(300, None))
        imza_icerik.add_widget(self.yetkili_ad); imza_icerik.add_widget(self.yetkili_unvan); imza_icerik.add_widget(self.yetkili_tel)
        imza_dis_kutu.add_widget(Label(size_hint_x=0.95)); imza_dis_kutu.add_widget(imza_icerik)
        self.kagit.add_widget(imza_dis_kutu)

        self.kagit_dis_kutu.add_widget(self.kagit); self.add_widget(self.kagit_dis_kutu)

        # --- YENİ İŞLEM PANELİ (KAĞIT DIŞINDA) ---
        alt_kontrol_paneli = BoxLayout(orientation='vertical', size_hint_y=None, height=180, spacing=5, padding=10)

        # EKLE - SİL BUTONLARI (KAYDET'in yarısı kadar ebatta)
        islem_bar = BoxLayout(size_hint_y=None, height=80, spacing=10)
        btn_ekle = Button(text="[+] EKLE", background_color=(0.1, 0.6, 0.3, 1), bold=True)
        btn_ekle.bind(on_release=lambda x: self.satir_ekle())
        btn_sil = Button(text="[-] SİL", background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_sil.bind(on_release=lambda x: self.satir_sil())
        islem_bar.add_widget(btn_ekle); islem_bar.add_widget(btn_sil)
        
        # ANA AKSİYON BUTONLARI
        ana_butonlar = BoxLayout(size_hint_y=None, height=80, spacing=10)
        self.kaydet_btn = Button(text="KAYDET", background_color=(0.1, 0.4, 0.7, 1), bold=True)
        self.kaydet_btn.bind(on_release=self.teklifi_kaydet)
        self.kapat_butonu = Button(text="KAPAT", background_color=(0.7, 0.2, 0.2, 1), bold=True)
        self.kapat_butonu.bind(on_release=self.ana_sayfaya_git)
        
        ana_butonlar.add_widget(self.kaydet_btn); ana_butonlar.add_widget(self.kapat_butonu)

        alt_kontrol_paneli.add_widget(islem_bar)
        alt_kontrol_paneli.add_widget(ana_butonlar)
        self.add_widget(alt_kontrol_paneli)
        
        # Formu Doldur veya Yeni Satır Aç
        if duzenleme_verisi:
            Clock.schedule_once(lambda dt: self.verileri_forma_yukle(duzenleme_verisi))
        else:
            self.satir_ekle()

    # --- DİĞER FONKSİYONLAR (Aynı Kaldı) ---
    def verileri_forma_yukle(self, veri):
        try:
            # Üst bilgiler (Müşteri, No vb.)
            self.firma_manuel.text = str(veri.get("musteri", ""))
            self.teklif_no.text = str(veri.get("no", ""))
            self.ilgili.text = str(veri.get("ilgili", ""))
            self.konu.text = str(veri.get("konu", ""))
            self.tarih_input.text = str(veri.get("tarih", ""))

            self.urun_alani.clear_widgets()
            self.urun_satirlari_listesi = []
            
            for kalem in veri.get("kalemler", []):
                self.satir_ekle()
                satir = self.urun_satirlari_listesi[-1]
                
                # 1. Önce açıklama ve miktarı giriyoruz
                satir.widgets['aciklama'].text = str(kalem.get('u', ''))
                satir.widgets['miktar'].text = str(kalem.get('m', ''))
                satir.widgets['birim'].text = str(kalem.get('b', 'Ad'))
                
                # 2. Döviz birimini temizleyip büyük harfe çevirerek atıyoruz
                fb_doviz = str(kalem.get('c', 'TL')).strip().upper()
                satir.widgets['curr'].text = fb_doviz
                
                # 3. Fiyatı atıyoruz (Bu 'hesapla'yı tetikler, o da yukarıdaki 'EUR'u okur)
                satir.widgets['fiyat'].text = str(kalem.get('f', ''))
                
            self.chk_kdv.active = veri.get("kdv_dahil", False)
            
            # En kritik nokta: Form dolduktan sonra toplamı EUR olarak kalması için zorla
            Clock.schedule_once(self.genel_toplam_guncelle, 0.5)
        except Exception as e:
            print(f"Yükleme hatası: {e}")

    def teklifi_kaydet(self, instance):
        # 1. Değişkeni en başta boş tanımlayalım ki "not defined" demesin
        teklif_verisi = {}
        
        # 2. Temel Bilgiler Kontrolü
        firma_adi = self.tr_karakter_duzelt(self.firma_manuel.text.strip().upper())
        teklif_no = self.teklif_no.text.strip()
        konu_metni = self.konu.text.strip()

        if not firma_adi or not teklif_no or not konu_metni:
            self.uyari_mesaji("Eksik Bilgi", "Lütfen Firma Adı, Teklif No ve Konu alanlarını doldurun.")
            return

        # 3. Satır Kontrolü ve Veri Toplama
        gecerli_kalemler = []
        for i, s in enumerate(self.urun_satirlari_listesi, 1):
            u = s.widgets['aciklama'].text.strip()
            m = s.widgets['miktar'].text.strip()
            f = s.widgets['fiyat'].text.strip()

            # SIKINTILI DURUM: Satırın herhangi bir yeri doluysa veya ilave satır açılmışsa hepsi tam olmalı
            if not u or not m or not f:
                self.uyari_mesaji("Boş/Eksik Satır", f"{i}. satır tam dolu değil!\nLütfen doldurun veya [-] SİL ile satırı kaldırın.")
                return # Eksik varsa aşağıya inmeden fonksiyonu bitirir

            gecerli_kalemler.append({
                "u": self.tr_karakter_duzelt(u), 
                "m": m,
                "b": s.widgets['birim'].text, 
                "f": f, 
                "c": s.widgets['curr'].text,
                "t": s.widgets['toplam'].text
            })

        if not gecerli_kalemler:
            self.uyari_mesaji("Hata", "Teklifte ürün bulunamadı.")
            return

        # 4. Veri Paketleme (Artık her şey tam, güvenle tanımlıyoruz)
        teklif_verisi = {
            "musteri": firma_adi, "no": teklif_no,
            "tarih": self.tarih_input.text.strip(),
            "ilgili": self.tr_karakter_duzelt(self.ilgili.text.strip()),
            "konu": self.tr_karakter_duzelt(konu_metni),
            "hitap": self.tr_karakter_duzelt(self.hitap.text.strip()),
            "giris": self.tr_karakter_duzelt(self.giris_metni.text.strip()),
            "termin_rakam": self.termin_rakam.text,
            "termin_birim": self.termin_birim.text,
            "kdv_dahil": self.chk_kdv.active,
            "kalemler": gecerli_kalemler,
            "toplam": self.genel_toplam_label.text,
            "durum": "BEKLIYOR"
        }

        # 5. Firebase Gönderimi
        fb_url = f"{FIREBASE_URL}/{self.isletme}/teklifler/{firma_adi}/{teklif_no}.json"
        try:
            res = requests.put(fb_url, json=teklif_verisi, timeout=5)
            if res.status_code == 200:
                self.uyari_mesaji("Başarılı", "Teklif buluta kaydedildi.", kapaninca_kapat=True)
            else:
                self.uyari_mesaji("Hata", f"Sunucu hatası: {res.status_code}")
        except:
            self.uyari_mesaji("Hata", "Bağlantı sorunu.")

    def musterileri_buluttan_cek(self):
        musteriler = {}
        try:
            res = requests.get(f"{FIREBASE_URL}/{self.isletme}/musteriler.json", timeout=5)
            if res.status_code == 200 and res.json():
                for k, icerik in res.json().items():
                    v = icerik.get("veri", "")
                    for l in v.split("\n"):
                        if "FIRMA" in l:
                            musteriler[l.split(":", 1)[1].strip()] = v
                            break
        except: pass
        return musteriler

    def satir_ekle(self):
        # Spacing değerini başlıkla aynı tut (2)
        satir = BoxLayout(size_hint_y=None, height=40, spacing=2)
        
        # 1. Açıklama (0.40)
        aciklama = TextInput(hint_text="Urun...", size_hint_x=0.40, font_size='11sp', multiline=False)
        
        # 2. Miktar (0.13)
        miktar = TextInput(text="", size_hint_x=0.13, font_size='11sp', input_filter='float', halign='center', multiline=False)
        
        # 3. Birim (0.07)
        birim = Spinner(text="Ad", values=("Kg", "Ad", "Mt", "Pkt"), size_hint_x=0.07, font_size='11sp', option_cls=KucukSpinnerSecenegi)
        
        # 4. B. Fiyat Kutusu (0.15)
        # İçindeki Spinner'ı çok küçük tutup TextInput'a yer açıyoruz
        f_box = BoxLayout(size_hint_x=0.15, spacing=1)
        f_val = TextInput(text="", font_size='11sp', input_filter='float', size_hint_x=0.7, multiline=False)
        f_curr = Spinner(text="TL", values=["TL", "USD", "EUR"], size_hint_x=0.3, font_size='9sp', option_cls=KucukSpinnerSecenegi)
        f_box.add_widget(f_val); f_box.add_widget(f_curr)
        
        # 5. Toplam Kutusu (0.25)
        t_box = BoxLayout(size_hint_x=0.25, spacing=1)
        # Label'ı sola, dövizi sağa yaslayarak daha okunaklı yapalım
        t_val = Label(text="0.00", color=(0,0,0,1), font_size='11sp', bold=True, size_hint_x=0.7, halign='right')
        t_val.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], None))) # Sağa yaslama için şart
        t_curr = Label(text="TL", color=(0,0,0,1), font_size='9sp', size_hint_x=0.3, halign='left')
        t_curr.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], None)))
        t_box.add_widget(t_val); t_box.add_widget(t_curr)

        # HESAPLA FONKSİYONU (Değişkenler tanımlandıktan SONRA gelmeli)
        def hesapla(*args):
            try:
                m_deger = float(miktar.text) if miktar.text else 0
                f_deger = float(f_val.text) if f_val.text else 0
                t_val.text = f"{m_deger * f_deger:,.2f}"
                t_curr.text = f_curr.text 
                self.genel_toplam_guncelle()
            except Exception as e:
                print(f"Hesaplama hatası: {e}")

        # Tetikleyiciler
        miktar.bind(text=hesapla)
        f_val.bind(text=hesapla)
        f_curr.bind(text=hesapla)

        # Sözlük kaydı (Düzeltildi)
        satir.widgets = {
            'aciklama': aciklama, 'miktar': miktar, 'birim': birim, 
            'fiyat': f_val, 'curr': f_curr, 'toplam': t_val, 't_curr': t_curr
        }
        
        satir.add_widget(aciklama); satir.add_widget(miktar); satir.add_widget(birim)
        satir.add_widget(f_box); satir.add_widget(t_box)
        
        self.urun_alani.add_widget(satir)
        self.urun_satirlari_listesi.append(satir)

    def satir_sil(self):
        if len(self.urun_satirlari_listesi) > 1:
            son = self.urun_satirlari_listesi.pop(); self.urun_alani.remove_widget(son)
            self.genel_toplam_guncelle()

    def genel_toplam_guncelle(self, *args):
        toplam = 0.0
        p_birimi = "TL"
        if self.urun_satirlari_listesi:
            # İlk satırdaki birimi baz al (EUR ise EUR olur)
            p_birimi = self.urun_satirlari_listesi[0].widgets['curr'].text
            
        for s in self.urun_satirlari_listesi:
            try:
                # Virgülleri temizleyip sayıya çevir
                t_str = s.widgets['toplam'].text.replace(',', '')
                toplam += float(t_str)
                # Satırın kendi para birimi etiketini de (t_curr) spinner ile eşitle
                s.widgets['t_curr'].text = s.widgets['curr'].text
            except: pass
            
        self.genel_toplam_label.text = f"GENEL TOPLAM: {toplam:,.2f} {p_birimi}"

    def tr_karakter_duzelt(self, metin):
        if not metin: return ""
        sz = {"İ": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g", "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c"}
        for k, h in sz.items(): metin = metin.replace(k, h)
        return metin

    def uyari_mesaji(self, baslik, mesaj, kapaninca_kapat=False):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        lbl = Label(text=mesaj, halign='center', valign='middle')
        lbl.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        
        btn = Button(text="TAMAM", size_hint=(1, 0.3), background_color=(0.1, 0.4, 0.7, 1))
        layout.add_widget(lbl)
        layout.add_widget(btn)
        
        popup = Popup(title=baslik, content=layout, size_hint=(0.8, 0.4))
        
        # Kilitlenmeyi önleyen yeni mantık:
        if kapaninca_kapat:
            # Önce bu popup'ı kapat, 0.1 saniye sonra ana formu kapat
            btn.bind(on_release=lambda x: [popup.dismiss(), Clock.schedule_once(self.ana_sayfaya_git, 0.1)])
        else:
            btn.bind(on_release=popup.dismiss)
            
        popup.open()

    def ana_sayfaya_git(self, dt=None):
        # Kendi üzerinde bulunduğu en dış pencereyi (ModalView veya Popup) bul ve kapat
        p = self.parent
        while p:
            # Hem Popup hem ModalView kontrolü yapıyoruz
            if hasattr(p, 'dismiss'):
                p.dismiss()
                break
            p = p.parent
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos; self.rect.size = instance.size

    def firma_filtrele(self, instance, value):
        f = [f for f in self.firma_isimleri if value.lower() in f.lower()]
        self.firma_spinner.values = f if f else ["Sonuç Bulunamadı"]

    def spinner_secildi(self, instance, value):
        if value not in ["Seçiniz", "Sonuç Bulunamadı"]:
            self.firma_manuel.text = value
            
            # 1. Sabit Bilgileri Hazırla
            on_ek = "OND" if "ONDULA" in self.isletme.upper() else "AMD"
            yil_ay = datetime.now().strftime("%y%m") # 2602 gibi
            firma_yolu = self.tr_karakter_duzelt(value.strip().upper())
            fb_url = f"{FIREBASE_URL}/{self.isletme}/teklifler/{firma_yolu}.json"
            
            def numara_hesapla():
                try:
                    res = requests.get(fb_url, timeout=5).json()
                    mevcut_nolar = []
                    if res:
                        baslangic = f"{on_ek}{yil_ay}"
                        for no in res.keys():
                            if no.startswith(baslangic):
                                try:
                                    sira = int(no[-2:]) 
                                    mevcut_nolar.append(sira)
                                except: continue
                    
                    yeni_sira = max(mevcut_nolar) + 1 if mevcut_nolar else 1
                    yeni_no = f"{on_ek}{yil_ay}{yeni_sira:02d}"
                    
                    # --- KRİTİK NOKTA: Arayüzü güncellemek için ana thread'e geri dönüyoruz ---
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.arayuzu_guncelle(yeni_no))
                
                except:
                    # Hata durumunda da ana thread'e dön
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.arayuzu_guncelle(f"{on_ek}{yil_ay}01"))

            # Thread'i başlat
            import threading
            threading.Thread(target=numara_hesapla, daemon=True).start()

    def arayuzu_guncelle(self, yeni_no):
        """Bu fonksiyon sadece ana thread üzerinde çalışır ve hatayı önler"""
        self.teklif_no.text = yeni_no



def ekrani_olustur(secili_isletme=None):
    if secili_isletme: os.environ["SECILI_ISLETME"] = secili_isletme
    return TeklifModulu()