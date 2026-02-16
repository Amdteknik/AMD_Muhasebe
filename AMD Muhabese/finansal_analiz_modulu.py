from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
import os
import requests
import threading
import importlib
from datetime import datetime

# --- MODÜL ENTEGRASYONU ---
try:
    from gider_kayit import ModernTakvimPopup
except ImportError:
    ModernTakvimPopup = None

class TiklanabilirKart(ButtonBehavior, BoxLayout):
    def __init__(self, baslik, deger, renk, modul_adi, callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.modul_adi = modul_adi
        self.callback = callback
        with self.canvas.before:
            Color(*renk)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            self.bind(pos=self._update_rect, size=self._update_rect)
        self.add_widget(Label(text=baslik, font_size='11sp', color=(0.9, 0.9, 0.9, 1), size_hint_y=0.4))
        self.lbl_deger = Label(text=deger, font_size='12sp', bold=True, size_hint_y=0.6)
        self.add_widget(self.lbl_deger)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_release(self):
        if self.callback:
            self.callback(self.children[1].text, self.lbl_deger.text)

class FinansalAnaliz:
    def __init__(self):
        self.popup_nesnesi = None 
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        # Çakılı URL'yi sildik, sistemden çekiyoruz:
        self.url = os.environ.get("FIREBASE_URL", "").strip("/")
        
        self.kisa_aylar = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        self.aylik_gelirler = [0.0] * 12; self.aylik_giderler = [0.0] * 12
        self.secili_yil = datetime.now().year

    def ekrani_olustur(self, p_nesnesi=None):
        self.popup_nesnesi = p_nesnesi
        self.ana_katman = AnchorLayout()
        self.ana_duzen = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        
        ust_bar = BoxLayout(size_hint_y=None, height=dp(50))
        ust_bar.add_widget(Label(text=f"{self.isletme} ANALİZ PANELİ", bold=True, font_size='18sp', color=(0.2, 0.7, 1, 1)))
        self.ana_duzen.add_widget(ust_bar)

        tarih_bar = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(5))
        self.btn_t1 = Button(text="01.01.2026", background_color=(0.3, 0.4, 0.5, 1))
        self.btn_t2 = Button(text=datetime.now().strftime("%d.%m.%Y"), background_color=(0.3, 0.4, 0.5, 1))
        self.btn_t1.bind(on_release=self.takvim_ac_modern)
        self.btn_t2.bind(on_release=self.takvim_ac_modern)
        btn_gncl = Button(text="YÜKLE", size_hint_x=0.5, bold=True, background_color=(0.1, 0.6, 0.3, 1))
        btn_gncl.bind(on_release=self.verileri_tazele)
        tarih_bar.add_widget(self.btn_t1); tarih_bar.add_widget(self.btn_t2); tarih_bar.add_widget(btn_gncl)
        self.ana_duzen.add_widget(tarih_bar)

        self.kart_izgara = GridLayout(cols=3, spacing=dp(12), size_hint_y=None, height=dp(220))
        kart_yapisi = [
            ("TOPLAM GELİR", "gelir_detay", (0.1, 0.4, 0.1, 1)), ("TOPLAM GİDER", "gider_detay", (0.5, 0.1, 0.1, 1)),
            ("KDV (%20)", "kdv_detay", (0.6, 0.4, 0.1, 1)), ("NET KÂR", "kar_detay", (0.1, 0.3, 0.5, 1)),
            ("KÂR MARJI", "oran_detay", (0.4, 0.2, 0.5, 1)), ("VERİMLİLİK", "verim_detay", (0.3, 0.3, 0.3, 1))
        ]
        self.kart_objeleri = {}
        for baslik, mod, renk in kart_yapisi:
            k = TiklanabilirKart(baslik, "...", renk, mod, self.yonlendir)
            self.kart_objeleri[baslik] = k
            self.kart_izgara.add_widget(k)
        self.ana_duzen.add_widget(self.kart_izgara)

        self.grafik_alani = BoxLayout(orientation='vertical', padding=[0, dp(20), 0, dp(10)])
        self.ana_duzen.add_widget(self.grafik_alani)

        alt_bar = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(10))
        self.sp_yil = Spinner(text=str(self.secili_yil), values=[str(i) for i in range(2024, 2031)], size_hint_x=0.4)
        self.sp_yil.bind(text=self.verileri_tazele)
        alt_bar.add_widget(Label(text="Yıl:", size_hint_x=0.15))
        alt_bar.add_widget(self.sp_yil)
        alt_bar.add_widget(Widget()) 
        self.ana_duzen.add_widget(alt_bar)

        self.ana_katman.add_widget(self.ana_duzen)

        kapat_alan = AnchorLayout(anchor_x='right', anchor_y='bottom', padding=dp(20))
        btn_kapat = Button(text="KAPAT", size_hint=(None, None), size=(dp(100), dp(45)), background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_kapat.bind(on_release=self.popup_kapat)
        kapat_alan.add_widget(btn_kapat)
        self.ana_katman.add_widget(kapat_alan)

        Clock.schedule_once(self.verileri_tazele, 0.5)
        return self.ana_katman

    def para_formatla(self, deger, birim="TL"):
        try:
            # Sayıyı 1.250,50 formatına sokar
            sayi = float(str(deger).replace(",", "."))
            formatli = "{:,.2f}".format(sayi).replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{formatli} {birim}"
        except:
            return f"{deger} {birim}"


    def yonlendir(self, baslik, deger):
        # --- YARDIMCI FORMAT FONKSİYONU ---
        def f(sayi_str, birim_olsun=True):
            try:
                # Sayıdaki noktaları ve birimleri temizle, float'a çevir
                temiz_sayi = float(sayi_str.replace("TL", "").replace("EUR", "").replace("USD", "")
                                  .replace(".", "").replace(",", ".").strip())
                # 1.250.000,00 formatına sok
                formatli = "{:,.2f}".format(temiz_sayi).replace(",", "X").replace(".", ",").replace("X", ".")
                
                if birim_olsun:
                    # Mevcut birimi tespit et (Kartın içindeki metinden al)
                    b = "EUR" if "EUR" in sayi_str else ("USD" if "USD" in sayi_str else "TL")
                    return f"{formatli} {b}"
                return formatli
            except:
                return sayi_str

        # Kartlardaki ham metinleri al
        gelir_ham = self.kart_objeleri["TOPLAM GELİR"].lbl_deger.text
        gider_ham = self.kart_objeleri["TOPLAM GİDER"].lbl_deger.text
        kdv_ham = self.kart_objeleri["KDV (%20)"].lbl_deger.text
        nkar_ham = self.kart_objeleri["NET KÂR"].lbl_deger.text

        # Veriler henüz yüklenmemişse işlem yapma
        if "..." in [gelir_ham, gider_ham]:
            return

        try:
            if baslik == "NET KÂR":
                hesap_detay = f"{f(gelir_ham)} - ({f(gider_ham)} + {f(kdv_ham)})"
                self.detay_popup_goster("NET KÂR", "Gelir - (Gider + KDV)", hesap_detay, f(nkar_ham))

            elif baslik == "KÂR MARJI":
                hesap_detay = f"({f(nkar_ham)} / {f(gelir_ham)}) x 100"
                self.detay_popup_goster("KÂR MARJI", "(Net Kâr / Gelir) x 100", hesap_detay, deger)

            elif baslik == "VERİMLİLİK":
                # %1333.5 gibi gelen metinden sayısal değeri geri alıyoruz
                yuzde_deger = float(deger.replace("%", "").replace(",", "."))
                birim = "EUR" if "EUR" in gelir_ham else ("USD" if "USD" in gelir_ham else "TL")
                
                # Formüle x100 ekledik ki kullanıcı neden % olduğunu anlasın
                hesap_detay = f"({f(gelir_ham)} / {f(gider_ham)}) x 100"
                
                not_txt = (f"[b][size=18sp]Bu işletme, harcadığı her 1 {birim} maliyet\n"
                           f"karşılığında {deger} verimlilik üretmektedir.[/size][/b]")
                
                # İkonun doğru seçilmesi için yuzde_deger'i tekrar katsayıya bölüp gönderiyoruz (13.3 gibi)
                self.detay_popup_goster("VERİMLİLİK", "(Gelir / Gider) x 100", hesap_detay, deger, not_txt, yuzde_deger / 100)

                
            else:
                # GELİR, GİDER veya KDV kartlarına tıklandığında kapanma, detay göster
                self.detay_popup_goster(baslik, "Genel Toplam", 
                                        "Seçili tarih aralığındaki fatura kayıtlarının toplamı.", f(deger))
        except Exception as e:
            print(f"Yönlendirme hatası: {e}")

    def detay_popup_goster(self, baslik, formul, hesap, sonuc, not_txt="", oran=None):
        icerik_ana = AnchorLayout()
        p_vbox = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))        
        lbl_f = Label(text=f"[color=33b5e5]FORMÜL:[/color]\n{formul}", markup=True, halign='left', size_hint_y=None, height=dp(50))
        lbl_h = Label(text=f"[color=aaaaaa]HESAP:[/color]\n{hesap}", markup=True, halign='left', size_hint_y=None, height=dp(50))
        lbl_s = Label(text=f"[b][color=66ff66]SONUÇ: {sonuc}[/color][/b]", markup=True, halign='left', font_size='20sp', size_hint_y=None, height=dp(40))
        
        for lb in [lbl_f, lbl_h, lbl_s]: lb.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        
        p_vbox.add_widget(lbl_f); p_vbox.add_widget(lbl_h); p_vbox.add_widget(lbl_s)

        if not_txt:
            p_vbox.add_widget(Label(text=not_txt, markup=True, halign='left', size_hint_y=None, height=dp(80)))

        # Büyük Resim Alanı
