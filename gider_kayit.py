import os
import requests
import threading
from datetime import datetime
import calendar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.dropdown import DropDown

# ==========================================
# KOLAY AYAR PANELİ
# ==========================================
AYAR = {
    "satir_yukseklik": dp(40),
    "baslik_yukseklik": dp(25),
    "alt_panel_yukseklik": dp(100),
    "ekle_sil_yukseklik": dp(35),
    "ana_buton_yukseklik": dp(45),
    "gen_tarih": 0.20,
    "gen_text": 0.45,
    "gen_tutar": 0.25,
    "gen_birim": 0.10,
}

def kivy_temizle():
    for rule in list(Builder.rules):
        if any(cls in str(rule) for cls in ["GiderSatiri", "AMDAccounting"]):
            Builder.rules.remove(rule)

kivy_temizle()

class ModernTakvimPopup(Popup):
    def __init__(self, hedef_buton, **kwargs):
        super().__init__(**kwargs)
        self.title = "Tarih Seç"
        self.size_hint = (0.8, 0.5)
        self.hedef_buton = hedef_buton
        simdi = datetime.now()
        self.yil, self.ay = simdi.year, simdi.month
        
        icerik = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        nav = BoxLayout(size_hint_y=None, height=dp(55))
        btn_geri = Button(text="<", size_hint_x=0.2, bold=True)
        btn_geri.bind(on_release=self.onceki_ay)
        self.baslik = Label(text="", bold=True, font_size='18sp')
        btn_ileri = Button(text=">", size_hint_x=0.2, bold=True)
        btn_ileri.bind(on_release=self.sonraki_ay)
        nav.add_widget(btn_geri); nav.add_widget(self.baslik); nav.add_widget(btn_ileri)
        
        self.gunler_izgara = GridLayout(cols=7, spacing=dp(2))
        btn_tamam = Button(text="TAMAM", size_hint_y=None, height=dp(50), background_color=(0.2, 0.6, 0.3, 1))
        btn_tamam.bind(on_release=self.dismiss)
        
        icerik.add_widget(nav); icerik.add_widget(self.gunler_izgara); icerik.add_widget(btn_tamam)
        self.content = icerik
        self.takvimi_yenile()

    def takvimi_yenile(self):
        self.gunler_izgara.clear_widgets()
        self.baslik.text = f"{self.yil} / {str(self.ay).zfill(2)}"
        gun_isimleri = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]
        for isim in gun_isimleri:
            self.gunler_izgara.add_widget(Label(text=isim, bold=True, color=(0.7, 0.7, 0.7, 1), font_size='12sp'))
        
        ilk_gun, toplam_gun = calendar.monthrange(self.yil, self.ay)
        for _ in range(ilk_gun): self.gunler_izgara.add_widget(Label())
        for gun in range(1, toplam_gun + 1):
            btn = Button(text=str(gun), font_size='14sp')
            btn.bind(on_release=self.tarih_onayla); self.gunler_izgara.add_widget(btn)

    def tarih_onayla(self, instance):
        kisa_yil = str(self.yil)[-2:]
        self.hedef_buton.text = f"{instance.text.zfill(2)}/{str(self.ay).zfill(2)}/{kisa_yil}"
        self.dismiss()

    def onceki_ay(self, *args):
        self.ay -= 1
        if self.ay < 1: self.ay = 12; self.yil -= 1
        self.takvimi_yenile()

    def sonraki_ay(self, *args):
        self.ay += 1
        if self.ay > 12: self.ay = 1; self.yil += 1
        self.takvimi_yenile()

