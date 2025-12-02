#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GRANT SCOUT AGENT v2.4.5 - HYBRID MODE + IMPROVED PARSER
Automatyczne skanowanie grantów dla gminy Czaplinka
NOWOŚĆ: Ulepszona ekstrakcja JSON z odpowiedzi Gemini!
"""

import os
import json
import argparse
import glob
import re
from datetime import datetime
import logging

from flask import Flask
import os

app = Flask(__name__)
PORT = int(os.getenv('PORT', 8080))

@app.route('/')
def health():
    return {'status': 'Grant Scout is running!'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

# Ładuj zmienne z .env
load_dotenv()

# ============================================================================
# KONFIGURACJA
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# FOLDERY
REPORTS_DIR = "reports"
UPLOADS_DIR = "uploads"
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ============================================================================
# DANE BUDŻETOWE GMINY CZAPLINKA
# ============================================================================

BUDZET_GMINY = {
    "nazwa": "Gmina Czaplinka",
    "razem": 85935554,
    "wydane": 25432123,
    "pozostalo": 60503431,
    "projekty": [
        {
            "id": "AI001",
            "nazwa": "Centrum Kompetencji AI",
            "budzet": 600000,
            "wydane": 0,
            "typ": "cyfryzacja",
            "opis": "Centrum edukacyjne dla sztucznej inteligencji",
            "source": "domyslny"
        },
        {
            "id": "EDU001",
            "nazwa": "Szkoła Podstawowa - Remont",
            "budzet": 450000,
            "wydane": 200000,
            "typ": "edukacja",
            "opis": "Modernizacja budynku szkoły",
            "source": "domyslny"
        },
        {
            "id": "INF001",
            "nazwa": "Drogi Lokalne",
            "budzet": 800000,
            "wydane": 450000,
            "typ": "infrastruktura",
            "opis": "Przebudowa dróg lokalnych",
            "source": "domyslny"
        },
        {
            "id": "ENV001",
            "nazwa": "Oczyszczalnia Sciekow",
            "budzet": 2500000,
            "wydane": 1200000,
            "typ": "srodowisko",
            "opis": "Budowa nowoczesnej oczyszczalni",
            "source": "domyslny"
        },
        {
            "id": "EDU002",
            "nazwa": "Przedszkole Samorządowe",
            "budzet": 350000,
            "wydane": 150000,
            "typ": "edukacja",
            "opis": "Rozbudowa przedszkola",
            "source": "domyslny"
        },
        {
            "id": "SEC001",
            "nazwa": "System Bezpieczeństwa",
            "budzet": 500000,
            "wydane": 0,
            "typ": "bezpieczenstwo",
            "opis": "Monitoring i system alarmowy",
            "source": "domyslny"
        },
        {
            "id": "CUL001",
            "nazwa": "Biblioteka Publiczna - Modernizacja",
            "budzet": 400000,
            "wydane": 100000,
            "typ": "kultura",
            "opis": "Remont i wyposażenie biblioteki",
            "source": "domyslny"
        },
        {
            "id": "SPO001",
            "nazwa": "Boisko Sportowe",
            "budzet": 300000,
            "wydane": 50000,
            "typ": "sport",
            "opis": "Wielofunkcyjne boisko",
            "source": "domyslny"
        },
        {
            "id": "ENE001",
            "nazwa": "Energetyka Odnawialna - Panele",
            "budzet": 1200000,
            "wydane": 0,
            "typ": "energia",
            "opis": "Instalacja paneli słonecznych",
            "source": "domyslny"
        },
        {
            "id": "TRA001",
            "nazwa": "Komunikacja Publiczna",
            "budzet": 250000,
            "wydane": 100000,
            "typ": "transport",
            "opis": "Modernizacja transportu lokalnego",
            "source": "domyslny"
        },
        {
            "id": "IT001",
            "nazwa": "Oprogramowanie Zarzadzania",
            "budzet": 185554,
            "wydane": 182123,
            "typ": "IT",
            "opis": "System informatyczny dla gminy",
            "source": "domyslny"
        }
    ]
}

# ============================================================================
# BAZA GRANTÓW (FALLBACK)
# ============================================================================

GRANTY_FALLBACK = [
    {
        "nazwa": "Horizon Europe - Digital Europe Programme",
        "kwota_min": 500000,
        "kwota_max": 2000000,
        "deadline": "2025-12-15",
        "typ": "cyfryzacja",
        "szansa": "85%",
        "match_score": 95,
        "source": "EU",
        "is_new": True,
        "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/"
    },
    {
        "nazwa": "Fundusz Klimatyczny - OZE dla Gmin",
        "kwota_min": 300000,
        "kwota_max": 1500000,
        "deadline": "2026-01-20",
        "typ": "energia",
        "szansa": "78%",
        "match_score": 88,
        "source": "NFOSiGW",
        "is_new": True,
        "url": "https://www.nfosigw.gov.pl/"
    },
    {
        "nazwa": "Program Rozwoju Edukacji",
        "kwota_min": 100000,
        "kwota_max": 800000,
        "deadline": "2025-12-30",
        "typ": "edukacja",
        "szansa": "72%",
        "match_score": 82,
        "source": "MEN",
        "is_new": False,
        "url": "https://www.men.gov.pl/"
    },
    {
        "nazwa": "KPO - Cyfrowa Polska",
        "kwota_min": 600000,
        "kwota_max": 3000000,
        "deadline": "2025-12-10",
        "typ": "cyfryzacja",
        "szansa": "90%",
        "match_score": 98,
        "source": "KPO",
        "is_new": True,
        "url": "https://www.kpo.gov.pl/"
    },
    {
        "nazwa": "Innowacyjne Rozwiazania dla Gmin",
        "kwota_min": 200000,
        "kwota_max": 1000000,
        "deadline": "2026-01-15",
        "typ": "IT",
        "szansa": "75%",
        "match_score": 85,
        "source": "NCBR",
        "is_new": False,
        "url": "https://www.ncbr.gov.pl/"
    },
    {
        "nazwa": "Program Rozwoju Sportu Lokalnego",
        "kwota_min": 50000,
        "kwota_max": 500000,
        "deadline": "2025-12-28",
        "typ": "sport",
        "szansa": "65%",
        "match_score": 70,
        "source": "MKiDN",
        "is_new": False,
        "url": "https://mkidn.gov.pl/"
    },
    {
        "nazwa": "Modernizacja Transportu Publicznego",
        "kwota_min": 150000,
        "kwota_max": 1200000,
        "deadline": "2026-02-01",
        "typ": "transport",
        "szansa": "68%",
        "match_score": 75,
        "source": "GDDKiA",
        "is_new": False,
        "url": "https://www.gddkia.gov.pl/"
    },
    {
        "nazwa": "Ochrona Zasobów Wodnych",
        "kwota_min": 400000,
        "kwota_max": 2500000,
        "deadline": "2026-01-10",
        "typ": "srodowisko",
        "szansa": "82%",
        "match_score": 90,
        "source": "NFOSiGW",
        "is_new": False,
        "url": "https://www.nfosigw.gov.pl/"
    }
]

# ============================================================================
# KONWERSJA PLIKÓW NA TEKST
# ============================================================================

def extract_text_from_docx(file_path):
    """Wyodrębnia tekst z DOCX bez bibliotek (zip + XML)"""
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        text = []
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Czytaj document.xml z DOCX
            xml_content = zip_ref.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # Namespace dla Word
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            # Wyodrębniaj tekst z każdego paragrafu
            for para in root.findall('.//w:p', ns):
                para_text = []
                for text_elem in para.findall('.//w:t', ns):
                    if text_elem.text:
                        para_text.append(text_elem.text)
                if para_text:
                    text.append(''.join(para_text))
        
        return '\\n'.join(text)
    except Exception as e:
        print(f"    ⚠️  Błąd wyodrębniania z DOCX: {e}")
        return ""

def extract_text_from_xlsx(file_path):
    """Wyodrębnia tekst z Excel bez bibliotek (zip + XML)"""
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        text = []
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Listuj wszystkie arkusze
            for sheet_file in zip_ref.namelist():
                if sheet_file.startswith('xl/worksheets/sheet') and sheet_file.endswith('.xml'):
                    xml_content = zip_ref.read(sheet_file)
                    root = ET.fromstring(xml_content)
                    
                    # Namespace dla Excel
                    ns = {'ss': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    
                    # Wyodrębniaj tekst z każdej komórki
                    for cell in root.findall('.//ss:v', ns):
                        if cell.text:
                            text.append(str(cell.text))
        
        return '\\n'.join(text)
    except Exception as e:
        print(f"    ⚠️  Błąd wyodrębniania z Excel: {e}")
        return ""

# ============================================================================
# IMPROVED JSON EXTRACTION (v2.4.5 NEW!)
# ============================================================================

def extract_json_from_response(response_text):
    """Wyodrębnia JSON z odpowiedzi Gemini - 4 strategie"""
    
    if not response_text or not isinstance(response_text, str):
        return None
    
    # TRY 1: Szukaj zwykłych klamr {} (zwykły JSON)
    print(f"    🔍 TRY 1: Szukam zwykłych klamr {{}}")
    json_match = re.search(r'\\{[^{}]*(?:\\{[^{}]*\\}[^{}]*)*\\}', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            print(f"    ✅ TRY 1: SUCCESS!")
            return result
        except json.JSONDecodeError as e:
            print(f"    ⚠️  TRY 1: Błąd parsowania JSON: {e}")
    
    # TRY 2: Szukaj w markdown code block ```json ... ```
    print(f"    🔍 TRY 2: Szukam ```json ... ```")
    json_match = re.search(r'```json\\s*\\n?(.+?)\\n?```', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            print(f"    ✅ TRY 2: SUCCESS!")
            return result
        except json.JSONDecodeError as e:
            print(f"    ⚠️  TRY 2: Błąd: {e}")
    
    # TRY 3: Szukaj w zwykłym code block ``` ... ```
    print(f"    🔍 TRY 3: Szukam ``` ... ```")
    json_match = re.search(r'```\\s*\\n?(.+?)\\n?```', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            print(f"    ✅ TRY 3: SUCCESS!")
            return result
        except json.JSONDecodeError as e:
            print(f"    ⚠️  TRY 3: Błąd: {e}")
    
    # TRY 4: Szukaj pierwszego { i ostatniego } (greedy)
    print(f"    🔍 TRY 4: Szukam {{ ... }} (greedy)")
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        try:
            result = json.loads(response_text[start_idx:end_idx+1])
            print(f"    ✅ TRY 4: SUCCESS!")
            return result
        except json.JSONDecodeError as e:
            print(f"    ⚠️  TRY 4: Błąd: {e}")
    
    print(f"    ❌ Żaden parser nie zadziałał!")
    return None

# ============================================================================
# GEMINI - CZYTANIE PLIKU (PDF wysyła binarnie, inne konwertuje)
# ============================================================================

def parse_project_with_gemini_hybrid(file_path):
    """Parsuje plik - PDF wysyła binarnie, Excel/Word konwertuje na tekst"""
    
    if not GEMINI_API_KEY:
        print(f"    ❌ GEMINI_API_KEY nie ustawiony!")
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        print(f"    🤖 Gemini analizuje {file_ext}...")
        
        # Prompt do Gemini
        prompt = f"""
        Jesteś ekspertem w analizie projektów gminnych.
        Przeanalizuj poniższy dokument i wyodrębnij dane projektu w formacie JSON.
        
        WAŻNE:
        - Zwróć TYLKO válidy JSON, bez żadnych komentarzy!
        - Jeśli pole nie istnieje, użyj sensownej wartości domyślnej
        - Pole "typ" musi być JEDNO z: edukacja, energia, infrastruktura, srodowisko, sport, kultura, cyfryzacja, transport, bezpieczenstwo
        - "budzet" i "wydane" muszą być liczbami (bez PLN, bez spacji)
        - ID powinno być unikalne, max 20 znaków
        
        FORMAT ODPOWIEDZI (TYLKO JSON):
        {{
            "id": "UNIQUE_CODE",
            "nazwa": "Nazwa projektu",
            "budzet": 1000000,
            "wydane": 500000,
            "typ": "typ_projektu",
            "opis": "Pełny opis projektu"
        }}
        
        DOKUMENT: {file_name}
        """
        
        # HYBRID MODE
        if file_ext == '.pdf':
            # PDF → wysyłaj binarnie (Vision API wspiera)
            print(f"    📤 Wysyłam PDF binarnie...")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "application/pdf",
                    "data": file_data
                }
            ])
        
        elif file_ext in ['.docx', '.doc']:
            # DOCX/DOC → konwertuj na tekst
            print(f"    📝 Konwertuję Word na tekst...")
            text = extract_text_from_docx(file_path)
            
            if not text or len(text.strip()) < 20:
                print(f"    ❌ Nie udało się wyodrębić tekstu z Word")
                return None
            
            response = model.generate_content([
                prompt + f"\\n\\nTEKST Z DOKUMENTU:\\n{text[:2000]}"
            ])
        
        elif file_ext in ['.xlsx', '.xls']:
            # Excel → konwertuj na tekst
            print(f"    📊 Konwertuję Excel na tekst...")
            text = extract_text_from_xlsx(file_path)
            
            if not text or len(text.strip()) < 20:
                print(f"    ❌ Nie udało się wyodrębić tekstu z Excel")
                return None
            
            response = model.generate_content([
                prompt + f"\\n\\nDANE Z ARKUSZA:\\n{text[:2000]}"
            ])
        
        else:
            print(f"    ❌ Nieobsługiwany format: {file_ext}")
            return None
        
        # Wyodrębnij JSON z odpowiedzi (IMPROVED v2.4.5)
        print(f"    📦 Parsuję odpowiedź Gemini...")
        project = extract_json_from_response(response.text)
        
        if project:
            project["source"] = "upload"
            
            # Walidacja
            if not project.get("id"):
                project["id"] = f"UPLOAD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if not project.get("nazwa"):
                project["nazwa"] = f"Projekt z {file_name}"
            if not project.get("typ"):
                project["typ"] = "infrastruktura"
            
            # Konwertuj na liczby
            project["budzet"] = int(str(project.get("budzet", 0)).replace(" ", ""))
            project["wydane"] = int(str(project.get("wydane", 0)).replace(" ", ""))
            
            print(f"  ✅ Sparsowano: {project['nazwa']}")
            print(f"     ID: {project['id']}, Typ: {project['typ']}, Budżet: PLN {project['budzet']:,}")
            return project
        else:
            print(f"    ❌ Nie udało się sparsować projektu")
            return None
    
    except Exception as e:
        print(f"    ❌ Błąd: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def load_projects_from_uploads(auto_load=False):
    """Ładuje projekty z folderu uploads/"""
    if not auto_load:
        return []

    print(f"\\n📁 Szukam plików w folderze {UPLOADS_DIR}/...")
    print("   (Obsługiwane: .pdf, .xlsx, .xls, .docx, .doc)")

    files = glob.glob(os.path.join(UPLOADS_DIR, "*"))
    if not files:
        print("  ⚠️  Brak plików w folderze uploads/")
        return []

    projects = []
    supported_exts = ['.pdf', '.xlsx', '.xls', '.docx', '.doc']
    
    for file_path in files:
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in supported_exts:
                print(f"  ⏭️  Pomijam: {os.path.basename(file_path)} (nieobsługiwany format)")
                continue
            
            print(f"\\n  📄 Czytam: {os.path.basename(file_path)}...")
            project = parse_project_with_gemini_hybrid(file_path)
            if project and project.get("nazwa"):
                projects.append(project)

    print(f"\\n✅ Załadowano {len(projects)} projektów z uploadów")
    return projects

# ============================================================================
# MATCHOWANIE GRANTÓW Z PROJEKTAMI
# ============================================================================

def match_granty_z_projektami(granty, projekty):
    """Matchuje granty z projektami"""
    matches = []

    for grant in granty:
        grant_typ = grant.get("typ", "").lower()
        grant_kwota_max = grant.get("kwota_max", 0)

        for projekt in projekty:
            projekt_typ = projekt.get("typ", "").lower()
            projekt_luka = projekt.get("budzet", 0) - projekt.get("wydane", 0)

            if grant_typ and projekt_typ and grant_typ != projekt_typ:
                continue

            if grant_kwota_max > 0 and grant_kwota_max < projekt_luka:
                continue

            score = grant.get("match_score", 50)

            if score >= 50:
                match = {
                    "grant_nazwa": grant.get("nazwa", ""),
                    "projekt_id": projekt.get("id", ""),
                    "projekt_nazwa": projekt.get("nazwa", ""),
                    "grant_typ": grant.get("typ", ""),
                    "projekt_typ": projekt.get("typ", ""),
                    "kwota_grantu": grant.get("kwota_max", 0),
                    "luka_projektu": projekt_luka,
                    "deadline": grant.get("deadline", "N/A"),
                    "szansa": grant.get("szansa", "0%"),
                    "match_score": score,
                    "source": grant.get("source", "")
                }
                matches.append(match)

    return sorted(matches, key=lambda x: x["match_score"], reverse=True)

# ============================================================================
# GENEROWANIE RAPORTU HTML
# ============================================================================

def generuj_raport_html_v245(granty, projekty, matches):
    """Generuje raport HTML v2.4.5"""
    data_dzisiaj = datetime.now().strftime("%d.%m.%Y %H:%M")

    projektow_domyslnych = len([p for p in projekty if p.get("source") == "domyslny"])
    projektow_uploadow = len([p for p in projekty if p.get("source") == "upload"])

    html = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Grant Scout v2.4.5</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 1500px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{ color: #667eea; font-size: 28px; margin-bottom: 10px; }}
            h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-number {{ font-size: 28px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; opacity: 0.9; margin-top: 5px; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            th {{
                background: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
                font-size: 13px;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }}
            tr:hover {{ background: #f8f9fa; }}
            .badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            .badge-upload {{ background: #d4edda; color: #155724; }}
            .badge-high {{ background: #28a745; color: white; }}
            .badge-medium {{ background: #ffc107; color: black; }}
            .badge-low {{ background: #dc3545; color: white; }}
            .info-box {{
                background: #d1ecf1;
                border: 1px solid #bee5eb;
                color: #0c5460;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Grant Scout Agent v2.4.5 - IMPROVED PARSER</h1>
            <p style="color: #666; font-size: 14px;">Data: <strong>{data_dzisiaj}</strong></p>

            <div class="info-box">
                ⚡ <strong>v2.4.5 New!</strong> Ulepszona ekstrakcja JSON - 4 strategie parsowania!
            </div>

            <h2>📊 Statystyka</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(granty)}</div>
                    <div class="stat-label">Granty znalezione</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(projekty)}</div>
                    <div class="stat-label">Projekty w gminie</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{projektow_domyslnych}</div>
                    <div class="stat-label">Projekty domyślne</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{projektow_uploadow}</div>
                    <div class="stat-label">Projekty z uploadów 🤖</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(matches)}</div>
                    <div class="stat-label">Matchowania grantów</div>
                </div>
            </div>
    """

    if projektow_uploadow > 0:
        html += """
            <h2>📁 Projekty z uploadów</h2>
            <table>
                <thead>
                    <tr>
                        <th>Projekt</th>
                        <th>Typ</th>
                        <th>Budżet</th>
                        <th>Luka finansowa</th>
                        <th>Pasujące granty</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for projekt in projekty:
            if projekt.get("source") == "upload":
                luka = projekt.get("budzet", 0) - projekt.get("wydane", 0)
                count_matches = len([m for m in matches if m["projekt_id"] == projekt.get("id")])
                
                html += f"""
                    <tr>
                        <td><strong>{projekt.get('nazwa', 'Unknown')}</strong></td>
                        <td><span class="badge badge-upload">UPLOAD</span> {projekt.get('typ', '')}</td>
                        <td>PLN {projekt.get('budzet', 0):,}</td>
                        <td>PLN {luka:,}</td>
                        <td><strong>{count_matches}</strong> grantów</td>
                    </tr>
                """
        
        html += """
                </tbody>
            </table>
        """

    html += """
            <h2>💰 Granty ze SMART Matching</h2>
            <table>
                <thead>
                    <tr>
                        <th>Grant</th>
                        <th>Przypisane projekty</th>
                        <th>Kwota</th>
                        <th>Deadline</th>
                        <th>Match %</th>
                    </tr>
                </thead>
                <tbody>
    """

    grant_groups = {}
    for match in matches:
        grant = match["grant_nazwa"]
        if grant not in grant_groups:
            grant_groups[grant] = []
        grant_groups[grant].append(match)

    for grant_name, grant_matches in grant_groups.items():
        first_match = grant_matches[0]

        projekty_html = '<div style="font-size: 12px;">'
        for match in grant_matches:
            projekty_html += f"• {match['projekt_nazwa']}<br>"
        projekty_html += '</div>'

        badge_class = 'badge-high' if first_match['match_score'] >= 80 else 'badge-medium' if first_match['match_score'] >= 60 else 'badge-low'

        html += f"""
                    <tr>
                        <td><strong>{grant_name}</strong></td>
                        <td>{projekty_html}</td>
                        <td>PLN {first_match.get('kwota_grantu', 0):,}</td>
                        <td>{first_match.get('deadline', 'N/A')}</td>
                        <td><span class="badge {badge_class}">{first_match['match_score']}%</span></td>
                    </tr>
        """

    html += """
                </tbody>
            </table>

            <p style="text-align: center; color: #999; margin-top: 40px; font-size: 12px;">
                Raport wygenerowany: Grant Scout Agent v2.4.5 IMPROVED PARSER<br>
                © 2025 Gmina Czaplinka
            </p>
        </div>
    </body>
    </html>
    """

    return html

def parse_arguments():
    parser = argparse.ArgumentParser(description="Grant Scout v2.4.5")
    parser.add_argument("--auto-load-uploads", action="store_true", help="Załaduj projekty z uploads/")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    return parser.parse_args()

def main():
    args = parse_arguments()

    print("=" * 70)
    print("🚀 GRANT SCOUT AGENT v2.4.5 - IMPROVED PARSER")
    print("=" * 70)

    try:
        uploaded_projects = load_projects_from_uploads(args.auto_load_uploads)

        if uploaded_projects:
            BUDZET_GMINY["projekty"].extend(uploaded_projects)
            print(f"\\n✅ Dodano {len(uploaded_projects)} projektów z uploadów")

        print("\\n🔍 Szukam grantów...")
        granty = list({g.get('nazwa'): g for g in GRANTY_FALLBACK}.values())
        print(f"✅ {len(granty)} unikalnych grantów")

        print("\\n🔗 Matchuję granty z projektami...")
        matches = match_granty_z_projektami(granty, BUDZET_GMINY["projekty"])
        print(f"✅ Znalazłem {len(matches)} matchowań")

        print("\\n📄 Generuję raport HTML...")
        raport_html = generuj_raport_html_v245(granty, BUDZET_GMINY["projekty"], matches)

        os.makedirs(REPORTS_DIR, exist_ok=True)
        data_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = os.path.join(REPORTS_DIR, f"report_{data_suffix}.html")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(raport_html)

        print(f"✅ Raport zapisany: {html_path}")

        print("\\n" + "=" * 70)
        print("✅ SUKCES! Grant Scout v2.4.5 - IMPROVED PARSER")
        print("=" * 70)
        print(f"\\n📊 Otwórz raport w przeglądarce:")
        print(f"   {html_path}")

        return 0

    except Exception as e:
        print(f"\\n❌ BŁĄD: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())