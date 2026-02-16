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
    
    # 1. Müşteri Seçimi (Satış Faturalarından Çekilecek)
    sol_kutu = BoxLayout(orientation='vertical', spacing='5dp')
    sol_kutu.add_widget(Label(text="MÜŞTERİ SEÇİMİ", bold=True, halign='left', text_size=(250, None)))
    
    spin_musteri = Spinner(
        text="Seçiniz...", values=(),
        background_color=(0.1, 0.4, 0.6, 1), # Müşteri için Mavi Tonu
        halign='left', padding=(15, 0)
    )
    spin_musteri.option_cls.halign = 'left'
    sol_kutu.add_widget(spin_musteri)
    
    # 2. Tutar Girişi
    sag_kutu = BoxLayout(orientation='vertical', spacing='5dp', size_hint_x=0.5)
    sag_kutu.add_widget(Label(text="ALINAN (TL)", bold=True))
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
        size_hint=(0.95, 0.30) 
    )

    # --- KAYIT FONKSİYONU (Tahsilat/Müşteri Versiyonu) ---
    def tahsilat_isleme(firma_ham, formatli_tutar):
        try:
            alinan_tutar = float(formatli_tutar.replace(".", ""))
            # Tedarikçideki gibi ismi bozmadan alıyoruz (MercanKağıt sorunu çözümü)
            firma = firma_ham.strip() 

            # 1. Hareket Kaydı (Müşteriden para girişi: +)
            requests.post(f"{FIREBASE_URL}/hareketler/{firma}.json", json={
                "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "tip": "Tahsilat",
                "tutar": alinan_tutar,
                "aciklama": "Müşteri Ödemesi"
            })

            # 2. Cari Borç Güncelleme
            r_cari = requests.get(f"{FIREBASE_URL}/musteriler/{firma}.json")
            mevcut_alacak = float(r_cari.json().get("bakiye", 0)) if r_cari.status_code == 200 and r_cari.json() else 0.0
            
            # Müşterinin borcu 10.000 ise 2.000 ödeyince 8.000 kalır
            yeni_bakiye = mevcut_alacak - alinan_tutar
            kalan_para = alinan_tutar

            # 3. FIFO (Satış Faturalarını Kapatma)
            r_fat = requests.get(f"{FIREBASE_URL}/satis_faturalari/{firma}.json")
            if r_fat.status_code == 200 and r_fat.json():
                faturalar = sorted(r_fat.json().items(), key=lambda x: x[1].get('TARİH', '01.01.2026'))
                for f_no, f_detay in faturalar:
                    if f_detay.get("DURUM") == "Ödenmiş": continue
                    f_tut = float(str(f_detay.get('TOPLAM','0')).replace("TL","").replace(".","").replace(",",".").strip())
                    if kalan_para >= f_tut:
                        requests.patch(f"{FIREBASE_URL}/satis_faturalari/{firma}/{f_no}.json", json={"DURUM": "Ödenmiş"})
                        kalan_para -= f_tut
                    else: break

            requests.patch(f"{FIREBASE_URL}/musteriler/{firma}.json", json={"bakiye": yeni_bakiye})
            ana_popup.dismiss()
            Popup(title="BAŞARILI", content=Label(text=f"{formatli_tutar} TL Tahsil Edildi."), size_hint=(None,None), size=('300dp', '150dp')).open()

        except Exception as e: print(f"Hata: {e}")

    # --- ONAY ---
    def onay_penceresi_ac(instance):
        if spin_musteri.text == "Seçiniz..." or not txt_tutar.text: return
        box = BoxLayout(orientation='vertical', padding=15, spacing=15)
        box.add_widget(Label(text=f"[b]{spin_musteri.text}[/b]\n[color=00ff00]{txt_tutar.text} TL[/color]\nTahsilatı onaylıyor musunuz?", markup=True, halign='center'))
        btn_alani = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        btn_evet = Button(text="EVET", background_color=(0,1,0,1), bold=True)
        btn_hayir = Button(text="HAYIR", background_color=(1,0,0,1))
        btn_alani.add_widget(btn_evet); btn_alani.add_widget(btn_hayir); box.add_widget(btn_alani)
        o_pop = Popup(title="İşlem Onayı", content=box, size_hint=(None,None), size=('320dp', '220dp'))
        btn_evet.bind(on_release=lambda x: [o_pop.dismiss(), tahsilat_isleme(spin_musteri.text, txt_tutar.text)])
        btn_hayir.bind(on_release=o_pop.dismiss)
        o_pop.open()

    # --- ALT BUTONLAR ---
    alt_bolum = BoxLayout(size_hint_y=None, height='50dp', spacing='10dp')
    btn_kaydet = Button(text="TAHSİLAT KAYDET", background_color=(0.1, 0.4, 0.6, 1), bold=True)
    btn_iptal = Button(text="İPTAL", background_color=(0.5, 0.5, 0.5, 1))
    alt_bolum.add_widget(btn_kaydet); alt_bolum.add_widget(btn_iptal); ana_duzen.add_widget(alt_bolum)

    # --- VERİ ÇEKME (DOĞRU DÜĞÜM: satis_faturalari) ---
    try:
        r = requests.get(f"{FIREBASE_URL}/satis_faturalari.json")
        if r.status_code == 200 and r.json():
            spin_musteri.values = sorted(r.json().keys())
    except: pass

    btn_kaydet.bind(on_release=onay_penceresi_ac)
    btn_iptal.bind(on_release=ana_popup.dismiss)
    
    ana_popup.open()
    return Widget()
