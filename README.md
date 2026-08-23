# Moodle - materialy dydaktyczne

Repozytorium zawiera interaktywne materialy do zajec z metodologii badan, psychologii spolecznej i statystyki. Wiekszosc zasobow to samodzielne strony HTML publikowane pod adresem [moodle.lieberfilip.pl](https://moodle.lieberfilip.pl).

## Zawartosc

| Katalog lub plik | Przeznaczenie |
| --- | --- |
| [`metody/`](metody/README.md) | Materialy na zajecia z metodologii badan, wraz z plikami pomocniczymi. |
| [`spoleczna/`](spoleczna/README.md) | Symulatory i materialy do zajec z psychologii spolecznej. |
| [`statystyka/`](statystyka/README.md) | Narzedzia wspierajace wybor i interpretacje testow statystycznych. |
| [`oceny/`](oceny/README.md) | Formularze pomocnicze do oceny zadan. |
| [`podstawy/`](podstawy/README.md) | Interaktywne wprowadzenia do podstawowych pojec metodologicznych i statystycznych. |

## Struktura

```text
.
|- metody/       strony zajec i ich multimedia
|- spoleczna/    symulatory i obrazy do zajec spolecznych
|- statystyka/   narzedzia do testow i korelacji
|- oceny/        formularze oceniania
|- podstawy/     wprowadzenia do pojec metodologicznych i statystycznych
`- CNAME         domena publikacji GitHub Pages
```

## Praca lokalna

Strony HTML nie wymagaja budowania: mozna je otworzyc w przegladarce. Dla funkcji zaleznych od bezwzglednych sciezek URL warto uruchomic lokalny serwer HTTP z katalogu glownego.

## Zasady zmian

- Zachowuj obecne nazwy i polozenie plikow statycznych: czesc stron oraz materialow korzysta z tych adresow bezposrednio.
- Nowe materialy do zajec dodawaj obok odpowiedniej strony w `metody/`.
- Zasoby uzywane przez dana strone przechowuj w jej podkatalogu, na przyklad `spoleczna/spo_7/`.
- Nie dodawaj plikow lokalnych, wirtualnych srodowisk ani sekretow do repozytorium.

## Publikacja

Plik [`CNAME`](CNAME) wskazuje domene wykorzystywana przez GitHub Pages. Publikacja powinna zachowywac katalogi i adresy URL wymienione powyzej.
