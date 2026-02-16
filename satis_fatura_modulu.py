from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
import os
import requests
from datetime import datetime

# --- BULUT AYARI ---
def get_firebase_url():
    return os.environ.get("FIREBASE_URL", "").strip("/")

def format_tr(sayi):
    try:
        if isinstance(sayi, (float, int)):
            f_sayi = float(sayi)
        else:
            s_metin = str(sayi).replace("TL", "").replace(" ", "").strip()
            if "," in s_metin:
                f_sayi = float(s_metin.replace(".", "").replace(",", "."))
            else:
                f_sayi = float(s_metin)
        s = "{:,.2f}".format(f_sayi)
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".") + " TL"
    except:
        return "0,00 TL"

def ekrani_olustur():
    gokyuzu_mavisi = (0.3, 0.6, 1, 1) 
    ana_duzen = BoxLayout(orientation='vertical', padding=[20, 220, 20, 20], spacing=30)
    
    ana_duzen.add_widget(Label(
        text="SATIŞ FATURASI YÖNETİMİ", 
        font_size='18sp', bold=True, size_hint_y=None, height=50
    ))
    
    btn_yeni = Button(
        text="YENİ", background_normal='', background_color=gokyuzu_mavisi, 
        bold=True, size_hint=(None, None), size=(200, 60), pos_hint={'center_x': 0.5}
    )
    btn_yeni.bind(on_release=lambda x: fatura_penceresi().open())
    
    ana_duzen.add_widget(btn_yeni)
    ana_duzen.add_widget(Widget()) 
    return ana_duzen

