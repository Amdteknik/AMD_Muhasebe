from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import importlib
import os
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget


class AMDAccounting(App):
    veriyolu = ""
    ana_uygulama = None

    def build(self):
        # --- DİZİN AYARLARI ---
        if self.veriyolu:
            try:
                os.chdir(self.veriyolu)
            except:
                pass

        # --- AYARLAR VE SABİTLER ---
        self.normal_renk = [0.05, 0.15, 0.3, 1]
        self.aktif_renk = [0.3, 0.6, 0.9, 1]
        self.evrensel_buton_metni = "Yeni Kayıt"
        self.aktif_buton = None
        isletme_adi = os.environ.get("SECILI_ISLETME", "AMD")

        # 1. ANA TAŞIYICI
        self.root_layout = FloatLayout()

        # 2. ARKA PLAN LOGOSU
        self.arka_plan_logosu = Image(
            source=f"{isletme_adi} LOGO.jpg",
            opacity=0.15,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.5, 0.5),
            pos_hint={'center_x': 0.6, 'center_y': 0.5}
        )
        self.root_layout.add_widget(self.arka_plan_logosu)

        # 3. ÖN PLAN ARAYÜZÜ
        self.main_layout = BoxLayout(orientation='horizontal')

        # --- SOL MENÜ ---
        self.side_menu = BoxLayout(orientation='vertical', size_hint_x=0.30, padding=[5, 10, 5, 10], spacing=5)
        self.side_menu.add_widget(Label(
            text=f"        {isletme_adi} ANALİZ", 
            font_size='18sp', bold=True, color=self.aktif_renk,
            size_hint_y=None, height=200
        ))

        self.menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None)
        self.menu_grid.bind(minimum_height=self.menu_grid.setter('height'))

        buton_listesi = [
            ("Müşteriler", "musteri_modulu"),
            ("Tedarikçiler", "tedarikci_modulu"),
            ("Teklif", "teklif_modulu"),
            ("Alış Fatura", "alis_fatura_modulu"),
            ("Satış Fatura", "satis_fatura_modulu"),
            ("Fatura Denetimi", "fatura_denetimi_menusu"),
            ("Siparişler", "siparis_takip_modulu"),
            ("Finansal Analiz", "finansal_analiz_modulu"),
            ("Giderler", "gider_modulu"),
            ("Projeler", "proje_modulu"),
            ("Stok Takip", "stok_takip_modulu")
        ]

        for metin, modul in buton_listesi:
            self.buton_ekle(self.menu_grid, metin, modul)

        # Standart butonları döngü ile ekle


# --- GÜNCEL ALT ÜST ÖDEME BUTONLARI ---

