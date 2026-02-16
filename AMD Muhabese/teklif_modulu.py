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
from datetime import datetime
import os

# FPDF kütüphanesi kontrolü
try:
    from fpdf import FPDF
except ImportError:
    print("Hata: fpdf2 kütüphanesi bulunamadı. Lütfen 'pip install fpdf2' yazın.")

class TeklifModulu(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        
        # Veri Yükleme
        self.musteri_verileri = self.musterileri_ayristir()
        self.firma_isimleri = sorted(list(self.musteri_verileri.keys())) if self.musteri_verileri else []

        # Kağıt Görünümü
        self.kagit_dis_kutu = ScrollView(do_scroll_x=False)
        self.kagit = BoxLayout(orientation='vertical', size_hint=(1, None), padding=[25, 20, 25, 20], spacing=8)
        self.kagit.bind(minimum_height=self.kagit.setter('height'))
        
        with self.kagit.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.kagit.size, pos=self.kagit.pos)
        self.kagit.bind(size=self._update_rect, pos=self._update_rect)

        # 1. LOGO
        logo_box = BoxLayout(size_hint_y=None, height=100)
        try:
            img = Image(source='LOGO.jpg', size_hint_x=None, width=180)
            img.fit_mode = "contain"
            logo_box.add_widget(img)
        except:
            logo_box.add_widget(Label(text="AMD LOGO", color=(0,0,0,1), size_hint_x=None, width=180))
        logo_box.add_widget(Label()) 
        self.kagit.add_widget(logo_box)

        # 2. ÜST BİLGİLER (GÜNCELLENDİ: Çift Taraflı Senkronizasyon)
        ust_tablo = GridLayout(cols=4, size_hint_y=None, height=130, spacing=10)
        
        def create_label(txt):
            return Label(
                text=txt, color=(0,0,0,1), bold=True, size_hint_x=0.15, 
                font_size='12sp', halign='left', valign='middle'
            )

        ust_tablo.add_widget(create_label("Müşteri Ara/Seç: "))
        
        firma_box = BoxLayout(size_hint_x=0.35, spacing=5)
        self.firma_manuel = TextInput(hint_text="SEÇ", multiline=False, font_size='11sp', size_hint_x=0.4)
        self.firma_spinner = Spinner(text="Seçiniz", values=self.firma_isimleri, font_size='11sp', size_hint_x=0.6)
        
        # Olay Bağlantıları (Event Binding)
        self.firma_manuel.bind(text=self.firma_filtrele) # Yazarken listeyi daralt
        self.firma_spinner.bind(text=self.spinner_secildi) # Listeden seçince kutuyu doldur
        
        firma_box.add_widget(self.firma_manuel)
        firma_box.add_widget(self.firma_spinner)
        ust_tablo.add_widget(firma_box)
        
        ust_tablo.add_widget(create_label("Tarih: "))
        self.tarih_input = TextInput(text=datetime.now().strftime("%d.%m.%Y"), multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.tarih_input)

        ust_tablo.add_widget(create_label("Ilgili: "))
        self.ilgili = TextInput(multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.ilgili)
        
        ust_tablo.add_widget(create_label("Teklif No: "))
        self.teklif_no = TextInput(multiline=False, size_hint_x=0.35, font_size='12sp')
        ust_tablo.add_widget(self.teklif_no)

        ust_tablo.add_widget(create_label("Konu: "))
        self.konu = TextInput(multiline=False, size_hint_x=1, font_size='12sp')
        ust_tablo.add_widget(self.konu)
        ust_tablo.add_widget(Label(size_hint_x=0.001)); ust_tablo.add_widget(Label(size_hint_x=0.001))
        self.kagit.add_widget(ust_tablo)

        # 3. HİTAP VE GİRİŞ
        self.hitap = TextInput(hint_text="Sayin ...", multiline=False, size_hint_y=None, height=35, font_size='12sp')
        self.giris_metni = TextInput(hint_text="Teklif giris metni...", size_hint_y=None, height=80, font_size='12sp', multiline=True)
        self.kagit.add_widget(self.hitap)
        self.kagit.add_widget(self.giris_metni)

        # 4. ÜRÜN TABLOSU
        baslik_box = BoxLayout(size_hint_y=None, height=30, spacing=2)
        self.cols_config = [("Aciklama", 0.57), ("Miktar", 0.08), ("Birim", 0.05), ("B. Fiyat", 0.15), ("Toplam", 0.15)]
        for text, hint in self.cols_config:
            baslik_box.add_widget(Button(text=text, background_normal='', background_color=(0.85,0.85,0.85,1), color=(0,0,0,1), font_size='11sp', bold=True, size_hint_x=hint))
        self.kagit.add_widget(baslik_box)

        self.urun_satirlari_listesi = []
        self.urun_alani = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.urun_alani.bind(minimum_height=self.urun_alani.setter('height'))
        self.kagit.add_widget(self.urun_alani)

        # GENEL TOPLAM
        toplam_bar = BoxLayout(size_hint_y=None, height=35, spacing=2)
        toplam_bar.add_widget(Label(size_hint_x=0.70)) 
        self.genel_toplam_label = Label(text="GENEL TOPLAM: 0.00 TL", color=(0,0,0,1), bold=True, font_size='12sp', size_hint_x=0.30, halign='right')
        toplam_bar.add_widget(self.genel_toplam_label)
        self.kagit.add_widget(toplam_bar)

        # İŞLEM BUTONLARI
        islem_bar = BoxLayout(size_hint_y=None, height=35, spacing=10)
        btn_ekle = Button(text="SATIR EKLE", size_hint_x=None, width=100, background_color=(0.1, 0.6, 0.3, 1), bold=True)
        btn_ekle.bind(on_release=lambda x: self.satir_ekle())
        btn_sil = Button(text="SATIR SIL", size_hint_x=None, width=100, background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_sil.bind(on_release=lambda x: self.satir_sil())
        islem_bar.add_widget(btn_ekle); islem_bar.add_widget(btn_sil); islem_bar.add_widget(Label()) 
        self.kagit.add_widget(islem_bar)

        # 5. ALT BİLGİLER
        self.chk_kdv = CheckBox(active=True, color=(0,0,0,1), size_hint_x=None, width=30)
        kdv_box = BoxLayout(size_hint_y=None, height=25); kdv_box.add_widget(self.chk_kdv)
        kdv_box.add_widget(Label(text="Fiyatlarimiza KDV dahil degildir.", color=(0,0,0,1), font_size='11sp', halign='left', text_size=(500,None)))
        self.kagit.add_widget(kdv_box)

        self.chk_termin = CheckBox(active=True, color=(0,0,0,1), size_hint_x=None, width=30)
        term_box = BoxLayout(size_hint_y=None, height=35, spacing=5); term_box.add_widget(self.chk_termin)
        term_box.add_widget(Label(text="Termin:", color=(0,0,0,1), size_hint_x=None, width=55, font_size='11sp'))
        self.termin_rakam = TextInput(text="5", multiline=False, size_hint_x=None, width=45, font_size='11sp')
        self.termin_birim = Spinner(text="Is Gunu", values=("Is Gunu", "Hafta", "Ay", "Yil"), size_hint_x=None, width=90, font_size='10sp')
        term_box.add_widget(self.termin_rakam); term_box.add_widget(self.termin_birim); term_box.add_widget(Label()) 
        self.kagit.add_widget(term_box)

        # 6. İMZA
        imza_dis_kutu = BoxLayout(size_hint_y=None, height=80)
        imza_icerik = BoxLayout(orientation='vertical', size_hint_x=None, width=250)
        imza_icerik.add_widget(Label(text="Hulya Sonmez", color=(0,0,0,1), bold=True, font_size='13sp', halign='right', text_size=(250,None)))
        imza_icerik.add_widget(Label(text="Sirket Yetkilisi", color=(0,0,0,1), font_size='11sp', halign='right', text_size=(250,None)))
        imza_icerik.add_widget(Label(text="05331652992", color=(0,0,0,1), font_size='11sp', halign='right', text_size=(250,None)))
        imza_dis_kutu.add_widget(Label(size_hint_x=0.95))
        imza_dis_kutu.add_widget(imza_icerik)
        self.kagit.add_widget(imza_dis_kutu)

        self.kagit_dis_kutu.add_widget(self.kagit); self.add_widget(self.kagit_dis_kutu)

        # ALT ANA BUTONLAR
        btn_grid = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        self.pdf_btn = Button(text="KAYDET/PDF OLUŞTUR/GÖR", background_color=(0.1, 0.4, 0.7, 1), bold=True)
        self.pdf_btn.bind(on_release=self.pdf_olustur)
        btn_grid.add_widget(self.pdf_btn)
        
        self.mail_btn = Button(text="MAİL GÖNDER", background_color=(0.2, 0.5, 0.5, 1), bold=True)
        btn_grid.add_widget(self.mail_btn)
        
        self.kapat_butonu = Button(text="ANA SAYFAYA DÖN", background_color=(0.7, 0.2, 0.2, 1), bold=True)
        btn_grid.add_widget(self.kapat_butonu)
        
        self.add_widget(btn_grid)
        self.satir_ekle()

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos; self.rect.size = instance.size

    def firma_filtrele(self, instance, value):
        """ TextInput'a yazarken listeyi filtreler """
        if not value:
            self.firma_spinner.values = self.firma_isimleri
        else:
            filtrelenmis = [f for f in self.firma_isimleri if value.lower() in f.lower()]
            self.firma_spinner.values = filtrelenmis
            # Eğer kutudaki yazı tam bir eşleşme değilse listeyi açıp kolaylık sağlar
            if len(filtrelenmis) > 0 and value != self.firma_spinner.text:
                self.firma_spinner.is_open = True 

    def spinner_secildi(self, instance, value):
        """ Listeden bir isim seçilince kutuyu otomatik doldurur """
        if value != "Seçiniz" and value != self.firma_manuel.text:
            self.firma_manuel.text = value

    def genel_toplam_guncelle(self, *args):
        toplam = 0.0
        para_birimi = "TL"
        for satir in self.urun_satirlari_listesi:
            try:
                val_str = satir.widgets['toplam'].text.replace(',', '')
                toplam += float(val_str)
                para_birimi = satir.widgets['curr'].text
            except: pass
        self.genel_toplam_label.text = f"GENEL TOPLAM: {toplam:,.2f} {para_birimi}"

    def satir_ekle(self):
        satir = BoxLayout(size_hint_y=None, height=35, spacing=2)
        dovizler = ["TL", "USD", "EUR"]
        aciklama = TextInput(hint_text="Urun...", size_hint_x=0.57, font_size='11sp')
        miktar = TextInput(text="", size_hint_x=0.08, font_size='11sp', input_filter='float')
        birim = Spinner(text="Adet", values=("Kg", "Adet", "Metre", "Paket"), size_hint_x=0.05, font_size='10sp')
        f_box = BoxLayout(size_hint_x=0.15, spacing=1)
        f_val = TextInput(text="", font_size='11sp', input_filter='float')
        f_curr = Spinner(text="TL", values=dovizler, font_size='9sp', size_hint_x=0.45)
        f_box.add_widget(f_val); f_box.add_widget(f_curr)
        t_box = BoxLayout(size_hint_x=0.15, spacing=1)
        t_val = Label(text="0.00", color=(0,0,0,1), font_size='11sp', bold=True)
        t_curr = Label(text="TL", color=(0,0,0,1), font_size='9sp', size_hint_x=0.45)
        t_box.add_widget(t_val); t_box.add_widget(t_curr)

        def hesapla(*args):
            try:
                m = float(miktar.text.replace(',', '.')) if miktar.text else 0
                f = float(f_val.text.replace(',', '.')) if f_val.text else 0
                t_val.text = f"{m * f:,.2f}"
                t_curr.text = f_curr.text
                self.genel_toplam_guncelle()
            except: t_val.text = "0.00"

        miktar.bind(text=hesapla); f_val.bind(text=hesapla); f_curr.bind(text=hesapla)
        satir.widgets = {'aciklama': aciklama, 'miktar': miktar, 'birim': birim, 'fiyat': f_val, 'curr': f_curr, 'toplam': t_val}
        satir.add_widget(aciklama); satir.add_widget(miktar); satir.add_widget(birim); satir.add_widget(f_box); satir.add_widget(t_box)
        self.urun_satirlari_listesi.append(satir); self.urun_alani.add_widget(satir)

    def satir_sil(self):
        if len(self.urun_satirlari_listesi) > 1:
            son = self.urun_satirlari_listesi.pop(); self.urun_alani.remove_widget(son)
            self.genel_toplam_guncelle()

    def pdf_olustur(self, instance):
        try:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists('LOGO.jpg'):
                pdf.image('LOGO.jpg', 10, 8, 45)

            def t(text):
                tr_map = str.maketrans("İıŞşĞğÜüÖöÇç", "IiSsGgUuOoCc")
                return str(text).translate(tr_map).encode('latin-1', 'replace').decode('latin-1')

            # PDF'de görünecek firma ismi: Kutudaki isim neyse o alınır
            firma_adi = self.firma_manuel.text.strip()
            if not firma_adi or firma_adi == "": firma_adi = "Genel"

            pdf.ln(25); pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, t("AMD TEKLIF"), ln=1, align='C'); pdf.ln(5)

            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(20, 7, t("Firma:"), 0, 0); pdf.set_font("Helvetica", '', 10)
            pdf.cell(75, 7, t(firma_adi), 0, 0)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(20, 7, t("Tarih:"), 0, 0); pdf.set_font("Helvetica", '', 10)
            pdf.cell(0, 7, t(self.tarih_input.text), 0, 1)
            
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(20, 7, t("Ilgili:"), 0, 0); pdf.set_font("Helvetica", '', 10)
            pdf.cell(75, 7, t(self.ilgili.text), 0, 0)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(20, 7, t("Teklif No:"), 0, 0); pdf.set_font("Helvetica", '', 10)
            pdf.cell(0, 7, t(self.teklif_no.text), 0, 1)
            
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(20, 7, t("Konu:"), 0, 0); pdf.set_font("Helvetica", '', 10)
            pdf.cell(0, 7, t(self.konu.text), 0, 1); pdf.ln(5)

            pdf.cell(0, 7, t(self.hitap.text), 0, 1)
            pdf.multi_cell(0, 7, t(self.giris_metni.text), 0, 'L'); pdf.ln(3)

            pdf.set_font("Helvetica", 'B', 9); pdf.set_fill_color(220, 220, 220)
            pdf.cell(108, 8, t("Aciklama"), 1, 0, 'C', True)
            pdf.cell(15, 8, t("Mik."), 1, 0, 'C', True)
            pdf.cell(10, 8, t("Birim"), 1, 0, 'C', True)
            pdf.cell(28, 8, t("Birim Fiyat"), 1, 0, 'C', True)
            pdf.cell(29, 8, t("Toplam"), 1, 1, 'C', True)

            pdf.set_font("Helvetica", '', 9)
            g_toplam = 0.0
            p_birimi = "TL"
            for s in self.urun_satirlari_listesi:
                w = s.widgets
                pdf.cell(108, 8, t(w['aciklama'].text), 1)
                pdf.cell(15, 8, t(w['miktar'].text), 1, 0, 'C')
                pdf.cell(10, 8, t(w['birim'].text), 1, 0, 'C')
                pdf.cell(28, 8, t(w['fiyat'].text), 1, 0, 'R')
                pdf.cell(29, 8, t(w['toplam'].text), 1, 1, 'R')
                try: 
                    g_toplam += float(w['toplam'].text.replace(',', ''))
                    p_birimi = w['curr'].text
                except: pass

            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(161, 8, t("GENEL TOPLAM:"), 1, 0, 'R')
            pdf.cell(29, 8, t(f"{g_toplam:,.2f} {p_birimi}"), 1, 1, 'R')

            pdf.ln(5)
            if self.chk_kdv.active:
                pdf.cell(0, 6, t("- Fiyatlarimiza KDV dahil degildir."), 0, 1)
            if self.chk_termin.active:
                pdf.cell(0, 6, t(f"- Termin: {self.termin_rakam.text} {self.termin_birim.text}"), 0, 1)
            
            pdf.ln(5); pdf.set_font("Helvetica", 'I', 10)
            pdf.cell(0, 7, t("Teklifimizi begeneceginizi umar, degerli siparislerinizi bekleriz."), 0, 1)

            pdf.ln(10); pdf.set_font("Helvetica", 'B', 11)
            pdf_offset = 145 
            pdf.cell(pdf_offset); pdf.cell(45, 6, t("Hulya Sonmez"), 0, 1, 'R')
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(pdf_offset); pdf.cell(45, 5, t("Sirket Yetkilisi"), 0, 1, 'R')
            pdf.cell(pdf_offset); pdf.cell(45, 5, t("05331652992"), 0, 1, 'R')

            # --- KAYIT DİZİNİ (Müşteri/İsim/Teklifler) ---
            kayit_dizini = os.path.join("Müşteri", firma_adi, "Teklifler")
            if not os.path.exists(kayit_dizini):
                os.makedirs(kayit_dizini)

            filename = f"Teklif_{self.teklif_no.text or 'Yeni'}.pdf"
            tam_dosya_yolu = os.path.join(kayit_dizini, filename)
            
            pdf.output(tam_dosya_yolu)
            if os.path.exists(tam_dosya_yolu):
                os.startfile(tam_dosya_yolu) 
            
            self.pdf_btn.text = "PDF ACILDI ✅"
            Clock.schedule_once(lambda dt: setattr(self.pdf_btn, 'text', 'KAYDET/PDF OLUŞTUR/GÖR'), 2)
        except Exception as e:
            print(f"Hata detayi: {e}")

    def musterileri_ayristir(self):
        musteriler = {}
        if os.path.exists("musteriler.txt"):
            try:
                with open("musteriler.txt", "r", encoding="utf-8") as f:
                    blocks = f.read().split("--- Yeni Müşteri ---")
                    for b in blocks:
                        if "FIRMA" in b:
                            for l in b.split("\n"):
                                if "FIRMA" in l: 
                                    name = l.split(":", 1)[1].strip()
                                    musteriler[name] = b
            except: pass
        return musteriler

def ekrani_olustur():
    return TeklifModulu()