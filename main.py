#!/usr/bin/env python3
"""
Ausbildungsnachweis PDF Generator (Form-Filling Version)

Reads a YAML config and fills in a prepared AcroForm PDF template with named fields.

Dependencies:
  pip install pyyaml holidays python-dateutil pypdf

Usage:
  # Generate example config
  python main.py --init example_config.yaml

  # Batch-create reports
  python main.py config.yaml
"""
import sys
import random
import datetime
import yaml
import holidays
from dateutil.relativedelta import relativedelta, MO
from pypdf import PdfReader, PdfWriter

# -----------------------------------------------------------------------------
# 1) Example config generator
# -----------------------------------------------------------------------------
def generate_example_config(path: str):
    example = {
        # Path to your editable PDF form
        'template': 'background_form.pdf',
        'name': 'Max Mustermann',
        'start_date': '2025-01-01',
        'end_date': '2028-01-01',
        'default_hours': 8,
        'tasks_year_1': [
            'Maschineneinrichtung überprüft',
            'Materiallager inventarisiert',
            'Unterweisung zum Arbeitsschutz'
        ],
        'tasks_year_2': [
            'Werkstücke vermessen',
            'Qualitätskontrolle durchgeführt',
            'Prozessoptimierung besprochen'
        ],
        'tasks_year_3': [
            'Eigenständiges Projekt geplant',
            'Abschlussdokumentation erstellt',
            'Prüfungsvorbereitung durchgeführt'
        ],
        'special_days': [
            {'date': '2025-05-07', 'label': 'Schule'},
            {'start': '2025-12-24', 'end': '2025-12-26', 'label': 'Urlaub'},
            {'start': '2026-03-10', 'label': 'Krankheit'}
        ]
    }
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(example, f, sort_keys=False, allow_unicode=True)
    print(f"📝 Example config written to {path}")

# -----------------------------------------------------------------------------
# 2) Config loader
# -----------------------------------------------------------------------------
def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    for key in ('name', 'start_date', 'end_date'):
        if key not in cfg:
            print(f"Missing config field: {key}")
            sys.exit(1)
    cfg['template']      = cfg.get('template', 'background_form.pdf')
    cfg['start_date']    = datetime.datetime.strptime(cfg['start_date'], '%Y-%m-%d').date()
    cfg['end_date']      = datetime.datetime.strptime(cfg['end_date'],   '%Y-%m-%d').date()
    cfg['default_hours'] = cfg.get('default_hours', 8)
    # Load tasks per year
    tasks = {}
    for y in (1, 2, 3):
        key = f'tasks_year_{y}'
        if key not in cfg or not isinstance(cfg[key], list):
            print(f"Invalid task list: {key}")
            sys.exit(1)
        tasks[y] = cfg[key]
    cfg['tasks'] = tasks
    # Expand special days/spans
    spec = {}
    for entry in cfg.get('special_days', []):
        label = entry['label']
        if 'date' in entry:
            d = datetime.datetime.strptime(entry['date'], '%Y-%m-%d').date()
            spec[d] = label
        else:
            start = datetime.datetime.strptime(entry['start'], '%Y-%m-%d').date()
            end   = datetime.datetime.strptime(entry.get('end', entry['start']), '%Y-%m-%d').date()
            for i in range((end - start).days + 1):
                spec[start + datetime.timedelta(days=i)] = label
    cfg['special_days'] = spec
    return cfg

# -----------------------------------------------------------------------------
# 3) Form-filling helper
# -----------------------------------------------------------------------------
def fill_week_form(template_path: str, output_path: str, data: dict):
    """
    Fill an AcroForm-based PDF template using pypdf's clone_document_from_reader.
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.update_page_form_field_values(writer.pages[0], data)
    with open(output_path, 'wb') as out:
        writer.write(out)
    print(f"✔️ {output_path}")

# -----------------------------------------------------------------------------
# 4) Batch report generator
# -----------------------------------------------------------------------------
def generate_all_reports(cfg: dict):
    template = cfg['template']
    full_name   = cfg['name']
    parts       = full_name.split()
    vorname     = parts[0]
    nachname    = ' '.join(parts[1:]) if len(parts) > 1 else ''
    start, end  = cfg['start_date'], cfg['end_date']
    default_hrs = cfg['default_hours']
    special     = cfg['special_days'].copy()
    # Load German holidays in native names
    yrs = range(start.year, end.year + 1)
    de_h = holidays.Germany(years=list(yrs), language='de')
    for d, label in de_h.items():
        if start <= d <= end and d not in special:
            special[d] = label
    # Compute first Monday on or before start
    first_mon = start + relativedelta(weekday=MO(-1))
    cur = first_mon
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    count = 0
    while cur <= end:
        count += 1
        week_end = cur + relativedelta(days=6)
        year_num = (cur - start).days // 365 + 1
        year_num = max(1, min(3, year_num))
        # Prepare data dict
        data = {
            'Vorname':                     vorname,
            'Nachname':                    nachname,
            'Ausbildungsjahr':             f"{year_num}. Ausbildungsjahr",
            'Ausbildungsnachweis_Nummer':  str(count),
            'Datum_Start':                 cur.strftime('%d.%m.%Y'),
            'Datum_Ende':                  (cur + datetime.timedelta(days=4)).strftime('%d.%m.%Y')
        }
        total = 0
        tasks = cfg['tasks'][year_num]
        for i, day in enumerate(weekdays):
            date = cur + datetime.timedelta(days=i)
            if date < start or date > end:
                entries, hrs = [], 0
            elif date in special:
                label = special[date]
                entries = [label]
                # No working hours for Krankheit or Schule
                hrs = 0 if label.lower() in ('krankheit', 'schule') else default_hrs
            else:
                sample = random.sample(tasks, random.randint(1, min(3, len(tasks))))
                entries = sample
                hrs = default_hrs
            total += hrs
            # Assign T1-T3 fields
            for j in range(1, 4):
                data[f"{day}_T{j}"] = entries[j-1] if j <= len(entries) else ''
            # Assign Stunden field
            data[f"{day}_Stunden"] = str(hrs)
        data['Gesamtstunden'] = str(total)
        # Output filename with prefix
        filename_body = f"ausbildungsnachweis-{cur.strftime('%d')}-{week_end.strftime('%d-%m-%Y')}.pdf"
        out_fn = f"{count:02d}_{filename_body}"
        fill_week_form(template, out_fn, data)
        cur += relativedelta(weeks=1)
    print(f"✅ {count} Berichte erstellt.")

# -----------------------------------------------------------------------------
# 5) CLI entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] in ('--init', '--generate-config'):
        generate_example_config(sys.argv[2])
        sys.exit(0)
    if len(sys.argv) != 2:
        print('Usage: python main.py config.yaml')
        print('       python main.py --init example.yaml')
        sys.exit(1)
    cfg = load_config(sys.argv[1])
    generate_all_reports(cfg)
