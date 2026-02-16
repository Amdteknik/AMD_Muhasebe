import os
import requests
import threading
from datetime import datetime, timedelta
from calendar import monthrange
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# --- 1. GERÇEK TAKVİM SINIFI (Açılmama Sorunu Giderildi) ---
class GercekTakvim(BoxLayout):
    def __init__(self, secim_yapildi_callback, kapat_callback, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)
        self.callback = secim_yapildi_callback
        self.kapat_callback = kapat_callback
        self.simdi = datetime.now()
        self.yil, self.ay = self.simdi.year, self.simdi.month
        self.aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        with self.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.ciz()

    def ciz(self):
        self.clear_widgets()
        ust = BoxLayout(size_hint_y=None, height=60)
        ust.add_widget(Button(text="<", size_hint_x=0.2, on_release=self.onceki_ay))
        ust.add_widget(Label(text=f"{self.aylar[self.ay-1]} {self.yil}", bold=True, color=(0,0,0,1), size_hint_x=0.6))
        ust.add_widget(Button(text=">", size_hint_x=0.2, on_release=self.sonraki_ay))
        self.add_widget(ust)
        
        gunler = GridLayout(cols=7, size_hint_y=None, height=60)
        for g in ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]:
            gunler.add_widget(Label(text=g, color=(0.4, 0.4, 0.4, 1), font_size='11sp'))
        self.add_widget(gunler)
        
        self.sayilar_grid = GridLayout(cols=7, spacing=2)
        ilk_gun, toplam_gun = monthrange(self.yil, self.ay)
        for _ in range(ilk_gun): self.sayilar_grid.add_widget(Label())
        for gun in range(1, toplam_gun + 1):
            b = Button(text=str(gun), background_normal='', background_color=(1, 1, 1, 1), color=(0, 0, 0, 1))
            b.bind(on_release=lambda x, g=gun: self.callback(f"{g:02d}.{self.ay:02d}.{self.yil}"))
            self.sayilar_grid.add_widget(b)
        self.add_widget(self.sayilar_grid)
        
        alt = AnchorLayout(anchor_x='right', size_hint_y=None, height=40)
        btn = Button(text="KAPAT", size_hint=(None, None), size=(90, 32), on_release=self.kapat_callback)
        alt.add_widget(btn)
        self.add_widget(alt)

    def _update_rect(self, i, v): self.rect.pos = i.pos; self.rect.size = i.size
    def onceki_ay(self, *a):
        self.ay -= 1
        if self.ay == 0: self.ay = 12; self.yil -= 1
        self.ciz()
    def sonraki_ay(self, *a):
        self.ay += 1
        if self.ay == 13: self.ay = 1; self.yil += 1
        self.ciz()