# --- GÜNCEL ALT ÜST ÖDEME BUTONLARI ---

        # 1. TAM BİR BUTON BOYU (100 birim) BOŞLUK
        self.menu_grid.add_widget(Label(size_hint_y=None, height=100))

        # 2. ÖDEME AL (Yükseklik 100, Genişlik Yarım)
        btn_odeme_al = Button(
            text="ÖDEME AL",
            size_hint_y=None, height=50,
            size_hint_x=0.5,  # Genişlik yarısı
            background_normal='',
            background_color=(0.1, 0.7, 0.3, 1), # Yeşil
            bold=True, font_size='13sp'
        )
        btn_odeme_al.bind(on_release=lambda x: self.modul_yonetici("odeme_al", "ÖDEME AL"))
        self.menu_grid.add_widget(btn_odeme_al) # Doğrudan menu_grid'e ekliyoruz

        # 3. ÖDEME YAP (Yükseklik 100, Genişlik Yarım)
        btn_odeme_yap = Button(
            text="ÖDEME YAP",
            size_hint_y=None, height=50,
            size_hint_x=0.5,  # Genişlik yarısı
            background_normal='',
            background_color=(0.8, 0.2, 0.2, 1), # Kırmızı
            bold=True, font_size='13sp'
        )
        btn_odeme_yap.bind(on_release=lambda x: self.modul_yonetici("odeme_yap", "ÖDEME YAP"))
        self.menu_grid.add_widget(btn_odeme_yap) # Doğrudan menu_grid'e ekliyoruz


        # Menüye ekle

        self.menu_scroll = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        self.menu_scroll.add_widget(self.menu_grid)
        self.side_menu.add_widget(self.menu_scroll)

        # --- SAĞ İÇERİK ALANI ---
        self.content_area = BoxLayout(orientation='vertical', size_hint_x=0.70, padding=0)
        self.content_area.add_widget(Label(
            text="Lütfen bir işlem seçiniz...", 
            color=(0.5, 0.5, 0.5, 0.3), font_size='20sp'
        ))

        self.main_layout.add_widget(self.side_menu)
        self.main_layout.add_widget(self.content_area)
        self.root_layout.add_widget(self.main_layout)

        # 4. SAĞ ALT KONTROL BUTONLARI
        btn_box = BoxLayout(size_hint=(None, None), size=('310dp', '50dp'), 
                            pos_hint={'right': 0.99, 'y': 0.01}, spacing='10dp')
        
        btn_geri = Button(text="ŞİRKET DEĞİŞTİR", background_normal='', 
                          background_color=[0.2, 0.4, 0.6, 1], bold=True, font_size='12sp')
        btn_geri.bind(on_release=self.ana_ekrana_don)
        
        btn_cikis = Button(text="PROGRAMI SONLANDIR", background_normal='', 
                           background_color=[0.8, 0.2, 0.2, 1], bold=True, font_size='12sp')
        btn_cikis.bind(on_release=self.cikis_onay_popup)

        btn_box.add_widget(btn_geri)
        btn_box.add_widget(btn_cikis)
        self.root_layout.add_widget(btn_box)

        return self.root_layout

    def cikis_onay_popup(self, instance):
        icerik = BoxLayout(orientation='vertical', padding=10, spacing=10)
        icerik.add_widget(Label(text='Programı kapatmak istediğinize\nemin misiniz?', halign='center'))
        buton_alani = BoxLayout(size_hint_y=None, height='50dp', spacing=10)
        btn_evet = Button(text='Evet', background_color=[0.8, 0.2, 0.2, 1], bold=True)
        btn_evet.bind(on_release=lambda x: App.get_running_app().stop())
        btn_hayir = Button(text='Hayır', background_color=[0.2, 0.6, 0.2, 1], bold=True)
        buton_alani.add_widget(btn_evet)
        buton_alani.add_widget(btn_hayir)
        icerik.add_widget(buton_alani)
        self.popup = Popup(title='Çıkış Onayı', content=icerik, size_hint=(None, None), size=('300dp', '180dp'))
        btn_hayir.bind(on_release=self.popup.dismiss)
        self.popup.open()

    def ana_ekrana_don(self, instance):
        try:
            os.chdir("..") 
            if os.path.exists("secilen_isletme.txt"):
                os.remove("secilen_isletme.txt")
            if self.ana_uygulama:
                self.ana_uygulama.hosgeldiniz_sayfasi()
        except Exception as e:
            print(f"Geri dönme hatası: {e}")

    def fatura_denetimi_alt_menusu_goster(self):
        self.content_area.clear_widgets()
        self.content_area.add_widget(Label(
            text="", font_size='22sp', bold=True, 
            color=self.aktif_renk, size_hint_y=None, height=100,
            halign='left', valign='middle', text_size=(None, 100)
        ))
        alt_menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[20, 120, 0, 0])
        alt_menu_grid.bind(minimum_height=alt_menu_grid.setter('height'))
        alt_butonlar = [("GÖR/ÖDE", "fatura_goruntule_modulu"), ("ALACAKLAR", "alacaklar_modulu"), ("VERECEKLER", "verecekler_modulu"), ("KDV", "kdv_modulu")]
        for isim, modul_adi in alt_butonlar:
            btn = Button(text=isim, size_hint_y=None, height=60, size_hint_x=None, width=350, background_normal='', background_color=self.aktif_renk, font_size='18sp', bold=True)
            btn.bind(on_release=lambda x, m=modul_adi, t=isim: self.modul_yonetici(m, t))
            alt_menu_grid.add_widget(btn)
        self.content_area.add_widget(alt_menu_grid)
        self.content_area.add_widget(BoxLayout(size_hint_y=1))

    def buton_ekle(self, target, text, module_name):
        btn = Button(text=text, size_hint_y=None, height=100, background_normal='', background_color=self.normal_renk, font_size='14sp', bold=True, halign='left', valign='middle', padding=(15, 0))
        btn.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        btn.bind(on_press=self.buton_vurgula)
        btn.bind(on_release=lambda x, m=module_name, t=text: self.modul_yonetici(m, t))
        target.add_widget(btn)

    def buton_vurgula(self, buton):
        if self.aktif_buton:
            self.aktif_buton.background_color = self.normal_renk
        buton.background_color = self.aktif_renk
        self.aktif_buton = buton

    def modul_yonetici(self, module_name, button_text):
        self.content_area.clear_widgets()
        
        from kivy.uix.modalview import ModalView
        from kivy.uix.popup import Popup as KivyPopup
        from kivy.uix.label import Label

        # --- ALT MENÜ KONTROLLERİ ---
        if button_text == "Fatura Denetimi":
            self.fatura_denetimi_alt_menusu_goster()
            return
        if button_text == "Teklif":
            self.teklif_alt_menusu_goster()
            return
        if button_text == "Siparişler":
            self.siparis_alt_menusu_goster()
            return
        if button_text == "Giderler":
            self.gider_alt_menusu_goster()
            return 
        # Yeni eklenen Projeler kontrolü
        if button_text == "Projeler":
            self.proje_alt_menusu_goster()
            return

        try:
            modul = importlib.import_module(module_name)
            importlib.reload(modul)
            ekran = modul.ekrani_olustur()
            
            if isinstance(ekran, (ModalView, KivyPopup)):
                ekran.bind(on_dismiss=lambda x: self.ekran_sifirla_ve_normal_yap())
                ekran.open() 
                return 

            # Popup tetikleyici kelimeler (yeni_proje gibi dosyalar burada yakalanır)
            dosya_adi = module_name.lower()
            yazi_kontrol = button_text.lower().replace("ı", "i").replace("I", "i").strip()
            
            popup_mi = (
                "analiz" in dosya_adi or 
                "gider" in dosya_adi or 
                "kayit" in dosya_adi or 
                "goruntule" in dosya_adi or
                "yeni" in dosya_adi or # yeni_proje için kritik
                any(kelime in yazi_kontrol for kelime in ["yeni", "gor/ode", "duzenle", "sil", "gider", "analiz"])
            )
            
            if popup_mi:
                popup = KivyPopup(
                    title=button_text, 
                    content=ekran, 
                    size_hint=(0.95, 0.95),
                    auto_dismiss=False
                )
                popup.bind(on_dismiss=lambda x: self.ekran_sifirla_ve_normal_yap())
                popup.open()
            else:
                self.content_area.add_widget(ekran)
                
        except Exception as e:
            print(f"Hata ({module_name}): {e}")
            KivyPopup(title="Modül Yükleme Hatası", 
                      content=Label(text=f"Modül: {module_name}\nHata: {str(e)}"),
                      size_hint=(0.8, 0.4)).open()

    # --- PROJE ALT MENÜSÜ ---
    def proje_alt_menusu_goster(self):
        self.content_area.clear_widgets()
        self.content_area.add_widget(Label(text="", size_hint_y=None, height=100))
        
        alt_menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[20, 120, 0, 0])
        alt_menu_grid.bind(minimum_height=alt_menu_grid.setter('height'))

        proje_aksiyonlari = [
            ("YENİ", "yeni_proje"), 
            ("GÖR/DÜZENLE/SİL", "proje_duzenle"), 
            ("FATURALANDIR", "proje_faturalandir")
        ]
        
        for isim, modul_adi in proje_aksiyonlari:
            btn = Button(
                text=isim, size_hint_y=None, height=65, size_hint_x=None, width=450,
                background_normal='', background_color=self.aktif_renk, 
                font_size='18sp', bold=True, halign='left', valign='middle'
            )
            btn.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 40, s.height)))
            btn.bind(on_release=lambda x, m=modul_adi, t=isim: self.modul_yonetici(m, t))
            alt_menu_grid.add_widget(btn)

        self.content_area.add_widget(alt_menu_grid)
        self.content_area.add_widget(BoxLayout(size_hint_y=1))

    def ekran_sifirla_ve_normal_yap(self):
        if self.aktif_buton:
            self.aktif_buton.background_color = self.normal_renk

    def gider_alt_menusu_goster(self):
        self.content_area.clear_widgets()
        self.content_area.add_widget(Label(
            text="", font_size='22sp', bold=True, 
            color=self.aktif_renk, size_hint_y=None, height=100,
            halign='left', valign='middle', text_size=(None, 100)
        ))
        
        alt_menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[20, 120, 0, 0])
        alt_menu_grid.bind(minimum_height=alt_menu_grid.setter('height'))
        
        # Buradaki modül isimleri ayrı .py dosyaların olacak
        gider_aksiyonlari = [
            ("YENİ", "gider_kayit"), 
            ("GÖR/DÜZENLE/SİL", "gider_duzenle")
        ]
        
        for isim, modul_adi in gider_aksiyonlari:
            btn = Button(
                text=isim, size_hint_y=None, height=65, size_hint_x=None, width=450,
                background_normal='', background_color=self.aktif_renk, 
                font_size='18sp', bold=True
            )
            # 'YENİ' metni sisteminde Popup açılmasını tetikler
            btn.bind(on_release=lambda x, m=modul_adi, t=isim: self.modul_yonetici(m, t))
            alt_menu_grid.add_widget(btn)

        self.content_area.add_widget(alt_menu_grid)
        self.content_area.add_widget(BoxLayout(size_hint_y=1))

    def siparis_alt_menusu_goster(self):
        self.content_area.clear_widgets()
        self.content_area.add_widget(Label(text="", font_size='22sp', bold=True, color=self.aktif_renk, size_hint_y=None, height=100, halign='left', valign='middle', text_size=(None, 100)))
        alt_menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[20, 120, 0, 0])
        alt_menu_grid.bind(minimum_height=alt_menu_grid.setter('height'))
        siparis_aksiyonlari = [("YENİ", "yeni_siparis"), ("GÖR/DÜZENLE/SİL", "siparis_duzenle"), ("FATURALANDIR", "siparis_faturalandir")]
        for isim, modul_adi in siparis_aksiyonlari:
            btn = Button(text=isim, size_hint_y=None, height=60, size_hint_x=None, width=400, background_normal='', background_color=self.aktif_renk, font_size='16sp', bold=True)
            btn.bind(on_release=lambda x, m=modul_adi, t=isim: self.modul_yonetici(m, t))
            alt_menu_grid.add_widget(btn)
        self.content_area.add_widget(alt_menu_grid)
        self.content_area.add_widget(BoxLayout(size_hint_y=1))

    def teklif_alt_menusu_goster(self):
        self.content_area.clear_widgets()
        self.content_area.add_widget(Label(
            text="", font_size='22sp', bold=True, color=self.aktif_renk,
            size_hint_y=None, height=100, halign='left', valign='middle', text_size=(None, 100)
        ))
        
        # Padding değerini ve butonlar arası boşluğu koruyoruz
        alt_menu_grid = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[20, 120, 0, 0])
        alt_menu_grid.bind(minimum_height=alt_menu_grid.setter('height'))

        teklif_aksiyonlari = [
            ("YENİ", "yeni_teklif"),
            ("GÖRÜNTÜLE", "teklif_goruntule"),
            ("DÜZENLE", "teklif_duzenle"),
            ("SİL", "teklif_sil"),
            ("FATURALANDIR", "teklif_faturalandir")
        ]

        for isim, modul_adi in teklif_aksiyonlari:
            btn = Button(
                text=isim, 
                size_hint_y=None, 
                height=65, 
                size_hint_x=None, 
                width=450, 
                background_normal='', 
                background_color=self.aktif_renk, 
                font_size='18sp', 
                bold=True,
                halign='left',   # Yazı yatayda sola
                valign='middle'  # Yazı dikeyde ortaya
            )
            
            # BURASI ÇOK ÖNEMLİ: Yazı kutusunu butonun genişliğine (s.width) eşitliyoruz
            # padding=(25, 0) ekleyerek yazının kenara yapışmasını da engelliyoruz
            btn.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 40, s.height)))
            
            btn.bind(on_release=lambda x, m=modul_adi, t=isim: self.modul_yonetici(m, t))
            alt_menu_grid.add_widget(btn)



        self.content_area.add_widget(alt_menu_grid)
        self.content_area.add_widget(BoxLayout(size_hint_y=1))


if __name__ == '__main__':
    AMDAccounting().run()


    

