from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from datetime import datetime, timedelta
import os

class GiderModulu(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GİDER YÖNETİMİ VE ANALİZ"
        self.size_hint = (0.95, 0.95)
        
        # Ana Taşıyıcı
        self.ana_panel = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # --- ÜST KISIM: YENİ KAYIT ALANI ---
        kayit_cerceve = GridLayout(cols=4, size_hint_y=None, height=120, spacing=10)
        
        # Tarih Seçimi (Varsayılan Bugün)
        self.tarih_btn = Button(text=datetime.now().strftime("%d.%m.%Y"), background_color=(0.2, 0.5, 0.8, 1))
        self.tarih_btn.bind(on_release=self.takvim_ac)
        
        # Kategori Seçimi (Dropdown)
        self.kategori_secici = Spinner(
            text='Kategori Seç',
            values=('YAKIT', 'KİRA', 'YEMEK', 'HGS', 'DİĞER'),
            background_color=(0.1, 0.1, 0.3, 1)
        )
        
        # Tutar Girişi
        self.tutar_input = TextInput(hint_text='Tutar (TL)', multiline=False, input_filter='float')
        
        # Kaydet Butonu
        btn_kaydet = Button(text='SİSTEME İŞLE', background_color=(0.1, 0.6, 0.2, 1), bold=True)
        btn_kaydet.bind(on_release=self.gider_kaydet)
        
        kayit_cerceve.add_widget(Label(text="Tarih:"))
        kayit_cerceve.add_widget(Label(text="Kategori:"))
        kayit_cerceve.add_widget(Label(text="Tutar:"))
        kayit_cerceve.add_widget(Label(text="İşlem:"))
        kayit_cerceve.add_widget(self.tarih_btn)
        kayit_cerceve.add_widget(self.kategori_secici)
        kayit_cerceve.add_widget(self.tutar_input)
        kayit_cerceve.add_widget(btn_kaydet)
        
        self.ana_panel.add_widget(kayit_cerceve)

        # --- ORTA KISIM: ANALİZ VE FİLTRELEME ---
        filtre_panel = BoxLayout(size_hint_y=None, height=50, spacing=5)
        filtre_panel.add_widget(Label(text="GİDERLERİ GÖR:", bold=True, size_hint_x=0.2))
        
        zamanlar = {
            "3 Gün": 3, "1 Hafta": 7, "3 Ay": 90, "6 Ay": 180, "1 Yıl": 365
        }
        
        for metin, gun in zamanlar.items():
            btn = Button(text=metin, background_color=(0.4, 0.4, 0.4, 1))
            btn.bind(on_release=lambda x, g=gun: self.listele(g))
            filtre_panel.add_widget(btn)
            
        self.ana_panel.add_widget(filtre_panel)

        # --- ALT KISIM: LİSTELEME ALANI ---
        self.liste_scroll = ScrollView()
        self.sonuc_alani = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.sonuc_alani.bind(minimum_height=self.sonuc_alani.setter('height'))
        self.liste_scroll.add_widget(self.sonuc_alani)
        
        self.ana_panel.add_widget(self.liste_scroll)

        # Kapat Butonu
        btn_kapat = Button(text="MODÜLÜ KAPAT", size_hint_y=None, height=45, background_color=(0.8, 0.2, 0.2, 1))
        btn_kapat.bind(on_release=self.dismiss)
        self.ana_panel.add_widget(btn_kapat)

        self.content = self.ana_panel

    def takvim_ac(self, instance):
        # Hızlı çözüm için basit bir TextInput popup; gerçek takvim modülü uzun sürer
        icerik = BoxLayout(orientation='vertical', padding=10)
        yeni_tarih = TextInput(text=self.tarih_btn.text, multiline=False)
        icerik.add_widget(Label(text="Tarihi Düzenle (GG.AA.YYYY):"))
        icerik.add_widget(yeni_tarih)
        
        btn_box = BoxLayout(size_hint_y=None, height=40)
        btn_tamam = Button(text="Tamam")
        p = Popup(title="Tarih Seç", content=icerik, size_hint=(0.6, 0.4))
        
        def tarih_set(x):
            self.tarih_btn.text = yeni_tarih.text
            p.dismiss()
            
        btn_tamam.bind(on_release=tarih_set)
        btn_box.add_widget(btn_tamam)
        icerik.add_widget(btn_box)
        p.open()

    def gider_kaydet(self, instance):
        if self.kategori_secici.text == 'Kategori Seç' or not self.tutar_input.text:
            return
        
        verisi = f"{self.tarih_btn.text}|{self.kategori_secici.text}|{self.tutar_input.text}\n"
        with open("giderler.txt", "a", encoding="utf-8") as f:
            f.write(verisi)
        
        self.tutar_input.text = ""
        self.listele(3) # Kayıttan sonra son 3 günü göster

    def listele(self, gun_sayisi):
        self.sonuc_alani.clear_widgets()
        if not os.path.exists("giderler.txt"): return

        hedef_tarih = datetime.now() - timedelta(days=gun_sayisi)
        kategoriler = {}

        with open("giderler.txt", "r", encoding="utf-8") as f:
            for satir in f:
                tarih_str, kat, tutar = satir.strip().split("|")
                t_obj = datetime.strptime(tarih_str, "%d.%m.%Y")
                
                if t_obj >= hedef_tarih:
                    kategoriler[kat] = kategoriler.get(kat, 0) + float(tutar)

        # Kategori Kategori Blok Listeleme
        for kat, toplam in kategoriler.items():
            blok = Button(text=f"{kat}: {toplam:.2f} TL", size_hint_y=None, height=50, 
                          background_normal='', background_color=(0.15, 0.25, 0.35, 1))
            self.sonuc_alani.add_widget(blok)

def ekrani_olustur(*args):
    return GiderModulu()