import os
import requests
import threading
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.clock import Clock

class SiparisDuzenleModulu:
    def __init__(self, ana_pencere_referansi=None):
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA")
        self.base_url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.satir_objeleri = []
        self.mevcut_filtre = "HEPSİ"
        # Sütun Genişlikleri
        # Toplamı 1.0 yapacak şekilde: 
        # SEÇ(0.05), DNT(0.12), ÜRÜN(0.23), MİK(0.08), BRM(0.06), FİY(0.08), BRM2(0.04), TOP(0.14), TÜR(0.10), PAK(0.10)
        self.widths = [0.02, 0.12, 0.25, 0.11, 0.06, 0.15, 0.04, 0.14, 0.08, 0.03]
        # ...
        h_isimler = ["SEÇ", "DURUM/NO/TAR", "ÜRÜN", "MİK", "BRM", "FİYAT", "BRM", "TOPLAM", "TÜR", "PAK"]        
        
        self.view = None
        self.bulut_verisi = {}

    def hucre_olustur(self, t, w, c=(1,1,1,1), bold=False, yukseklik=dp(30), hizala='left', fs='10sp'):
        l = Label(
            text=str(t), 
            size_hint=(w, None), 
            height=yukseklik,
            halign=hizala, 
            valign='middle', # Dikeyde mutlaka ortala
            font_size=fs, 
            color=c, 
            bold=bold, 
            padding=(dp(5), 0)
        )
        # Metnin Label sınırları içinde hizalanması için gerekli
        l.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        return l

    def buluttan_oku(self):
        def fetch():
            try:
                # Firebase URL yapısını kontrol et
                url = f"{self.base_url}/{self.isletme}/siparisler.json"
                res = requests.get(url, timeout=10).json()
                
                islenmis_veri = {}
                if res and isinstance(res, dict):
                    # image_3b85da daki gibi GULERYUZ, JALUZICAM gibi klasörleri dönüyoruz
                    for klasor_adi, klasor_icerik in res.items():
                        if isinstance(klasor_icerik, dict):
                            # Klasörün içindeki siparişleri al (OND024435 vb.)
                            for s_id, s_veri in klasor_icerik.items():
                                if isinstance(s_veri, dict):
                                    # s_id zaten Firebase'den "OND031531" olarak geliyor. 
                                    # Bunu bozmadan direkt mühürle.
                                    s_veri["_sip_id"] = str(s_id) 
                                    s_veri["_firma_klasoru"] = klasor_adi
                                    islenmis_veri[s_id] = s_veri                # Veriyi sınıfa kaydet ve arayüzü ana thread'de yenile
                self.bulut_verisi = islenmis_veri
                Clock.schedule_once(lambda dt: self.listeyi_yenile(), 0)
            except Exception as e:
                print(f"KRİTİK HATA (Veri Çekme): {e}")
                
        threading.Thread(target=fetch, daemon=True).start()
        
    def listeyi_yenile(self):
        if not self.view: return
        self.liste_layout.clear_widgets()
        self.satir_objeleri = []
        h = {"T": [0.0, 0.0], "O": [0.0, 0.0], "B": [0.0, 0.0]}
        gruplanmis = {}

        # --- GENİŞLİK AYARLARI (Buradaki değerleri değiştirerek sütunları ayarlayabilirsin) ---
        # Toplamı 1.0 olmalı: [SEÇ, DURUM, ÜRÜN ADI, MİK, BRM, FİYAT, BRM2, TOPLAM, TÜR/PK]
        self.widths = [0.05, 0.17, 0.20, 0.11, 0.06, 0.1, 0.04, 0.15, 0.12]
        # ----------------------------------------------------------------------------------

        # 1. Verileri Grupla
        for sip_id_key, veri in self.bulut_verisi.items():
            if veri.get("durum") == "faturalandi": continue
            firma = veri.get("_firma_klasoru", "Bilinmeyen")
            if firma not in gruplanmis: gruplanmis[firma] = []
            for i, urun in enumerate(veri.get("urunler", [])):
                u = urun.copy()
                u.update({
                    "_sip_id": str(sip_id_key), 
                    "_firma_klasoru": firma, 
                    "_durum": veri.get("durum", "bekliyor"), 
                    "_tarih": veri.get("tarih", "-"), 
                    "_idx": i
                })
                gruplanmis[firma].append(u)

        # 2. Arayüzü Oluştur
        for firma, kalemler in gruplanmis.items():
            gorunur = [u for u in kalemler if (self.mevcut_filtre == "HEPSİ") or 
                       (self.mevcut_filtre == "ONAYLANDI" and "ONAY" in u["_durum"].upper()) or 
                       (self.mevcut_filtre == "BEKLİYOR" and "ONAY" not in u["_durum"].upper())]
            if not gorunur: continue

            # Firma Başlığı
            self.liste_layout.add_widget(self.hucre_olustur(firma, 1.0, c=(0.2, 0.7, 1, 1), bold=True, yukseklik=dp(40), fs='14sp'))
            
            # Kolon Başlıkları (Widths listesini kullanır)
            baslik_row = GridLayout(cols=len(self.widths), size_hint_y=None, height=dp(40), spacing=2)
            basliklar = ["Seç", "Dur/No/Tar", "Ürün", "Mik", "Brm", "Fiyat", "Brm", "Toplam", "Tür/Pak"]
            for i, m in enumerate(basliklar):
                baslik_row.add_widget(self.hucre_olustur(m, self.widths[i], c=(1, 0.8, 0, 1), bold=True, hizala='center', fs='9sp'))
            self.liste_layout.add_widget(baslik_row)

            # Satırları Oluştur
            for urun in gorunur:
                durum = urun["_durum"].upper()
                try:
                    f_val = float(str(urun.get("fiyat",0)).replace(",","."))
                    m_val = float(str(urun.get("miktar",0)).replace(",","."))
                    tutar = f_val * m_val
                    h["T"][0]+=tutar; h["T"][1]+=m_val
                    if "ONAY" in durum: h["O"][0]+=tutar; h["O"][1]+=m_val
                    else: h["B"][0]+=tutar; h["B"][1]+=m_val
                except: tutar=0; m_val=0

                row_h = dp(80) # Satır yüksekliği dikey kutu için 80
                row = GridLayout(cols=len(self.widths), size_hint_y=None, height=row_h, spacing=dp(2))
                
                # 1. Seçim (CheckBox)
                cb_cont = BoxLayout(size_hint=(self.widths[0], None), height=row_h, padding=[0, dp(25)])
                cb = CheckBox(active=False); cb.bind(active=self.toplamlar_ara_hesap); cb_cont.add_widget(cb)
                
                # 2. Durum Bilgisi
                lbl_dnt = self.hucre_olustur(f"{durum}\n{urun['_sip_id']}\n{urun['_tarih']}", self.widths[1], 
                                            c=((0,1,0,1) if "ONAY" in durum else (1,0.6,0,1)), fs='8sp', yukseklik=row_h)

                # TextInput oluşturucu (Ortalı ve temiz görünüm için)
                def ti(text, w, is_f=False):
                    c = BoxLayout(size_hint=(w, None), height=row_h, padding=[dp(2), dp(25)])
                    t = TextInput(text=str(text), multiline=False, font_size='11sp', 
                                  input_filter=('float' if is_f else None), halign='center')
                    c.add_widget(t); return c, t

                # 3, 4, 6. TextInput Sütunları
                box_ad, txt_ad = ti(urun.get("ad",""), self.widths[2])
                box_mik, txt_mik = ti(str(m_val), self.widths[3], True)
                box_fiy, txt_fiy = ti(str(f_val), self.widths[5], True)

                # 9. Tür ve Paket Hesaplama (Dikey Kutu)
                box_tur = BoxLayout(orientation='vertical', size_hint_x=self.widths[8], spacing=dp(2), padding=[dp(5), dp(10)])
                
                txt_tur = TextInput(
                    text=str(urun.get("paket_ici", "1")), 
                    multiline=False, font_size='11sp', input_filter='float', 
                    size_hint=(0.7, None), height=dp(28), # Küçük ve zarif boyut
                    halign='center', pos_hint={'center_x': 0.5}
                )
                
                lbl_pk_hesap = Label(
                    text="", size_hint_y=0.5, font_size='10sp', 
                    bold=True, color=(0.8, 0.8, 0.8, 1)
                )
                
                box_tur.add_widget(txt_tur)
                box_tur.add_widget(lbl_pk_hesap)

                # Dinamik Paket Hesaplama Fonksiyonu
                def p_guncelle(*a, tm=txt_mik, tt=txt_tur, lp=lbl_pk_hesap):
                    try:
                        m = float(tm.text.replace(",", ".")); t = float(tt.text.replace(",", "."))
                        lp.text = f"{m/t:g} Pkt" if t > 0 else "0 Pkt"
                    except: lp.text = "0 Pkt"

                txt_mik.bind(text=p_guncelle); txt_tur.bind(text=p_guncelle); p_guncelle()

                # --- Widgetları Sırayla Satıra Ekle ---
                row.add_widget(cb_cont) #1
                row.add_widget(lbl_dnt) #2
                row.add_widget(box_ad)  #3
                row.add_widget(box_mik) #4
                row.add_widget(self.hucre_olustur(urun.get("birim","kg"), self.widths[4], yukseklik=row_h, hizala='center')) #5
                row.add_widget(box_fiy) #6
                row.add_widget(self.hucre_olustur("TL", self.widths[6], yukseklik=row_h, hizala='center')) #7
                row.add_widget(self.hucre_olustur(f"{tutar:,.2f} TL", self.widths[7], yukseklik=row_h, hizala='right', fs='9sp')) #8
                row.add_widget(box_tur) #9

                self.liste_layout.add_widget(row)
                
                # Güncelleme için nesneleri listeye mühürle
                self.satir_objeleri.append({
                    "cb": cb, "sip_id": urun["_sip_id"], "firma": urun["_firma_klasoru"], "u_idx": urun["_idx"],
                    "t_ad": txt_ad, "t_mik": txt_mik, "t_fiy": txt_fiy, "t_tur": txt_tur, "l_pk": lbl_pk_hesap
                })

        # Alt Toplam Etiketlerini Güncelle
        self.lbl_tum_val.text = f"TOPLAM {h['T'][1]:,.0f} Kg\n{h['T'][0]:,.2f} TL"
        self.lbl_onay_val.text = f"ONAYLI {h['O'][1]:,.0f} Kg\n{h['O'][0]:,.2f} TL"
        self.lbl_bekle_val.text = f"BEKLEYEN {h['B'][1]:,.0f} Kg\n{h['B'][0]:,.2f} TL"



    def toplu_islem(self, islem):
        # GUNCELLE için seçili olmasına bakma, hepsini tara
        if islem == "GUNCELLE":
            islem_yapilacaklar = self.satir_objeleri
        else:
            islem_yapilacaklar = [s for s in self.satir_objeleri if s["cb"].active]

        if not islem_yapilacaklar:
            return 

        def run():
            sip_bazli = {}
            for s in islem_yapilacaklar:
                sid = s["sip_id"]
                if sid not in sip_bazli: sip_bazli[sid] = []
                sip_bazli[sid].append(s)

            for sid, satirlar in sip_bazli.items():
                # Firma adını olduğu gibi alıyoruz, büyük harfe zorlamıyoruz. [cite: 2026-02-01]
                firma = str(satirlar[0]["firma"])
                url = f"{self.base_url}/{self.isletme}/siparisler/{firma}/{sid}.json"
                
                try:
                    # 1. Mevcut veriyi çek
                    res = requests.get(url, timeout=5).json()
                    if not res or res == "null": 
                        print(f"UYARI: {sid} verisi bulunamadı!")
                        continue
                    
                    urunler = res.get("urunler", [])

                    if islem == "GUNCELLE":
                        for s in satirlar:
                            idx = s["u_idx"]
                            if idx < len(urunler):
                                # Ekrandaki yeni değerleri listeye işle
                                urunler[idx]["ad"] = s["t_ad"].text
                                urunler[idx]["miktar"] = s["t_mik"].text.replace(",", ".")
                                urunler[idx]["fiyat"] = s["t_fiy"].text.replace(",", ".")
                                
                                # --- YENİ EKLENEN KISIM ---
                                # Tür (paket_ici) ve Pk (hesaplanan metin) buluta gönderiliyor
                                urunler[idx]["paket_ici"] = s["t_tur"].text.replace(",", ".")
                                urunler[idx]["paket"] = s["l_pk"].text 
                                # -------------------------
                        
                        # Toplamı yeniden hesapla [cite: 2026-02-01]
                        yeni_genel = 0.0
                        for u in urunler:
                            try:
                                m = float(str(u.get("miktar",0)).replace(",","."))
                                f = float(str(u.get("fiyat",0)).replace(",","."))
                                yeni_genel += (m * f)
                            except: pass
                        
                        # 2. KRİTİK NOKTA: Veriyi Firebase'e geri gönder (PATCH)
                        guncelleme_paketi = {
                            "urunler": urunler,
                            "toplam_tutar": f"{yeni_genel:,.2f} TL"
                        }
                        
                        patch_res = requests.patch(url, json=guncelleme_paketi, timeout=5)
                        if patch_res.status_code == 200:
                            print(f"BAŞARI: {sid} güncellendi.")
                        else:
                            print(f"HATA: Firebase güncellenemedi! Kod: {patch_res.status_code}")

                    elif islem == "ONAY":
                        yeni_durum = "onaylandi" if res.get("durum") != "onaylandi" else "bekliyor"
                        requests.patch(url, json={"durum": yeni_durum}, timeout=5)
                    
                    elif islem == "SIL":
                        # Seçili ürünleri (satirlar) urunler listesinden çıkar ve güncelle
                        # Not: Bu kısım isteğe bağlıdır, toplu silme mantığına göre uyarlanabilir
                        pass

                except Exception as e:
                    print(f"İşlem Hatası ({sid}): {e}")

            # Ekranı yenile
            Clock.schedule_once(lambda dt: self.buluttan_oku(), 0.5)

        threading.Thread(target=run, daemon=True).start()

    def ekrani_olustur(self):
        self.view = ModalView(size_hint=(1, 1), auto_dismiss=False)
        self.ana_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 1. BAŞLIK
        self.ana_layout.add_widget(Label(text=f"{self.isletme} SİPARİŞ DÜZENLEME", size_hint_y=None, height=dp(40), bold=True, color=(1, 0.6, 0, 1))) 
        
        # 2. ÖZET PANELİ (Hatalı olan kısım eklendi)
        u_p = BoxLayout(size_hint_y=None, height=dp(120), padding=[dp(5), 0], spacing=10)
        t_g = GridLayout(cols=2, rows=2, size_hint_x=0.80, spacing=dp(5))

        def ozet_kutusu_olustur(referans_etiketi, renk=(1,1,1,1)):
            referans_etiketi.font_size = '12sp'
            referans_etiketi.color = renk
            referans_etiketi.halign = 'left'
            referans_etiketi.valign = 'middle'
            referans_etiketi.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
            return referans_etiketi

        self.lbl_tum_val = Label(text="TOPLAM 0 Kg\n0,00 TL", bold=True)
        self.lbl_onay_val = Label(text="ONAYLI 0 Kg\n0,00 TL", bold=True)
        self.lbl_bekle_val = Label(text="BEKLEYEN 0 Kg\n0,00 TL", bold=True)
        self.lbl_secili_val = Label(text="SEÇİLİ 0 Kg\n0,00 TL", bold=True)

        t_g.add_widget(ozet_kutusu_olustur(self.lbl_tum_val))
        t_g.add_widget(ozet_kutusu_olustur(self.lbl_onay_val, (0, 1, 0, 1)))
        t_g.add_widget(ozet_kutusu_olustur(self.lbl_bekle_val, (1, 0.6, 0, 1)))
        t_g.add_widget(ozet_kutusu_olustur(self.lbl_secili_val, (1, 1, 0, 1)))
        
        # Filtre Spinner'ı
        self.spinner = Spinner(text="HEPSİ", values=('HEPSİ', 'ONAYLANDI', 'BEKLİYOR'), size_hint=(0.20, None), height=dp(60), pos_hint={'center_y': .5})
        self.spinner.bind(text=lambda s, t: setattr(self, 'mevcut_filtre', t) or self.listeyi_yenile())

        u_p.add_widget(t_g)
        u_p.add_widget(self.spinner)
        self.ana_layout.add_widget(u_p) # ÜST PANEL BURADA EKLENDİ

        # 3. LİSTE ALANI
        self.scroll = ScrollView()
        self.liste_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        self.liste_layout.bind(minimum_height=self.liste_layout.setter('height'))
        self.scroll.add_widget(self.liste_layout)
        self.ana_layout.add_widget(self.scroll)
        
        # 4. ALT BUTONLAR
        alt = GridLayout(cols=3, size_hint_y=None, height=dp(120), spacing=10)
        btns = [
            ("ONAY/BEKLE", (0.1, 0.6, 0.2, 1), lambda x: self.toplu_islem("ONAY")), 
            ("GÜNCELLE", (0.2, 0.4, 0.8, 1), lambda x: self.toplu_islem("GUNCELLE")),
            ("SİL", (0.8, 0.1, 0.1, 1), lambda x: self.toplu_islem("SIL")), 
            ("YAZDIR", (0.4, 0.4, 0.4, 1), None), ("E-POSTA", (0.7, 0.4, 0.1, 1), None),
            ("KAPAT", (0.2, 0.2, 0.2, 1), lambda x: self.view.dismiss())
        ]
        for m, r, f in btns:
            btn = Button(text=m, background_color=r, bold=True)
            if f: btn.bind(on_release=f)
            alt.add_widget(btn)
            
        self.ana_layout.add_widget(alt)
        self.view.add_widget(self.ana_layout)
        self.buluttan_oku()
        self.view.open()
        return self.view


    def toplamlar_ara_hesap(self, *args):
        s_t, s_m = 0.0, 0.0
        for s in self.satir_objeleri:
            if s["cb"].active:
                try:
                    m = float(s["t_mik"].text.replace(",","."))
                    f = float(s["t_fiy"].text.replace(",","."))
                    s_t += (m * f); s_m += m
                except: pass
        self.lbl_secili_val.text = f"{s_t:,.2f} TL\n{s_m:,.0f} Kg"


def ekrani_olustur(): return SiparisDuzenleModulu().ekrani_olustur()