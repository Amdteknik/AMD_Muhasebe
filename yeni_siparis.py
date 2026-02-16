import os
import requests
import json
import threading
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.utils import get_color_from_hex
from kivy.uix.anchorlayout import AnchorLayout

def get_firebase_url():
    # URL'yi sistem değişkenlerinden çeker, kod içine gömmez
    return os.environ.get("FIREBASE_URL", "").strip("/")

class SiparisModulu:
    def __init__(self):
        # İşletme ve Bulut Ayarları
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.base_url = get_firebase_url()
        
        # 2026-02-01: Rehber dosyası kalktı, liste buluttan dolacak
        self.musteriler = ["Müşteriler Yükleniyor..."]
        self.gokyuzu_mavisi = (0.3, 0.6, 1, 1)
        
        self.renkler_sozluk = {
            "Siyah": "#000000", "Beyaz": "#FFFFFF", "Kırmızı": "#FF0000", "Kraft": "#BC987E", 
            "Yeşil": "#008000", "Sarı": "#FFFF00", "Pembe": "#FFC0CB", "Mor": "#800080",
            "Turkuaz": "#40E0D0", "Gri": "#808080", "Lacivert": "#000080", "Antrasit": "#2F4F4F",
            "Turuncu": "#FFA500", "Kahve": "#8B4513", "Bordo": "#800000", "Altın": "#FFD700",
            "Gümüş": "#C0C0C0", "Bej": "#F5F5DC", "Lila": "#C8A2C8", "Haki": "#BDB76B",
            "Mercan": "#FF7F50", "Vişne": "#790604", "Hardal": "#E1AD01", "Fıstık": "#93C572", 
            "Mavi": "#0000FF", "Gökyüzü": "#87CEEB", "Zeytin": "#808000", "Şeftali": "#FFDAB9",
            "Eflatun": "#7F00FF", "Petrol": "#005F6B", "Kiremit": "#8A3324", "Platin": "#E5E4E2"
        }        

