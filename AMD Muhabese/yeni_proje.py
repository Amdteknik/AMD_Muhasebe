from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
import requests, os
from datetime import datetime
import threading

class YeniProje:
    def __init__(self):
        # Ortam değişkenlerinden URL ve İşletme bilgisini alıyoruz
        self.url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.isletme = os.environ.get("SECILI_ISLETME", "AMD")
        self.musteri_verileri = {}
        self.duzenlenen_id = None
        self.mevcut_durum = "BEKLEMEDE" # Kayıt anındaki varsayılan durum

    def ekrani_olustur(self, p_nesnesi=None, duzenleme_verisi=None, p_id=None):
        self.duzenlenen_id = p_id
        ana_duzen = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # --- 1. SATIR: BAŞLIK VE SAĞ ÜST SERİ NO ---
        ust_seri_panel = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        ust_seri_panel.add_widget(Label(text="PROJE DETAY FORMU", bold=True, font_size='15sp', size_hint_x=0.6, halign='left'))
        
        seri_no_box = BoxLayout(orientation='vertical', size_hint_x=0.4)
        seri_no_box.add_widget(Label(text="PROJE SERİ NO", font_size='9sp', color=(1, 0.8, 0, 1)))
        self.txt_proje_seri = TextInput(text="Yükleniyor...", readonly=True, halign='center', 
                                        background_color=(0.1, 0.1, 0.1, 1), foreground_color=(1, 1, 0, 1), 
                                        font_size='13sp', multiline=False)
        seri_no_box.add_widget(self.txt_proje_seri)
        ust_seri_panel.add_widget(seri_no_box)
        ana_duzen.add_widget(ust_seri_panel)

        # --- 2. SATIR: MÜŞTERİ VE YETKİLİ ---
        musteri_panel = GridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(100))
        
        # Müşteri Seçimi (Filtreleme + Spinner)
        sol = BoxLayout(orientation='vertical', spacing=dp(2))
        sol.add_widget(Label(text="MÜŞTERİ SEÇİMİ", font_size='11sp', color=(.7,.7,.7,1), bold=True))
        self.txt_mus = TextInput(hint_text="Filtrele...", multiline=False, size_hint_y=None, height=dp(35))
        self.sp_mus = Spinner(text="Rehber", values=[], size_hint_y=None, height=dp(35))
        self.txt_mus.bind(text=self.firma_filtrele)
        self.sp_mus.bind(text=lambda s, v: setattr(self.txt_mus, 'text', v) if v not in ["Rehber", "Yok"] else None)
        sol.add_widget(self.txt_mus); sol.add_widget(self.sp_mus)
        
        # Firma Yetkilisi
        sag = BoxLayout(orientation='vertical', spacing=dp(2))
        sag.add_widget(Label(text="FİRMA YETKİLİSİ", font_size='11sp', color=(.7,.7,.7,1), bold=True))
        self.txt_yetkili = TextInput(hint_text="Ad Soyad...", size_hint_y=None, height=dp(35), multiline=False)
        sag.add_widget(self.txt_yetkili)
        sag.add_widget(Label(text="Proje muhatabı", font_size='9sp', color=(.5,.5,.5,1)))
        
        musteri_panel.add_widget(sol); musteri_panel.add_widget(sag)
        ana_duzen.add_widget(musteri_panel)

        # --- 3. SATIR: MAKİNE BİLGİLERİ ---
        makine_panel = GridLayout(cols=2, spacing=dp(15), size_hint_y=None, height=dp(60))
        self.txt_mak = TextInput(hint_text="Makine Adı...", size_hint_y=None, height=dp(38))
        self.txt_ser = TextInput(hint_text="Seri No...", size_hint_y=None, height=dp(38))
        makine_panel.add_widget(self.txt_mak); makine_panel.add_widget(self.txt_ser)
        ana_duzen.add_widget(makine_panel)

        # --- 4 & 5: PROJE BAŞLIĞI VE TEKNİK DETAYLAR ---
        ana_duzen.add_widget(Label(text="PROJE BAŞLIĞI", font_size='11sp', size_hint_y=None, height=dp(15)))
        self.txt_proje = TextInput(size_hint_y=None, height=dp(38), multiline=False)
        ana_duzen.add_widget(self.txt_proje)
        
        ana_duzen.add_widget(Label(text="MANUEL PROJE GİRDİSİ (TEKNİK DETAYLAR)", font_size='11sp', size_hint_y=None, height=dp(15)))
        self.txt_detay = TextInput(size_hint_y=1, multiline=True)
        ana_duzen.add_widget(self.txt_detay)

        # --- 6. SATIR: TAHMİNİ PROJE BEDELİ (YENİLENMİŞ VE GENİŞ) ---
        alt_bilgi_paneli = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        lbl_bedel = Label(text="Tahmini Proje Bedeli:", size_hint_x=0.4, halign='right', valign='middle', font_size='13sp')
        lbl_bedel.bind(size=lbl_bedel.setter('text_size'))
        
        self.txt_bedel = TextInput(hint_text="0.00", multiline=False, size_hint_x=0.4, halign='right', 
                                   font_size='16sp', input_filter='float', 
                                   background_color=(0.15, 0.15, 0.15, 1), foreground_color=(0, 1, 0, 1))
        
        self.sp_doviz = Spinner(text="TL", values=("TL", "USD", "EUR"), size_hint_x=0.2)
        
        alt_bilgi_paneli.add_widget(lbl_bedel)
        alt_bilgi_paneli.add_widget(self.txt_bedel)
        alt_bilgi_paneli.add_widget(self.sp_doviz)
        ana_duzen.add_widget(alt_bilgi_paneli)

        # --- 7. SATIR: BUTONLAR ---
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        btn_pdf = Button(text="PDF", background_color=(0.3, 0.2, 0.1, 1), size_hint_x=0.15)
        btn_yazdir = Button(text="YAZDIR", background_color=(0.1, 0.2, 0.3, 1), size_hint_x=0.15)
        btn_kaydet = Button(text="KAYDET", background_color=(0.1, 0.4, 0.1, 1), bold=True, size_hint_x=0.45)
        btn_kapat = Button(text="KAPAT", background_color=(0.4, 0.1, 0.1, 1), size_hint_x=0.25)
        
        btn_kaydet.bind(on_release=self.kaydet)
        btn_kapat.bind(on_release=self.kapat_mantigi)
        
        btn_layout.add_widget(btn_pdf); btn_layout.add_widget(btn_yazdir)
        btn_layout.add_widget(btn_kaydet); btn_layout.add_widget(btn_kapat)
        ana_duzen.add_widget(btn_layout)

        # --- VERİ DOLDURMA (PROJE DÜZENLE'DEN GELİYORSA) ---
        if duzenleme_verisi:
            self.txt_proje_seri.text = str(duzenleme_verisi.get("proje_seri_no", ""))
            self.txt_mus.text = str(duzenleme_verisi.get("musteri", ""))
            self.txt_yetkili.text = str(duzenleme_verisi.get("firma_yetkilisi", ""))
            self.txt_mak.text = str(duzenleme_verisi.get("makine_adi", ""))
            self.txt_ser.text = str(duzenleme_verisi.get("seri_no", ""))
            self.txt_proje.text = str(duzenleme_verisi.get("proje_adi", ""))
            self.txt_detay.text = str(duzenleme_verisi.get("aciklama", ""))
            self.txt_bedel.text = str(duzenleme_verisi.get("bedel", "0"))
            self.sp_doviz.text = str(duzenleme_verisi.get("doviz", "TL"))
            self.mevcut_durum = duzenleme_verisi.get("durum", "BEKLEMEDE")
            btn_kaydet.text = "GÜNCELLE"
        else:
            Clock.schedule_once(self.yeni_seri_no_uret, 0.5)

        Clock.schedule_once(self.rehber_yukle, 0.2)
        return ana_duzen

    def kapat_mantigi(self, instance):
        # Daha güvenli bir kapatma yöntemi
        p = instance.parent
        while p:
            if isinstance(p, Popup):
                p.dismiss()
                break # Return yerine break daha temiz
            p = p.parent

    def yeni_seri_no_uret(self, *args):
        # Arayüzün donmaması için Thread içine alıyoruz
        def işlem():
            tarih_str = datetime.now().strftime("%y%m%d")
            prefix = f"OND_{tarih_str}_"
            try:
                # URL sonuna .json eklemeyi unutma
                r = requests.get(f"{self.url}/{self.isletme}/projeler.json", timeout=5).json()
                max_sira = 0
                if r and isinstance(r, dict):
                    for m_k, p_v in r.items():
                        if isinstance(p_v, dict):
                            for p_id, veri in p_v.items():
                                no = veri.get("proje_seri_no", "")
                                if no.startswith(prefix):
                                    try:
                                        sira = int(no.split("_")[-1])
                                        if sira > max_sira: max_sira = sira
                                    except: continue
                
                final_no = f"{prefix}{str(max_sira + 1).zfill(2)}"
                # Kivy arayüzünü güncellerken Clock kullanmalısın
                Clock.schedule_once(lambda dt: self.set_seri_no(final_no))
            except Exception as e:
                print(f"Seri no hatası: {e}")
                Clock.schedule_once(lambda dt: self.set_seri_no(f"{prefix}01"))

        threading.Thread(target=işlem, daemon=True).start()

    def yeni_seri_no_uret(self, musteri_adi):
        def işlem():
            try:
                temiz_m = musteri_adi.replace(".", "_").upper()
                # ÖNEMLİ: Artık direkt müşterinin kendi klasörüne bakıyoruz
                url = f"{self.url}/projeler/{self.isletme}/{temiz_m}.json"
                r = requests.get(url, timeout=5).json()
                
                # Örn: OND2602
                prefix = f"{self.isletme}{datetime.now().strftime('%y%m')}"
                max_sira = 0
                if r and isinstance(r, dict):
                    # Klasör içindeki anahtarları (Proje No) kontrol et
                    nolar = [int(k[len(prefix):]) for k in r.keys() if k.startswith(prefix) and k[len(prefix):].isdigit()]
                    if nolar: max_sira = max(nolar)
                
                final_no = f"{prefix}{str(max_sira + 1).zfill(2)}"
                Clock.schedule_once(lambda dt: self.set_seri_no(final_no))
            except:
                prefix = f"{self.isletme}{datetime.now().strftime('%y%m')}"
                Clock.schedule_once(lambda dt: self.set_seri_no(f"{prefix}01"))

        threading.Thread(target=işlem, daemon=True).start()

    def firma_filtrele(self, instance, value):
        """Müşteri TextInput'una yazıldığında Spinner'ı (Rehber) filtreler"""
        if not value:
            # Eğer kutu boşsa tüm listeyi göster
            self.sp_mus.values = sorted(list(self.musteri_verileri.keys()))
        else:
            # Yazılan metne göre isimleri filtrele (büyük harf uyumuyla)
            filtreli_liste = [k for k in self.musteri_verileri.keys() if value.upper() in k.upper()]
            if filtreli_liste:
                self.sp_mus.values = filtreli_liste
            else:
                self.sp_mus.values = ["Yok"]

    def set_seri_no(self, metin):
        """Thread içinden gelen seri numarasını TextInput'a yazar"""
        self.txt_proje_seri.text = metin

    def rehber_yukle(self, *args):
            def işlem():
                try:
                    # Rehber hala işletme bazlı (AMD/musteriler veya OND/musteriler gibi)
                    r = requests.get(f"{self.url}/{self.isletme}/musteriler.json", timeout=5).json()
                    if r:
                        temp_rehber = {}
                        for k, v in r.items():
                            metin = v.get("veri", "")
                            for s in metin.split("\n"):
                                # Faturadaki FIRMA: kısmını ayıklar
                                if "FIRMA" in s and ":" in s:
                                    isim = s.split(":", 1)[1].strip().upper()
                                    temp_rehber[isim] = metin
                        
                        # Arayüzü güncellemek için ana thread'e bağlan
                        Clock.schedule_once(lambda dt: self.rehber_arayuz_guncelle(temp_rehber))
                except Exception as e:
                    print(f"Rehber yükleme hatası: {e}")

            threading.Thread(target=işlem, daemon=True).start()

    def rehber_arayuz_guncelle(self, veri):
        self.musteri_verileri = veri
        self.sp_mus.values = sorted(list(self.musteri_verileri.keys()))

    def kaydet(self, instance):
        musteri = self.txt_mus.text.strip().upper()
        # Firebase için yasaklı karakterleri temizle
        temiz_m = musteri.replace(".", "_").replace("$", "_").replace("#", "_").replace("[", "_").replace("]", "_")
        proje_no = self.txt_proje_seri.text
        
        if not temiz_m or "Müşteri" in proje_no: 
            return # Müşteri seçilmeden kayda izin verme

        veri = {
            "proje_seri_no": proje_no,
            "firma_yetkilisi": self.txt_yetkili.text,
            "proje_adi": self.txt_proje.text, 
            "musteri": musteri,
            "makine_adi": self.txt_mak.text, 
            "seri_no": self.txt_ser.text,
            "aciklama": self.txt_detay.text, 
            "bedel": self.txt_bedel.text,
            "doviz": self.sp_doviz.text, 
            "durum": self.mevcut_durum,
            "tarih": datetime.now().strftime("%d.%m.%Y")
        }

        def kayit_islem():
            try:
                # PUT kullanarak Proje No'yu klasör ismi (key) yapıyoruz
                # Yapı: projeler / AMD / MERCAN_KAGIT / OND260201.json
                yol = f"{self.url}/projeler/{self.isletme}/{temiz_m}/{proje_no}.json"
                
                # requests.put veriyi direkt belirttiğimiz dosya ismiyle kaydeder
                response = requests.put(yol, json=veri, timeout=5)
                
                if response.status_code == 200:
                    Clock.schedule_once(lambda dt: self.kapat_mantigi(instance))
            except Exception as e:
                print(f"Kayıt Hatası: {e}")

        threading.Thread(target=kayit_islem, daemon=True).start()


def ekrani_olustur(p_nesnesi=None, duzenleme_verisi=None, p_id=None):
    """Main.py'nin aradığı giriş kapısı"""
    return YeniProje().ekrani_olustur(p_nesnesi, duzenleme_verisi, p_id)