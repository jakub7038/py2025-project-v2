# py2025-project-v2

## Temat projektu:

Stwórz aplikację symulującą rozgrywkę w pokera pięciokartowego dobieranego. System powinien umożliwiać tworzenie talii kart, rozdawanie kart, ocenę układu (hand rank) oraz interakcję z graczem (np. wymiana kart, obstawianie). Implementacja musi wykorzystywać programowanie obiektowe wraz z getter/setter, operacje na plikach, a także: prosty interfejs graficzny (GUI) i komunikację sieciową.

## Główne funkcjonalności:

### Logika gry i symulacja rozgrywki:

    Implementacja funkcji pomocniczych takich jak histogram, deck, deal, hand_rank oraz exchange_cards.

    Zasady określające wartość układu kart (np. poker królewski, kareta, full house itp.).

### Programowanie obiektowe:

    Utworzenie klas reprezentujących elementy gry:

        Card – reprezentuje pojedynczą kartę, posiada pola przechowujące rangę i kolor oraz metody do wygodnej reprezentacji.

        Deck – klasa zarządzająca talią kart, posiada metody do tasowania, rozdawania oraz jej reprezentację.

        Player – klasa reprezentująca gracza, przechowująca m.in. rękę kart oraz stan żetonów. Klasa powinna korzystać z dekoratora @property do implementacji getter/setter dla atrybutu stanu (stack) oraz metody klasowej create_players.

### Operacje na plikach i serializacja:

    Zapisywanie wyników rozgrywki, logów oraz historii gier do plików (txt, csv, JSON).

    Możliwość zapisywania i odczytywania konfiguracji gry.

### Rozszerzenia:

    GUI: Utworzenie graficznego interfejsu użytkownika (za pomocą Tkinter), który pozwoli na rozpoczęcie rozgrywki, podgląd rozdanych kart, stan żetonów oraz interakcję (wybór opcji zakładu, wymiany kart).

    Komunikacja sieciowa: Implementacja prostego mechanizmu serwer-klient, umożliwiającego przesyłanie danych o stanie gry na odległy terminal lub aplikację.

    Zaawansowane zagadnienia Pythona: Stosowanie dekoratorów, generatorów, wirtualnych środowisk (venv, pip, conda) i serializacji (pickle, JSON).


## Jeśli wybierzesz ten projekt powinieneś:

- zrobić forka tego repozytorium na swoim koncie i commitować kolejne postępy,
- rozpocząć od implementacji modułu logiki gry, do którego wymagania opisane są w pliku poker.md, wymagania do kolejnych modułów pojawią się na kolejnych laboratoriach.

### Struktura gałęzi

Warto przyjąć prostą strategię gałęzi, która umożliwi łatwe zarządzanie różnymi etapami pracy:

**Główna gałąź (main lub master):**
Zawiera stabilny kod – wersje gotowe do demonstracji lub udostępnienia.

**Gałąź deweloperska (develop):**
Na niej integrowane są wszystkie zmiany przed scalenie ich do głównej gałęzi. Może służyć jako staging area.

### Propozycja podziału pracy i wskazówki implementacyjne

### Architektura i podział modułów

**Moduł logiki gry:**
    
    Zawiera funkcje takie jak histogram, deck, deal, hand_rank oraz exchange_cards. Odpowiada za podstawową logikę rozgrywki i mechanizmy gry.

    Definiuje klasy:

        Card – reprezentacja pojedynczej karty.

        Deck – zarządzanie talią kart (tworzenie, tasowanie, rozdawanie).

        Player – reprezentacja gracza wraz z metodami przyjmowania kart, wymiany, a także zarządzania stanem żetonów (stack) poprzez getter/setter.
        Klasy te powinny zapewnić podstawowy interfejs wykorzystywany w rozgrywce.

**Moduł rozgrywki:**
    Implementuje logikę interakcji między graczem a botami: obstawianie, wymiana kart, przyjmowanie decyzji gracza (np. check, call, raise, fold). Umożliwia obsługę wejścia z klawiatury, wyświetlanie stanu gry i obsługę wyjątków.

**Moduł operacji na plikach i logowania:**
    Klasa lub zbiór funkcji odpowiedzialnych za zapis historii rozgrywki oraz logów do plików (np. CSV, JSON). Pozwala na późniejszą analizę statystyk rozgrywek.

**Moduł komunikacji sieciowej (opcjonalnie):**
    Implementacja prostego serwera (i opcjonalnie klienta) przy użyciu gniazd (sockets), umożliwiająca transmisję wyników gry lub aktualnych stanów.

**Moduł GUI (opcjonalnie):**
    Prosty interfejs graficzny oparty na Tkinter (lub innym frameworku), który umożliwia uruchomienie rozgrywki, wyświetlenie kart, stan żetonów oraz interakcję użytkownika.

### Tagowanie wersji:

Oznaczaj istotne etapy rozwoju projektu tagami, na przykład:

v0.1: Wstępna implementacja funkcji generowania talii i rozdawania kart.

v0.2: Dodanie logiki oceny układu kart (hand_rank) oraz klasy Player.

v0.3: Implementacja operacji na plikach i zapisu logów.

v0.4: Dodanie testów jednostkowych.

v0.5: Rozszerzenie o interfejs GUI i/lub komunikację sieciową.

v1.0: Stabilna, pełna wersja gry.
