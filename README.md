# Flask Form App

Jednoduchá Flask aplikace s formulářem (jméno, e‑mail, pohlaví, zpráva) ukládající data do perzistentní SQLite databáze a administrací pro zobrazení a mazání záznamů.
Jednoduchy chat.

## Funkce
- Formulář: jméno, e‑mail, pohlaví (muž/žena), zpráva; počítadlo znaků a spinner při odeslání.
- Validace: povinná pole, formát e‑mailu, přesměrování po úspěchu (PRG).
- Ukládání do SQLite + auto‑migrace chybějících sloupců (`gender`, `message`).
- Autentizace: registrace/přihlášení uživatele (username, email, gender, heslo hash), odhlášení.
- Zprávy: vyhledávání uživatelů, seznam konverzací seřazený podle poslední zprávy, chat thread (moje vlevo/šedé, ostatní vpravo/modré) s časem pod bublinou.
- Admin: přihlášení admina (demo `admin`/`admin`), výpis a mazání záznamů.
- Šablony: Jinja makra pro komponenty (navbar, pole formuláře, alerty, toast, tabulka admina); externí CSS v `static/css/style.css`.
- Docker Compose: perzistentní databáze přes mount adresáře `dbdata/`, port publikovaný na hostu `5001`.

## Struktura
```
app.py
Dockerfile
requirements.txt
dbdata/            # host složka s perzistentní DB (formdata.db)
docker-compose.yml
templates/
  auth/
    login.html
    register.html
    login_admin.html
  sites/
    index.html
    admin.html
    messages.html
  macros/
    macros.html
static/
  css/
    style.css
.gitignore
.env.example
```

## Technologie
- Jazyky: Python, HTML, CSS
- Backend: Flask, Flask‑WTF/WTForms, Werkzeug (hashování hesla)
- Databáze: SQLAlchemy ORM (SQLite)
- Frontend: Bootstrap 5 + Bootstrap Icons, Jinja makra
- Kontejnerizace: Docker + Docker Compose (python:3.10‑slim)

## Databáze a perzistence
Databázový soubor je v kontejneru v adresáři `/app/dbdata/` (`formdata.db`). Doporučené je mountovat celý adresář kvůli kompatibilitě napříč OS:
```
-v $(pwd)/dbdata:/app/dbdata
```
V Docker Compose je toto již nastaveno a aplikace používá `SQLALCHEMY_DATABASE_URI=sqlite:///dbdata/formdata.db` přes proměnnou prostředí.

## Build a běh (Docker)
V kořenovém adresáři projektu:
```bash
# Build image
docker build -t flask-form-app .

# Spuštění (mapování portu 5001->5000 a perzistence DB)
docker run -d --name flask-form-app \
  -p 5001:5000 \
  -e SQLALCHEMY_DATABASE_URI=sqlite:///dbdata/formdata.db \
  -v $(pwd)/dbdata:/app/dbdata \
  flask-form-app

# Kontrola běhu
docker ps --filter name=flask-form-app

# Logy
docker logs -f flask-form-app

# Zastavení a znovuspuštění
docker stop flask-form-app
docker start flask-form-app
```
Aplikace pak poslouchá na adrese: http://localhost:5001

## Docker Compose
Pro jednodušší spuštění použijte Docker Compose:
```bash
docker compose up --build
```
Kompozice:
- Mapuje port `5001:5000`
- Mountuje adresář `dbdata/` do kontejneru na `/app/dbdata`
- Nastaví `SQLALCHEMY_DATABASE_URI` na `sqlite:///dbdata/formdata.db`

Pokud se kontejner ukončí s Exit Code 1, zkontrolujte logy:
```bash
docker compose logs -f web
```
Častá příčina na Windows: mountoval se neexistující soubor místo adresáře a SQLite neotevřela databázi. Řešením je výše uvedené mountování celého adresáře `dbdata/`.

## LAN přístup
- Zjistěte IP adresu hostitele (Windows): `ipconfig` → IPv4 adresa aktivního adaptéru.
- Otevřete z jiného zařízení v LAN: `http://<host-ip>:5001/` (např. `http://192.168.1.50:5001/`).
- Windows: nastavte profil sítě na Soukromá (Private) a povolte příchozí TCP port 5001 v Bráně Windows Defender.
  - PowerShell (spuštěný jako správce):
    - `Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory Private`
    - `New-NetFirewallRule -DisplayName "Flask 5001 Inbound (Private)" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow -Profile Private`
- Používejte `http://` (ne `https://`) pokud nemáte reverzní proxy s TLS.

## Konfigurace prostředí (.env)
- Konfigurace se načítá z proměnných prostředí. Vzorová konfigurace je v [.env.example](.env.example).
- Vytvořte `.env` (nekontroluje se do Git díky [.gitignore](.gitignore)) a nastavte:
  - `SECRET_KEY` – tajný klíč Flasku
  - `SQLALCHEMY_DATABASE_URI=sqlite:///dbdata/formdata.db`
  - `FLASK_APP=app.py`, `FLASK_RUN_HOST=0.0.0.0`, `FLASK_RUN_PORT=5000`

## Vývoj lokálně bez Dockeru (volitelně)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

## Bezpečnostní poznámky
Tato ukázka není připravena pro produkci.
- Admin heslo je natvrdo `admin` – doporučeno nahradit env proměnnou + hash (např. bcrypt).
- CSRF je vypnutý (`WTF_CSRF_ENABLED = False`) – v produkci zapnout.
- Použit je vývojový Flask server – pro produkci použijte WSGI (gunicorn / uWSGI).
- Chybí rate-limiting a audit logy.

## Doporučená vylepšení (next steps)
- Alembic migrace místo ručního ALTER TABLE.
- Hashování hesla a ukládání do proměnné prostředí.
- Zapnutí CSRF ochrany a přidání testů.
- Pagination / vyhledávání v adminu, export do CSV.
- Docker Compose (oddělení DB, reverse proxy) – i když pro SQLite často není nutné.
- Přidání healthchecku do Dockerfile.
- Přidání jednoduchých unit testů pro validaci formuláře.

## Řešení problémů
| Problém | Řešení |
|---------|--------|
| Záznamy nemají nové sloupce | Smažte `dbdata/formdata.db` (pokud lze) nebo spusťte aplikaci – auto-migrace přidá chybějící sloupce. |
| Chyba při mountu (přepsaná aplikace) | Ujistěte se, že mountujete pouze soubor, ne celý adresář `/app`. |
| Aplikace neběží na portu 5001 | Zkontrolujte `docker run` parametr `-p 5001:5000`. |
| Nelze se přihlásit | Ověřte, že používáte `admin` / `admin`. |

## Licence
Interní demonstrační projekt.
