import os
import json
import importlib
import requests
import webbrowser
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp

# Firebase ayarları
try:
    import ayarlar
    FIREBASE_URL = ayarlar.FIREBASE_URL.strip("/")
except:
    FIREBASE_URL = ""

class TeklifDuzenle(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        self.isletme = os.environ.get("SECILI_ISLETME", "ONDULA") 
        self.aktif_veri = None

        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Başlık
        isletme_ust_baslik = Label(
            text=f"{self.isletme} TEKLİF TAKİP MODÜLÜ", 
            size_hint_y=None, height=45, 
            color=(0.1, 0.4, 0.6, 1), bold=True, font_size='18sp',
            halign='center', valign='middle'
        )
        isletme_ust_baslik.bind(size=isletme_ust_baslik.setter('text_size'))
        self.add_widget(isletme_ust_baslik)

        # --- 2. ÜST PAKET (MİLİMETRİK SİMETRİ) ---
        ust_paket = BoxLayout(orientation='vertical', size_hint_y=None, height=185, spacing=25)
        
        # 1. SATIR: Müşteri ve No Grubu
        satir_1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=25)

        # Müşteri Grubu (Sol Üst) - İçerideki elemanlar %50-%50
        grup_musteri = BoxLayout(spacing=5, size_hint_x=0.55)
        self.bul_firma_input = TextInput(hint_text="Müşteri Ara", size_hint_x=0.5, multiline=False)
        self.bul_firma_spinner = Spinner(text="Müşteri Seç", values=self.musterileri_getir(), size_hint_x=0.5)
        grup_musteri.add_widget(self.bul_firma_input)
        grup_musteri.add_widget(self.bul_firma_spinner)

        # No Grubu (Sağ Üst)
        grup_no = BoxLayout(spacing=5, size_hint_x=0.45)
        self.secili_no_input = TextInput(hint_text="No Yaz...", size_hint_x=0.7, halign='center', multiline=False)
        btn_ac = Button(text="AÇ", size_hint_x=0.3, background_color=(0.1, 0.3, 0.5, 1), bold=True)
        btn_ac.bind(on_release=self.no_ile_direkt_ac)
        grup_no.add_widget(self.secili_no_input)
        grup_no.add_widget(btn_ac)

        satir_1.add_widget(grup_musteri)
        satir_1.add_widget(grup_no)

        # 2. SATIR: İşlem ve Konu Grubu
        satir_2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=25)

        # İşlem Grubu (Sol Alt) - Buradaki oranları ÜSTTEKİYLE AYNI (%50-%50) yaptık
        grup_islem = BoxLayout(spacing=5, size_hint_x=0.55)
        btn_duzenle = Button(text="GÖR", size_hint_x=0.5, background_color=(0.1, 0.4, 0.2, 1), bold=True)
        btn_temizle = Button(text="TEMİZLE", size_hint_x=0.5, background_color=(0.5, 0.1, 0.1, 1), bold=True)
        btn_duzenle.bind(on_release=self.teklifi_sadece_goruntule)
        btn_temizle.bind(on_release=self.ekran_temizle)
        grup_islem.add_widget(btn_duzenle)
        grup_islem.add_widget(btn_temizle)

        # Konu Grubu (Sağ Alt)
        grup_konu = BoxLayout(spacing=5, size_hint_x=0.45)
        self.konu_ara_input = TextInput(hint_text="Konu Yaz...", size_hint_x=0.7, halign='center', multiline=False)
        btn_bul = Button(text="BUL", size_hint_x=0.3, background_color=(0.5, 0.3, 0, 1), bold=True)
        btn_bul.bind(on_release=self.konu_ile_bul)
        grup_konu.add_widget(self.konu_ara_input)
        grup_konu.add_widget(btn_bul)

        satir_2.add_widget(grup_islem)
        satir_2.add_widget(grup_konu)

        ust_paket.add_widget(satir_1)
        ust_paket.add_widget(satir_2)
        self.add_widget(ust_paket)

        # --- 3. LİSTE BAŞLIKLARI ---
        baslik_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=20) # Spacing artırıldı
        baslik_layout.add_widget(Label(text="SEÇ", size_hint_x=0.15, color=(0,0,0,1), bold=True))
        
        lbl_h_no = Label(text="TEKLİF NO", size_hint_x=0.50, color=(0,0,0,1), bold=True, halign='left', valign='middle')
        lbl_h_no.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        baslik_layout.add_widget(lbl_h_no)
        
        lbl_h_konu = Label(text="KONU", size_hint_x=0.35, color=(0,0,0,1), bold=True, halign='left', valign='middle')
        lbl_h_konu.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        baslik_layout.add_widget(lbl_h_konu)
        self.add_widget(baslik_layout)


        # --- 4. LİSTE ALANI ---
        self.scroll = ScrollView()
        self.liste_grid = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.liste_grid.bind(minimum_height=self.liste_grid.setter('height'))
        self.scroll.add_widget(self.liste_grid)
        self.add_widget(self.scroll)

        # --- 5. KAPAT BUTONU (SAĞ ALT) ---
        alt_buton_cubugu = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, padding=[0, 5, 0, 5])
        alt_buton_cubugu.add_widget(Label()) 
        self.kapat_butonu = Button(text="KAPAT", size_hint_x=None, width=dp(100), background_color=(0.6, 0.1, 0.1, 1), bold=True)
        self.kapat_butonu.bind(on_release=self.pencereyi_kapat)
        alt_buton_cubugu.add_widget(self.kapat_butonu)
        self.add_widget(alt_buton_cubugu)

        # Event Bindings
        self.bul_firma_input.bind(text=self.filtrele)
        self.bul_firma_spinner.bind(text=self.teklifleri_listele)
        # Event Bindings (En alttaki toplu kısım şöyle görünmeli)
        self.bul_firma_input.bind(text=self.filtrele)
        self.bul_firma_spinner.bind(text=self.teklifleri_listele)
        # btn_ara satırı silindi, yerine hiçbir şey koymana gerek yok çünkü yukarıda bağladık.        btn_temizle.bind(on_release=self.ekran_temizle)
        btn_duzenle.bind(on_release=self.teklifi_sadece_goruntule)

    def konu_ile_bul(self, instance):
        anahtar_kelime = self.konu_ara_input.text.strip().upper()
        if not anahtar_kelime:
            print("Lütfen aranacak bir konu yazın!")
            return

        try:
            # Firebase'den tüm teklifleri çekiyoruz
            res = requests.get(f"{FIREBASE_URL}/{self.isletme}/teklifler.json")
            if res.status_code == 200 and res.json():
                self.liste_grid.clear_widgets() # Listeyi temizleyip eşleşenleri gösterelim
                bulundu = False
                
                for firma, teklifler in res.json().items():
                    # teklifler bir sözlük (dict) olmalı, değilse atla
                    if not isinstance(teklifler, dict): continue
                    
                    for t_no, veri in teklifler.items():
                        # Veri yapısı kontrolü: Bazı kayıtlar 'json_verisi' içinde olabilir
                        icerik = veri.get("json_verisi", veri) if isinstance(veri, dict) else {}
                        
                        teklif_konusu = str(icerik.get("konu", "")).upper()
                        
                        if anahtar_kelime in teklif_konusu:
                            # BULUNDU: Önce aktif veriyi set edelim
                            self.aktif_veri = veri
                            # Ekranda listeye ekleyelim (opsiyonel ama kullanıcı için daha iyi)
                            self.listeye_satir_ekle(t_no, icerik) 
                            bulundu = True
                
                if bulundu:
                    # Eğer en az bir tane bulunduysa, en sonuncuyu direkt açabilirsin
                    # veya kullanıcının listeden seçmesini bekleyebilirsin.
                    # Direkt açmak istersen: self.teklifi_sadece_goruntule(None)
                    print(f"'{anahtar_kelime}' ile eşleşen kayıtlar listelendi.")
                else:
                    print(f"'{anahtar_kelime}' içeren bir teklif bulunamadı.")
        except Exception as e:
            print(f"Hata oluştu: {e}")

    # Yardımcı fonksiyon: Bulunanları ekrana basmak için
    def listeye_satir_ekle(self, t_id, d):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=20)
        cb = CheckBox(size_hint_x=0.10, color=(0,0,0,1), group="sec")
        cb.bind(active=lambda inst, val, v=d: self.secim_yap(v, val))
        
        lbl_no = Label(text=str(d.get("no", t_id)), color=(0,0,0,1), size_hint_x=0.30, halign='left', valign='middle', font_size='13sp')        
        lbl_no.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None))) 
        lbl_konu = Label(text=str(d.get("konu", "---")), color=(0,0,0,1), size_hint_x=0.60, halign='left', valign='middle', font_size='13sp')
        lbl_konu.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        
        row.add_widget(cb)
        row.add_widget(lbl_no)
        row.add_widget(lbl_konu)
        self.liste_grid.add_widget(row)


    def no_ile_direkt_ac(self, instance):
        hedef_no = self.secili_no_input.text.strip()
        if not hedef_no:
            print("Lütfen bir numara yazın!")
            return

        # Firebase'den tüm teklifleri çekip içinde bu numarayı arayalım
        try:
            res = requests.get(f"{FIREBASE_URL}/{self.isletme}/teklifler.json")
            if res.status_code == 200 and res.json():
                for firma, teklifler in res.json().items():
                    if hedef_no in teklifler:
                        # Teklifi bulduk!
                        self.aktif_veri = teklifler[hedef_no]
                        self.teklifi_sadece_goruntule(None) # Mevcut görüntüleme fonksiyonunu tetikle
                        return
                
                # Döngü biterse bulunamamıştır
                print(f"{hedef_no} bulunamadı.")
        except Exception as e:
            print(f"Bağlantı hatası: {e}")


    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos; self.rect.size = instance.size

    def musterileri_getir(self):
        try:
            res = requests.get(f"{FIREBASE_URL}/{self.isletme}/teklifler.json?shallow=true", timeout=5)
            if res.status_code == 200 and res.json():
                return sorted([str(k) for k in res.json().keys()])
        except: pass
        return []

    def filtrele(self, instance, value):
        self.bul_firma_spinner.values = [f for f in self.musterileri_getir() if value.upper() in f.upper()]

    def teklifleri_listele(self, instance, firma_adi):
        if not firma_adi or firma_adi == "Müşteri Seç": return
        self.liste_grid.clear_widgets()
        try:
            res = requests.get(f"{FIREBASE_URL}/{self.isletme}/teklifler/{firma_adi}.json")
            if res.status_code == 200 and res.json():
                for t_id, veri in res.json().items():
                    d = veri.get("json_verisi", veri) 
                    
                    # teklifleri_listele fonksiyonu içindeki ilgili kısım:
                    row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=20) # Spacing 20 yapıldı
                    
                    # 1. Seç (Checkbox) - Oran 0.15 yapıldı
                    cb = CheckBox(size_hint_x=0.15, color=(0,0,0,1), group="sec")
                    cb.bind(active=lambda inst, val, v=veri: self.secim_yap(v, val))
                    
                    # 2. TEKLİF NO - Oran 0.30 yapıldı
                    lbl_no = Label(text=str(d.get("no", t_id)), color=(0,0,0,1), size_hint_x=0.50, halign='left', valign='middle')
                    lbl_no.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
                    
                    # 3. KONU - Oran 0.60 yapıldı
                    lbl_konu = Label(text=str(d.get("konu", "---")), color=(0,0,0,1), size_hint_x=0.35, halign='left', valign='middle', font_size='13sp')
                    lbl_konu.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))  
                                      
                    row.add_widget(cb)
                    row.add_widget(lbl_no)
                    row.add_widget(lbl_konu)
                    
                    self.liste_grid.add_widget(row)
        except Exception as e:
            print(f"Hata: {e}")

    def secim_yap(self, veri, aktif):
        self.aktif_veri = veri if aktif else None

    def teklifi_sadece_goruntule(self, instance):
        if not self.aktif_veri:
            print("Lütfen listeden bir teklif seçin!")
            return
            
        import yeni_teklif
        importlib.reload(yeni_teklif)
        form = yeni_teklif.ekrani_olustur()
        if isinstance(form, Popup): form = form.content
        
        # Veriyi aktar
        veri_detay = self.aktif_veri.get("json_verisi", self.aktif_veri)
        self.forma_aktar(form, veri_detay)
        
        # --- KİLİTLEME MANTIĞI ---
        # Form üzerindeki tüm TextInput'ları bul ve etkisizleştir (disabled)
        def kilitle(widget):
            if hasattr(widget, 'children'):
                for child in widget.children:
                    if isinstance(child, TextInput):
                        child.readonly = True
                        child.background_color = (0.9, 0.9, 0.9, 1) # Gri yaparak kilitli olduğunu belli et
                    kilitle(child)
        
        kilitle(form)
        
        # Eğer formda 'KAYDET' butonu varsa onu da gizleyelim veya devre dışı bırakalım
        # Genelde yeni_teklif içinde b_kaydet gibi bir isimle bulunur
        for child in form.walk():
            if isinstance(child, Button) and "KAYDET" in child.text.upper():
                child.disabled = True
                child.text = "SADECE OKUNUR MOD"

        # Popup olarak aç
        view_popup = Popup(title="Teklif Detayı (Düzenlemeye Kapalı)", content=form, size_hint=(0.95, 0.95))
        view_popup.open()

    def forma_aktar(self, form, icerik):
        try:
            form.firma_manuel.text = str(icerik.get("musteri", icerik.get("firma", "")))
            form.teklif_no.text = str(icerik.get("no", ""))
            form.tarih_input.text = str(icerik.get("tarih", ""))
            form.ilgili.text = str(icerik.get("ilgili", ""))
            form.konu.text = str(icerik.get("konu", ""))
            form.hitap.text = str(icerik.get("hitap", ""))
            form.giris_metni.text = str(icerik.get("giris_metni", icerik.get("giris", "")))

            if hasattr(form, 'urun_alani'):
                form.urun_alani.clear_widgets()
                form.urun_satirlari_listesi = []
                for k in icerik.get("kalemler", []):
                    form.satir_ekle()
                    yeni_satir = form.urun_satirlari_listesi[-1]
                    yeni_satir.widgets['aciklama'].text = str(k.get("u", ""))
                    yeni_satir.widgets['miktar'].text = str(k.get("m", ""))
                    yeni_satir.widgets['fiyat'].text = str(k.get("f", ""))
        except Exception as e:
            print(f"Aktarma Hatası: {e}")

    def teklif_mail(self, instance):
        if not self.aktif_veri: return
        d = self.aktif_veri.get("json_verisi", self.aktif_veri)
        subject = f"Teklif: {d.get('musteri', '')}"
        body = f"Sayın Yetkili,%0D%0A{d.get('no')} nolu teklifimiz ekte sunulmuştur."
        webbrowser.open(f"mailto:?subject={subject}&body={body}")

    def teklif_yazdir(self, instance):
        if not self.aktif_veri: return
        # Yazdırma için verinin URL'sini tarayıcıda açar
        d = self.aktif_veri.get("json_verisi", self.aktif_veri)
        firma = d.get('musteri', '').replace(" ", "%20")
        no = d.get('no', '')
        url = f"{FIREBASE_URL}/{self.isletme}/teklifler/{firma}/{no}.json"
        webbrowser.open(url)

    def pencereyi_kapat(self, instance):
        p = self.parent
        while p:
            if isinstance(p, Popup): p.dismiss(); break
            p = p.parent

    def ekran_temizle(self, instance):
        self.bul_firma_input.text = ""
        self.bul_firma_spinner.text = "Müşteri Seç"
        self.secili_no_input.text = ""
        self.konu_ara_input.text = ""  # Yeni eklenen alan temizleniyor
        self.liste_grid.clear_widgets()
        self.aktif_veri = None # Seçili veriyi de sıfırla
def ekrani_olustur():
    icerik = TeklifDuzenle()
    # BURASI ÖNEMLİ: Ana dosyanda popup olarak açılması için Popup nesnesi döndürüyoruz.
    return Popup(title="Kayıtlı Teklifleri Yönet", content=icerik, size_hint=(0.95, 0.95))