from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
import requests
import os
import re
from datetime import datetime

# Firebase Ayarları
BASE_URL = os.environ.get("FIREBASE_URL", "").rstrip('/')
SECILI_ISLETME = os.environ.get("SECILI_ISLETME", "ONDULA")
FIREBASE_URL = f"{BASE_URL}/{SECILI_ISLETME}"

def ekrani_olustur():
    ana_duzen = BoxLayout(orientation='vertical', padding=20, spacing=15)
    
    # --- ÜST SATIR ---
    ust_satir = BoxLayout(size_hint_y=None, height='90dp', spacing='15dp')
    
    # 1. Tedarikçi Seçimi (Alış Faturalarından Çekilecek)
    sol_kutu = BoxLayout(orientation='vertical', spacing='5dp')
    sol_kutu.add_widget(Label(text="TEDARİKÇİ SEÇİMİ", bold=True, halign='left', text_size=(250, None)))
    
    spin_tedarikci = Spinner(
        text="Seçiniz...", values=(),
        background_color=(0.7, 0.3, 0.1, 1),
        halign='left', padding=(15, 0)
    )
    spin_tedarikci.option_cls.halign = 'left'
    sol_kutu.add_widget(spin_tedarikci)
    
    # 2. Tutar Girişi
    sag_kutu = BoxLayout(orientation='vertical', spacing='5dp', size_hint_x=0.5)
    sag_kutu.add_widget(Label(text="ÖDENECEK (TL)", bold=True))
    txt_tutar = TextInput(hint_text="0", multiline=False, font_size='20sp', input_type='number')

    def formatla(instance, value):
        sayi = re.sub(r'[^0-9]', '', value)
        if sayi:
            yeni_deger = "{:,}".format(int(sayi)).replace(",", ".")
            if instance.text != yeni_deger: instance.text = yeni_deger
        else: instance.text = ""

    txt_tutar.bind(text=formatla)
    sag_kutu.add_widget(txt_tutar)
    
    ust_satir.add_widget(sol_kutu)
    ust_satir.add_widget(sag_kutu)
    ana_duzen.add_widget(ust_satir)
    ana_popup = Popup(
        title='Tahsilat Girişi', 
        content=ana_duzen, 
        size_hint=(0.95, 0.30)  # Genişlik %95, Yükseklik %65
    )

    # --- KAYIT FONKSİYONU ---
    def odeme_isleme(firma_ham, formatli_tutar):
        try:
            odenen_tutar = float(formatli_tutar.replace(".", ""))
            # title() yerine sadece boşlukları temizle, Spinner'daki ismi bozma
            firma = firma_ham.strip() 


            # 1. Hareket Kaydı (Tedarikçi için para çıkışı: -)
            requests.post(f"{FIREBASE_URL}/hareketler/{firma}.json", json={
                "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "tip": "Ödeme",
                "tutar": -odenen_tutar,
                "aciklama": "Tedarikçi Ödemesi"
            })

            # 2. Cari Borç Güncelleme
            r_cari = requests.get(f"{FIREBASE_URL}/tedarikciler/{firma}.json")
            mevcut_borc = float(r_cari.json().get("bakiye", 0)) if r_cari.status_code == 200 and r_cari.json() else 0.0
            
            # Borcumuz 10.000 ise 2.000 ödeyince 8.000 kalır
            yeni_borc = mevcut_borc - odenen_tutar
            kalan_para = odenen_tutar

            # 3. FIFO (Alış Faturalarını Kapatma)
            r_fat = requests.get(f"{FIREBASE_URL}/alis_faturalari/{firma}.json")
            if r_fat.status_code == 200 and r_fat.json():
                faturalar = sorted(r_fat.json().items(), key=lambda x: datetime.strptime(x[1].get('TARİH', '01.01.2026'), '%d.%m.%Y'))
                for f_no, f_detay in faturalar:
                    if f_detay.get("DURUM") == "Ödenmiş": continue
                    f_tut = float(str(f_detay.get('TOPLAM','0')).replace("TL","").replace(".","").replace(",",".").strip())
                    if kalan_para >= f_tut:
                        requests.patch(f"{FIREBASE_URL}/alis_faturalari/{firma}/{f_no}.json", json={"DURUM": "Ödenmiş"})
                        kalan_para -= f_tut
                    else: break

            requests.patch(f"{FIREBASE_URL}/tedarikciler/{firma}.json", json={"bakiye": yeni_borc})
            ana_popup.dismiss()
            Popup(title="BAŞARILI", content=Label(text=f"{formatli_tutar} TL Ödeme Yapıldı."), size_hint=(None,None), size=('300dp', '150dp')).open()

        except Exception as e: print(f"Hata: {e}")

    # --- ONAY ---
    def onay_penceresi_ac(instance):
        if spin_tedarikci.text == "Seçiniz..." or not txt_tutar.text: return
        box = BoxLayout(orientation='vertical', padding=15, spacing=15)
        box.add_widget(Label(text=f"[b]{spin_tedarikci.text}[/b]\n[color=ff3333]{txt_tutar.text} TL[/color]\nÖdemeyi onaylıyor musunuz?", markup=True, halign='center'))
        btn_alani = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        btn_evet = Button(text="EVET", background_color=(0,1,0,1), bold=True)
        btn_hayir = Button(text="HAYIR", background_color=(1,0,0,1))
        btn_alani.add_widget(btn_evet); btn_alani.add_widget(btn_hayir); box.add_widget(btn_alani)
        o_pop = Popup(title="İşlem Onayı", content=box, size_hint=(None,None), size=('320dp', '220dp'))
        btn_evet.bind(on_release=lambda x: [o_pop.dismiss(), odeme_isleme(spin_tedarikci.text, txt_tutar.text)])
        btn_hayir.bind(on_release=o_pop.dismiss)
        o_pop.open()

    # --- ALT BUTONLAR ---
    alt_bolum = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
    btn_kaydet = Button(text="ÖDEMEYİ KAYDET", background_color=(0.8, 0.3, 0.1, 1), bold=True)
    btn_iptal = Button(text="İPTAL", background_color=(0.5, 0.5, 0.5, 1))
    alt_bolum.add_widget(btn_kaydet); alt_bolum.add_widget(btn_iptal); ana_duzen.add_widget(alt_bolum)

    # --- VERİ ÇEKME (DOĞRU DÜĞÜM: alis_faturalari) ---
    try:
        r = requests.get(f"{FIREBASE_URL}/alis_faturalari.json") # Burayı düzelttim!
        if r.status_code == 200 and r.json():
            spin_tedarikci.values = sorted(r.json().keys())
    except: pass

    btn_kaydet.bind(on_release=onay_penceresi_ac)
    btn_iptal.bind(on_release=ana_popup.dismiss)
    
    ana_popup.open()
    return Widget()