def fatura_penceresi(aktarilan_siparisler=None):
    ana_icerik = BoxLayout(orientation='vertical', padding=20, spacing=5)
    satir_objeleri = []
    isletme = os.environ.get("SECILI_ISLETME", "AMD")
    url = get_firebase_url()

    def hata_mesaji_ver(metin):
        icerik = BoxLayout(orientation='vertical', padding=20, spacing=10)
        icerik.add_widget(Label(text=metin, halign='center'))
        btn_t = Button(text="TAMAM", size_hint_y=None, height=50, background_color=(0.1, 0.5, 0.8, 1))
        icerik.add_widget(btn_t)
        h_pop = Popup(title="Uyarı", content=icerik, size_hint=(0.6, 0.4))
        btn_t.bind(on_release=h_pop.dismiss); h_pop.open()

    # --- MÜŞTERİ VE MEVCUT KAYITLARI ÇEKME ---
    musteriler = set()
    try:
        # 1. Sabit Müşteriler listesini çek
        res_t = requests.get(f"{url}/{isletme}/musteriler.json", timeout=5)
        if res_t.status_code == 200 and res_t.json():
            for k, icerik in res_t.json().items():
                if isinstance(icerik, dict) and "veri" in icerik:
                    for l in icerik["veri"].split("\n"):
                        if "FIRMA" in l:
                            isim = l.split(":", 1)[1].strip()
                            if isim: musteriler.add(isim)
        
        # 2. satış Faturaları altındaki kayıtlı firmaları çek (Gruplandırma için)
        res_f = requests.get(f"{url}/{isletme}/satis_faturalari.json?shallow=true", timeout=5)
        if res_f.status_code == 200 and res_f.json():
            for firma_adi in res_f.json().keys():
                musteriler.add(firma_adi.replace("_", "."))
    except: pass
    
    musteri_listesi = sorted(list(musteriler))

    # --- Üst Bilgiler (Height: 80) ---
    ust_satir = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=80)
    musteri_input = TextInput(hint_text="Müşteri Seç/Yaz...", multiline=False, size_hint_x=0.4)
    fatura_no = TextInput(hint_text="Fatura No", multiline=False, size_hint_x=0.3)
    tarih = TextInput(text=datetime.now().strftime("%d.%m.%Y"), size_hint_x=0.3)
    ust_satir.add_widget(musteri_input); ust_satir.add_widget(fatura_no); ust_satir.add_widget(tarih)
    ana_icerik.add_widget(ust_satir)

    # Öneri Listesi Katmanı
    dropdown_katmani = BoxLayout(orientation='horizontal', size_hint_y=None, height=0)
    oneri_scroll = ScrollView(size_hint_x=0.4, size_hint_y=None, height=0)
    oneri_listesi = GridLayout(cols=1, size_hint_y=None, spacing=5)
    oneri_listesi.bind(minimum_height=oneri_listesi.setter('height'))
    oneri_scroll.add_widget(oneri_listesi); dropdown_katmani.add_widget(oneri_scroll)
    dropdown_katmani.add_widget(BoxLayout(size_hint_x=0.6)); ana_icerik.add_widget(dropdown_katmani)

    def secim_yap(instance):
        musteri_input.text = instance.text
        oneri_scroll.height = 0; dropdown_katmani.height = 0
        musteri_input.focus = False

    def onerileri_guncelle(instance, value, is_focus=False):
        oneri_listesi.clear_widgets()
        if instance.focus or is_focus:
            arama_metni = value.lower() if value else ""
            uygun = [t for t in musteri_listesi if arama_metni in t.lower()]
            if uygun:
                h = min(len(uygun) * 60, 180)
                oneri_scroll.height = h; dropdown_katmani.height = h
                for t in uygun:
                    b = Button(text=t, size_hint_y=None, height=60, background_color=(0.2, 0.6, 1, 1))
                    b.bind(on_press=secim_yap); oneri_listesi.add_widget(b)
                return
        oneri_scroll.height = 0; dropdown_katmani.height = 0

    musteri_input.bind(text=lambda ins, val: onerileri_guncelle(ins, val))
    musteri_input.bind(focus=lambda ins, foc: onerileri_guncelle(ins, ins.text, is_focus=foc))

    # Hesaplama Labellerı
    ara_lab = Label(text="0,00 TL", bold=True)
    kdv_lab = Label(text="0,00 TL", bold=True)
    genel_toplam_lab = Label(text="0,00 TL", bold=True, color=(0,1,0,1))
    isk_inp = TextInput(text="0", input_filter='float', multiline=False)
    kdv_kontrol = CheckBox(active=True, size_hint_x=None, width=40)
    kdv_oran_inp = TextInput(text="20", input_filter='float', multiline=False, size_hint_x=None, width=50)

    def kdv_checkbox_tetiklendi(checkbox, value):
        if value: # Eğer CheckBox işaretli ise
            kdv_oran_inp.text = "20"
            kdv_oran_inp.disabled = False # Manuel girişe izin ver
        else: # Eğer CheckBox işareti kaldırıldıysa
            kdv_oran_inp.text = "0"
            kdv_oran_inp.disabled = True # 0 iken girişi kilitlemek istersen (isteğe bağlı)
        
        hesapla() # Değer değişince toplamı da anında güncelle

    kdv_kontrol.bind(active=kdv_checkbox_tetiklendi)

    def hesapla(*args):
        ara = 0.0
        for s in satir_objeleri:
            try:
                f_text = s['f'].text.replace(',', '.')
                m_text = s['m'].text.replace(',', '.')
                f = float(f_text) if f_text and f_text != "." else 0.0
                m = float(m_text) if m_text and m_text != "." else 0.0
                s_ara = f * m
                s['t'].text = format_tr(s_ara)
                ara += s_ara
            except: continue
        isk_oran = float(isk_inp.text) if (isk_inp.text and isk_inp.text != ".") else 0.0
        ara_iskontolu = ara - (ara * (isk_oran / 100))
        kdv_oran = float(kdv_oran_inp.text) if (kdv_oran_inp.text and kdv_oran_inp.text != ".") else 0.0
        kdv_t = (ara_iskontolu * (kdv_oran/100)) if kdv_kontrol.active else 0.0
        ara_lab.text = format_tr(ara)
        kdv_lab.text = format_tr(kdv_t)
        genel_toplam_lab.text = format_tr(ara_iskontolu + kdv_t)

    # Başlıklar (Height: 40)
    basliklar = GridLayout(cols=6, size_hint_y=None, height=40, spacing=2)
    for m, o in zip(["Ürün Adı", "Miktar", "Birim", "B.Fiyat", "", "Toplam"], [3.0, 0.6, 0.6, 0.8, 0.3, 1]):
        basliklar.add_widget(Button(text=m, background_color=(0.2, 0.2, 0.2, 1), disabled=True, size_hint_x=o, font_size='11sp'))
    ana_icerik.add_widget(basliklar)

    # Satırlar Scroll (Size Hint: 0.5)
    scroll = ScrollView(size_hint=(1, 0.5))
    satir_konu = GridLayout(cols=1, size_hint_y=None, spacing=2)
    satir_konu.bind(minimum_height=satir_konu.setter('height'))
    scroll.add_widget(satir_konu); ana_icerik.add_widget(scroll)

    def satir_ekle(instance=None):
        satir = GridLayout(cols=6, size_hint_y=None, height=60, spacing=2)
        u = TextInput(hint_text="Ürün...", size_hint_x=3.0)
        m = TextInput(input_filter='float', hint_text="0", size_hint_x=0.6)
        b_sp = Spinner(text="ad", values=("ad", "kg", "mt", "pk"), size_hint_x=0.6)
        f = TextInput(input_filter='float', hint_text="0.00", size_hint_x=0.8)
        t_l = Label(text="0,00 TL", bold=True, size_hint_x=1)
        for i in [f, m]: i.bind(text=hesapla)
        satir.add_widget(u); satir.add_widget(m); satir.add_widget(b_sp); satir.add_widget(f); 
        satir.add_widget(Label(text="TL", size_hint_x=0.3)); satir.add_widget(t_l)
        satir_konu.add_widget(satir)
        satir_objeleri.append({'u':u, 'f':f, 'm':m, 'b':b_sp, 't':t_l, 'layout': satir})

    # Buton Bar (Height: 60)
    btn_bar = BoxLayout(size_hint_y=None, height=60, spacing=10)
    btn_e = Button(text="SATIR EKLE", background_color=(0.2, 0.6, 1, 1), bold=True); btn_e.bind(on_release=satir_ekle)
    btn_s = Button(text="SATIR SİL", background_color=(1, 0.3, 0.3, 1), bold=True)
    btn_s.bind(on_release=lambda x: (satir_konu.remove_widget(satir_objeleri.pop()['layout']), hesapla()) if len(satir_objeleri)>1 else None)
    btn_bar.add_widget(btn_e); btn_bar.add_widget(btn_s); ana_icerik.add_widget(btn_bar)

    # Alt Panel (Height: 180)
    alt_panel = BoxLayout(orientation='horizontal', size_hint_y=None, height=300, spacing=10)
    sol = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=10)
    kaydet = Button(text="FATURAYI KAYDET", background_color=(0.1, 0.7, 0.3, 1), bold=True)
    vazgec = Button(text="İPTAL / KAPAT", background_color=(0.8, 0.2, 0.2, 1), bold=True)
    sol.add_widget(kaydet); sol.add_widget(vazgec)

    sag = GridLayout(cols=2, size_hint_x=0.6, spacing=5)
    sag.add_widget(Label(text="Ara Toplam:")); sag.add_widget(ara_lab)
    sag.add_widget(Label(text="İskonto (%):")); sag.add_widget(isk_inp)

    # k_kutu düzenlemesi: Textbox genişletildi, Checkbox sağa itildi
    k_kutu = BoxLayout(spacing=10, padding=[10, 0, 0, 0]) 
    
    # Textbox'ı biraz daha genişletmek için size_hint_x'i 0.6 yapıyoruz (eskisi çok küçüktü)
    kdv_oran_inp.size_hint_x = 0.6 
    
    # Checkbox'ı sağa yaslamak için araya boş bir Widget (esnek boşluk) atıyoruz
    k_kutu.add_widget(kdv_oran_inp)
    k_kutu.add_widget(Widget()) # Bu aradaki tüm boşluğu emerek Checkbox'ı sağa itecek
    k_kutu.add_widget(kdv_kontrol)
    
    sag.add_widget(Label(text="KDV %:")); sag.add_widget(k_kutu)

    sag.add_widget(Label(text="GENEL TOPLAM:", color=(0,1,0,1))); sag.add_widget(genel_toplam_lab)
    stok_dus_kontrol = CheckBox(active=False, size_hint_x=None, width=40)
    sag.add_widget(Label(text="[i]Stoktan Düş[/i]", markup=True, font_size='12sp')); sag.add_widget(stok_dus_kontrol)
    alt_panel.add_widget(sol); alt_panel.add_widget(sag); ana_icerik.add_widget(alt_panel)

    satir_ekle(); isk_inp.bind(text=hesapla); kdv_kontrol.bind(active=hesapla); kdv_oran_inp.bind(text=hesapla)

    # --- POPUP TANIMI ---
    pop = Popup(title="Yeni satış Faturası Girişi", content=ana_icerik, size_hint=(0.98, 0.98))
    vazgec.bind(on_release=pop.dismiss)

    # --- GRUPLANDIRILMIŞ KAYIT FONKSİYONU ---
    def stok_dus_islemi(urunler, aktarilan_siparisler=None):
        isletme_adi = os.environ.get("SECILI_ISLETME", "ONDULA")
        url = get_firebase_url()

        try:
            # 1. Stokları güncel halini çek
            res_stoklar = requests.get(f"{url}/{isletme_adi}/stok.json", timeout=5).json()
            if not res_stoklar: return

            for kalem in urunler:
                # Faturadaki ürün adını al (Örn: "Mercan")
                fatura_urun_adi = str(kalem.get('urun', '')).strip().lower()
                
                if any(x in fatura_urun_adi for x in ["işçilik", "fason", "nakliye"]): 
                    continue
                
                bulunan_key = None
                # 2. Esnek İsim Eşleşmesi
                for firebase_key in res_stoklar.keys():
                    stok_anahtar_adi = str(firebase_key).lower().strip()
                    
                    # Tam eşleşme veya kapsama kontrolü (Mercan == mercan)
                    if fatura_urun_adi == stok_anahtar_adi or fatura_urun_adi in stok_anahtar_adi:
                        bulunan_key = firebase_key
                        break
                
                if bulunan_key:
                    try:
                        # 3. String Miktarları Sayıya Çevirme (Örn: "500" -> 500.0)
                        mevcut_stok_miktari = float(str(res_stoklar[bulunan_key]).replace(',', '.'))
                        
                        # Düşülecek miktarı faturadan al (Örn: "200")
                        dusulecek_miktar = float(str(kalem.get('miktar', '0')).replace(',', '.'))
                        
                        yeni_stok = max(0, mevcut_stok_miktari - dusulecek_miktar)
                        
                        # 4. Firebase Güncelleme
                        requests.patch(f"{url}/{isletme_adi}/stok.json", 
                                    json={bulunan_key: str(yeni_stok)}, timeout=5)
                        print(f"BAŞARILI: {bulunan_key} yeni stok: {yeni_stok}")
                        
                    except Exception as e:
                        print(f"Sayısal dönüşüm hatası ({bulunan_key}): {e}")
                else:
                    print(f"UYARI: '{kalem.get('urun')}' ismi stokta bulunamadı!")

        except Exception as e:
            print(f"Sistem Hatası: {e}")

        # Sipariş Kapatma (faturalandi yapma)
        if aktarilan_siparisler:
            for sid, firma in aktarilan_siparisler:
                requests.patch(f"{url}/{isletme_adi}/siparisler/{firma}/{sid}.json", 
                            json={"durum": "faturalandi"}, timeout=5)
                           
    def fatura_kaydet(instance):
            # 1. Temel Bilgi Kontrolü
        if not musteri_input.text.strip() or not fatura_no.text.strip():
            hata_mesaji_ver("Müşteri ve Fatura No boş olamaz!")
            return

        # 2. Ürün ve Tutar Kontrolü
        urun_listesi = []
        for s in satir_objeleri:
            u_adi = s['u'].text.strip()
            miktar = s['m'].text.strip()
            fiyat = s['f'].text.strip()

            if u_adi: # Sadece ürün adı girilmiş satırları dikkate al
                if not miktar or float(miktar.replace(',', '.')) <= 0:
                    hata_mesaji_ver(f"'{u_adi}' için miktar girmelisiniz!")
                    return
                if not fiyat or float(fiyat.replace(',', '.')) <= 0:
                    hata_mesaji_ver(f"'{u_adi}' için fiyat girmelisiniz!")
                    return
                    
                urun_listesi.append({
                    "urun": u_adi, "miktar": miktar, 
                    "birim": s['b'].text, "fiyat": fiyat, "toplam": s['t'].text
                })

        if not urun_listesi:
            hata_mesaji_ver("En az bir geçerli ürün satırı girmelisiniz!")
            return

        if not musteri_input.text.strip() or not fatura_no.text.strip():
            hata_mesaji_ver("Müşteri ve Fatura No boş olamaz!"); return
        
        urun_listesi = []
        for s in satir_objeleri:
            if s['u'].text.strip():
                urun_listesi.append({
                    "urun": s['u'].text, "miktar": s['m'].text, 
                    "birim": s['b'].text, "fiyat": s['f'].text, "toplam": s['t'].text
                })
        
        fatura_verisi = {
            "FIRMA": musteri_input.text.strip(),
            "NO": fatura_no.text.strip(),
            "TARİH": tarih.text,
            "TOPLAM": genel_toplam_lab.text,
            "DURUM": "Bekliyor",
            "URUNLER": urun_listesi,
            # EĞER ALTTAKİ 4 SATIR DOSYANDA YOKSA KAYDETMEZ!
            "ISKONTO_ORANI": isk_inp.text or "0",
            "KDV_ORANI": kdv_oran_inp.text or "20",
            "KDV_ETKIN": kdv_kontrol.active, 
            "ARA_TOPLAM": ara_lab.text
        }
        
        try:
            # Firebase yollarında nokta (.) yasaktır, alt tireye çeviriyoruz
            f_key = fatura_no.text.replace(".", "_")
            t_key = musteri_input.text.replace(".", "_").strip()
            
            # YENİ YOL: satis_faturalari / FIRMA_ADI / FATURA_NO
            yol = f"{url}/{isletme}/satis_faturalari/{t_key}/{f_key}.json"

                # --- TEKRAR KONTROLÜ ---
            # Önce bu adreste veri var mı diye bakıyoruz (GET sorgusu)
            kontrol_res = requests.get(yol, timeout=5)
            if kontrol_res.status_code == 200 and kontrol_res.json() is not None:
                hata_mesaji_ver(f"HATA: {fatura_no.text} numaralı fatura zaten kayıtlı!")
                return
            # -----------------------
            
            res = requests.put(yol, json=fatura_verisi, timeout=5)
            if res.status_code == 200:
                # Eğer Checkbox işaretli ise hem stok düşer hem siparişleri etiketler [cite: 2026-02-01]
                if stok_dus_kontrol.active:
                    stok_dus_islemi(urun_listesi, aktarilan_siparisler) 
                
                pop.dismiss()     

            else:
                hata_mesaji_ver(f"Hata: {res.status_code}")
        except:
            hata_mesaji_ver("Bulut bağlantı hatası!")

    kaydet.bind(on_release=fatura_kaydet)
    return pop