# --- 2. ANA PANEL ---
class KDVAnalizPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.title = f"{self.isletme} KDV ANALİZ"
        self.size_hint = (0.98, 0.95)

        self.bas_tarih_str = "01.01.2026"
        self.bit_tarih_str = datetime.now().strftime("%d.%m.%Y")

        self.ana_icerik = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Üst Panel (Takvimler Solda, Süzgeç Sağda)
        ust_panel = BoxLayout(size_hint_y=None, height=100)
        
        period_sol = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=5)
        period_sol.add_widget(Label(text="[color=aaaaaa]Period Belirle[/color]", markup=True, font_size='12sp', halign='left', size_hint_y=None, height=20))
        btn_box = BoxLayout(spacing=8)
        self.btn_bas = Button(text=f"BAŞ\n{self.bas_tarih_str}", halign='center', font_size='10sp', background_color=(0.2, 0.2, 0.2, 1))
        self.btn_bit = Button(text=f"BİTİŞ\n{self.bit_tarih_str}", halign='center', font_size='10sp', background_color=(0.2, 0.2, 0.2, 1))
        self.btn_bas.bind(on_release=lambda x: self.takvimi_goster("bas"))
        self.btn_bit.bind(on_release=lambda x: self.takvimi_goster("bit"))
        btn_box.add_widget(self.btn_bas); btn_box.add_widget(self.btn_bit)
        period_sol.add_widget(btn_box)
        
        suzec_sag = AnchorLayout(anchor_x='right', anchor_y='bottom', size_hint_x=0.5)
        self.filtre_btn = Button(text='HIZLI SÜZGEÇ', size_hint=(None, None), size=(250, 45), background_color=(0.1, 0.4, 0.6, 1))
        self.dropdown = DropDown()
        for s in ['Son 1 Ay', 'Son 3 Ay', 'Son 6 Ay', '2026 HEPSİ']:
            btn = Button(text=s, size_hint_y=None, height=60)
            btn.bind(on_release=lambda b: self.dropdown.select(b.text))
            self.dropdown.add_widget(btn)
        self.filtre_btn.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=self.hizli_filtre_uygula)
        suzec_sag.add_widget(self.filtre_btn)

        ust_panel.add_widget(period_sol); ust_panel.add_widget(suzec_sag)
        self.ana_icerik.add_widget(ust_panel)

        # Tablo Başlığı
        baslik_bg = BoxLayout(size_hint_y=None, height=60)
        with baslik_bg.canvas.before:
            Color(0.12, 0.12, 0.12, 1); self.rect_b = Rectangle(pos=baslik_bg.pos, size=baslik_bg.size)
        baslik_bg.bind(pos=self._up_rect, size=self._up_rect)
        self.ana_icerik.add_widget(baslik_bg)
        # Başlık Yazıları
        l1 = Label(text="[b]ANALİZ / BİLDİRİ KALEMİ[/b]", markup=True, size_hint_x=0.7, halign='left', padding=[15,0])
        l1.bind(size=lambda i, v: setattr(i, 'text_size', (i.width, None)))
        l2 = Label(text="[b]TUTAR (TL)[/b]", markup=True, size_hint_x=0.3, halign='left')
        l2.bind(size=lambda i, v: setattr(i, 'text_size', (i.width, None)))
        baslik_bg.add_widget(l1); baslik_bg.add_widget(l2)

        # Liste
        self.tablo = GridLayout(cols=1, spacing=1, size_hint_y=None)
        self.tablo.bind(minimum_height=self.tablo.setter('height'))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.tablo)
        self.ana_icerik.add_widget(scroll)

        # Kapat Butonu Alanı
        alt_buton_alani = AnchorLayout(anchor_x='right', size_hint_y=None, height=60, padding=[0, 0, 10, 5])
        btn_kapat = Button(
            text="KAPAT", 
            size_hint=(None, None), 
            size=(120, 40), 
            background_color=(0.7, 0.1, 0.1, 1), 
            bold=True,
            on_release=self.dismiss
        )
        alt_buton_alani.add_widget(btn_kapat)
        self.ana_icerik.add_widget(alt_buton_alani)

        self.content = self.ana_icerik # Bu satır zaten vardı, bunun üstüne eklemiş oldun
        self.verileri_tazele()

    def _up_rect(self, i, v): self.rect_b.pos = i.pos; self.rect_b.size = i.size

    def takvimi_goster(self, hedef):
        self.aktif_hedef = hedef
        self.t_popup = Popup(title="Tarih Seç", size_hint=(0.85, 0.8))
        self.t_popup.content = GercekTakvim(secim_yapildi_callback=self.tarih_secildi, kapat_callback=self.t_popup.dismiss)
        self.t_popup.open()

    def tarih_secildi(self, tarih):
        if self.aktif_hedef == "bas": self.btn_bas.text = f"BAŞ\n{tarih}"
        else: self.btn_bit.text = f"BİTİŞ\n{tarih}"
        self.t_popup.dismiss()
        self.verileri_tazele()

    def hizli_filtre_uygula(self, instance, secim):
        bugun = datetime.now()
        if '1 Ay' in secim: bas = bugun - timedelta(days=30)
        elif '3 Ay' in secim: bas = bugun - timedelta(days=90)
        elif '6 Ay' in secim: bas = bugun - timedelta(days=180)
        else: bas = datetime(2026, 1, 1)
        self.btn_bas.text = f"BAŞ\n{bas.strftime('%d.%m.%Y')}"
        self.btn_bit.text = f"BİTİŞ\n{bugun.strftime('%d.%m.%Y')}"
        self.verileri_tazele()

    def verileri_tazele(self, *args):
        self.tablo.clear_widgets()
        self.satir_ekle("VERİLER ANALİZ EDİLİYOR...", "Lütfen Bekleyin")
        threading.Thread(target=self.firebase_analiz, daemon=True).start()

    def firebase_analiz(self):
        s_kdv, a_kdv = 0.0, 0.0
        try:
            t1 = datetime.strptime(self.btn_bas.text.split("\n")[-1], "%d.%m.%Y")
            t2 = datetime.strptime(self.btn_bit.text.split("\n")[-1], "%d.%m.%Y")
            
            for p, tip in [("satis_faturalari", "s"), ("alis_faturalari", "a")]:
                r = requests.get(f"{self.url}/{self.isletme}/{p}.json", timeout=10).json()
                if not r: continue
                for firma, fats in r.items():
                    if not isinstance(fats, dict): continue
                    for f_id, d in fats.items():
                        # TARİH (İ harfi) veya TARIH kontrolü
                        t_str = d.get("TARİH") or d.get("TARIH") or ""
                        try:
                            f_dt = datetime.strptime(t_str, "%d.%m.%Y")
                            if t1 <= f_dt <= t2:
                                tutar = float(str(d.get("TOPLAM", 0)).replace("TL","").replace(".","").replace(",",".").strip())
                                oran = float(d.get("KDV_ORANI", 20))
                                kdv = tutar - (tutar / (1 + (oran/100)))
                                if tip == "s": s_kdv += kdv
                                else: a_kdv += kdv
                        except: continue
            Clock.schedule_once(lambda dt: self.sonuc_goster(s_kdv, a_kdv), 0)
        except: Clock.schedule_once(lambda dt: self.satir_ekle("HATA", "Bağlantı Sorunu"), 0)

    def sonuc_goster(self, s, a):
        self.tablo.clear_widgets()
        def fmt(v): return "{:,.2f} TL".format(v).replace(",", "X").replace(".", ",").replace("X", ".")
        self.satir_ekle("TOPLAM SATIŞ KDV", fmt(s))
        self.satir_ekle("TOPLAM ALIŞ KDV", fmt(a))
        f = s - a
        if f < 0: self.satir_ekle("DEVREDEN KDV", fmt(abs(f)), (0.3, 1, 0.3, 1), True)
        else: self.satir_ekle("ÖDENECEK KDV", fmt(f), (1, 0.3, 0.3, 1), True)

    def satir_ekle(self, aciklama, tutar, renk=(1,1,1,1), bold=False):
        row = BoxLayout(size_hint_y=None, height=60)
        l1 = Label(text=aciklama, size_hint_x=0.7, halign='left', padding=[15,0], bold=bold)
        l1.bind(size=lambda i, v: setattr(i, 'text_size', (i.width, None)))
        l2 = Label(text=tutar, size_hint_x=0.3, halign='left', color=renk, bold=bold)
        l2.bind(size=lambda i, v: setattr(i, 'text_size', (i.width, None)))
        row.add_widget(l1); row.add_widget(l2)
        self.tablo.add_widget(row)

def ekrani_olustur(p=None):
    return KDVAnalizPopup()