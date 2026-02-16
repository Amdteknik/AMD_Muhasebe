import json
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup 
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from urllib.parse import quote 
import os
import json
from urllib.parse import quote
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.core.window import Window

from kivy.uix.floatlayout import FloatLayout

class FaturaGezgini:
    def __init__(self, screen_manager=None, **kwargs):
        self.sm = screen_manager
        self.tum_faturalar = []
        self.secili_fatura_objesi = None
        # Renk ve Font Ayarları
        self.renk_standart = (0.2, 0.4, 0.6, 1) 
        self.renk_secili = (0.05, 0.15, 0.3, 1)  
        self.font_normal = '11sp'
        self.font_buyuk = '14sp'

    def ekrani_olustur(self):
        self.ana_duzen = BoxLayout(orientation='vertical', padding=5, spacing=3)
        
# 1. ÜST BAR (GÜNCELLENDİ)
        ust_bar = BoxLayout(size_hint_y=None, height=100, spacing=10)
        self.lbl_baslik = Label(text="FATURA PANELİ", bold=True, color=(0.2, 0.7, 1, 1), size_hint_x=0.4)
        
        # Butonlar için dikey bir kutu (Üst üste binmeleri için)
        btn_vbox = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=2)
        
        self.btn_bakiye_gor = Button(text="BAKİYE GÖR", background_color=(0.1, 0.5, 0.8, 1), bold=True, font_size='11sp')
        self.btn_bakiye_gor.bind(on_release=self.bakiye_penceresini_ac)
        
        self.btn_ust_gor = Button(text="SEÇİLENİ GÖR", background_color=(0.2, 0.6, 0.4, 1), bold=True, font_size='11sp', disabled=True)
        self.btn_ust_gor.bind(on_release=self.secileni_gor_tiklandi)
        
        btn_vbox.add_widget(self.btn_bakiye_gor)
        btn_vbox.add_widget(self.btn_ust_gor)

        btn_kapat = Button(text="KAPAT", size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_kapat.bind(on_release=self.kapat_tiklandi)
        
        ust_bar.add_widget(self.lbl_baslik)
        ust_bar.add_widget(btn_vbox)
        ust_bar.add_widget(btn_kapat)
        self.ana_duzen.add_widget(ust_bar)

        # 2. FİLTRELER
        filtre_satiri = BoxLayout(size_hint_y=None, height=200, spacing=10)
        
        # Müşteriler Sütunu (Aynı kalıyor)
        m_vbox = BoxLayout(orientation='vertical', size_hint_x=0.33, spacing=2)
        self.btn_m_yukle = Button(text="MÜŞTERİLER", background_color=self.renk_standart, background_normal='', bold=False, font_size=self.font_normal)
        self.btn_m_yukle.bind(on_release=lambda x: self.verileri_yukle("satis_faturalari"))
        self.spin_m_liste = Spinner(text="Müşteri Seç", values=[], font_size='10sp', background_color=self.renk_standart, background_normal='')
        self.spin_m_liste.bind(text=self.filtrele)
        m_vbox.add_widget(self.btn_m_yukle); m_vbox.add_widget(self.spin_m_liste)
        
        # Tedarikçiler Sütunu (Aynı kalıyor)
        t_vbox = BoxLayout(orientation='vertical', size_hint_x=0.33, spacing=2)
        self.btn_t_yukle = Button(text="TEDARİKÇİLER", background_color=self.renk_standart, background_normal='', bold=False, font_size=self.font_normal)
        self.btn_t_yukle.bind(on_release=lambda x: self.verileri_yukle("alis_faturalari"))
        self.spin_t_liste = Spinner(text="Tedarikçi Seç", values=[], font_size='10sp', background_color=self.renk_standart, background_normal='')
        self.spin_t_liste.bind(text=self.filtrele)
        t_vbox.add_widget(self.btn_t_yukle); t_vbox.add_widget(self.spin_t_liste)

        # --- Arama, Tarih ve Durum Sütunu (BURASI DEĞİŞTİ) ---
        a_vbox = BoxLayout(orientation='vertical', size_hint_x=0.34, spacing=2)
        self.txt_u_ara = TextInput(hint_text="No/İçerik Ara...", multiline=False, font_size='11sp')
        self.txt_u_ara.bind(text=self.filtrele)
        
        # YENİ EKLENEN TARİH DROPBOX
        self.spin_tarih_filtre = Spinner(
            text="Son 1 Ay", 
            values=["Son 1 Ay", "Son 3 Ay", "Son 6 Ay", "Son 1 Yıl", "Hepsi"], 
            font_size='10sp'
        )
        self.spin_tarih_filtre.bind(text=lambda spinner, text: self.verileri_yukle(getattr(self, 'su_anki_klasor', 'alis_faturalari')))
        
        self.spin_durum_filtre = Spinner(text="Hepsi", values=["Hepsi", "Ödenmemiş", "Ödenmiş"], font_size='10sp')
        self.spin_durum_filtre.bind(text=self.filtrele)
        
        # Sıralama: Arama Üstte, Tarih Ortada, Durum Altta
        a_vbox.add_widget(self.txt_u_ara)
        a_vbox.add_widget(self.spin_tarih_filtre) 
        a_vbox.add_widget(self.spin_durum_filtre)
        
        filtre_satiri.add_widget(m_vbox); filtre_satiri.add_widget(t_vbox); filtre_satiri.add_widget(a_vbox)
        self.ana_duzen.add_widget(filtre_satiri)

        # 3. TABLO BAŞLIKLARI (Açıklama Geri Geldi - cols=7)
        baslik_izgara = GridLayout(cols=7, size_hint_y=None, height=60, spacing=2) 
        sutunlar = [
            ("Seç", 0.04), ("Fatura No", 0.12), ("Tarih", 0.10), 
            ("İsim", 0.22), ("Açıklama", 0.20), ("Tutar", 0.15), ("Durum", 0.15)
        ]
        for b, o in sutunlar:
            baslik_izgara.add_widget(Label(text=b, size_hint_x=o, font_size='9sp', color=(0.6,0.6,0.6,1)))
        self.ana_duzen.add_widget(baslik_izgara)

        # 4. LİSTE ALANI (Aynı kalıyor)
        self.izgara_l = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.izgara_l.bind(minimum_height=self.izgara_l.setter('height'))
        scroll_l = ScrollView(size_hint_y=0.45); scroll_l.add_widget(self.izgara_l)
        self.ana_duzen.add_widget(scroll_l)

        # 5. ALT DETAY
        self.detay_kutu = BoxLayout(orientation='vertical', size_hint_y=0.35, padding=2)
        self.izgara_d = GridLayout(cols=1, size_hint_y=None, spacing=1)
        self.izgara_d.bind(minimum_height=self.izgara_d.setter('height'))
        scroll_d = ScrollView(); scroll_d.add_widget(self.izgara_d)
        self.lbl_t = Label(text="SEÇİLEN TOPLAM: 0,00 TL", size_hint_y=None, height=50, bold=True, font_size='16sp', color=(0, 1, 0, 1))
        self.detay_kutu.add_widget(scroll_d); self.detay_kutu.add_widget(self.lbl_t)
        self.ana_duzen.add_widget(self.detay_kutu)

        Clock.schedule_once(lambda dt: self.verileri_yukle("alis_faturalari"), 0.5)
        return self.ana_duzen




    def verileri_yukle(self, klasor, *args):
        self.su_anki_klasor = klasor
        secilen_aralik = self.spin_tarih_filtre.text # Dropbox'tan seçilen değer
        simdi = datetime.now()

        def tarih_uygun_mu(f_tarihi_str):
            if secilen_aralik == "Hepsi": return True
            try:
                # Fatura tarihlerini (03.02.2026 gibi) karşılaştırılabilir hale getiriyoruz
                f_tarihi = datetime.strptime(f_tarihi_str.strip(), "%d.%m.%Y")
                gun_farki = (simdi - f_tarihi).days
                
                araliklar = {"Son 1 Ay": 30, "Son 3 Ay": 90, "Son 6 Ay": 180, "Son 1 Yıl": 365}
                return gun_farki <= araliklar.get(secilen_aralik, 9999)
            except:
                return True # Tarih okunamıyorsa faturayı her ihtimale karşı göster

        is_alis = "alis" in klasor
        # Görsel Güncelleme: Seçilen büyür ve bold olur
        if is_alis:
            self.btn_t_yukle.background_color = self.renk_secili
            self.btn_t_yukle.bold = True
            self.btn_t_yukle.font_size = self.font_buyuk
            self.btn_m_yukle.background_color = self.renk_standart
            self.btn_m_yukle.bold = False
            self.btn_m_yukle.font_size = self.font_normal
        else:
            self.btn_m_yukle.background_color = self.renk_secili
            self.btn_m_yukle.bold = True
            self.btn_m_yukle.font_size = self.font_buyuk
            self.btn_t_yukle.background_color = self.renk_standart
            self.btn_t_yukle.bold = False
            self.btn_t_yukle.font_size = self.font_normal

        # MainLauncher'dan gelen değerleri çekiyoruz
        base_url = os.environ.get("FIREBASE_URL", "").rstrip('/')
        secili_isletme = os.environ.get("SECILI_ISLETME", "AMD") # Varsayılan AMD
        
        # Dinamik URL oluşturma
        url = f"{base_url}/{secili_isletme}/{klasor}.json"

        def basarili(req, sonuc):
            self.tum_faturalar = []
            firmalar = set()
            if sonuc and isinstance(sonuc, dict):
                for f_k, f_g in sonuc.items():
                    isim = f_k.replace("_", ".").title()
                    firmalar.add(isim)
                    liste = f_g.values() if isinstance(f_g, dict) else f_g
                    for f in liste:
                        if isinstance(f, dict):
                            f_yeni = f.copy(); f_yeni["FIRMA"] = isim
                            f_yeni["FIRMA_HAM"] = f_k  # Veritabanındaki gerçek, büyük harfli, dokunulmamış isim
                            f_yeni["KLASOR"] = klasor
                            self.tum_faturalar.append(f_yeni)
            
            if is_alis:
                self.spin_t_liste.values = ["Tümü"] + sorted(list(firmalar))
                self.spin_t_liste.text = "Tümü"; self.spin_m_liste.text = "Müşteri Seç"
            else:
                self.spin_m_liste.values = ["Tümü"] + sorted(list(firmalar))
                self.spin_m_liste.text = "Tümü"; self.spin_t_liste.text = "Tedarikçi Seç"
            self.filtrele()
        UrlRequest(url, on_success=basarili)



    def durum_guncelle(self, yeni_durum, pop=None):
        
        if not self.secili_fatura_objesi: return
        f = self.secili_fatura_objesi
        
        # URL içindeki boşluk ve Türkçe karakterleri temizlemek/kodlamak için quote kullanıyoruz
        f_no = quote(str(f.get("NO", "")))
        f_firma = quote(str(f.get("FIRMA", "")))
        klasor = f.get("KLASOR")
        
        # Yeni format: DURUM: Bekliyor / DURUM: Ödenmiş
        veri_sozluk = {"DURUM": yeni_durum} 
        veri = json.dumps(veri_sozluk)
        
        if not self.secili_fatura_objesi: return
    
        base_url = os.environ.get("FIREBASE_URL", "").rstrip('/')
        secili_isletme = os.environ.get("SECILI_ISLETME", "AMD")
        
        f_no = quote(str(self.secili_fatura_objesi.get("NO", "")))
        f_firma = quote(str(self.secili_fatura_objesi.get("FIRMA", "")))
        klasor = self.secili_fatura_objesi.get("KLASOR")
        
        # Dinamik yol oluşturma
        url = f"{base_url}/{secili_isletme}/{klasor}/{f_firma}/{f_no}.json"
        
        def basarili(req, sonuc):
        # BURAYI DEĞİŞTİR: f"DURUM: {yeni_durum}" yerine sadece yeni_durum
            f["DURUM"] = yeni_durum 
            if pop: pop.dismiss()
            self.filtrele()
            print(f"Güncellendi: {yeni_durum}")

        UrlRequest(url, req_body=veri, method='PATCH', on_success=basarili)

    def filtrele(self, *args):
        self.izgara_l.clear_widgets()
        f_m, f_t = self.spin_m_liste.text, self.spin_t_liste.text
        f_d, f_ara = self.spin_durum_filtre.text, self.txt_u_ara.text.lower().strip()
        
        for f in self.tum_faturalar:
            # Önce faturanın açıklamasını temizle (yeni arama için taze sayfa)
            f["ACIKLAMA"] = "" 
            
            f_isim = f.get("FIRMA", "").title()
            if f_m != "Tümü" and f_m != "Müşteri Seç" and f_m != f_isim: continue
            if f_t != "Tümü" and f_t != "Tedarikçi Seç" and f_t != f_isim: continue
            
            durum = f.get("DURUM", "Bekliyor")
            if f_d == "Ödenmemiş" and "Bekliyor" not in durum: continue
            if f_d == "Ödenmiş" and "Ödenmiş" not in durum: continue

            # Ürünlerin içinde arama yapalım (İçerik Ara)
            urun_bulundu = False
            urunler = f.get("URUNLER", {})
            dongu = urunler.values() if isinstance(urunler, dict) else urunler
            for u in dongu:
                if isinstance(u, dict):
                    ad = (str(u.get('urun','')) + str(u.get('ad','')) + str(u.get('AD',''))).lower()
                    if f_ara and f_ara in ad:
                        urun_bulundu = True; break

            no_eslesme = f_ara in str(f.get("NO","")).lower()
            
            if f_ara:
                if no_eslesme or urun_bulundu:
                    # EŞLEŞME VARSA: Aranan kelimeyi açıklamaya basıyoruz
                    f["ACIKLAMA"] = f_ara.upper()
                else:
                    # Eşleşme yoksa bu faturayı gösterme
                    continue

            self.satir_ekle(f)

    def satir_ekle(self, v):
        s = GridLayout(cols=7, size_hint_y=None, height=80, spacing=2)
        cb = CheckBox(size_hint_x=0.04); cb.fatura_verisi = v; cb.bind(active=self.toplam_guncelle)
        s.add_widget(cb)
        s.add_widget(Label(text=str(v.get("NO", "")), size_hint_x=0.12, font_size='9sp'))
        s.add_widget(Label(text=v.get("TARİH",""), size_hint_x=0.10, font_size='9sp'))
        s.add_widget(Label(text=v.get("FIRMA", "")[:12], size_hint_x=0.22, font_size='10sp'))
        s.add_widget(Label(text=v.get("ACIKLAMA", "")[:15], size_hint_x=0.20, font_size='9sp'))
        s.add_widget(Label(text=str(v.get("TOPLAM","0")), size_hint_x=0.17, bold=True, font_size='10sp'))
        d = v.get("DURUM", "Bekliyor").replace("DURUM: ", "").strip() # Güvenlik için temizliyoruz
        s.add_widget(Label(text=d, size_hint_x=0.15, font_size='9sp', color=(0,1,0,1) 
        if d=="Ödenmiş" else (1,0.2,0.2,1)))        
        self.izgara_l.add_widget(s)

    def toplam_guncelle(self, checkbox, value):
        secili = [c.fatura_verisi for satir in self.izgara_l.children for c in satir.children if isinstance(c, CheckBox) and c.active]
        t_toplam = 0.0
        for s in secili:
            try: t_toplam += float(str(s.get("TOPLAM", "0")).replace("TL","").replace(".","").replace(",",".").strip())
            except: pass
        self.lbl_t.text = f"SEÇİLEN TOPLAM: {t_toplam:,.2f} TL"
        self.btn_ust_gor.disabled = (len(secili) != 1)
        if len(secili) == 1:
            self.secili_fatura_objesi = secili[0]
            self.detayi_goster(secili[0])
        else: self.izgara_d.clear_widgets()

    def detayi_goster(self, f):
        self.izgara_d.clear_widgets()
        self.izgara_d.cols = 1
        
        kdv_etkin = f.get("KDV_ETKIN", True)
        fatura_kdv_orani = f.get("KDV_ORANI", "20") if kdv_etkin else "0"
        
        # BAŞLIKLAR (Hizalama için alttaki verilerle aynı oranlara sahip olmalı)
        h_satir = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=1)
        # Sütun oranları: Ürün(0.40) + Mik(0.1) + Birim(0.1) + Fiyat(0.15) + KDV(0.1) + Toplam(0.15) = 1.0
        sutun_plan = [
            ("ÜRÜN ADI", 0.40), ("MİK.", 0.1), ("BİRİM", 0.1), 
            ("B.FİYAT", 0.15), ("KDV", 0.1), ("TOPLAM", 0.15)
        ]
        
        for m, g in sutun_plan:
            h_satir.add_widget(Button(text=m, bold=True, font_size='9sp', size_hint_x=g, 
                                     background_color=(0.1, 0.4, 0.6, 1), background_normal=''))
        self.izgara_d.add_widget(h_satir)
        
        urunler = f.get("URUNLER", {})
        dongu = urunler.values() if isinstance(urunler, dict) else urunler
        
        for u in dongu:
            if isinstance(u, dict):
                un = {str(k).lower(): v for k, v in u.items()}
                u_ad = un.get('urun') or un.get('ad') or ''
                u_miktar = un.get('miktar') or un.get('adet') or '0'
                u_birim = un.get('birim') or ''
                u_fiyat = un.get('fiyat') or '0'
                u_toplam = un.get('toplam') or '0'

                r = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=1)
                
                # 1. Ürün Adı (Sola yaslı ve paddingli)
                u_adi_label = Label(text=str(u_ad), size_hint_x=0.40, font_size='10sp', 
                                    halign='left', valign='middle')
                u_adi_label.bind(size=lambda ins, val: setattr(ins, 'text_size', (ins.width, None)))
                u_adi_label.padding = [15, 0]
                
                # 2. Miktar
                u_mik_label = Label(text=str(u_miktar), size_hint_x=0.1, font_size='10sp')
                
                # 3. Birim
                u_birim_label = Label(text=str(u_birim), size_hint_x=0.1, font_size='10sp')
                
                # 4. Birim Fiyat (Yanına TL ekleyerek tek kolonda çözüyoruz)
                fiyat_metni = f"{str(u_fiyat)} TL"
                u_fiyat_label = Label(text=fiyat_metni, size_hint_x=0.15, font_size='10sp')
                
                # 5. KDV
                u_kdv_label = Label(text=f"%{fatura_kdv_orani}", size_hint_x=0.1, font_size='10sp')
                
                # 6. Toplam (TL simgesi metnin içinde, ayrı kolonda değil)
                # Firebase'den gelen u_toplam içinde zaten TL varsa tekrar eklemiyoruz
                toplam_deger = str(u_toplam) if "TL" in str(u_toplam) else f"{u_toplam} TL"
                u_toplam_label = Label(text=toplam_deger, size_hint_x=0.15, font_size='10sp', bold=True)

                # Sırasıyla ekle
                r.add_widget(u_adi_label)
                r.add_widget(u_mik_label)
                r.add_widget(u_birim_label)
                r.add_widget(u_fiyat_label)
                r.add_widget(u_kdv_label)
                r.add_widget(u_toplam_label)
                
                self.izgara_d.add_widget(r)

    def _rect_guncelle(self, instance, value):
        """Arka planın pencereyle birlikte büyümesini sağlar"""
        self.arka_plan_dikdortgen.pos = instance.pos
        self.arka_plan_dikdortgen.size = instance.size

    def secileni_gor_tiklandi(self, instance):
        if not self.secili_fatura_objesi: return
        f = self.secili_fatura_objesi 
        
        # 1. Veritabanından değerleri güvenli bir şekilde çek
        isk_orani = float(str(f.get("ISKONTO_ORANI", "0")).replace(",", "."))
        kdv_orani = float(str(f.get("KDV_ORANI", "20")).replace(",", "."))
        kdv_etkin = f.get("KDV_ETKIN", True)

        f_tarih = f.get('TARİH') or f.get('tarih') or '-'
        f_no = f.get('NO') or f.get('no') or '-'
        f_firma = f.get('FIRMA') or f.get('firma') or '-'
        f_durum = f.get('DURUM') or f.get('durum') or ''

        secili_isletme = os.environ.get("SECILI_ISLETME", "AMD")
        logo_dosyasi = f"{secili_isletme} LOGO.jpg"

        pencere_duzeni = BoxLayout(orientation='vertical', padding=10, spacing=5)
        ana_icerik = BoxLayout(orientation='vertical', padding=20, spacing=10)
        with ana_icerik.canvas.before:
            Color(1, 1, 1, 1) 
            self.arka_plan_dikdortgen = Rectangle(size=ana_icerik.size, pos=ana_icerik.pos)
        ana_icerik.bind(size=self._rect_guncelle, pos=self._rect_guncelle)

        # Üst Bilgi (Logo ve No/Tarih)
        ust_bilgi = BoxLayout(size_hint_y=None, height=100)
        if os.path.exists(logo_dosyasi):
            ust_bilgi.add_widget(Image(source=logo_dosyasi, size_hint_x=0.3, allow_stretch=True))
        else:
            ust_bilgi.add_widget(Label(text=f"[b]{secili_isletme}[/b]", markup=True, color=(0,0,0,1), size_hint_x=0.3))

        sag_ust = BoxLayout(orientation='vertical', size_hint_x=0.7)
        sag_ust.add_widget(Label(text=f"[color=000000][b]FATURA NO:[/b] {f_no}[/color]", markup=True, halign='right'))
        sag_ust.add_widget(Label(text=f"[color=000000][b]TARİH:[/b] {f_tarih}[/color]", markup=True, halign='right'))
        ust_bilgi.add_widget(sag_ust)
        ana_icerik.add_widget(ust_bilgi)

        # Başlık Çubuğu
        b_bari = BoxLayout(size_hint_y=None, height=80, spacing=1)
        basliklar = [("Ürün Açıklaması", 0.40), ("Mik.", 0.1), ("Birim", 0.1), ("B.Fiyat", 0.15), ("Birim", 0.05), ("Toplam", 0.2)]
        for t, s in basliklar:
            b_bari.add_widget(Button(text=t, size_hint_x=s, background_normal='', background_color=(0.1, 0.4, 0.6, 1), bold=True, font_size='11sp'))
        ana_icerik.add_widget(b_bari)

        scroll = ScrollView(size_hint_y=0.45)
        liste_grid = GridLayout(cols=1, size_hint_y=None, spacing=2)
        liste_grid.bind(minimum_height=liste_grid.setter('height'))
        
        urunler = f.get("URUNLER", {})
        dongu = urunler.values() if isinstance(urunler, dict) else urunler
        
        # 2. ÜRÜN DÖNGÜSÜ (SADECE ÜRÜNLERİ LİSTELER)
        ara_toplam_hesap = 0.0
        for u in dongu:
            if isinstance(u, dict):
                u_ad = u.get('urun') or u.get('AD') or u.get('ad') or ''
                u_miktar = u.get('miktar') or u.get('ADET') or u.get('adet') or '0'
                u_birim = u.get('birim') or u.get('BIRIM') or ''
                u_fiyat_str = str(u.get('fiyat') or u.get('FIYAT') or '0').replace(',','.').replace("TL","").strip()
                
                try:
                    fiyat_val = float(u_fiyat_str)
                    adet_val = float(str(u_miktar).strip())
                    satir_toplam = fiyat_val * adet_val
                    ara_toplam_hesap += satir_toplam
                except:
                    fiyat_val = 0.0; satir_toplam = 0.0

                satir = BoxLayout(size_hint_y=None, height=80, spacing=1)
                satir.add_widget(Label(text=str(u_ad), size_hint_x=0.40, color=(0,0,0,1), halign='center', text_size=(300, None)))
                satir.add_widget(Label(text=str(u_miktar), size_hint_x=0.1, color=(0,0,0,1)))
                satir.add_widget(Label(text=str(u_birim), size_hint_x=0.1, color=(0,0,0,1)))
                satir.add_widget(Label(text=f"{fiyat_val:,.2f}", size_hint_x=0.15, color=(0,0,0,1)))
                satir.add_widget(Label(text="TL", size_hint_x=0.05, color=(0.5,0.5,0.5,1)))
                satir.add_widget(Label(text=f"{satir_toplam:,.2f} TL", size_hint_x=0.2, color=(0,0,0,1), bold=True))
                liste_grid.add_widget(satir)
        
        scroll.add_widget(liste_grid)
        ana_icerik.add_widget(scroll)

        # 3. HESAPLAMA (Döngü bittikten sonra 1 kez yapılır)
        iskonto_tutari = ara_toplam_hesap * (isk_orani / 100)
        ara_toplam_iskontolu = ara_toplam_hesap - iskonto_tutari
        kdv_tutari = (ara_toplam_iskontolu * (kdv_orani / 100)) if kdv_etkin else 0.0
        genel_toplam_son = ara_toplam_iskontolu + kdv_tutari

        hesap_dis_kutu = BoxLayout(size_hint_y=None, height=120)
        hesap_dis_kutu.add_widget(Widget(size_hint_x=0.45)) 
        sag_hesap_izgara = GridLayout(cols=3, size_hint_x=0.55, spacing=2)
        
        hesap_verileri = [
            ("ARA TOPLAM", ":", f"{ara_toplam_hesap:,.2f} TL"),
            (f"İSKONTO (%{isk_orani})", ":", f"{iskonto_tutari:,.2f} TL"),
            (f"KDV (%{kdv_orani if kdv_etkin else 0})", ":", f"{kdv_tutari:,.2f} TL"),
            ("GENEL TOPLAM", ":", f"[b]{genel_toplam_son:,.2f} TL[/b]")
        ]

        for metin, nokta, deger in hesap_verileri:
            sag_hesap_izgara.add_widget(Label(text=metin, color=(0,0,0,1), font_size='11sp', bold=True))
            sag_hesap_izgara.add_widget(Label(text=nokta, color=(0,0,0,1), size_hint_x=None, width=15))
            sag_hesap_izgara.add_widget(Label(text=deger, color=(0,0,0,1), font_size='11sp', markup=True))

        hesap_dis_kutu.add_widget(sag_hesap_izgara) 
        ana_icerik.add_widget(hesap_dis_kutu)
        pencere_duzeni.add_widget(ana_icerik)

        # Butonlar
        alt_buton_bari = BoxLayout(size_hint_y=None, height=80, spacing=10, padding=[5, 10, 5, 5])
        durum_mevcut = str(f_durum).replace("DURUM: ", "")
        hedef_d = "Ödenmiş" if "Bekliyor" in durum_mevcut else "Bekliyor"

        btn_odeme = Button(text=f"{hedef_d.upper()} YAP", background_color=(0.1, 0.5, 0.2, 1), bold=True)
        btn_odeme.bind(on_release=lambda x: self.durum_guncelle(hedef_d, self.detay_popup))
        btn_pdf = Button(text="PDF", background_color=(0.1, 0.3, 0.5, 1), bold=True)
        btn_sil = Button(text="SİL", background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_kapat = Button(text="KAPAT", background_color=(0.6, 0.1, 0.1, 1), bold=True)

        btn_sil.bind(on_release=lambda x: self.sil_onay_popup(f))
        alt_buton_bari.add_widget(btn_odeme); alt_buton_bari.add_widget(btn_pdf); alt_buton_bari.add_widget(btn_sil); alt_buton_bari.add_widget(btn_kapat)
        pencere_duzeni.add_widget(alt_buton_bari)

        self.detay_popup = Popup(title=f"Fatura Detayı: {f_firma}", content=pencere_duzeni, size_hint=(0.98, 0.98))
        btn_kapat.bind(on_release=self.detay_popup.dismiss)
        self.detay_popup.open()
        
    def sil_onay_popup(self, fatura_objesi):
        duzen = BoxLayout(orientation='vertical', padding=15, spacing=10)
        duzen.add_widget(Label(text="Bu faturayı silmek istediğinize emin misiniz?", halign='center'))
        
        butonlar = BoxLayout(size_hint_y=None, height=80, spacing=10)
        btn_evet = Button(text="EVET, SİL", background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_hayir = Button(text="HAYIR, VAZGEÇ", background_color=(0.2, 0.6, 0.2, 1), bold=True)
        
        butonlar.add_widget(btn_evet)
        butonlar.add_widget(btn_hayir)
        duzen.add_widget(butonlar)
        
        self.onay_p = Popup(title="Silme Onayı", content=duzen, size_hint=(0.7, 0.3))
        
        # HAYIR butonu zaten sadece kapatıyor
        btn_hayir.bind(on_release=self.onay_p.dismiss)
        
        # EVET butonu için garantili kapatma
        def evet_basildi(instance):
            # Kivy'nin tüm açık popup'larını o saniye kapatmaya zorla
            for child in Window.children:
                if isinstance(child, Popup) and child.title == "Silme Onayı":
                    child.dismiss()
            self.faturayı_veritabanından_sil(fatura_objesi)
            
        btn_evet.bind(on_release=evet_basildi)
        
        self.onay_p.open()

    def faturayı_veritabanından_sil(self, fatura):
        try:
            base_url = os.environ.get("FIREBASE_URL", "").rstrip('/')
            secili_isletme = os.environ.get("SECILI_ISLETME", "AMD")
            f_no = str(fatura.get('NO', '')).strip()
            f_firma_asli = fatura.get('FIRMA_HAM', '') 
            klasor = fatura.get("KLASOR", "alis_faturalari") 

            url = f"{base_url}/{secili_isletme}/{klasor}/{quote(f_firma_asli)}/{quote(f_no)}.json"

            def silme_basarili(req, sonuc):
                # Silme bittiğinde ana listeyi tazeleriz
                # Böylece kullanıcı modül ekranını kapattığında ana listede faturayı görmez
                self.verileri_yukle(klasor)
                print("Firebase'den silindi, liste güncellendi.")

            UrlRequest(url, method='DELETE', on_success=silme_basarili)

        except Exception as e:
            print(f"Hata: {e}")

    def pencereleri_kapat_ve_tazele(self, klasor):
        # 1. Onay Popup'ını kapat
        if hasattr(self, 'onay_p') and self.onay_p:
            self.onay_p.dismiss()
            self.onay_p = None # Referansı temizle
        
        # 2. Detay Popup'ını kapat
        if hasattr(self, 'detay_popup') and self.detay_popup:
            self.detay_popup.dismiss()
            self.detay_popup = None
            
        # 3. Listeyi tazele
        self.verileri_yukle(klasor)
        
        # 4. Seçili faturayı temizle
        self.secili_fatura_objesi = None
        self.btn_ust_gor.disabled = True

    def bakiye_penceresini_ac(self, instance):
        # Spinner'dan seçilen firma
        secili_firma = self.spin_m_liste.text if self.spin_m_liste.text not in ["Tümü", "Müşteri Seç"] else self.spin_t_liste.text
        if secili_firma in ["Tümü", "Müşteri Seç", "Tedarikçi Seç"]: return

        base_url = os.environ.get("FIREBASE_URL", "").rstrip('/')
        secili_isletme = os.environ.get("SECILI_ISLETME", "AMD")
        
        # Karşılaştırma için seçili ismi normalize et (Boşluksuz ve Büyük)
        norm_secili = secili_firma.replace(" ", "").upper()

        # Firebase'den tüm hareketler klasörünü çekiyoruz ki isim farklarını kod içinde ayıklayalım
        url_tum_hareketler = f"{base_url}/{secili_isletme}/hareketler.json"

        def verileri_isleyerek_ac(req, tum_hareketler_sonuc):
            tum_islemler = []
            
            # 1. FATURALARI EKLE (Kendi listemizden)
            for f in self.tum_faturalar:
                f_adi_norm = str(f.get("FIRMA", "")).replace(" ", "").upper()
                if f_adi_norm == norm_secili:
                    try:
                        t_ham = str(f.get("TOPLAM", "0")).replace("TL","").replace(".","").replace(",",".").strip()
                        tum_islemler.append({
                            "tarih": f.get("TARİH") or "01.01.2026",
                            "f_tutar": -abs(float(t_ham)),
                            "o_tutar": 0.0
                        })
                    except: pass

            # 2. HAREKETLERİ EKLE (Veritabanından)
            # Burada 'MercanKağıt' ve 'MERCAN KAĞIT' gibi farklı klasörleri tarıyoruz
            if tum_hareketler_sonuc and isinstance(tum_hareketler_sonuc, dict):
                for klasor_adi, hareket_listesi in tum_hareketler_sonuc.items():
                    # Klasör adını normalize et ve seçili firmayla eşleşiyor mu bak
                    if klasor_adi.replace(" ", "").upper() == norm_secili:
                        if isinstance(hareket_listesi, dict):
                            for h_id, h_v in hareket_listesi.items():
                                try:
                                    # Sayı veya metin fark etmeksizin tutarı al
                                    raw_tutar = h_v.get("tutar", 0)
                                    # Eğer negatif geliyorsa (görseldeki gibi -250000), bunu ödeme (+) olarak kabul et
                                    val = abs(float(str(raw_tutar).replace(",", ".")))
                                    
                                    h_tarih = str(h_v.get("tarih", "01.01.2026")).split(" ")[0]
                                    tum_islemler.append({
                                        "tarih": h_tarih,
                                        "f_tutar": 0.0,
                                        "o_tutar": val
                                    })
                                except: pass

            # Tarihe göre diz
            try:
                tum_islemler.sort(key=lambda x: datetime.strptime(x['tarih'], "%d.%m.%Y"))
            except: pass

            # --- ARAYÜZ ---
            ana_duzen = BoxLayout(orientation='vertical', padding=[15, 10, 15, 15], spacing=10)
            
            def tl_format(rakam):
                if rakam == 0: return "-"
                return f"{abs(rakam):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"

            # Başlıklar
            h_grid = GridLayout(cols=4, size_hint_y=None, height=60)
            for b_metin, b_hiza in [("TARİH", 'left'), ("FATURA (-)", 'right'), ("İŞLEM (+)", 'right'), ("BAKİYE", 'right')]:
                lbl_h = Label(text=b_metin, halign=b_hiza, valign='middle', bold=True, color=(0.2, 0.7, 1, 1))
                lbl_h.bind(size=lambda s, v: setattr(s, 'text_size', (s.width, s.height)))
                if b_hiza == 'right': lbl_h.padding_x = 10
                h_grid.add_widget(lbl_h)
            ana_duzen.add_widget(h_grid)

            # Liste
            scroll = ScrollView(size_hint=(1, 0.7))
            liste_izgara = GridLayout(cols=4, size_hint_y=None, spacing=5)
            liste_izgara.bind(minimum_height=liste_izgara.setter('height'))

            kumulatif = 0.0
            for islem in tum_islemler:
                kumulatif += (islem['f_tutar'] + islem['o_tutar'])
                
                for txt, color, hiza in [
                    (islem['tarih'], (1,1,1,1), 'left'),
                    (tl_format(islem['f_tutar']), (1, .4, .4, 1), 'right'),
                    (tl_format(islem['o_tutar']), (.4, 1, .4, 1), 'right'),
                    (tl_format(kumulatif), ((.4, 1, .4, 1) if kumulatif >= -0.01 else (1, .4, .4, 1)), 'right')
                ]:
                    l = Label(text=txt, color=color, font_size='11sp', size_hint_y=None, height=45, halign=hiza, valign='middle')
                    l.bind(size=lambda s, v: setattr(s, 'text_size', (s.width, s.height)))
                    if hiza == 'right': l.padding_x = 10
                    liste_izgara.add_widget(l)

            scroll.add_widget(liste_izgara)
            ana_duzen.add_widget(scroll)

            # --- ALT ALAN (Görselde istediğiniz gibi sağ alt köşe butonlu) ---
            alt_alan = FloatLayout(size_hint_y=None, height=120)
            
            son_renk = (0, 1, 0, 1) if kumulatif >= -0.01 else (1, 0, 0, 1)
            b_label = Label(
                text=f"GÜNCEL BAKİYE: {tl_format(kumulatif)}", 
                bold=True, color=son_renk, font_size='18sp',
                size_hint=(1, None), height=50,
                pos_hint={'right': 1, 'top': 1}, halign='right', padding_x=20
            )
            b_label.bind(size=lambda s, v: setattr(s, 'text_size', (s.width, s.height)))
            alt_alan.add_widget(b_label)

            btn_kapat_b = Button(
                text="KAPAT", 
                size_hint=(0.3, 0.45),
                pos_hint={'right': 1, 'y': 0},
                background_color=(0.6, 0.1, 0.1, 1),
                bold=True
            )
            alt_alan.add_widget(btn_kapat_b)
            
            ana_duzen.add_widget(alt_alan)
            
            pop = Popup(title=f"Hesap Ekstresi: {secili_firma}", content=ana_duzen, size_hint=(0.95, 0.9))
            btn_kapat_b.bind(on_release=pop.dismiss)
            pop.open()

        # Kritik Değişiklik: Tek bir firma yerine tüm hareketleri çekiyoruz ki normalize edip birleştirebilelim
        UrlRequest(url_tum_hareketler, on_success=verileri_isleyerek_ac)


    def kapat_tiklandi(self, instance):
        if self.sm: self.sm.current = "ana_menu"
        else:
            p = instance.parent
            while p:
                if isinstance(p, Popup): p.dismiss(); break
                p = p.parent

def ekrani_olustur():
    """Ana uygulamanın (main.py) modülü tanıması için gereken aracı fonksiyon"""
    gezgin = FaturaGezgini()
    return gezgin.ekrani_olustur()

    