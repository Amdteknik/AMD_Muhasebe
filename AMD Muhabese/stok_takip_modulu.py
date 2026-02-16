import os
import requests
import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.metrics import dp

class YuvarlakRenk(Widget):
    def __init__(self, renk_hex, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = ("18dp", "18dp")
        with self.canvas:
            Color(*self.hex_to_rgb(renk_hex))
            self.dot = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def hex_to_rgb(self, h):
        h = h.lstrip('#')
        if len(h) == 6:
            return [int(h[i:i+2], 16)/255.0 for i in (0, 2, 4)] + [1]
        return [0.5, 0.5, 0.5, 1] # Hata durumunda gri döner

    def _update(self, *args):
        self.dot.pos = self.pos
        self.dot.size = self.size

# --- GÖRSEL BİLEŞENLER ---
class RenkKutusuMini(BoxLayout):
    def __init__(self, isim, hex_kod, secili_gelsin=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = ("42dp", "60dp")
        self.renk_adi = isim
        self.renk_hex = hex_kod
        
        self.cizim = Widget(size_hint_y=0.7)
        with self.cizim.canvas:
            Color(*self.hex_to_rgb(hex_kod))
            self.rect = Rectangle(pos=self.cizim.pos, size=self.cizim.size)
        self.cizim.bind(pos=self._update, size=self._update)
        
        # Checkbox'ı oluştur
        self.secici = CheckBox(active=secili_gelsin, size_hint=(None, None), size=("20dp", "20dp"))
        self.add_widget(self.cizim)
        self.add_widget(Label(text=isim, font_size='7sp', size_hint_y=0.3, shorten=True))
        
        # Checkbox'ı cizim widget'ına değil, ana kutuya ekleyip üstte yüzdürebiliriz 
        # veya cizim içinde update ile tutabiliriz.
        self.cizim.add_widget(self.secici)

    def hex_to_rgb(self, h):
        try:
            h = h.lstrip('#')
            return [int(h[i:i+2], 16)/255.0 for i in (0, 2, 4)] + [1]
        except: return [0.5, 0.5, 0.5, 1]

    def _update(self, inst, val):
        self.rect.pos = inst.pos
        self.rect.size = inst.size
        # Tiki kutunun tam ortasına sabitle
        self.secici.center = inst.center


class StokTakipIcerik(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10 
        self.spacing = 10
        
        self.base_url = os.environ.get("FIREBASE_URL", "")
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        
        # --- KATALOG AYNI KALIYOR ---
        self.katalog = {
            "Siyah": "#000000", "Beyaz": "#FFFFFF", "Kırmızı": "#FF0000", "Mavi": "#0000FF",
            "Yeşil": "#008000", "Sarı": "#FFFF00", "Kraft": "#BDA58E", "Kraft Koyu": "#8B7355",
            "Kraft Açık": "#D2B48C", "Pembe": "#FFC0CB", "Şeker Pembe": "#FF69B4", "Turuncu": "#FFA500",
            "Gri": "#808080", "Gümüş": "#C0C0C0", "Altın": "#FFD700", "Bakır": "#B87333",
            "Lacivert": "#000080", "Turkuaz": "#40E0D0", "Antrasit": "#2F4F4F", "Bordo": "#800000",
            "Mor": "#800080", "Lila": "#C8A2C8", "Mürdüm": "#4E0B2F", "Vişne": "#800020",
            "Bej": "#F5F5DC", "Ekru": "#F5F5F5", "Şampanya": "#F7E7CE", "Haki": "#BDB76B",
            "Zeytin": "#808000", "Petrol": "#005F6B", "Saks": "#4169E1", "Bebek Mavi": "#89CFF0",
            "Mint": "#98FF98", "Fıstık": "#93C572", "Çimen": "#3CB371", "Hardal": "#E1AD01",
            "Kiremit": "#B22222", "Kahve": "#8B4513", "Taba": "#A52A2A", "Somon": "#FA8072",
            "Mercan": "#FF7F50", "Şeftali": "#FFDAB9", "Limon": "#FFF700", "Fuşya": "#FF00FF",
            "Gül": "#FF66CC", "Lavanta": "#E6E6FA", "Cam Göbeği": "#00FFFF", "Gece Mavisi": "#191970",
            "Toprak": "#A0522D", "Duman": "#696969", "İnci": "#F0EAD6"
        }

        # --- ÜST YAPI (3 Sütunlu Düzen) ---
        ust = BoxLayout(size_hint_y=0.80, spacing=20) # Ara boşluğu biraz daralttık
        
        # SOL: TÜM RENKLER
        sol_box = BoxLayout(orientation='vertical', spacing=5)
        sol_box.add_widget(Label(text="TÜM RENKLER", bold=True, size_hint_y=None, height='25dp', color=(0.2, 0.7, 1, 1)))
        self.sv_tum = ScrollView(do_scroll_x=False)
        # COLS=3 yapıldı
        self.grid_tum = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=5) 
        self.grid_tum.bind(minimum_height=self.grid_tum.setter('height'))
        self.sv_tum.add_widget(self.grid_tum)
        sol_box.add_widget(self.sv_tum)
        
        btn_fav = Button(text="Favorilere Ekle >>", size_hint_y=None, height='32dp', background_color=(0.1, 0.4, 0.6, 1))
        btn_fav.bind(on_release=self.favori_ekle)
        sol_box.add_widget(btn_fav)

        # SAĞ: FAVORİLERİM
        sag_box = BoxLayout(orientation='vertical', spacing=5)
        sag_box.add_widget(Label(text="FAVORİLERİM", bold=True, size_hint_y=None, height='25dp', color=(0.1, 0.8, 0.4, 1)))
        self.sv_fav = ScrollView(do_scroll_x=False)
        # COLS=3 yapıldı
        self.grid_fav = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=5) 
        self.grid_fav.bind(minimum_height=self.grid_fav.setter('height'))
        self.sv_fav.add_widget(self.grid_fav)
        sag_box.add_widget(self.sv_fav)

        # Alt Satırlar (Inputlar)
        ekstra_satir = BoxLayout(size_hint_y=None, height='35dp', spacing=3)
        self.txt_ekstra = TextInput(hint_text="Ekstra Renk...", multiline=False, font_size='11sp')
        
        btn_ekle = Button(text="Ekle", size_hint_x=0.25)
        btn_ekle.bind(on_release=self.ekstra_renk_ekle) # İsmi senin kodunla eşitledim (Bozukluk gitti)
        
        btn_sil = Button(text="Sil", size_hint_x=0.25, background_color=(0.7, 0.2, 0.2, 1))
        btn_sil.bind(on_release=self.favoriden_sil)
        
        ekstra_satir.add_widget(self.txt_ekstra); ekstra_satir.add_widget(btn_ekle); ekstra_satir.add_widget(btn_sil)
        sag_box.add_widget(ekstra_satir)
        
        btn_list = Button(text="Stok Listesine Gönder", size_hint_y=None, height='32dp', background_color=(0.1, 0.5, 0.3, 1))
        btn_list.bind(on_release=self.stok_listesine_gonder)
        sag_box.add_widget(btn_list)

        ust.add_widget(sol_box); ust.add_widget(sag_box)
        self.add_widget(ust)

        # ... (Alt liste ve final butonları senin orijinal kodundakiyle aynı) ...
        # ... (Firebase fonksiyonları ve satir_ekle senin kodunla aynı kalsın) ...
        # ALT LİSTE
        self.grid_stok = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.grid_stok.bind(minimum_height=self.grid_stok.setter('height'))
        sv_stok = ScrollView()
        sv_stok.add_widget(self.grid_stok)
        self.add_widget(sv_stok)

    # FİNAL BUTONLAR (3 Butonlu Yeni Düzen)
        f_btns = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        
        self.btn_save = Button(text="KAYDET", background_color=(0.1, 0.6, 0.2, 1), bold=True)
        self.btn_save.bind(on_release=self.firebase_kaydet)
        
        btn_secileni_kaldir = Button(text="SEÇİLENİ KALDIR", background_color=(0.8, 0.4, 0, 1), bold=True)
        btn_secileni_kaldir.bind(on_release=self.silme_onay_popup) # Onay popup'ına bağladık
        
        self.btn_kapat = Button(text="KAPAT", background_color=(0.6, 0.1, 0.1, 1), size_hint_x=0.4)
        
        f_btns.add_widget(self.btn_save)
        f_btns.add_widget(btn_secileni_kaldir)
        f_btns.add_widget(self.btn_kapat)
        self.add_widget(f_btns)
        Clock.schedule_once(self.verileri_yukle, 0.2)

    def silme_onay_popup(self, *args):
        # Seçili var mı kontrol et
        secili_var = any(getattr(row, 'cb_sil', None).active for row in self.grid_stok.children if hasattr(row, 'cb_sil'))
        if not secili_var: return # Seçili yoksa bir şey yapma

        icerik = BoxLayout(orientation='vertical', padding=10, spacing=10)
        icerik.add_widget(Label(text="Seçili renkler stok listesinden\ntemelli kaldırılacak.\nEmin misiniz?"))
        
        btns = BoxLayout(spacing=10, size_hint_y=None, height='40dp')
        btn_evet = Button(text="EVET", background_color=(0.8, 0.2, 0.2, 1))
        btn_hayir = Button(text="HAYIR")
        
        btns.add_widget(btn_evet); btns.add_widget(btn_hayir)
        icerik.add_widget(btns)
        
        popup = Popup(title="DİKKAT", content=icerik, size_hint=(0.6, 0.4))
        btn_hayir.bind(on_release=popup.dismiss)
        btn_evet.bind(on_release=lambda x: [self.secilenleri_listeden_temizle(), popup.dismiss()])
        popup.open()

    def secilenleri_listeden_temizle(self):
        # Sadece Checkbox'ı işaretli olanları kaldır
        silinecekler = [row for row in self.grid_stok.children if hasattr(row, 'cb_sil') and row.cb_sil.active]
        for row in silinecekler:
            self.grid_stok.remove_widget(row)

    def verileri_yukle(self, *args):
        if not self.base_url: return
        def run():
            try:
                res = requests.get(f"{self.base_url}/{self.isletme}.json", timeout=10).json()
                if res: Clock.schedule_once(lambda dt: self.arayuzu_yenile(res), 0)
            except: pass
        threading.Thread(target=run, daemon=True).start()

    def arayuzu_yenile(self, data):
        ayarlar = data.get("ayarlar", {})
        stoklar = data.get("stok", {})
        havuz_tikleri = ayarlar.get("havuz_tikleri", [])
        favoriler = ayarlar.get("favoriler", [])

        # 1. HAVUZ (Tüm Renkler)
        self.grid_tum.clear_widgets()
        for isim, hex_kod in sorted(self.katalog.items()):
            # Havuzda tikli olanları işaretle
            self.grid_tum.add_widget(RenkKutusuMini(isim, hex_kod, secili_gelsin=(isim in havuz_tikleri)))

        # 2. FAVORİLER (Otomatik Tik Kontrolü)
        self.grid_fav.clear_widgets()
        for isim in favoriler:
            hex_kod = self.katalog.get(isim, "#7F8C8D")
            
            # KRİTİK NOKTA: Eğer bu renk 'stoklar' içinde varsa ve miktarı 0 değilse tikli gelsin
            stokta_var_mi = False
            if isim in stoklar and str(stoklar[isim]) not in ["0", "", "0.0"]:
                stokta_var_mi = True
                
            self.grid_fav.add_widget(RenkKutusuMini(isim, hex_kod, secili_gelsin=stokta_var_mi))

        # 3. STOK LİSTESİ
        self.grid_stok.clear_widgets()
        for isim, miktar in stoklar.items():
            if str(miktar) not in ["0", "", "0.0"]:
                hex_kod = self.katalog.get(isim, "#7F8C8D")
                self.yeni_stok_satiri(isim, hex_kod, miktar)

    def favori_ekle(self, *args):
        for k in self.grid_tum.children:
            if k.secici.active:
                # Eğer zaten favorilerde yoksa ekle
                if not any(f.renk_adi == k.renk_adi for f in self.grid_fav.children):
                    # Favoriye eklerken tiki pasif (False) başlatıyoruz ki favoride yeni bir seçim yapılabilsin
                    self.grid_fav.add_widget(RenkKutusuMini(k.renk_adi, k.renk_hex, secili_gelsin=False))
                # ÖNEMLİ: k.secici.active = True satırına dokunmuyoruz, havuzda tikli kalıyor.

    def favoriden_sil(self, *args):
        silinecekler = [k for k in self.grid_fav.children if k.secici.active]
        for k in silinecekler:
            self.grid_fav.remove_widget(k)

    def ekstra_renk_ekle(self, *args):
        isim = self.txt_ekstra.text.strip()
        if isim:
            # Ekstra renk havuzda yoksa bile favoriye ekle
            self.grid_fav.add_widget(RenkKutusuMini(isim, "#7F8C8D", secili_gelsin=False))
            self.txt_ekstra.text = ""

    def stok_listesine_gonder(self, *args):
        for k in self.grid_fav.children:
            if k.secici.active:
                self.yeni_stok_satiri(k.renk_adi, k.renk_hex)


    def yeni_stok_satiri(self, isim, hex_kod, miktar="0"):
        if any(hasattr(c, 'renk_key') and c.renk_key == isim for c in self.grid_stok.children): return
        
        row = BoxLayout(size_hint_y=None, height='40dp', spacing=10, padding=[5,0])
        row.renk_key = isim
        
        with row.canvas.before:
            row.bg_color = Color(0, 0, 0, 0)
            row.rect = Rectangle(pos=row.pos, size=row.size)
        
        row.bind(pos=lambda inst, v: setattr(inst.rect, 'pos', v), 
                 size=lambda inst, v: setattr(inst.rect, 'size', v))
        
        cb_sil = CheckBox(size_hint_x=None, width=dp(30))
        row.cb_sil = cb_sil
        
        sol = BoxLayout(size_hint_x=0.5, spacing=10, padding=[5,5])
        sol.add_widget(YuvarlakRenk(hex_kod))
        sol.add_widget(Label(text=isim, halign='left'))
        
        # --- DÜZELTİLMİŞ INPUT VE ODAKLANMA MANTIĞI ---
        ti = TextInput(
            text=str(miktar), 
            multiline=False, 
            input_filter='float', 
            halign='center', 
            size_hint_x=0.3,
            hint_text="0",
            hint_text_color=(0.5, 0.5, 0.5, 1)
        )
        
        # Tıklandığında 0'ı temizleyen fonksiyon
        def on_focus_clear(instance, value):
            if value: # Eğer kutuya tıklandıysa (odaklandıysa)
                if instance.text == "0" or instance.text == "0.0":
                    instance.text = "" # İçini boşalt

        ti.bind(focus=on_focus_clear)

        # Satırı sönükleştiren fonksiyon
        def satir_gorunumu_guncelle(instance, value):
            try:
                # Boş metni 0 kabul et
                sayi = float(value if value else 0)
                if sayi == 0:
                    row.opacity = 0.4 # Satırı %60 sönükleştirir
                    row.bg_color.rgba = (0.8, 0.1, 0.1, 0.1) # Hafif kırmızı uyarı
                else:
                    row.opacity = 1.0 # Satırı tamamen görünür yapar
                    row.bg_color.rgba = (0, 0, 0, 0) # Normal şeffaf arka plan
            except:
                row.opacity = 1.0

        ti.bind(text=satir_gorunumu_guncelle)
        # İlk yüklemede durumu kontrol et
        Clock.schedule_once(lambda dt: satir_gorunumu_guncelle(ti, miktar), 0)
        
        row.add_widget(cb_sil)
        row.add_widget(sol)
        row.add_widget(ti)
        row.add_widget(Label(text="kg", size_hint_x=0.1))
        
        self.grid_stok.add_widget(row)


    def firebase_kaydet(self, instance):
        stok_verisi = {}
        for row in self.grid_stok.children:
            isim = getattr(row, 'renk_key', None)
            if isim:
                for child in row.children:
                    if isinstance(child, TextInput):
                        val = child.text.strip().replace(",", ".")
                        # Artık 0 olsa bile listeye ekliyoruz, sadece boşsa (hata varsa) geçiyoruz
                        try:
                            stok_verisi[isim] = val if val else "0"
                        except: pass

        paket = {
            "stok": stok_verisi,
            "ayarlar": {
                "havuz_tikleri": [k.renk_adi for k in self.grid_tum.children if k.secici.active],
                "favoriler": [k.renk_adi for k in self.grid_fav.children]
            }
        }
        # ... geri kalan threading ve requests kısımları aynı ...
        def run():
            try:
                requests.patch(f"{self.base_url}/{self.isletme}.json", json=paket, timeout=10)
            except: pass
        threading.Thread(target=run, daemon=True).start()
        instance.text = "GÜNCELLENDİ ✔"
        Clock.schedule_once(lambda dt: setattr(instance, 'text', "KAYDET"), 2)



def ekrani_olustur():
    icerik = StokTakipIcerik()
    p = Popup(title="GELİŞMİŞ STOK VE RENK YÖNETİMİ", content=icerik, size_hint=(0.98, 0.98))
    icerik.btn_kapat.bind(on_release=p.dismiss)
    p.open()
    return Widget()