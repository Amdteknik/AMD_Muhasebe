import os
import requests
import threading
from datetime import datetime
import webbrowser
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.clock import Clock
import importlib
from kivy.uix.popup import Popup


class TeklifDuzenleModulu:
    def __init__(self, ana_pencere_referansi=None):
        self.isletme = os.environ.get("SECILI_ISLETME", "AMD")
        self.base_url = os.environ.get("FIREBASE_URL", "").strip("/")
        self.satir_objeleri = []
        self.mevcut_filtre = "HEPSİ"
        # İSTEDİĞİN ORANLAR: SEÇ(0.08), DURUM(0.12), NO/TARİH(0.25), KONU(0.35), TOPLAM(0.20)
        self.widths = [0.08, 0.12, 0.25, 0.35, 0.20]        
        self.view = None
        self.bulut_verisi = {}

    def hucre_olustur(self, t, w, c=(1,1,1,1), bold=False, yukseklik=dp(35), hizala='left', fs='10sp'):
        # Sol hizalamayı bozmadan sadece TOPLAM sütununa biraz iç boşluk veriyoruz
        # Böylece "TOPLAM" yazısının tam altına denk gelecek
        p_val = (dp(15), 0, 0, 0) if hizala == 'toplam_sutunu' else (dp(5), 0, 0, 0)
        
        l = Label(
            text=str(t), 
            size_hint_x=w, 
            size_hint_y=None, 
            height=dp(60) if yukseklik > dp(35) else yukseklik, # Satır yüksekliği dengesi
            halign='left', # HER ŞEY SOLA YASLI (Başlık ve veri aynı hizada olur)
            valign='middle', 
            font_size=fs, 
            color=c, 
            bold=bold, 
            padding=p_val
        )
        l.bind(size=lambda obj, s: setattr(obj, 'text_size', (s[0], s[1])))
        return l



    def buluttan_oku(self):
        def fetch():
            try:
                url = f"{self.base_url}/{self.isletme}/teklifler.json"
                res = requests.get(url, timeout=10).json()
                self.bulut_verisi = res if res else {}
                Clock.schedule_once(lambda dt: self.listeyi_yenile(), 0)
            except Exception as e: print(f"Hata: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def duzenle_baslat(self, instance):
        secili = next((s for s in self.satir_objeleri if s["cb"].active), None)
        if not secili: return

        # Seçilen veriyi hazırla
        veri_detay = secili['veri'].copy()
        veri_detay["musteri"] = secili["musteri"]
        veri_detay["no"] = secili["t_no"]

        if self.view:
            self.view.dismiss()

        def formu_yukle(dt):
            import yeni_teklif
            importlib.reload(yeni_teklif)
            
            # Formu oluştur
            form_nesnesi = yeni_teklif.ekrani_olustur()
            
            # VERİ AKTARIMI (Fonksiyonu aşağıda güncelledim)
            self.forma_aktar_disardan(form_nesnesi, veri_detay)

            yeni_pencere = ModalView(size_hint=(1, 1), auto_dismiss=False)
            yeni_pencere.add_widget(form_nesnesi)
            yeni_pencere.open()

        Clock.schedule_once(formu_yukle, 0.2)


    def guvenli_kaydet(self, form_layout, pencere_objesi):
        """Kilitlenme yaratan Popup'ı açmadan veriyi buluta gönderir ve ekranı kapatır"""
        try:
            # yeni_teklif içindeki veriyi toplama fonksiyonunu çağır (Örn: veri_topla)
            # Bu kısım yeni_teklif.py içindeki kayıt mantığına göre uyarlanmalı
            if hasattr(form_layout, 'teklif_kaydet'):
                form_layout.teklif_kaydet() # Sadece buluta yazma kısmını tetikle
            
            # Kilitlenen Popup açılmadan önce biz bu pencereyi kapatıyoruz
            pencere_objesi.dismiss()
            
            # Ana listeyi tekrar aç (Yenilenmiş haliyle)
            Clock.schedule_once(lambda dt: self.ekrani_olustur(), 0.5)
            
        except Exception as e:
            print(f"Güvenli Kayıt Hatası: {e}")

    def forma_aktar_disardan(self, form, icerik):
        """Verilerin düşmeme sorununu çözen güncellenmiş aktarım"""
        try:
            # Temel bilgiler - .text atamaları
            if hasattr(form, 'firma_manuel'): form.firma_manuel.text = str(icerik.get("musteri", ""))
            if hasattr(form, 'teklif_no'): form.teklif_no.text = str(icerik.get("no", ""))
            if hasattr(form, 'konu'): form.konu.text = str(icerik.get("konu", "-"))
            if hasattr(form, 'ilgili'): form.ilgili.text = str(icerik.get("ilgili", ""))
            if hasattr(form, 'tarih_input'): form.tarih_input.text = str(icerik.get("tarih", ""))
            
            # Kalemleri aktarma
            if hasattr(form, 'urun_alani') and "kalemler" in icerik:
                form.urun_alani.clear_widgets()
                form.urun_satirlari_listesi = []
                
                def kalemleri_diz(dt):
                    for k in icerik["kalemler"]:
                        form.satir_ekle()
                        if form.urun_satirlari_listesi:
                            yeni_satir = form.urun_satirlari_listesi[-1]
                            # yeni_teklif.py içindeki sözlük yapılandırmasına (widgets) erişim
                            yeni_satir.widgets['aciklama'].text = str(k.get("u", ""))
                            yeni_satir.widgets['miktar'].text = str(k.get("m", "1"))
                            yeni_satir.widgets['fiyat'].text = str(k.get("f", "0"))
                            if 'c' in k: yeni_satir.widgets['curr'].text = str(k.get("c", "TL"))
                            if 'b' in k: yeni_satir.widgets['birim'].text = str(k.get("b", "Ad"))
                    
                    # Toplamı güncellemesini tetikle
                    if hasattr(form, 'genel_toplam_guncelle'):
                        form.genel_toplam_guncelle()
                
                Clock.schedule_once(kalemleri_diz, 0.2)
                
        except Exception as e:
            print(f"Aktarma Hatası: {e}")


    def listeyi_yenile(self):
        if not self.view: return
        self.liste_layout.clear_widgets()
        self.satir_objeleri = []
        
        for musteri, teklifler in self.bulut_verisi.items():
            gecerli_teklifler = []
            for t_no, veri in teklifler.items():
                # --- KRİTİK NOKTA BURASI ---
                # Eğer teklif arşivlenmişse listeye hiç ekleme
                if veri.get("arsivlendi") is True:
                    continue 
                
                durum = veri.get("durum", "BEKLIYOR").upper()
                if self.mevcut_filtre == "ONAYLANDI" and durum != "ONAYLANDI": continue
                if self.mevcut_filtre == "BEKLİYOR" and durum == "ONAYLANDI": continue
                gecerli_teklifler.append((t_no, veri, durum))

            if not gecerli_teklifler: continue

            # 1. Müşteri Başlığı
            self.liste_layout.add_widget(self.hucre_olustur(musteri.upper(), 1.0, c=(0.2, 0.7, 1, 1), bold=True, yukseklik=dp(40), fs='12sp'))
            
            # 2. Sütun Başlıkları (Burada başlıkları manuel ekliyoruz)
            baslik_row = GridLayout(cols=5, size_hint_y=None, height=dp(30), spacing=5)
            h_isimler = ["SEÇ", "DURUM", "NO / TARİH", "KONU", "TOPLAM"]

            for i, metin in enumerate(h_isimler):
                # Başlıkları 'left' yapıyoruz
                h_tip = 'toplam_sutunu' if metin == "TOPLAM" else 'left'
                baslik_row.add_widget(self.hucre_olustur(metin, self.widths[i], c=(1, 0.8, 0, 1), bold=True, hizala=h_tip, fs='9sp'))
            self.liste_layout.add_widget(baslik_row)
            
            # 3. Veri Satırları
            for t_no, veri, durum in gecerli_teklifler:
                row = GridLayout(cols=5, size_hint_y=None, height=dp(60), spacing=2)
                
                # SEÇ, DURUM, NO/TARİH, KONU (Standart Akış)
                cb = CheckBox(size_hint_x=self.widths[0], group="teklif_sec")
                self.satir_objeleri.append({"cb": cb, "musteri": musteri, "t_no": t_no, "veri": veri}) 
                row.add_widget(cb)
                
                row.add_widget(self.hucre_olustur(durum, self.widths[1], c=(0,1,0,1) if durum == "ONAYLANDI" else (1,0.6,0,1), fs='9sp', yukseklik=dp(60)))
                
                # No/Tarih kutusunu genişliğe göre ayarla
                no_tarih = f"{t_no}\n{veri.get('tarih', '-')}"
                row.add_widget(self.hucre_olustur(no_tarih, self.widths[2], fs='9sp', yukseklik=dp(60)))
                
                row.add_widget(self.hucre_olustur(veri.get("konu", "-"), self.widths[3], fs='10sp', yukseklik=dp(60)))
                
                # TOPLAM (Başlığın tam altına hizalı)
                ham_veri = str(veri.get("toplam", "0"))
                sadece_tutar = ham_veri.replace("GENEL TOPLAM:", "").strip()
                row.add_widget(self.hucre_olustur(sadece_tutar, self.widths[4], hizala='toplam_sutunu', bold=True, fs='10sp', yukseklik=dp(60)))

                self.liste_layout.add_widget(row)


    def pdf_olustur_ve_yazdir(self, secili_satirlar):
        # HTML Şablonu
        html = f"<html><head><meta charset='UTF-8'><style>table{{width:100%;border-collapse:collapse;}} th,td{{border:1px solid black;padding:8px;text-align:left;font-size:12px;}} th{{background-color:#eee;}}</style></head><body>"
        html += f"<h2>{self.isletme} TEKLİF LİSTESİ</h2><p>Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p><table>"
        html += "<tr><th>Müşteri</th><th>No</th><th>Konu</th><th>Tarih</th><th>Toplam</th></tr>"
        
        for s in secili_satirlar:
            v = s['veri']
            html += f"<tr><td>{s['musteri']}</td><td>{s['t_no']}</td><td>{v.get('konu','-')}</td><td>{v.get('tarih','-')}</td><td>{v.get('toplam','0')}</td></tr>"
        
        html += "</table></body></html>"

        try:
            path = os.path.join(os.path.expanduser('~'), 'Documents', 'teklif_listesi.html')
            if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
            with open(path, 'w', encoding='utf-8') as f: f.write(html)
            from plyer import share
            share.share(path)
        except Exception as e: print(f"Yazdırma Hatası: {e}")

    def toplu_islem(self, islem):
        secili_satirlar = [s for s in self.satir_objeleri if s["cb"].active]
        if not secili_satirlar: return
        
        if islem == "YAZDIR":
            self.pdf_olustur_ve_yazdir(secili_satirlar)
            return

        def run():
            for s in secili_satirlar:
                url = f"{self.base_url}/{self.isletme}/teklifler/{s['musteri']}/{s['t_no']}.json"
                if islem == "ONAY":
                    m_d = s['veri'].get("durum", "bekliyor")
                    requests.patch(url, json={"durum": "onaylandı" if m_d != "onaylandı" else "bekliyor"})
                elif islem == "SIL": requests.delete(url)
            Clock.schedule_once(lambda dt: self.buluttan_oku(), 0)
        threading.Thread(target=run, daemon=True).start()

    def teklifi_arsivle(self, instance):
        # 1. Seçili olan satırı bul
        secili = next((s for s in self.satir_objeleri if s["cb"].active), None)
        
        if not secili:
            print("Hata: Önce listeden bir teklif seçmelisiniz.")
            return

        firma = secili["musteri"]
        t_no = secili["t_no"]
        
        # 2. Firebase URL'sini oluştur (Senin yapına uygun: isletme/teklifler/firma/teklif_no)
        # self.base_url zaten init içinde tanımlı
        url = f"{self.base_url}/{self.isletme}/teklifler/{firma}/{t_no}.json"
        
        def run_archive():
            try:
                # 3. Sadece 'arsivlendi' alanını güncelle (Patch)
                res = requests.patch(url, json={"arsivlendi": True}, timeout=5)
                
                if res.status_code == 200:
                    print(f"{t_no} numaralı teklif başarıyla arşivlendi.")
                    # 4. Listeyi buluttan tekrar oku ve ekranı tazele
                    Clock.schedule_once(lambda dt: self.buluttan_oku(), 0)
                else:
                    print(f"Arşivleme hatası: {res.status_code}")
            except Exception as e:
                print(f"Bağlantı hatası: {e}")

        # Arayüz kilitlenmesin diye thread içinde çalıştır
        threading.Thread(target=run_archive, daemon=True).start()


    def ekrani_olustur(self):
        self.view = ModalView(size_hint=(1, 1), auto_dismiss=False)
        l = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # BAŞLIK
        l.add_widget(Label(text=f"{self.isletme} TEKLİF YÖNETİMİ", size_hint_y=None, height=dp(40), bold=True, color=(1,0.6,0,1))) 



        # --- ÜST PANEL (Düzenle ve Filtre sağa dayalı) ---
        u_p = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        u_p.add_widget(Label(text="", size_hint_x=0.4))
        btn_duzenle = Button(text="SEÇİLENİ DÜZENLE", size_hint=(None, None), width=dp(150), height=dp(40), background_color=(0.1, 0.4, 0.2, 1), bold=True)
        btn_duzenle.bind(on_release=self.duzenle_baslat)
        self.spinner = Spinner(text=self.mevcut_filtre, values=('HEPSİ', 'ONAYLANDI', 'BEKLİYOR'), size_hint=(None, None), width=dp(150), height=dp(40))
        self.spinner.bind(text=lambda s, t: setattr(self, 'mevcut_filtre', t) or self.listeyi_tazele())
        u_p.add_widget(btn_duzenle); u_p.add_widget(self.spinner)
        l.add_widget(u_p)

        # --- LİSTE ALANI ---
        self.scroll = ScrollView()
        self.liste_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        self.liste_layout.bind(minimum_height=self.liste_layout.setter('height'))
        self.scroll.add_widget(self.liste_layout)
        l.add_widget(self.scroll)

        # --- ALT BUTON PANELİ (2 Satır x 3 Sütun) ---
        # Tam olarak istediğin düzen: 
        # Satır 1: ONAY - YAZDIR - SİL
        # Satır 2: YENİLE - ARŞİVLE - KAPAT
        alt_panel = GridLayout(cols=3, rows=2, size_hint_y=None, height=dp(110), spacing=5)
        
        # Satır 1
        btn_onay = Button(text="ONAY/BEKLE", background_color=(0, 0.3, 0.1, 1), bold=True)
        btn_onay.bind(on_release=lambda x: self.toplu_islem("ONAY"))
        
        btn_yazdir = Button(text="YAZDIR/PDF", background_color=(0.1, 0.2, 0.4, 1), bold=True)
        btn_yazdir.bind(on_release=lambda x: self.toplu_islem("YAZDIR"))
        
        btn_sil = Button(text="SİL", background_color=(0.4, 0, 0, 1), bold=True)
        btn_sil.bind(on_release=lambda x: self.toplu_islem("SIL"))

        # Satır 2
        btn_yenile = Button(text="YENİLE", background_color=(0.15, 0.15, 0.15, 1), bold=True)
        btn_yenile.bind(on_release=lambda x: self.buluttan_oku())
        
        btn_arsiv = Button(text="ARŞİVLE", background_color=(0.3, 0.2, 0, 1), bold=True)
        btn_arsiv.bind(on_release=self.teklifi_arsivle)
        
        btn_kapat = Button(text="KAPAT", background_color=(0.1, 0.1, 0.1, 1), bold=True)
        btn_kapat.bind(on_release=lambda x: self.view.dismiss())

        # Sırayla ekle (GridLayout soldan sağa, yukarıdan aşağı doldurur)
        alt_panel.add_widget(btn_onay); alt_panel.add_widget(btn_yazdir); alt_panel.add_widget(btn_sil)
        alt_panel.add_widget(btn_yenile); alt_panel.add_widget(btn_arsiv); alt_panel.add_widget(btn_kapat)
        
        l.add_widget(alt_panel)
        self.view.add_widget(l)
        self.buluttan_oku()
        self.view.open()
        return self.view


def ekrani_olustur(): return TeklifDuzenleModulu().ekrani_olustur()