# Açılışta listeyi buluttan çekmeye başla
        self.musteri_listesini_guncelle()

    def hata_mesaji(self, metin):
        popup = Popup(title="BILGI", size_hint=(0.6, 0.3))
        icerik = BoxLayout(orientation='vertical', padding=10)
        icerik.add_widget(Label(text=metin))
        btn = Button(text="TAMAM", size_hint_y=0.4, background_color=self.gokyuzu_mavisi)
        btn.bind(on_release=popup.dismiss)
        icerik.add_widget(btn)
        popup.content = icerik
        popup.open()

    def format_tl(self, miktar):
        formatted = "{:,.2f}".format(float(miktar))
        return formatted.replace(",", "temp").replace(".", ",").replace("temp", ".") + " TL"

    def musteri_listesini_guncelle(self):
        from kivy.clock import Clock
        
        def fetch():
            try:
                url_base = os.environ.get("FIREBASE_URL", "").strip("/")
                isl = os.environ.get("SECILI_ISLETME", "ONDULA")
                
                if not url_base: return

                # Müşteriler düğümünü çekiyoruz
                url = f"{url_base}/{isl}/musteriler.json"
                res = requests.get(url, timeout=5).json()
                
                yeni_liste = []
                if res and isinstance(res, dict):
                    for k, icerik in res.items():
                        # YÖNTEM 1: İçeride 'veri' anahtarı varsa ve içinde FIRMA: satırı varsa
                        v = icerik.get("veri", "")
                        found_in_text = False
                        if isinstance(v, str) and v.strip():
                            for satir in v.split("\n"):
                                if "FIRMA" in satir.upper():
                                    f_adi = satir.split(":", 1)[1].strip()
                                    if f_adi: 
                                        yeni_liste.append(f_adi)
                                        found_in_text = True
                                        break
                        
                        # YÖNTEM 2: Eğer 'veri' içinde FIRMA yoksa veya 'veri' boşsa 
                        # Direkt düğümün ismini (Key) müşteri adı kabul et
                        if not found_in_text:
                            # Firebase anahtarı 'MERCAN KAGIT' gibi temizse onu al
                            yeni_liste.append(str(k).replace("_", " ")) 
                    
                    self.musteriler = sorted(list(set(yeni_liste)))
                    
                    # Eğer liste hala boşsa kullanıcıya bilgi ver
                    if not self.musteriler:
                        self.musteriler = ["Müşteri Bulunamadı"]
                else:
                    self.musteriler = ["Rehber Boş"]

                Clock.schedule_once(lambda dt: self.spinner_guncelle(), 0)
                
            except Exception as e:
                print(f"Hata: {e}")
                self.musteriler = ["Bağlantı Hatası"]
                Clock.schedule_once(lambda dt: self.spinner_guncelle(), 0)

        threading.Thread(target=fetch, daemon=True).start()

    def spinner_guncelle(self):
        # Spinner mevcutsa listeyi içine bas ve yazıyı düzelt
        if hasattr(self, 'ent_cari'):
            self.ent_cari.values = self.musteriler
            self.ent_cari.text = "Müşteri Seç..."

    def renk_ve_islem_ac(self, hedef_input):
        # Ana kapsayıcı
        ana_kutu = BoxLayout(orientation='vertical', padding=10, spacing=15)
        
        # Üst Kısım: İşlem Seçenekleri
        islem_kutu = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=10)
        chk_k = CheckBox(size_hint_x=None, width=50)
        chk_p = CheckBox(size_hint_x=None, width=50)
        islem_kutu.add_widget(Widget()) 
        islem_kutu.add_widget(chk_k); islem_kutu.add_widget(Label(text="KIRPMA", font_size='16sp', bold=True))
        islem_kutu.add_widget(chk_p); islem_kutu.add_widget(Label(text="PAKETLEME", font_size='16sp', bold=True))
        islem_kutu.add_widget(Widget()) 
        ana_kutu.add_widget(islem_kutu)
        
        # Orta Kısım: Renk Grid (Kaydırılabilir)
        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(cols=4, spacing=10, size_hint_y=None, padding=10)
        grid.bind(minimum_height=grid.setter('height'))
        
        pop = Popup(title="İşlem ve Renk Seçimi", content=ana_kutu, size_hint=(0.98, 0.98))

        def secimi_onayla(renk):
            islem = ""
            if chk_k.active: islem += "[KIRPMA] "
            if chk_p.active: islem += "[PAKETLEME] "
            mevcut = hedef_input.text
            for r in self.renkler_sozluk.keys(): mevcut = mevcut.replace(r, "")
            mevcut = mevcut.replace("[KIRPMA]", "").replace("[PAKETLEME]", "").strip()
            hedef_input.text = f"{islem}{renk} {mevcut}".strip()
            pop.dismiss()

        for isim, hex_kod in self.renkler_sozluk.items():
            b_kutu = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
            btn = Button(background_normal='', background_color=get_color_from_hex(hex_kod), size_hint_y=0.8)
            btn.bind(on_release=lambda x, i=isim: secimi_onayla(i))
            lbl = Label(text=isim, font_size='13sp', size_hint_y=0.2)
            b_kutu.add_widget(btn); b_kutu.add_widget(lbl)
            grid.add_widget(b_kutu)
        
        scroll.add_widget(grid)
        ana_kutu.add_widget(scroll)
        
        # --- SAĞ ALT KÖŞE KAPAT BUTONU TASARIMI ---
        # alt_panel butonu sağa yaslamak için AnchorLayout kullanır
        alt_panel = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        alt_panel.add_widget(Widget()) # Sol tarafı boşlukla doldurur, butonu sağa iter
        
        btn_iptal = Button(
            text="KAPAT", 
            size_hint=(None, None), 
            width=220,  # Buradan genişliği ayarlayabilirsin
            height=60,  # Buradan yüksekliği ayarlayabilirsin
            background_color=(0.7, 0.2, 0.2, 1),
            bold=True
        )
        btn_iptal.bind(on_release=pop.dismiss)
        
        alt_panel.add_widget(btn_iptal)
        ana_kutu.add_widget(alt_panel)
        # ------------------------------------------
        
        pop.open()

    def ortak_form_ac(self, baslik="Sipariş Giriş Formu"):
        # Tüm kutucuklar için standart font (Başlıklarla uyumlu)
        std_font = '12sp'
        
        ana_icerik = BoxLayout(orientation='vertical', padding=10, spacing=10)
        ust = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=80)
        
        # 1. Müşteri Spinner'ı (Numara sorgulama tetikleyicisi bağlandı)
        self.ent_cari = Spinner(text="Müşteri Seç...", values=self.musteriler, size_hint_x=0.4, 
                                background_color=self.gokyuzu_mavisi, font_size=std_font)
        self.ent_cari.bind(text=self.siparis_no_sorgula) # Seçilince numara üretir
        
        # 2. Sipariş No (Artık --- olarak başlar, müşteri seçilince OND260201 olur)
        self.ent_no = TextInput(text="---", size_hint_x=0.3, padding_y=[25, 0], 
                                readonly=True, font_size=std_font, halign='center')
        
        self.ent_tarih = TextInput(text=datetime.now().strftime("%d.%m.%Y"), 
                                   size_hint_x=0.3, padding_y=[25, 0], font_size=std_font, halign='center')
        
        ust.add_widget(self.ent_cari); ust.add_widget(self.ent_no); ust.add_widget(self.ent_tarih)
        ana_icerik.add_widget(ust)

        basliklar = GridLayout(cols=7, size_hint_y=None, height=50, spacing=2)
        h_metin = ["Seç", "Ürün", "Miktar", "Birim", "B.Fiyat", "Toplam", "Tür/Pkt"]
        h_oran = [0.3, 1.5, 0.6, 0.4, 0.7, 0.8, 0.6]

        for m, g in zip(h_metin, h_oran):
            basliklar.add_widget(Button(text=m, background_color=(0.1, 0.1, 0.1, 1), 
                                        disabled=True, font_size='12sp', size_hint_x=g))
        ana_icerik.add_widget(basliklar)

        scroll = ScrollView(size_hint=(1, 0.6))
        self.satir_konu = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.satir_konu.bind(minimum_height=self.satir_konu.setter('height'))
        scroll.add_widget(self.satir_konu)
        ana_icerik.add_widget(scroll)

        self.satir_objeleri = []
        self.ara_lab = Label(text="0,00 TL", font_size=std_font)
        self.isk_inp = TextInput(text="0", input_filter='float', padding_y=[15, 0], halign='center', font_size=std_font)
        self.kdv_oran_inp = TextInput(text="20", input_filter='float', padding_y=[15, 0], halign='center', font_size=std_font, size_hint_x=0.3)
        self.kdv_kontrol = CheckBox(active=True, size_hint_x=None, width=40)
        self.kdv_lab = Label(text="0,00 TL", font_size=std_font)
        self.genel_toplam_lab = Label(text="0,00 TL", bold=True, color=(0,1,0,1), font_size='14sp')

        def hesapla(*args):
            ara_toplam = 0.0
            for s in self.satir_objeleri:
                try:
                    fv = float(s['f'].text.replace(",", ".") or 0)
                    mv = float(s['m'].text.replace(",", ".") or 0)
                    top = fv * mv
                    s['t_lab'].text = self.format_tl(top)
                    ara_toplam += top
                    p_tip = float(s['p_sec'].text)
                    s['p_not'].text = f"{round(mv/p_tip, 1)} Pkt" if mv > 0 else "-"
                except: continue
            
            self.ara_lab.text = self.format_tl(ara_toplam)
            ara_isk = ara_toplam * (1 - (float(self.isk_inp.text or 0)/100))
            try:
                guncel_oran = float(self.kdv_oran_inp.text.replace(",", ".") or 0) / 100
            except: guncel_oran = 0
            
            kdv = ara_isk * guncel_oran if self.kdv_kontrol.active else 0
            self.kdv_lab.text = self.format_tl(kdv)
            self.genel_toplam_lab.text = self.format_tl(ara_isk + kdv)

        def satir_ekle(*args):
            row = GridLayout(cols=7, size_hint_y=None, height=70, spacing=5)
            btn_r = Button(text="+", size_hint_x=0.3, background_color=self.gokyuzu_mavisi, bold=True)
            u = TextInput(hint_text="Ürün...", size_hint_x=1.5, font_size='14sp', multiline=False)
            btn_r.bind(on_release=lambda x: self.renk_ve_islem_ac(u))
            m = TextInput(input_filter='float', hint_text="0", size_hint_x=0.6, font_size='14sp', halign='center', multiline=False)
            b = Spinner(text="kg", values=("kg", "Adet"), size_hint_x=0.4, font_size='11sp')
            f = TextInput(input_filter='float', hint_text="0", size_hint_x=0.7, font_size='14sp', halign='center', multiline=False)
            t_lab = Label(text="0,00 TL", size_hint_x=0.8, font_size='13sp')
            tur_pkt_kapsayici = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=2)
            p_not = Label(text="-", size_hint_y=0.4, font_size='10sp', color=(0.7, 0.7, 0.7, 1))
            ps = Spinner(text="1", values=("1", "2", "2.5", "5", "10"), size_hint_y=0.6, font_size='11sp', background_color=(0.2, 0.2, 0.2, 1))
            tur_pkt_kapsayici.add_widget(p_not); tur_pkt_kapsayici.add_widget(ps)
            f.bind(text=hesapla); m.bind(text=hesapla); ps.bind(text=hesapla)
            row.add_widget(btn_r); row.add_widget(u); row.add_widget(m); row.add_widget(b); row.add_widget(f); row.add_widget(t_lab); row.add_widget(tur_pkt_kapsayici)
            self.satir_konu.add_widget(row)
            self.satir_objeleri.append({'f':f, 'm':m, 't_lab':t_lab, 'u':u, 'b':b, 'p_sec':ps, 'p_not':p_not, 'layout':row})

        def satir_sil(*args):
            if len(self.satir_objeleri) > 1:
                son = self.satir_objeleri.pop()
                self.satir_konu.remove_widget(son['layout'])
                hesapla()

        alt_panel = BoxLayout(orientation='horizontal', size_hint_y=None, height=300, spacing=40)
        sol_kontrol = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=20)
        btn_artir = Button(text="+ SATIR", background_color=(0.2, 0.6, 0.6, 1), bold=True, font_size=std_font)
        btn_azalt = Button(text="- SATIR", background_color=(0.6, 0.3, 0.3, 1), bold=True, font_size=std_font)
        btn_kaydet = Button(text="SİPARİŞİ KAYDET", background_color=(0.1, 0.6, 0.2, 1), bold=True, font_size=std_font)
        btn_kapat = Button(text="KAPAT", background_color=(0.4, 0.4, 0.4, 1), font_size=std_font)
        
        h_kutu = BoxLayout(spacing=5); h_kutu.add_widget(btn_artir); h_kutu.add_widget(btn_azalt)
        sol_kontrol.add_widget(h_kutu); sol_kontrol.add_widget(btn_kaydet); sol_kontrol.add_widget(btn_kapat)
        
        sag_hesap = GridLayout(cols=2, size_hint_x=0.6, spacing=12)
        sag_hesap.add_widget(Label(text="Ara Toplam:", font_size=std_font))
        sag_hesap.add_widget(self.ara_lab)
        sag_hesap.add_widget(Label(text="İskonto (%):", font_size=std_font))
        sag_hesap.add_widget(self.isk_inp)
        
        kdv_kapsayici = BoxLayout(spacing=5)
        kdv_kapsayici.add_widget(Label(text="KDV %:", font_size=std_font, size_hint_x=0.4))
        kdv_kapsayici.add_widget(self.kdv_oran_inp)
        kdv_kapsayici.add_widget(self.kdv_kontrol)
        
        sag_hesap.add_widget(kdv_kapsayici); sag_hesap.add_widget(self.kdv_lab)
        sag_hesap.add_widget(Label(text="GENEL TOPLAM:", bold=True, font_size=std_font))
        sag_hesap.add_widget(self.genel_toplam_lab)         
        alt_panel.add_widget(sol_kontrol); alt_panel.add_widget(sag_hesap)
        ana_icerik.add_widget(alt_panel)

        btn_artir.bind(on_release=satir_ekle)
        btn_azalt.bind(on_release=satir_sil)
        btn_kapat.bind(on_release=self.pencereyi_kapat) 
        btn_kaydet.bind(on_release=self.veriyi_kaydet)
        self.isk_inp.bind(text=hesapla)
        self.kdv_oran_inp.bind(text=hesapla)
        self.kdv_kontrol.bind(active=hesapla)
        
        satir_ekle() 
        return ana_icerik

    # --- BU İKİ FONKSİYONU ortak_form_ac'NIN ALTINA EKLE ---
    def siparis_no_sorgula(self, instance, value):
        if value not in ["Müşteri Seç...", "Müşteriler Yükleniyor...", "Bağlantı Hatası", "Rehber Boş"]:
            on_ek = self.isletme[:3].upper()
            yil_ay = datetime.now().strftime("%y%m")
            firma_yolu = value.strip().replace(".", "_").replace("$", "_")
            fb_url = f"{self.base_url}/{self.isletme}/siparisler/{firma_yolu}.json"
            
            def fetch():
                from kivy.clock import Clock
                try:
                    res = requests.get(fb_url, timeout=5).json()
                    mevcut_nolar = []
                    if res and isinstance(res, dict):
                        baslangic = f"{on_ek}{yil_ay}"
                        for no in res.keys():
                            if no.startswith(baslangic):
                                try:
                                    sira = int(str(no)[-2:])
                                    mevcut_nolar.append(sira)
                                except: continue
                    yeni_sira = max(mevcut_nolar) + 1 if mevcut_nolar else 1
                    yeni_no = f"{on_ek}{yil_ay}{yeni_sira:02d}"
                    Clock.schedule_once(lambda dt: self.no_kutusunu_guncelle(yeni_no))
                except:
                    Clock.schedule_once(lambda dt: self.no_kutusunu_guncelle(f"{on_ek}{yil_ay}01"))

            threading.Thread(target=fetch, daemon=True).start()

    def no_kutusunu_guncelle(self, metin):
        self.ent_no.text = metin

    def pencereyi_kapat(self, instance):
        p = instance
        while p:
            if hasattr(p, 'dismiss'): p.dismiss(); return
            p = p.parent

    def veriyi_kaydet(self, instance):
        # 1. Müşteri seçimi kontrolü
        firma_adi = self.ent_cari.text
        if firma_adi in ["Müşteri Seç...", "Müşteriler Yükleniyor...", "Bağlantı Hatası"]:
            self.hata_mesaji("Lütfen listeden geçerli bir müşteri seçin!")
            return
        
        siparis_id = self.ent_no.text
        siparis_verisi = {
            "firma": firma_adi,
            "tarih": self.ent_tarih.text,
            "toplam_tutar": self.genel_toplam_lab.text,
            "durum": "bekliyor",
            "urunler": []
        }
        
        for s in self.satir_objeleri:
            u, f, m = s['u'].text.strip(), s['f'].text.strip(), s['m'].text.strip()
            if u and f and m:
                siparis_verisi["urunler"].append({
                    "ad": u, 
                    "birim": s['b'].text, 
                    "fiyat": f, 
                    "miktar": m,
                    "satir_toplam": s['t_lab'].text, 
                    "paket": s['p_not'].text,      # Örn: "20.0 Pkt"
                    "paket_ici": s['p_sec'].text   # Örn: "10" (Yeni eklenen kritik veri)
                })
        
        if not siparis_verisi["urunler"]:
            self.hata_mesaji("Dolu satır yok!"); return

        # Threading'e firma_adi parametresini ekledik
        threading.Thread(target=self.buluta_gonder, args=(firma_adi, siparis_id, siparis_verisi, instance)).start()


    def buluta_gonder(self, firma_adi, sip_id, veri, instance):
        from kivy.clock import Clock 
        try:
            # KRİTİK DEĞİŞİKLİK: Tekliflerdeki gibi müşteri klasörü altına kaydediyoruz
            # URL: .../siparisler/MÜŞTERİ_ADI/SIP_ID.json
            url = f"{self.base_url}/{self.isletme}/siparisler/{firma_adi}/{sip_id}.json"
            
            response = requests.put(url, json=veri, timeout=10)
            
            if response.status_code == 200:
                Clock.schedule_once(lambda dt: self.hata_mesaji(f"Sipariş Kaydedildi: {sip_id}"), 0)
                Clock.schedule_once(lambda dt: self.pencereyi_kapat(instance), 0.1)
            else:
                Clock.schedule_once(lambda dt: self.hata_mesaji(f"Hata Kodu: {response.status_code}"), 0)
        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.hata_mesaji(f"Bağlantı Hatası: {str(e)}"), 0)

            
def ekrani_olustur():
    return SiparisModulu().ortak_form_ac()