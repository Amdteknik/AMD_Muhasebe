from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.utils import platform
import os
import importlib
import giris_modulu 
from kivy.clock import Clock

# --- EKRAN AYARLARI ---
os.environ["KIVY_METRICS_DENSITY"] = "3"
os.environ["KIVY_METRICS_FONTSCALE"] = "1.0"

if platform not in ['android', 'ios']:
    Window.size = (300, 500)
else:
    Window.softinput_mode = 'below_target'

class ImageButton(ButtonBehavior, Image):
    pass

class MainLauncher(App):
    def build(self):
        self.root_container = BoxLayout()
        self.sifre_ekrani()
        return self.root_container


    def sifre_ekrani(self):
        self.root_container.clear_widgets()
        layout = FloatLayout()
        box = BoxLayout(orientation='vertical', size_hint=(0.8, 0.45), 
                        pos_hint={'center_x': 0.5, 'center_y': 0.5}, 
                        spacing='15dp', padding='20dp')
        
        box.add_widget(Label(text="GÜVENLİ GİRİŞ", font_size='28sp', bold=True, color=(0.1, 0.4, 0.9, 1)))
        
        self.sifre_input = TextInput(
            hint_text="Giriş Şifresi", 
            password=True, 
            multiline=False, 
            size_hint_y=None, 
            height='55dp',
            halign='center',
            font_size='20sp',
            input_filter='int'
        )
        box.add_widget(self.sifre_input)
        
        btn_giris = Button(
            text="SİSTEME GİRİŞ YAP", 
            size_hint_y=None, 
            height='60dp',
            background_color=(0.1, 0.6, 0.1, 1),
            bold=True
        )
        btn_giris.bind(on_release=self.sifre_kontrol)
        box.add_widget(btn_giris)
        
        layout.add_widget(box)
        self.root_container.add_widget(layout)

    def sifre_kontrol(self, instance):
        try:
            import ayarlar
            importlib.reload(ayarlar)
            dogru_sifre = str(getattr(ayarlar, 'GIRIS_SIFRESI', "1234"))
        except:
            dogru_sifre = "1234"

        if self.sifre_input.text == dogru_sifre:
            self.hosgeldiniz_sayfasi()
        else:
            instance.text = "HATALI ŞİFRE!"
            instance.background_color = (0.8, 0.1, 0.1, 1)
            self.sifre_input.text = ""
            Clock.schedule_once(lambda dt: self.reset_giris_butonu(instance), 2)

    def reset_giris_butonu(self, instance):
        instance.text = "SİSTEME GİRİŞ YAP"
        instance.background_color = (0.1, 0.6, 0.1, 1)

    def hosgeldiniz_sayfasi(self):
        self.root_container.clear_widgets()
        ana_dizin = os.path.dirname(os.path.abspath(__file__))
        os.chdir(ana_dizin)
            
        layout_katmanli = FloatLayout()
        main_box = BoxLayout(orientation='vertical', padding='35dp', spacing='20dp')
        
        header = BoxLayout(orientation='vertical', size_hint_y=0.33, spacing='10dp')
        header.add_widget(Label(text="HOŞGELDİNİZ", font_size='32sp', bold=True, halign='center', valign='middle'))
        header.add_widget(Label(text="[i]Lütfen bir işletme seçiniz[/i]", markup=True, font_size='18sp', color=(0.7, 0.7, 0.7, 1)))
        main_box.add_widget(header)

        logos_area = BoxLayout(orientation='horizontal', size_hint_y=0.33, spacing='25dp')
        btn_amd = ImageButton(source='AMD LOGO.jpg', allow_stretch=True, keep_ratio=True)
        btn_amd.bind(on_release=lambda x: self.uygulamayi_baslat("AMD"))
        btn_ondula = ImageButton(source='ONDULA LOGO.jpg', allow_stretch=True, keep_ratio=True)
        btn_ondula.bind(on_release=lambda x: self.uygulamayi_baslat("ONDULA"))
        
        logos_area.add_widget(btn_amd)
        logos_area.add_widget(btn_ondula)
        main_box.add_widget(logos_area)
        main_box.add_widget(BoxLayout(size_hint_y=0.33))
        
        resim_adi = 'ayarlar_butonu.jpg' 
        buton_yolu = os.path.join(ana_dizin, resim_adi)
        
        self.btn_ayarlar = Button(
            size_hint=(None, None), 
            size=('100dp', '100dp'),
            background_normal=buton_yolu,
            background_down=buton_yolu
        )
        self.btn_ayarlar.bind(on_release=self.ayarlar_popup_ac)

        layout_katmanli.add_widget(main_box)
        layout_katmanli.add_widget(self.btn_ayarlar)
        self.root_container.add_widget(layout_katmanli)

    def ayarlar_popup_ac(self, instance):
        icerik = BoxLayout(orientation='vertical', padding='15dp', spacing='10dp')
        
        import ayarlar
        importlib.reload(ayarlar)
        
        # --- SADECE GEREKLİ VERİLERİ ÇEK ---
        mevcut_url = getattr(ayarlar, 'FIREBASE_URL', "")
        mevcut_sifre = str(getattr(ayarlar, 'GIRIS_SIFRESI', "1234"))
        mevcut_g_url = getattr(ayarlar, 'GUNCELLEME_URL', "")

        # --- ARAYÜZ (Cloudinary Alanları Silindi) ---
        icerik.add_widget(Label(text="Güncelleme Paketi URL:", size_hint_y=None, height='25dp'))
        self.guncelleme_url_giris = TextInput(text=mevcut_g_url, multiline=False, size_hint_y=None, height='40dp')
        icerik.add_widget(self.guncelleme_url_giris)

        icerik.add_widget(Label(text="Firebase URL:", size_hint_y=None, height='25dp'))
        self.url_giris = TextInput(text=mevcut_url, multiline=False, size_hint_y=None, height='40dp')
        icerik.add_widget(self.url_giris)

        icerik.add_widget(Label(text="Giriş Şifresi:", size_hint_y=None, height='25dp'))
        self.sifre_yeni_giris = TextInput(text=mevcut_sifre, multiline=False, size_hint_y=None, height='40dp', input_filter='int')
        icerik.add_widget(self.sifre_yeni_giris)

        # Butonlar
        btn_guncelle = Button(text="SİSTEMİ GÜNCELLE", size_hint_y=None, height='45dp', background_color=(0.9, 0.5, 0.1, 1), bold=True)
        btn_guncelle.bind(on_release=self.guncellemeyi_baslat)
        icerik.add_widget(btn_guncelle)

        btn_url_kaydet = Button(text="AYARLARI KAYDET", size_hint_y=None, height='45dp', background_color=(0.1, 0.4, 0.9, 1), bold=True)
        btn_url_kaydet.bind(on_release=self.url_kaydet)
        icerik.add_widget(btn_url_kaydet)

        self.popup_ayar = Popup(title="Yönetim Paneli", content=icerik, size_hint=(0.9, 0.7)) 
        self.popup_ayar.open()

    def url_kaydet(self, instance):
        try:
            with open("ayarlar.py", "w", encoding="utf-8") as f:
                f.write(f'FIREBASE_URL = "{self.url_giris.text.strip()}"\n')
                f.write(f'GIRIS_SIFRESI = "{self.sifre_yeni_giris.text.strip()}"\n')
                f.write(f'GUNCELLEME_URL = "{self.guncelleme_url_giris.text.strip()}"\n')
            
            instance.text = "AYARLAR KAYDEDİLDİ!"
            instance.background_color = (0.2, 0.8, 0.2, 1)
            Clock.schedule_once(lambda dt: self.popup_ayar.dismiss(), 1.2)
        except Exception as e:
            print(f"Hata: {e}")

    def uygulamayi_baslat(self, isletme_adi):
        os.environ["SECILI_ISLETME"] = isletme_adi 
        try:
            import ayarlar
            importlib.reload(ayarlar)
            
            # Ayarları Sistem Ortamına Yükle
            os.environ["FIREBASE_URL"] = getattr(ayarlar, 'FIREBASE_URL', "")
            
            importlib.reload(giris_modulu)
            self.muhasebe_motoru = giris_modulu.AMDAccounting()
            self.muhasebe_motoru.ana_uygulama = self
            self.root_container.clear_widgets()
            self.root_container.add_widget(self.muhasebe_motoru.build())
        except Exception as e: 
            print(f"Hata: {e}")

    def guncellemeyi_baslat(self, instance):
        pass

if __name__ == '__main__':
    MainLauncher().run()