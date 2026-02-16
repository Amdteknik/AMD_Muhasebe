import os
import webbrowser
import requests
from urllib.parse import quote
from fpdf import FPDF
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.metrics import dp 

# --- FIREBASE AYARLARI ---

# --- YARDIMCI FONKSİYONLAR ---
def temiz_sayi(metin):
    if not metin: return 0.0
    try:
        ham = str(metin).replace("TL", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
        return float(ham)
    except: return 0.0

def format_tr(sayi):
    try:
        s = "{:,.2f}".format(float(sayi))
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".") + " TL"
    except: return "0,00 TL"

def format_tr_pdf(sayi):
    try:
        s = "{:,.2f}".format(float(sayi))
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    except: return "0,00"

class vereceklarPopup(Popup):
    def __init__(self, **kwargs):
        self.secili_fatura_verisi = None  # Programın çökmesini engelleyen kritik satır
        super().__init__(**kwargs)

        self.secili_fatura_verisi = None 
        self.tahmini_toplam_genel = 0.0
        self.checkbox_referanslari = {}

        base = os.environ.get("FIREBASE_URL", "").rstrip('/')
        isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.dinamik_url = f"{base}/{isletme}/alis_faturalari"

        # __init__ içinde
        self.lbl_tahmini_verecek = Label(
            text="TAHMİNİ VERİLECEK: 0,00 TL", 
            bold=True, 
            halign='left', 
            color=(0, 1, 0.8, 1), 
            font_size='14sp'
        )

        self.title = "GELİR FATURA PANELİ - MİZAN VE TAHSİLAT RAPORU"
        self.size_hint = (0.98, 0.95)
        self.tahmini_toplam_genel = 0.0
        self.tedarikci_verileri = {}
        self.checkbox_referanslari = {} 
        
        ana_icerik = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # --- ÜST ÖZET PANELİ ---
        # --- ÜST ÖZET VE AKSİYON PANELİ ---
        ust_panel = BoxLayout(size_hint_y=None, height=120, spacing=10)

        # Sol Taraf: Özet Bilgiler
        bilgi_kutusu = BoxLayout(orientation='vertical', spacing=5, size_hint_x=0.6)
        
        self.lbl_toplam_verecek = Label(text="TOPLAM verecek: 0,00 TL", bold=True, halign='left', valign='middle', font_size='14sp')
        self.lbl_toplam_verecek.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
        
        self.lbl_tahmini_verecek = Label(text="TAHMİNİ VERİLECEK: 0,00 TL", bold=True, halign='left', valign='middle', color=(0, 1, 0.8, 1), font_size='14sp')
        self.lbl_tahmini_verecek.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
        
        bilgi_kutusu.add_widget(self.lbl_toplam_verecek)
        bilgi_kutusu.add_widget(self.lbl_tahmini_verecek)

        # Sağ Taraf: Dinamik "SEÇİLENİ GÖR" Butonu
        # Bu buton başlangıçta pasif (disabled) olacak, bir fatura seçilince aktifleşecek.
        self.btn_secileni_gor = Button(
            text="SEÇİLENİ GÖR", 
            size_hint_x=0.3, 
            background_color=(0.1, 0.4, 0.6, 1),
            bold=True,
            disabled=True 
        )
        self.btn_secileni_gor.bind(on_release=lambda x: self.pdf_olustur_detay(self.secili_fatura_verisi))

        ust_panel.add_widget(bilgi_kutusu)
        ust_panel.add_widget(self.btn_secileni_gor)
        ana_icerik.add_widget(ust_panel)

            
                # --- LİSTE ALANI ---
        self.scroll = ScrollView(bar_width=10, scroll_type=['bars', 'content'])
        self.liste_izgara = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.liste_izgara.bind(minimum_height=self.liste_izgara.setter('height'))
        self.scroll.add_widget(self.liste_izgara)
        ana_icerik.add_widget(self.scroll)

        # --- ALT AKSİYON BUTONLARI ---
        alt_butonlar = BoxLayout(size_hint_y=None, height=100, spacing=50)
        btn_pdf = Button(text="PDF AKTAR", background_color=(0.2, 0.5, 0.8, 1), on_release=lambda x: self.toplu_pdf_olustur())
        btn_yazdir = Button(text="YAZDIR", background_color=(0.1, 0.7, 0.3, 1), on_release=lambda x: self.yazdir_pdf())
        btn_mail = Button(text="E-POSTA", background_color=(0.8, 0.5, 0.2, 1), on_release=lambda x: self.outlook_mail_hazirla())
        btn_kapat = Button(text="KAPAT", background_color=(0.4, 0.4, 0.4, 1), on_release=self.dismiss)
        
        for b in [btn_pdf, btn_yazdir, btn_mail, btn_kapat]:
            alt_butonlar.add_widget(b)
        ana_icerik.add_widget(alt_butonlar)
        
        self.content = ana_icerik
        self.verileri_yukle()

    def no_tarih_hucre_olustur(self, no, tarih, w):
        # Tek bir Label kullanıyoruz, aradaki boşluğu line_height ile yönetiyoruz
        # line_height: 1.0 normaldir, 0.8 daraltır, 1.2 arttırır.
        lbl = Label(
            text=f"[b][color=ffb300]{no}[/color][/b]\n[size=9sp][color=b3b3b3]{tarih}[/color][/size]",
            markup=True,
            font_size='11sp',
            halign='left',
            valign='middle',
            size_hint_x=None,
            width=dp(100),
            line_height=1  # <--- İşte aradığın parametre bu!
        )
        lbl.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        return lbl

    def verileri_yukle(self):
        from kivy.metrics import dp
        self.liste_izgara.clear_widgets()
        self.liste_izgara.spacing = dp(12) 
        self.checkbox_referanslari = {}
        
        try:
            response = requests.get(f"{self.dinamik_url}.json")
            data = response.json()
            if not data: return

            genel_toplam = 0.0
            for firma_adi, faturalar in data.items():
                if not isinstance(faturalar, dict): continue
                
                bekleyenler = []
                for f_key, f_val in faturalar.items():
                    if f_val.get("DURUM") == "Bekliyor":
                        f_val["FB_KEY"] = f_key
                        f_val["FIRMA_ADI"] = firma_adi
                        bekleyenler.append(f_val)
                
                if not bekleyenler: continue

                # --- FIRMA ADI (Sarı) ---
                self.liste_izgara.add_widget(Label(text=" ", size_hint_y=None, height=dp(10)))
                m_lbl = Label(text=f" {firma_adi.upper()}", size_hint_y=None, height=dp(35), 
                              bold=True, color=(1, 0.9, 0.3, 1), halign='left', valign='middle')
                m_lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
                self.liste_izgara.add_widget(m_lbl)

                # --- SÜTUN BAŞLIKLARI (Turkuaz) ---
                baslik_satiri = BoxLayout(size_hint_y=None, height=dp(25), padding=[dp(10), 0], spacing=dp(10))
                # Başlık genişliklerini aşağıdaki veri satırıyla birebir aynı yaptık
                basliklar = [
                    ("SEÇ", None, dp(40)), 
                    ("NO / TARİH", None, dp(100)), 
                    ("AÇIKLAMA", 0.6, None), 
                    ("TUTAR", 0.4, None)
                ]
                for metin, oran, sabit_w in basliklar:
                    b_lbl = Label(text=metin, font_size='9sp', color=(0, 0.7, 0.8, 1), bold=True, halign='left', valign='middle')
                    if sabit_w:
                        b_lbl.size_hint_x = None
                        b_lbl.width = sabit_w
                    else:
                        b_lbl.size_hint_x = oran
                    
                    b_lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
                    if metin == "TUTAR": b_lbl.halign = 'right'
                    baslik_satiri.add_widget(b_lbl)
                self.liste_izgara.add_widget(baslik_satiri)                
                # --- FATURALAR (Hizalanmış Satırlar) ---
                m_ara_toplam = 0.0
                for f in bekleyenler:
                    t_sayi = temiz_sayi(f.get("TOPLAM", "0"))
                    m_ara_toplam += t_sayi
                    genel_toplam += t_sayi
                    
                    urunler = f.get("URUNLER", [])
                    if isinstance(urunler, dict): urunler = list(urunler.values())
                    aciklama = urunler[0].get("urun", "-")[:35] if urunler else "-"
                    
                    # Satır yüksekliği dikey ferahlık sağlar
                    satir = BoxLayout(size_hint_y=None, height=dp(45), padding=[dp(10), 0], spacing=dp(10))
                    
                    cb = CheckBox(size_hint_x=None, width=dp(40)) 
                    cb.tutar = t_sayi 
                    cb.fatura_verisi = f 
                    cb.bind(active=self.tahmin_hesapla)
                    satir.add_widget(cb)                    
                    
                    self.checkbox_referanslari[f"{f['FIRMA_ADI']}_{f['NO']}"] = cb
                    
                    # 2. NO / TARİH
                    satir.add_widget(self.no_tarih_hucre_olustur(f.get("NO", "-"), f.get("TARİH", "-"), 0.15))

                    # 3. AÇIKLAMA (Lacivert/Beyaz metni tam ortada)
                    lbl_ac = Label(text=str(aciklama), size_hint_x=0.50, halign='left', 
                                   valign='middle', font_size='11sp')
                    lbl_ac.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
                    satir.add_widget(lbl_ac)
                    
                    # 4. TUTAR
                    lbl_tu = Label(text=format_tr(t_sayi), size_hint_x=0.25, halign='right', 
                                   valign='middle', bold=True, font_size='11sp')
                    lbl_tu.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
                    satir.add_widget(lbl_tu)
                    
                    self.liste_izgara.add_widget(satir)

                # ARA TOPLAM
                m_top_lbl = Label(text=f"ARA TOPLAM: {format_tr(m_ara_toplam)}", size_hint_y=None, 
                                  height=dp(35), italic=True, color=(0.4, 0.8, 1, 1), halign='left', valign='middle')             
                m_top_lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
                self.liste_izgara.add_widget(m_top_lbl)
            
            self.lbl_toplam_verecek.text = f"TOPLAM VERİLECEK: {format_tr(genel_toplam)}"
        except Exception as e:
            print(f"Hata: {e}")


    def fatura_secim_kontrol(self, checkbox, value):
        # 1. Tahmini Toplamı Güncelle
        if value:
            self.tahmini_toplam_genel += checkbox.tutar
        else:
            self.tahmini_toplam_genel -= checkbox.tutar
        
        # Etiketi güncelle (max(0,...) ile eksiye düşmesini engelliyoruz)
        self.lbl_tahmini_verecek.text = f"TAHMİNİ GELECEK: {format_tr(max(0, self.tahmini_toplam_genel))}"

        # 2. "SEÇİLENİ GÖR" Buton Mantığı
        # Aktif olan tüm checkboxları bul
        secili_kutular = [cb for cb in self.checkbox_referanslari.values() if cb.active]
        
        # Sadece 1 tane seçiliyse butonu aktif et ve veriyi ata
        if len(secili_kutular) == 1:
            self.secili_fatura_verisi = secili_kutular[0].fatura_verisi
            self.btn_secileni_gor.disabled = False
            self.btn_secileni_gor.background_color = (0.1, 0.7, 0.3, 1) # Yeşil (Aktif)
        else:
            # Birden fazla veya sıfır seçim varsa "GÖR" butonu pasif olur (Kafa karışıklığını önler)
            self.secili_fatura_verisi = None
            self.btn_secileni_gor.disabled = True
            self.btn_secileni_gor.background_color = (0.1, 0.4, 0.6, 1) # Mavi-Gri (Pasif)

    def tahmin_hesapla(self, checkbox, value):
        yeni_toplam = 0.0
        secili_sayisi = 0
        son_secilen = None

        # Checkbox listesini kontrol et
        for cb in self.checkbox_referanslari.values():
            
            if cb.active:
                yeni_toplam += getattr(cb, 'tutar', 0.0)
                secili_sayisi += 1
                son_secilen = cb.fatura_verisi

        # Yazıyı Güncelle
        self.tahmini_toplam_genel = yeni_toplam
        self.lbl_tahmini_verecek.text = f"TAHMİNİ GELECEK: {format_tr(max(0, self.tahmini_toplam_genel))}"

        # Buton Mantığı (Tamir Edildi)
        if secili_sayisi == 1:
            self.secili_fatura_verisi = son_secilen
            self.btn_secileni_gor.disabled = False
            self.btn_secileni_gor.background_color = (0.1, 0.7, 0.3, 1)  # Yeşil
        else:
            self.secili_fatura_verisi = None
            self.btn_secileni_gor.disabled = True
            self.btn_secileni_gor.background_color = (0.1, 0.4, 0.6, 1)  # Pasif Mavi
