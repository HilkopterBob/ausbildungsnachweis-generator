
# Ausbildungsnachweis PDF Generator

> Automatisches Ausfüllen eines PDF-AcroForm-Formulars mit wöchentlichen Ausbildungsnachweisen für drei Jahre.

---

## Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)  
2. [Installation](#installation)  
   - [Repository klonen](#repository-klonen)  
   - [Virtuelle Umgebung anlegen](#virtuelle-umgebung-anlegen)  
   - [Abhängigkeiten installieren](#abhängigkeiten-installieren)  
3. [Formular-Preset vorbereiten](#formular-preset-vorbereiten)  
4. [Konfiguration (`config.yaml`)](#konfiguration-configyaml)  
   - [Beispiel-Config erzeugen](#beispiel-config-erzeugen)  
   - [Wichtige Felder](#wichtige-felder)  
   - [Sondertage definieren](#sondertage-definieren)  
   - [Hinweis zum 3-Jahres-Zeitraum](#hinweis-zum-3-jahres-zeitraum)  
5. [Skript verwenden](#skript-verwenden)  
6. [Fehlerbehebung & Tipps](#fehlerbehebung--tipps)  
7. [Lizenz & Beiträge](#lizenz--beitrage)  

---

## Voraussetzungen

- **Betriebssystem**: Windows 10/11 oder Linux (Ubuntu, Debian, CentOS etc.)  
- **Python**: Version ≥ 3.8  
- **Optional**: `git` zum Klonen, `virtualenv` oder eingebautes `venv`  

---

## Installation

### Repository klonen

```bash
git clone https://github.com/dein-user/ausbildungsnachweis-generator.git
cd ausbildungsnachweis-generator
```

### Virtuelle Umgebung anlegen

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install pyyaml holidays python-dateutil pypdf
```

* * *

Formular-Preset vorbereiten
---------------------------

1.  Öffne deine PDF-Vorlage in LibreOffice Draw, Master PDF Editor o. Ä.
    
2.  Füge **AcroForm-Textfelder** mit genau folgenden **Namen** hinzu:
    
    *   `Vorname`, `Nachname`
        
    *   `Ausbildungsjahr`, `Ausbildungsnachweis_Nummer`
        
    *   `Datum_Start`, `Datum_Ende`
        
    *   Für jeden Wochentag (**Montag**–**Freitag**):
        
        *   `<Tag>_T1`, `<Tag>_T2`, `<Tag>_T3` (z. B. `Montag_T1`)
            
        *   `<Tag>_Stunden` (z. B. `Donnerstag_Stunden`)
            
    *   `Gesamtstunden`
        
3.  Speichere die bearbeitete Datei als **`background_form.pdf`** im Skript-Verzeichnis.
    

* * *

Konfiguration (`config.yaml`)
-----------------------------

### Beispiel-Config erzeugen

```bash
python main.py --init example_config.yaml
```

### Wichtige Felder

```yaml
template: background_form.pdf      # Name deiner Formular-PDF
tasks_year_1:
  - Beispiel-Aufgabe 1
tasks_year_2:
  - Beispiel-Aufgabe 2
tasks_year_3:
  - Beispiel-Aufgabe 3
name: "Max Mustermann"
start_date: "2025-01-01"           # Ausbildungsbeginn
end_date:   "2028-01-01"           # Ausbildungsende (3 Jahre später)
default_hours: 8                   # Std/Tag für Schule & Feiertage

special_days:
  - date: 2025-05-07
    label: Schule
  - start: 2025-12-24
    end:   2025-12-26
    label: Urlaub
  - start: 2026-03-10
    label: Krankheit
```

### Sondertage definieren

*   **Einzeltag**: `date: YYYY-MM-DD`
    
*   **Zeitraum**: `start: YYYY-MM-DD` + optional `end: YYYY-MM-DD`
    
*   **Label**: z. B. `Urlaub`, `Schule`, `Krankheit`
    

### Hinweis zum 3-Jahres-Zeitraum

Das Skript legt **jede Kalenderwoche** im festgelegten Zeitraum an. **Setze `start_date` und `end_date` so**, dass sie exakt drei Jahre abdecken (z. B. `2025-01-01` bis `2028-01-01`). Möchtest du nur wenige Berichte, lösche anschließend die überschüssigen PDFs.

* * *

Skript verwenden
----------------

```bash
python main.py config.yaml
```

*   Erzeugt nummerierte PDF-Dateien im Format  
    `01_ausbildungsnachweis-<Mo>-<Fr-MM-JJJJ>.pdf`
    
*   Daten basieren auf dem ersten Montag vor oder am `start_date`.
    

* * *

Fehlerbehebung & Tipps
----------------------

*   **Missing config field**: Prüfe, ob `template`, `tasks_year_*`, `name`, `start_date`, `end_date` vorhanden sind.
    
*   **No /AcroForm dictionary**: Stelle sicher, dass deine PDF echte AcroForm-Felder enthält.
    
*   **Felder bleiben leer**: Feldnamen müssen exakt (inkl. Groß-/Kleinschreibung) übereinstimmen.
    
*   **Sondertage nicht übernommen**: Labels `Krankheit`, `Urlaub` etc. beachten.
    
*   **Falsche Wochentage**: Installiere `python-dateutil`, falls es fehlt.
    

* * *

Lizenz & Beiträge
-----------------

*   **Lizenz**: MIT
    
*   Contributions, Issues und Pull Requests sind willkommen!
    

* * *

_Hinweis: Diese Anleitung wurde auf Grammatik und Konsistenz geprüft und final angepasst._

