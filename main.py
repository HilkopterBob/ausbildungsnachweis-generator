#!/usr/bin/env python3
"""
Ausbildungsnachweis PDF Generator

This script reads a YAML configuration describing your apprenticeship period (split into three years),
your daily tasks per year, and any pre-planned special days (single days or spans, e.g. Urlaub, Krankheit, Schule).
It then batch-generates a weekly report PDF for every week between start_date and end_date, automatically:
  • Selecting 1–3 random tasks per workday (Mon–Fri) from the appropriate year's list
  • Marking German public holidays (in native German names)
  • Marking all user-defined special days or spans
  • Assigning a default of 8 hours per normal workday (configurable)
  • Counting school days and holidays as full 8-hour days
  • Leaving vacation and illness days at 0h

Dependencies:
  pip install reportlab pyyaml holidays python-dateutil

Usage:
  # Generate all weekly reports based on config.yaml
  python generate_reports.py config.yaml

  # Create an example YAML config (with three yearly sections)
  python generate_reports.py --init example_config.yaml
"""
import sys
import random
import datetime
import yaml
import holidays
from dateutil.relativedelta import relativedelta, MO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def generate_example_config(path: str):
    """Write an example YAML config file to `path`."""
    example = {
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
            {'start': '2026-03-10', 'label': 'Krankheit'}  # single via start only
        ]
    }
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(example, f, sort_keys=False, allow_unicode=True)
    print(f"📝 Example config written to {path}")


def load_config(path: str) -> dict:
    """Load and validate YAML config, expanding special-day spans."""
    with open(path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    for key in ('name', 'start_date', 'end_date'):
        if key not in cfg:
            print(f"Missing required config field: {key}")
            sys.exit(1)
    cfg['start_date'] = datetime.datetime.strptime(cfg['start_date'], '%Y-%m-%d').date()
    cfg['end_date']   = datetime.datetime.strptime(cfg['end_date'],   '%Y-%m-%d').date()
    cfg['default_hours'] = cfg.get('default_hours', 8)
    tasks = {}
    for y in (1,2,3):
        key = f'tasks_year_{y}'
        if key not in cfg or not isinstance(cfg[key], list):
            print(f"Missing or invalid task list: {key}")
            sys.exit(1)
        tasks[y] = cfg[key]
    cfg['tasks'] = tasks
    spec_map = {}
    for entry in cfg.get('special_days', []):
        label = entry.get('label')
        if 'date' in entry:
            d = datetime.datetime.strptime(entry['date'], '%Y-%m-%d').date()
            spec_map[d] = label
        elif 'start' in entry:
            start = datetime.datetime.strptime(entry['start'], '%Y-%m-%d').date()
            end = datetime.datetime.strptime(entry.get('end', entry['start']), '%Y-%m-%d').date()
            for i in range((end - start).days + 1):
                d = start + datetime.timedelta(days=i)
                spec_map[d] = label
    cfg['special_days'] = spec_map
    return cfg


def generate_weekly_report(
    name: str,
    apprenticeship_year: str,
    week_start: datetime.date,
    tasks_list: list,
    special_days: dict,
    output_filename: str,
    default_hours: int,
    global_start: datetime.date,
    global_end: datetime.date
):
    week_end = week_start + datetime.timedelta(days=6)
    header = [
        ['Name:', name, 'Ausbildungsjahr:', apprenticeship_year],
        ['Woche vom', week_start.strftime('%d.%m.%Y'), 'bis', week_end.strftime('%d.%m.%Y')]
    ]
    days = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag','Sonntag']
    table = [[ 'Tag', 'Arbeiten / Unterweisungen', 'Einzelstunden', 'Gesamtstunden', 'Abteilung' ]]
    weekly_total = 0
    for i, day in enumerate(days):
        date = week_start + datetime.timedelta(days=i)
        wd = date.weekday()
        if date < global_start or date > global_end or wd >= 5:
            entry, hours = '', 0
        elif date in special_days:
            label = special_days[date]
            entry = label
            if label.lower() in ('urlaub', 'krankheit'):
                hours = 0
            else:
                hours = default_hours
        else:
            count = random.randint(1, min(3, len(tasks_list)))
            entry = '\n'.join(random.sample(tasks_list, count))
            hours = default_hours
        weekly_total += hours
        table.append([day, entry, str(hours), str(hours), ''])
    table.append(['Gesamtstunden', '', '', str(weekly_total), ''])
    doc = SimpleDocTemplate(output_filename, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    elems, styles = [], getSampleStyleSheet()
    for row in header:
        elems.append(Table([[Paragraph(f'<b>{c}</b>', styles['Normal']) for c in row]],
                           colWidths=[30*mm,60*mm,30*mm,60*mm]))
        elems.append(Spacer(1,5*mm))
    tbl = Table(table, colWidths=[25*mm,90*mm,20*mm,20*mm,35*mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(1,1),(-1,-1),3),
        ('FONTSIZE',(0,0),(-1,0),9), ('FONTSIZE',(0,1),(-1,-1),8)
    ]))
    elems.append(tbl); elems.append(Spacer(1,10*mm))
    remarks = [ [Paragraph('<b>Besondere Bemerkungen:</b>',styles['Normal']), ''],
                [Paragraph('<b>Für die Richtigkeit:</b>',styles['Normal']),
                 'Unterschrift Auszubildender / Ausbilder'],
                ['Datum',''] ]
    for r in remarks:
        elems.append(Table([r], colWidths=[50*mm,None])); elems.append(Spacer(1,3*mm))
    doc.build(elems)
    print(f'✍️ {output_filename} fertig')


def generate_all_reports(cfg: dict):
    name = cfg['name']
    start = cfg['start_date']
    end   = cfg['end_date']
    default_hours = cfg['default_hours']
    special = cfg['special_days'].copy()
    years = list(range(start.year, end.year+1))
    de_hols = holidays.Germany(years=years, language='de')
    for d, label in de_hols.items():
        if start <= d <= end and d not in special:
            special[d] = label
    # First Monday on or before start for partial first week
    first_monday = start + relativedelta(weekday=MO(-1))
    cur = first_monday
    count = 0
    while cur <= end:
        count += 1
        # Calculate apprenticeship year, clamp between 1 and 3
        delta_days = (cur - start).days
        year_num = delta_days // 365 + 1
        year_num = max(1, min(3, year_num))
        apron = f'{year_num}. Ausbildungsjahr'
        tasks = cfg['tasks'][year_num]
        fn = f'ausbildungsnachweis_{cur.strftime("%Y%m%d")}.pdf'
        generate_weekly_report(
            name, apron, cur, tasks, special, fn,
            default_hours, start, end
        )
        cur += relativedelta(weeks=1)
    print(f'✅ {count} Berichte erstellt')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] in ('--init', '--generate-config'):
        generate_example_config(sys.argv[2]); sys.exit(0)
    if len(sys.argv) != 2:
        print('Usage: python generate_reports.py config.yaml')
        print('   or: python generate_reports.py --init example.yaml')
        sys.exit(1)
    cfg = load_config(sys.argv[1])
    generate_all_reports(cfg)