# İkonları Getiren Alan
        if oran is not None:
            img_box = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_y=0.4)
            # Oran 2.0'dan büyükse (Giderin 2 katı kazanç) -> MUTLU
            # Oran 1.0 - 2.0 arası (Zarar yok ama düşük) -> İFADESİZ
            # Oran 1.0'dan küçükse (Zarar) -> ÜZGÜN
            src = "mutlu.png" if oran >= 2.0 else ("ifadesiz.png" if oran >= 1.0 else "uzgun.png")
            
            img_box.add_widget(Image(source=src, size_hint=(None, None), size=(dp(120), dp(120))))
            p_vbox.add_widget(img_box)

            
        p_vbox.add_widget(Widget()) # Boşluk bırak
        icerik_ana.add_widget(p_vbox)

        # Sağ Alt TAMAM Butonu
        btn_box = AnchorLayout(anchor_x='right', anchor_y='bottom', padding=dp(15))
        btn_tamam = Button(text="TAMAM", size_hint=(None, None), size=(dp(90), dp(40)), background_color=(0.2, 0.6, 1, 1), bold=True)
        btn_box.add_widget(btn_tamam)
        icerik_ana.add_widget(btn_box)

        p = Popup(title=f"{baslik} ANALİZİ", content=icerik_ana, size_hint=(0.9, 0.75))
        btn_tamam.bind(on_release=p.dismiss); p.open()

    def arayuzu_guncelle(self, gel, gid, kdv, nkar, marj, verim, agel, agid):
        def f(s): return "{:,.2f} TL".format(s).replace(",", "X").replace(".", ",").replace("X", ".")
        self.kart_objeleri["TOPLAM GELİR"].lbl_deger.text = f(gel)
        self.kart_objeleri["TOPLAM GİDER"].lbl_deger.text = f(gid)
        self.kart_objeleri["KDV (%20)"].lbl_deger.text = f(kdv)
        self.kart_objeleri["NET KÂR"].lbl_deger.text = f(nkar)
        self.kart_objeleri["KÂR MARJI"].lbl_deger.text = f"%{marj:.1f}"
        
        # --- VERİMLİLİK DÜZENLEMESİ ---
        # 13.34 olan katsayıyı %1334 (verimlilik oranı) olarak gösteriyoruz
        yuzde_verim = verim * 100
        self.kart_objeleri["VERİMLİLİK"].lbl_deger.text = f"%{yuzde_verim:.1f}"
        # ------------------------------

        self.aylik_gelirler, self.aylik_giderler = agel, agid; self.sutun_grafik_ciz()


    def takvim_ac_modern(self, instance):
        if ModernTakvimPopup:
            p = ModernTakvimPopup(hedef_buton=instance)
            p.bind(on_dismiss=lambda x: self.verileri_tazele()); p.open()

    def popup_kapat(self, *args):
        p = self.ana_duzen.parent
        while p:
            if isinstance(p, Popup): p.dismiss(); return 
            p = p.parent
        try: self.popup_nesnesi.dismiss()
        except: pass

    def verileri_tazele(self, *args):
        for k in self.kart_objeleri.values(): k.lbl_deger.text = "..."
        threading.Thread(target=self.firebase_sorgula, daemon=True).start()

    def firebase_sorgula(self):
        g_top = 0.0; gi_top = 0.0; a_gel = [0.0]*12; a_gid = [0.0]*12
        yil = int(self.sp_yil.text); t1 = datetime.strptime(self.btn_t1.text, "%d.%m.%Y"); t2 = datetime.strptime(self.btn_t2.text, "%d.%m.%Y")
        def tara(path, is_g):
            nonlocal g_top, gi_top
            try:
                r = requests.get(f"{self.url}/{self.isletme}/{path}.json", timeout=10).json()
                if not r: return
                for f, fats in r.items():
                    for n, d in fats.items():
                        try:
                            dt = datetime.strptime(d.get("TARİH",""), "%d.%m.%Y")
                            v = float(str(d.get("TOPLAM","0")).replace("TL","").replace(".","").replace(",",".").strip())
                            if dt.year == yil:
                                if is_g: a_gel[dt.month-1] += v
                                else: a_gid[dt.month-1] += v
                                if t1 <= dt <= t2:
                                    if is_g: g_top += v
                                    else: gi_top += v
                        except: continue
            except: pass
        tara("satis_faturalari", True); tara("alis_faturalari", False)
        kdv = (g_top - gi_top) * 0.20 if g_top > gi_top else 0.0
        n_kar = g_top - gi_top - kdv; marj = (n_kar/g_top*100) if g_top>0 else 0; verim = (g_top/gi_top) if gi_top>0 else 0
        Clock.schedule_once(lambda x: self.arayuzu_guncelle(g_top, gi_top, kdv, n_kar, marj, verim, a_gel, a_gid), 0)

    def sutun_grafik_ciz(self):
        self.grafik_alani.clear_widgets(); g_box = BoxLayout(spacing=dp(10))
        m_v = max(max(self.aylik_gelirler), max(self.aylik_giderler), 1)
        for i in range(12):
            s_k = BoxLayout(orientation='vertical'); czm = Widget()
            def draw(ins, val, idx=i):
                ins.canvas.clear()
                h = ins.height * 0.9; gh = (self.aylik_gelirler[idx]/m_v)*h; gih = (self.aylik_giderler[idx]/m_v)*h
                with ins.canvas:
                    Color(0.2, 0.6, 0.2, 1); Rectangle(pos=(ins.x + ins.width*0.1, ins.y), size=(ins.width*0.35, gh))
                    Color(0.7, 0.2, 0.2, 1); Rectangle(pos=(ins.x + ins.width*0.55, ins.y), size=(ins.width*0.35, gih))
            czm.bind(pos=draw, size=draw); s_k.add_widget(czm)
            s_k.add_widget(Label(text=self.kisa_aylar[i], font_size='8sp', size_hint_y=None, height=dp(20)))
            g_box.add_widget(s_k)
        self.grafik_alani.add_widget(g_box)

def ekrani_olustur(p=None): return FinansalAnaliz().ekrani_olustur(p)

