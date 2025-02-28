import subprocess
import sys
import os


def ensure_packages():
    required_packages = ["requests", "kivy", "groq"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


ensure_packages()

import requests
import json
import groq
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

API_KEY = "ZeFjBtqTCSSR2gLHN2cTeW1G75Vq8G7DnWztMzIFP0ixgtcI8Q"
PLANT_ID_URL = "https://api.plant.id/v2/identify"
GROQ_API_KEY = "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"


def rozpoznaj_rosline(zdjecie):
    try:
        with open(zdjecie, "rb") as img_file:
            files = {"images": img_file}
            headers = {"Api-Key": API_KEY}
            dane = {
                "organy": ["liść", "kwiat"],
                "szerokość_geograficzna": None,
                "długość_geograficzna": None,
                "podobne_zdjęcia": True
            }
            response = requests.post(PLANT_ID_URL, headers=headers, files=files, data={"data": json.dumps(dane)})
            response.raise_for_status()
            return response.json()
    except:
        return None


def informacje_o_pielegnacji(nazwa_rosliny):
    klient = groq.Client(api_key=GROQ_API_KEY)
    prompt = f"Jak pielęgnować roślinę {nazwa_rosliny}? Jakie są jej najczęstsze choroby i jak je leczyć?"

    try:
        response = klient.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od roślin."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content if response.choices else "Brak informacji."
    except:
        return "Nie udało się pobrać informacji o pielęgnacji."


class AplikacjaRoslinna(App):
    def build(self):
        self.layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)

        self.sekcja_zdjecia = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
        self.zdjecie = Image(size_hint=(1, 0.8))
        self.przycisk_wyboru = Button(text="Wybierz zdjęcie", size_hint=(1, 0.2), background_color=(0.2, 0.6, 0.2, 1))
        self.przycisk_wyboru.bind(on_press=self.otworz_przegladarke)

        self.sekcja_zdjecia.add_widget(self.zdjecie)
        self.sekcja_zdjecia.add_widget(self.przycisk_wyboru)

        self.sekcja_szczegoly = BoxLayout(orientation='vertical', size_hint=(0.5, 1), padding=10)
        self.etykieta = Label(text="Wybierz zdjęcie rośliny", font_size=18, halign='left', valign='top', markup=True)
        self.etykieta.bind(size=self.etykieta.setter('text_size'))

        przewijanie = ScrollView()
        przewijanie.add_widget(self.etykieta)

        self.sekcja_szczegoly.add_widget(przewijanie)

        self.layout.add_widget(self.sekcja_zdjecia)
        self.layout.add_widget(self.sekcja_szczegoly)

        return self.layout

    def otworz_przegladarke(self, instance):
        sciezka_domyslna = os.path.expanduser("~/Downloads")
        przegladarka = FileChooserListView(path=sciezka_domyslna, filters=["*.jpg", "*.png", "*.jpeg"])
        popup = Popup(title='Wybierz zdjęcie', content=przegladarka, size_hint=(0.9, 0.9))
        przegladarka.bind(on_submit=lambda obj, selection, touch: self.przetworz_zdjecie(selection, popup))
        popup.open()

    def przetworz_zdjecie(self, selection, popup):
        if selection:
            sciezka = selection[0]
            self.zdjecie.source = sciezka
            wynik = rozpoznaj_rosline(sciezka)
            self.wyswietl_wynik(wynik)
        else:
            self.etykieta.text = "Nie wybrano zdjęcia."
        popup.dismiss()

    def wyswietl_wynik(self, wynik):
        if wynik:
            if not wynik.get("is_plant", True):
                self.etykieta.text = "Przesłano zdjęcie, ale to nie jest roślina."
                return

            sugestie = wynik.get("suggestions", [])
            if sugestie:
                najlepsza = sugestie[0]
                nazwa_rosliny = najlepsza.get("plant_name", "Nie znaleziono")
                pewnosc = najlepsza.get("probability", 0) * 100

                if pewnosc < 50:
                    self.etykieta.text = "Przesłano zdjęcie, ale nie rozpoznano rośliny z dużą pewnością."
                    return

                pielegnacja = informacje_o_pielegnacji(nazwa_rosliny)
            else:
                self.etykieta.text = "Nie znaleziono rośliny."
                return

            self.etykieta.text = f"[b]Rozpoznano:[/b] {nazwa_rosliny} ({pewnosc:.2f}% pewności)\n[b]Pielęgnacja:[/b] {pielegnacja}"
        else:
            self.etykieta.text = "Nie udało się rozpoznać rośliny."


if __name__ == "__main__":
    AplikacjaRoslinna().run()
