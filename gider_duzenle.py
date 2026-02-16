import os
import requests
import threading
from datetime import datetime, timedelta
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from kivy.metrics import dp

# Gider Kayıt modülünden sınıfları çekiyoruz
try:
    from gider_kayit import ModernTakvimPopup, GiderSatiri, AMDAccounting
except ImportError:
    ModernTakvimPopup = None
    GiderSatiri = None
    AMDAccounting = None

class GiderDuzenleFormu(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)

        # URL ve İŞLETME BİLGİSİNİ SİSTEMDEN ALIYORUZ
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.base_url = os.environ.get("FIREBASE_URL", "https://amd-accounting-default-rtdb.europe-west1.firebasedatabase.app")
        
        self.bulut_verisi = {}
        self.secili_satir_id = None 
        self.bugun = datetime.now().strftime("%d/%m/%y")
        
        # ---------- ÜST PANEL ----------
        ust = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(5))
        
        self.lbl_genel_toplam = Label(
            text="GENEL TOPLAM: 0.00 TL",
            bold=True, font_size='16sp', color=(1, 0.8, 0, 1),
            size_hint_y=None, height=dp(30)
        )
        
        # Tarih Seçimi
        tarih_kutu = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
        self.btn_basla = Button(text="01/01/26", font_size='12sp')
        self.btn_bitis = Button(text=self.bugun, font_size='12sp')
        self.btn_basla.bind(on_release=self.takvim_ac)
        self.btn_bitis.bind(on_release=self.takvim_ac)
        
        self.sp_hizli = Spinner(
            text="HIZLI SEÇ",
            values=("1 AY", "3 AY", "6 AY", "1 YIL", "TÜMÜ"),
            background_normal='', background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1), halign='left', size_hint_x=0.6, font_size='12sp'
        )
        self.sp_hizli.bind(size=self._spinner_hizala)
        self.sp_hizli.bind(text=self.hizli_filtre_uygula)
        
        tarih_kutu.add_widget(self.btn_basla)
        tarih_kutu.add_widget(self.btn_bitis)
        tarih_kutu.add_widget(self.sp_hizli)

        kat_kutu = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
        self.sp_kat = Spinner(
            text="HEPSİ", values=("HEPSİ",),
            background_normal='', background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1), halign='left', font_size='12sp'
        )
        self.sp_kat.bind(size=self._spinner_hizala)
        self.sp_kat.bind(text=lambda *a: self.arayuzu_guncelle())
        
        btn_duzenle = Button(text="DÜZENLE", size_hint_x=0.33, background_color=(0.1, 0.4, 0.7, 1), bold=True, font_size='11sp')
        btn_duzenle.bind(on_release=self.satiri_duzenle_penceresi)

        btn_sil = Button(text="SİL", size_hint_x=0.33, background_color=(0.8, 0.2, 0.2, 1), bold=True, font_size='11sp')
        btn_sil.bind(on_release=self.veriyi_sil_onay)

        btn_sifirla = Button(text="SIFIRLA", size_hint_x=0.33, background_color=(0.1, 0.5, 0.1, 1), bold=True, font_size='11sp')
        btn_sifirla.bind(on_release=self.verileri_sifirla)
        
        kat_kutu.add_widget(self.sp_kat)
        kat_kutu.add_widget(btn_duzenle)
        kat_kutu.add_widget(btn_sil)
        kat_kutu.add_widget(btn_sifirla)

        ust.add_widget(self.lbl_genel_toplam); ust.add_widget(tarih_kutu); ust.add_widget(kat_kutu)
        self.add_widget(ust)

        # ---------- LİSTE ALANI ----------
        self.scroll = ScrollView()
        self.liste_icerik = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=[dp(10), 0])
        self.liste_icerik.bind(minimum_height=self.liste_icerik.setter('height'))
        self.scroll.add_widget(self.liste_icerik)
        self.add_widget(self.scroll)

        # ---------- ALT PANEL ----------
        alt = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(90), spacing=dp(5))
        s1 = BoxLayout(spacing=dp(5)); s1.add_widget(Button(text="PDF")); s1.add_widget(Button(text="E-POSTA"))
        s2 = BoxLayout(spacing=dp(5)); s2.add_widget(Button(text="YAZDIR"))
        s2.add_widget(Button(text="KAPAT", background_color=(0.5, 0, 0, 1), on_release=self.kapat))
        alt.add_widget(s1); alt.add_widget(s2)
        self.add_widget(alt)

        self.verileri_yukle()

    def verileri_sifirla(self, *args):
        self.btn_basla.disabled = False
        self.btn_bitis.disabled = False
        self.btn_basla.opacity = 1.0
        self.btn_bitis.opacity = 1.0
        self.btn_basla.text = "01/01/26"
        self.btn_bitis.text = datetime.now().strftime("%d/%m/%y")
        self.sp_kat.text = "HEPSİ" 
        self.sp_hizli.text = "HIZLI SEÇ"
        self.verileri_yukle()

    def _spinner_hizala(self, instance, size):
        instance.text_size = (instance.width - dp(20), instance.height)
        instance.valign = 'middle'

    def hizli_filtre_uygula(self, spinner, text):
        bitis = datetime.now()
        is_manual = (text == "TÜMÜ" or text == "HIZLI SEÇ")
        
        if text == "1 AY": baslangic = bitis - timedelta(days=30)
        elif text == "3 AY": baslangic = bitis - timedelta(days=90)
        elif text == "6 AY": baslangic = bitis - timedelta(days=180)
        elif text == "1 YIL": baslangic = bitis - timedelta(days=365)
        else: baslangic = datetime(2026, 1, 1)
        
        self.btn_basla.disabled = not is_manual
        self.btn_bitis.disabled = not is_manual
        self.btn_basla.opacity = 1.0 if is_manual else 0.5
        self.btn_bitis.opacity = 1.0 if is_manual else 0.5
        self.btn_basla.text = baslangic.strftime("%d/%m/%y")
        self.btn_bitis.text = bitis.strftime("%d/%m/%y")
        self.verileri_yukle()

    def verileri_yukle(self, *args):
        def run():
            try:
                url = f"{self.base_url.rstrip('/')}/{self.isletme}/giderler.json"
                res = requests.get(url, timeout=10).json()
                self.bulut_verisi = res if res else {}
                Clock.schedule_once(lambda dt: self.arayuzu_guncelle(), 0)
            except: pass
        threading.Thread(target=run, daemon=True).start()

    def arayuzu_guncelle(self):
        self.liste_icerik.clear_widgets()
        self.secili_satir_id = None 
        
        try:
            bas = datetime.strptime(self.btn_basla.text, "%d/%m/%y")
            bit = datetime.strptime(self.btn_bitis.text, "%d/%m/%y")
        except:
            bas = datetime(2026, 1, 1); bit = datetime.now()
        
        kategoriler = {}
        tum_kats = set(["HEPSİ"])

        for gid, g in self.bulut_verisi.items():
            dt_str = g.get("tarih", "")
            if not dt_str: continue
            try:
                dt = datetime.strptime(dt_str, "%d/%m/%y")
                tur = g.get("tur", "DİĞER").upper()
                tum_kats.add(tur)

                if bas <= dt <= bit and (self.sp_kat.text == "HEPSİ" or self.sp_kat.text == tur):
                    if tur not in kategoriler: kategoriler[tur] = []
                    g["_fb_id"] = gid
                    kategoriler[tur].append(g)
            except: continue

        eski_secim = self.sp_kat.text
        self.sp_kat.values = sorted(list(tum_kats))
        self.sp_kat.text = eski_secim if eski_secim in self.sp_kat.values else "HEPSİ"

        genel_toplam_degeri = 0.0 

        for kat in sorted(kategoriler.keys()):
            lbl_kat = Label(text=f"[b][color=33b5e5]{kat}[/color][/b]", markup=True, 
                            size_hint_y=None, height=dp(30), halign='left', valign='middle', font_size='14sp')
            lbl_kat.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
            self.liste_icerik.add_widget(lbl_kat)
            
            baslik_row = BoxLayout(size_hint_y=None, height=dp(25), spacing=dp(2))
            baslik_row.add_widget(Label(text="SEÇ", size_hint_x=None, width=dp(40), font_size='11sp', color=(1, 0.7, 0, 1)))
            
            for b_text, b_hint in [("TARİH", 0.2), ("GİDER TÜRÜ", 0.3), ("TUTAR / BRM", 0.4)]:
                align = 'right' if "TUTAR" in b_text else 'left'
                l_baslik = Label(text=b_text, size_hint_x=b_hint, halign=align, valign='middle', 
                                 font_size='11sp', color=(1, 0.7, 0, 1))
                l_baslik.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
                baslik_row.add_widget(l_baslik)
            self.liste_icerik.add_widget(baslik_row)
            
            kat_toplam = 0.0
            for g in kategoriler[kat]:
                row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(2))
                
                cb = CheckBox(size_hint_x=None, width=dp(40), group='gider_secim')
                cb.bind(active=lambda inst, val, gid=g["_fb_id"]: self.satir_secildi(val, gid))
                row.add_widget(cb)
                
                for val, hint in [(str(g.get("tarih")), 0.2), (str(g.get("tur")), 0.3)]:
                    lbl = Label(text=val, size_hint_x=hint, halign='left', valign='middle', font_size='11sp')
                    lbl.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
                    row.add_widget(lbl)
                
                tutar_raw = str(g.get("tutar", "0"))
                birim_raw = str(g.get("birim", "TL"))
                lbl_tutar = Label(text=f"{tutar_raw} {birim_raw}", size_hint_x=0.4, halign='right', valign='middle', padding=(0, 0, dp(10), 0), font_size='11sp')
                lbl_tutar.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
                row.add_widget(lbl_tutar)
                
                self.liste_icerik.add_widget(row)
                try:
                    kat_toplam += float(tutar_raw.replace(",", "."))
                except: pass

            lbl_kat_top = Label(text=f"[b][color=66ff66]TOPLAM = {kat_toplam:,.2f} TL[/color][/b]", markup=True, 
                                size_hint_y=None, height=dp(30), halign='right', valign='middle', font_size='12sp')
            lbl_kat_top.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
            self.liste_icerik.add_widget(lbl_kat_top)
            genel_toplam_degeri += kat_toplam

        self.lbl_genel_toplam.text = f" GENEL TOPLAM: {genel_toplam_degeri:,.2f} TL"
        self.lbl_genel_toplam.halign = 'left'
        self.lbl_genel_toplam.valign = 'middle'
        self.lbl_genel_toplam.bind(size=lambda s, w: setattr(s, 'text_size', s.size))

    def satir_secildi(self, aktif, fb_id):
        if aktif: self.secili_satir_id = fb_id
        elif self.secili_satir_id == fb_id: self.secili_satir_id = None

    def veriyi_sil_onay(self, *args):
        if not self.secili_satir_id: return
        url = f"{self.base_url.rstrip('/')}/{self.isletme}/giderler/{self.secili_satir_id}.json"
        try:
            requests.delete(url, timeout=10)
            self.verileri_yukle()
        except: pass

    def satiri_duzenle_penceresi(self, *args):
        if not self.secili_satir_id or not GiderSatiri: return
        gider = self.bulut_verisi.get(self.secili_satir_id)
        ana_motor = AMDAccounting()
        icerik = ana_motor.build()
        ana_motor.liste.clear_widgets()
        yeni_satir = GiderSatiri(mevcut_turler=ana_motor.gider_turleri)
        yeni_satir.btn_takvim.text = gider.get("tarih", "")
        yeni_satir.tur_in.text = gider.get("tur", "")
        yeni_satir.tutar.text = str(gider.get("tutar", ""))
        yeni_satir.birim.text = gider.get("birim", "TL")
        ana_motor.liste.add_widget(yeni_satir)
        ana_motor.btn_kaydet.text = "GÜNCELLE"
        ana_motor.btn_kaydet.unbind(on_release=ana_motor.verileri_gonder)
        ana_motor.btn_kaydet.bind(on_release=lambda x: self.firebase_guncelle(ana_motor, yeni_satir))
        self.edit_popup = Popup(title="GİDER DÜZENLE", content=icerik, size_hint=(0.95, 0.9))
        self.edit_popup.open()

    def firebase_guncelle(self, motor, satir):
        yeni_veri = {
            "tarih": satir.btn_takvim.text,
            "tur": satir.tur_in.text.strip().upper(),
            "tutar": satir.tutar.text.strip(),
            "birim": satir.birim.text,
            "isletme": self.isletme,
            "vakit": datetime.now().strftime("%H:%M")
        }
        url = f"{self.base_url.rstrip('/')}/{self.isletme}/giderler/{self.secili_satir_id}.json"
        try:
            requests.put(url, json=yeni_veri, timeout=10)
            self.edit_popup.dismiss()
            self.verileri_yukle()
        except: pass

    def takvim_ac(self, instance):
        if ModernTakvimPopup: 
            p = ModernTakvimPopup(instance)
            p.bind(on_dismiss=lambda x: self.verileri_yukle())
            p.open()

    def kapat(self, *args):
        from kivy.core.window import Window
        for c in Window.children[:]:
            if isinstance(c, Popup): c.dismiss()

def ekrani_olustur():
    return GiderDuzenleFormu()