class GiderSatiri(BoxLayout):
    def __init__(self, mevcut_turler, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = AYAR["satir_yukseklik"]
        self.spacing = dp(5)
        self.mevcut_turler = mevcut_turler

        # 1. TARİH (GG/AA/YY)
        bugun = datetime.now().strftime("%d/%m/%y")
        self.btn_takvim = Button(text=bugun, size_hint_x=0.20, font_size='12sp')
        self.btn_takvim.bind(on_release=lambda x: ModernTakvimPopup(self.btn_takvim).open())

        # 2. GİDER TÜRÜ (Dropdown Bağlandı)
        self.tur_in = TextInput(
            hint_text='Gider seç...', multiline=False, font_size='13sp',
            padding=[dp(10), dp(8), dp(10), dp(8)], size_hint_x=0.45
        )
        self.tur_in.bind(focus=self.liste_ac) # Listeyi açan bağlatı eklendi

        # 3. TUTAR
        self.tutar = TextInput(
            hint_text='0.00', input_filter='float', size_hint_x=0.25, 
            halign='center', padding=[dp(10), dp(8), dp(10), dp(8)], font_size='13sp'
        )

        # 4. BİRİM
        self.birim = Spinner(text='TL', values=('TL', 'USD', 'EUR'), size_hint_x=0.10, font_size='11sp')

        self.add_widget(self.btn_takvim)
        self.add_widget(self.tur_in)
        self.add_widget(self.tutar)
        self.add_widget(self.birim)

    def liste_ac(self, instance, value):
        if value:  # Focus olduğunda
            dropdown = DropDown()
            for tur in self.mevcut_turler:
                btn = Button(text=str(tur), size_hint_y=None, height=dp(40), background_color=(0.2, 0.2, 0.2, 1))
                btn.bind(on_release=lambda btn: dropdown.select(btn.text))
                dropdown.add_widget(btn)
            
            dropdown.bind(on_select=lambda instance, x: self.set_tur(x))
            dropdown.open(instance)

    def set_tur(self, x):
        self.tur_in.text = x
        self.tur_in.focus = False

class AMDAccounting:
    def __init__(self):
        self.base_url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.isletme = os.environ.get("SECILI_ISLETME", "AMD")
        self.gider_turleri = ['YAKIT', 'HGS', 'YEMEK', 'ELEKTRİK', 'SU', 'KİRA', 'MAAŞ']

    def _spinner_text_hizala(self, instance, size):
        instance.text_size = (instance.width - dp(20), instance.height)

    def build(self):
        self.ana_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        self.ana_layout.add_widget(Label(text=f"{self.isletme} GİDER GİRİŞİ", size_hint_y=None, height=dp(30), bold=True))
        
        # ÜST PANEL
        yonetim_kapsayici = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), spacing=dp(3))
        ekle_layout = BoxLayout(spacing=dp(5))
        self.yeni_tur_in = TextInput(hint_text='Yeni Gider Türü...', multiline=False, font_size='13sp', padding=[dp(10), dp(8)])
        btn_tur_ekle = Button(text="EKLE", size_hint_x=0.25, background_color=(0.1, 0.5, 0.7, 1), font_size='12sp')
        btn_tur_ekle.bind(on_release=self.yeni_tur_kaydet)
        ekle_layout.add_widget(self.yeni_tur_in); ekle_layout.add_widget(btn_tur_ekle)
        
        sil_layout = BoxLayout(spacing=dp(5))
        self.silinecek_tur_sp = Spinner(
            text='Tür Seç...', values=self.gider_turleri,
            background_normal='', background_color=(1, 1, 1, 1), color=(0.4, 0.4, 0.4, 1),
            halign='left', valign='middle', font_size='13sp'
        )
        self.silinecek_tur_sp.bind(size=self._spinner_text_hizala)
        btn_tur_sil = Button(text="SİL", size_hint_x=0.25, background_color=(0.8, 0.2, 0.2, 1), font_size='12sp')
        btn_tur_sil.bind(on_release=self.tur_sil)
        sil_layout.add_widget(self.silinecek_tur_sp); sil_layout.add_widget(btn_tur_sil)
        
        yonetim_kapsayici.add_widget(ekle_layout); yonetim_kapsayici.add_widget(sil_layout)
        self.ana_layout.add_widget(yonetim_kapsayici)

        # LİSTE BAŞLIKLARI
        baslik_layout = BoxLayout(size_hint_y=None, height=AYAR["baslik_yukseklik"], spacing=dp(5))
        baslik_layout.add_widget(Label(text="Tarih", size_hint_x=0.20, font_size='12sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        baslik_layout.add_widget(Label(text="Gider Türü", size_hint_x=0.45, font_size='12sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        baslik_layout.add_widget(Label(text="Tutar", size_hint_x=0.25, font_size='12sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        baslik_layout.add_widget(Label(text="Brm", size_hint_x=0.10, font_size='12sp', bold=True, color=(0.8, 0.8, 0.8, 1)))
        self.ana_layout.add_widget(baslik_layout)

        self.scroll = ScrollView(do_scroll_x=False)
        self.liste = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        self.liste.bind(minimum_height=self.liste.setter('height'))
        self.scroll.add_widget(self.liste); self.ana_layout.add_widget(self.scroll)
        
        # ALT PANEL (Orijinal Yapı)
        alt_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=AYAR["alt_panel_yukseklik"], spacing=dp(5))
        ekle_sil_satiri = BoxLayout(size_hint_y=None, height=AYAR["ekle_sil_yukseklik"], spacing=dp(5))
        sol_blok = BoxLayout(spacing=dp(5), size_hint_x=0.45)
        btn_ekle_satir = Button(text="+ SATIR", background_color=(0.2, 0.6, 0.4, 1), font_size='11sp')
        btn_ekle_satir.bind(on_release=lambda x: self.satir_ekle())
        btn_sil_satir = Button(text="- SİL", background_color=(0.8, 0.4, 0.2, 1), font_size='11sp')
        btn_sil_satir.bind(on_release=self.satir_sil)
        sol_blok.add_widget(btn_ekle_satir); sol_blok.add_widget(btn_sil_satir)
        ekle_sil_satiri.add_widget(sol_blok); ekle_sil_satiri.add_widget(Label(size_hint_x=0.55))
        
        ana_buton_satiri = BoxLayout(size_hint_y=None, height=AYAR["ana_buton_yukseklik"], spacing=dp(0))
        self.btn_kaydet = Button(text="BULUTA KAYDET", size_hint_x=0.45, background_color=(0.1, 0.7, 0.2, 1), bold=True)
        self.btn_kaydet.bind(on_release=self.verileri_gonder)
        btn_kapat = Button(text="KAPAT", size_hint_x=0.45, background_color=(0.7, 0.1, 0.1, 1), bold=True)
        btn_kapat.bind(on_release=self.ekrani_kapat)
        ana_buton_satiri.add_widget(self.btn_kaydet); ana_buton_satiri.add_widget(Label(size_hint_x=0.1)); ana_buton_satiri.add_widget(btn_kapat)
        
        alt_panel.add_widget(ekle_sil_satiri); alt_panel.add_widget(ana_buton_satiri)
        self.ana_layout.add_widget(alt_panel)

        self.satir_ekle()
        return self.ana_layout

    def yeni_tur_kaydet(self, *args):
        t = self.yeni_tur_in.text.strip().upper()
        if t and t not in self.gider_turleri:
            self.gider_turleri.append(t); self.yeni_tur_in.text = ""
            self.spinnerlari_yenile()

    def tur_sil(self, *args):
        t = self.silinecek_tur_sp.text
        if t in self.gider_turleri:
            self.gider_turleri.remove(t)
            self.silinecek_tur_sp.text = 'Tür Seç...'
            self.spinnerlari_yenile()

    def spinnerlari_yenile(self):
        self.silinecek_tur_sp.values = list(self.gider_turleri)
        for s in self.liste.children:
            if isinstance(s, GiderSatiri):
                s.mevcut_turler = list(self.gider_turleri)

    def satir_ekle(self):
        self.liste.add_widget(GiderSatiri(mevcut_turler=self.gider_turleri))

    def satir_sil(self, *args):
        if len(self.liste.children) > 1: self.liste.remove_widget(self.liste.children[0])

    def verileri_gonder(self, *args):
        payload = []
        for s in self.liste.children:
            if s.tur_in.text and s.tutar.text:
                payload.append({"tarih": s.btn_takvim.text, "tur": s.tur_in.text.strip().upper(), "tutar": s.tutar.text.strip(), "birim": s.birim.text, "isletme": self.isletme, "vakit": datetime.now().strftime("%H:%M")})
        if payload:
            self.btn_kaydet.disabled = True; self.btn_kaydet.text = "YÜKLENİYOR..."
            threading.Thread(target=self.firebase_post, args=(payload,), daemon=True).start()

    def firebase_post(self, veriler):
        try:
            url = f"{self.base_url}/{self.isletme}/giderler.json"
            for v in veriler: requests.post(url, json=v, timeout=10)
            Clock.schedule_once(self.islem_basarili, 0)
        except: Clock.schedule_once(lambda dt: self.buton_reset(), 0)

    def islem_basarili(self, dt):
        self.liste.clear_widgets(); self.satir_ekle(); self.buton_reset()

    def buton_reset(self):
        self.btn_kaydet.disabled = False; self.btn_kaydet.text = "BULUTA KAYDET"

    def ekrani_kapat(self, *args):
        from kivy.core.window import Window
        for widget in Window.children:
            if isinstance(widget, Popup): widget.dismiss(); return

def ekrani_olustur():
    return AMDAccounting().build()