# Bu fonksiyonu vereceklarPopup sınıfının içine yerleştirin
    def pdf_olustur_detay(self, f):
        # 1. Değerleri güvenli bir şekilde çek
        # Firebase'den gelen verilerde anahtar isimlerine dikkat (KDV_ORANI, ISKONTO_ORANI vb.)
        isk_orani = float(str(f.get("ISKONTO_ORANI", "0")).replace(",", "."))
        kdv_orani = float(str(f.get("KDV_ORANI", "20")).replace(",", "."))
        kdv_etkin = f.get("KDV_ETKIN", True)

        f_tarih = f.get('TARİH') or f.get('tarih') or '-'
        f_no = f.get('NO') or f.get('no') or '-'
        f_firma = f.get('FIRMA') or f.get('firma') or f.get('FIRMA_ADI') or '-'

        secili_isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        logo_dosyasi = f"{secili_isletme} LOGO.jpg"

        # --- GÖRSEL PENCERE DÜZENİ (Birebir Aynı Format) ---
        from kivy.graphics import Color, Rectangle
        from kivy.uix.image import Image
        from kivy.uix.widget import Widget

        pencere_duzeni = BoxLayout(orientation='vertical', padding=10, spacing=5)
        ana_icerik = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        with ana_icerik.canvas.before:
            Color(1, 1, 1, 1) # Beyaz kağıt efekti
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
        b_bari = BoxLayout(size_hint_y=None, height=35, spacing=1)
        basliklar = [("Ürün Açıklaması", 0.40), ("Mik.", 0.1), ("Birim", 0.1), ("B.Fiyat", 0.15), ("Birim", 0.05), ("Toplam", 0.2)]
        for t, s in basliklar:
            b_bari.add_widget(Button(text=t, size_hint_x=s, background_normal='', background_color=(0.1, 0.4, 0.6, 1), bold=True, font_size='11sp'))
        ana_icerik.add_widget(b_bari)

        scroll = ScrollView(size_hint_y=0.45)
        liste_grid = GridLayout(cols=1, size_hint_y=None, spacing=2)
        liste_grid.bind(minimum_height=liste_grid.setter('height'))
        
        urunler = f.get("URUNLER", [])
        dongu = urunler.values() if isinstance(urunler, dict) else urunler
        
        # Ürün Döngüsü
        ara_toplam_hesap = 0.0
        for u in dongu:
            if isinstance(u, dict):
                u_ad = u.get('urun') or u.get('ad') or ''
                u_miktar = u.get('miktar') or u.get('adet') or '0'
                u_birim = u.get('birim') or ''
                u_fiyat_str = str(u.get('fiyat') or '0').replace(',','.').replace("TL","").strip()
                
                try:
                    fiyat_val = float(u_fiyat_str)
                    adet_val = float(str(u_miktar).strip())
                    satir_toplam = fiyat_val * adet_val
                    ara_toplam_hesap += satir_toplam
                except:
                    fiyat_val = 0.0; satir_toplam = 0.0

                satir = BoxLayout(size_hint_y=None, height=30, spacing=1)
                satir.add_widget(Label(text=str(u_ad), size_hint_x=0.40, color=(0,0,0,1), halign='left', padding=[10,0]))
                satir.add_widget(Label(text=str(u_miktar), size_hint_x=0.1, color=(0,0,0,1)))
                satir.add_widget(Label(text=str(u_birim), size_hint_x=0.1, color=(0,0,0,1)))
                satir.add_widget(Label(text=f"{fiyat_val:,.2f}", size_hint_x=0.15, color=(0,0,0,1)))
                satir.add_widget(Label(text="TL", size_hint_x=0.05, color=(0.5,0.5,0.5,1)))
                satir.add_widget(Label(text=f"{satir_toplam:,.2f} TL", size_hint_x=0.2, color=(0,0,0,1), bold=True))
                liste_grid.add_widget(satir)
        
        scroll.add_widget(liste_grid)
        ana_icerik.add_widget(scroll)

        # Hesaplamalar
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
            sag_hesap_izgara.add_widget(Label(text=metin, color=(0,0,0,1), font_size='11sp', bold=True, halign='right'))
            sag_hesap_izgara.add_widget(Label(text=nokta, color=(0,0,0,1), size_hint_x=None, width=15))
            sag_hesap_izgara.add_widget(Label(text=deger, color=(0,0,0,1), font_size='11sp', markup=True, halign='left'))

        hesap_dis_kutu.add_widget(sag_hesap_izgara) 
        ana_icerik.add_widget(hesap_dis_kutu)
        pencere_duzeni.add_widget(ana_icerik)

        # Alt Butonlar (PDF, YAZDIR, KAPAT)
        alt_buton_bari = BoxLayout(size_hint_y=None, height=60, spacing=10, padding=[5, 10, 5, 5])
        
        btn_pdf = Button(text="PDF AKTAR", background_color=(0.1, 0.3, 0.5, 1), bold=True)
        # PDF butonuna gerçek PDF üretme fonksiyonunu bağlayabilirsin
        btn_pdf.bind(on_release=lambda x: self.tek_fatura_pdf_uret(f))
        
        btn_yazdir = Button(text="YAZDIR", background_color=(0.1, 0.5, 0.2, 1), bold=True)
        btn_kapat = Button(text="KAPAT", background_color=(0.6, 0.1, 0.1, 1), bold=True)

        alt_buton_bari.add_widget(btn_pdf)
        alt_buton_bari.add_widget(btn_yazdir)
        alt_buton_bari.add_widget(btn_kapat)
        pencere_duzeni.add_widget(alt_buton_bari)

        detay_popup = Popup(title=f"Fatura Detayı: {f_firma}", content=pencere_duzeni, size_hint=(0.98, 0.98))
        btn_kapat.bind(on_release=detay_popup.dismiss)
        detay_popup.open()

    # Arka plan güncelleme yardımcısı
    def _rect_guncelle(self, instance, value):
        self.arka_plan_dikdortgen.pos = instance.pos
        self.arka_plan_dikdortgen.size = instance.size
        
    def toplu_pdf_olustur(self):
        # Mizan Raporu kodları buraya (Yukarıdaki mantıkla benzer)
        pass

    def yazdir_pdf(self):
        # Yazdırma fonksiyonu
        pass

    def outlook_mail_hazirla(self):
        # Mail fonksiyonu
        pass

def ekrani_olustur():
    return vereceklarPopup()