# MSI Komiwojażer

## Opis projektu

Projekt został wykonany w ramach przedmiotu **Metody Sztucznej Inteligencji**.

Celem aplikacji jest stworzenie systemu wsparcia logistycznego, który wyznacza możliwie najkrótszą trasę dla kuriera odwiedzającego wiele punktów i wracającego na końcu do punktu startowego (magazynu).

Aplikacja minimalizuje dystans przejazdu przy wykorzystaniu algorytmu genetycznego oraz umożliwia wizualizację trasy na rzeczywistej mapie.

Program został przygotowany jako **aplikacja desktopowa w Pythonie**.

---

## Grupa realizująca projekt

- Dawid Nowak  
- Krzysztof Sułkowski (lider projektu)  
- Anna Trybel  
- Aneta Walczak  

---

## Technologie

Projekt został przygotowany w języku **Python**.

Wykorzystane technologie i biblioteki:

- Python 3.12  
- Tkinter (interfejs graficzny)  
- tkintermapview (mapa OpenStreetMap)  
- NumPy (obliczenia matematyczne)  
- geopy / Nominatim (geokodowanie adresów)  
- OSRM (wyznaczanie tras po drogach)  

---

## Funkcjonalności

Aplikacja umożliwia:

- ustawienie punktu startowego (magazynu)
- dodawanie punktów dostaw (ręcznie lub przez wyszukiwanie adresu)
- automatyczne pobieranie współrzędnych GPS z adresu
- wyznaczanie trasy w linii prostej
- optymalizację kolejności punktów (algorytm genetyczny)
- wyznaczanie trasy po rzeczywistych drogach (OSRM)
- oznaczanie punktów jako dostarczone
- dodawanie komentarzy do punktów
- eksport trasy do pliku JSON
- import trasy z pliku JSON
- generowanie raportu wydajności

---

## Algorytm optymalizacji

Do rozwiązania problemu komiwojażera wykorzystano **algorytm genetyczny**.

Zastosowane mechanizmy:

- losowa populacja początkowa
- selekcja turniejowa
- krzyżowanie (crossover)
- mutacja
- elityzm (zachowanie najlepszej trasy)

Algorytm działa na macierzy odległości pomiędzy punktami i minimalizuje całkowity dystans trasy.

---

## Wymagania funkcjonalne (z projektu)

System realizuje:

- wprowadzanie danych (punkty GPS + magazyn)
- obliczanie macierzy kosztów (odległości między punktami)
- zastosowanie algorytmu optymalizacyjnego (AI)
- wizualizację trasy na mapie
- eksport danych do JSON
- pobieranie lokalizacji (geokodowanie)

---

## Raport wydajności

Aplikacja umożliwia wygenerowanie raportu wydajności (`performance_report.txt`).

Raport zawiera:

- test dla 10 punktów
- test dla 100 punktów
- czas działania algorytmu
- długość trasy
- informację czy spełniono wymagania czasowe

Uwaga:
Raport mierzy **wyłącznie czas działania algorytmu optymalizacji**, bez uwzględniania:
- geokodowania
- pobierania tras z OSRM
- rysowania mapy

---

## Format danych (JSON)

Aplikacja zapisuje dane w formacie:

- depot (magazyn)
- locations (punkty dostawy)
- route (kolejność trasy)
- total_distance
- created_at

Dane mogą być ponownie zaimportowane do aplikacji.

---

## Instrukcja uruchomienia

### Wymagania wstępne

- Python 3.12

---

### Uruchomienie programu

1. Przejdź do terminala

2. Sklonuj repozytorium

`git clone https://github.com/krzysztofsulkowski/msi-komiwojazer.git`

3. Przejdź do folderu projektu

`cd msi-komiwojazer`

4. Utwórz i aktywuj środowisko wirtualne

`python -m venv .venv`

`.venv\Scripts\activate`

5. Zainstaluj zależności

`pip install -r requirements.txt`

6. Uruchom aplikację

`python main.py`

---

## Ograniczenia

- brak uwzględnienia ruchu drogowego
- brak informacji o korkach
- zależność od zewnętrznych API (Nominatim, OSRM)
- dokładność zależna od jakości danych OpenStreetMap

---