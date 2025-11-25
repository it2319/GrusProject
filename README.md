# Flask Form App

Jednoduchá Flask aplikace s formulářem (jméno, e‑mail, pohlaví, zpráva) ukládající data do perzistentní SQLite databáze a administrací pro zobrazení a mazání záznamů.

## Funkce
- Formulářová stránka s poli: jméno, e‑mail, pohlaví (muž/žena), zpráva (počet znaků se zobrazuje), tlačítko odeslat se spinnerem.
- Validace: povinná pole, e‑mail formát.
- Post/Redirect/Get pattern (po uložení proběhne redirect, formulář se vyčistí).
- Uložení dat do SQLite (`formdata.db`).
- Automatické doplnění schématu (přidání sloupců `gender`, `message` pokud chybí).
- Admin rozhraní (`/admin`) s přihlášením (`/login`, uživatelské jméno a heslo: `admin` / `admin` – pouze pro demo), výpisem záznamů (nejstarší nahoře, sekvenční číslování 1..N), mazáním jednotlivých záznamů a odhlášením.
- Perzistence databáze přes bind mount souboru `formdata.db` mimo image.
- Styling pomocí Bootstrap 5 a Bootstrap Icons.

## Struktura
```
app.py
Dockerfile
requirements.txt
dbdata/            # host složka s perzistentní DB (formdata.db)
```

## Technologie
- Python + Flask + Flask-WTF + WTForms
- SQLAlchemy ORM (SQLite)
- Docker (python:3.10-slim)
- Bootstrap 5 (CDN)

## Databáze a perzistence
Databázový soubor je v kontejneru na cestě `/app/formdata.db`. Hostitel má adresář `dbdata/` a pomocí bind mountu se mapuje:
```
-v $(pwd)/dbdata/formdata.db:/app/formdata.db
```
Pokud soubor na hostiteli neexistuje, vytvořte ho prázdný:
```
touch dbdata/formdata.db
```

## Build a běh (Docker)
V kořenovém adresáři projektu:
```bash
# Build image
docker build -t flask-form-app .

# Spuštění (mapování portu 5001->5000 a perzistence DB)
docker run -d --name flask-form-app \
  -p 5001:5000 \
  -v $(pwd)/dbdata/formdata.db:/app/formdata.db \
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
