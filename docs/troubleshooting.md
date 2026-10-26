# Problēmu novēršana

Biežākās kļūdas uzstādīšanas un palaišanas laikā. Uzstādīšanas soļi: [uzstādīšanas ceļvedis](setup.md).

| Kļūda | Iemesls | Risinājums |
|---|---|---|
| `…/.env was not found and DJANGO_SECRET_KEY is not set…` | Nav `.env` faila projekta saknē (blakus `manage.py`) | Izpildi `scripts/setup_env.py` vai izveido `.env` manuāli |
| `DJANGO_SECRET_KEY is missing or empty in …/.env` | `.env` ir, bet atslēga nav ierakstīta | Ģenerē atslēgu un ielīmē to (skat. [„Ja `.env` jāizveido manuāli"](setup.md#ja-env-jāizveido-manuāli)) |
| `.env already exists, not overwriting it.` | `.env` jau ir izveidots | Viss kārtībā – turpini ar `migrate` |
| `uv` / `git` netiek atrasts (`not recognized`, `command not found`) | Terminālis atvērts pirms rīka uzstādīšanas | Aizver un no jauna atver termināli vai redaktoru |
| `ModuleNotFoundError: No module named 'django'` | Komanda palaista bez `uv run` | Raksti `uv run` priekšā, piemēram, `uv run python manage.py runserver` |
| `running scripts is disabled on this system` (PowerShell) | VS Code mēģina aktivizēt `.venv` ar `Activate.ps1` | Var ignorēt – `uv run` aktivizācija nav vajadzīga. Lai paziņojums pazustu: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `python` atver Microsoft Store (Windows) | Palaists sistēmas `python`, nevis projekta | Izmanto `uv run python` |
| `InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency testsite.0001_initial on database 'default'.` | `db.sqlite3` izveidota pirms projekts pārgāja uz savu lietotāja modeli | Izdzēs `db.sqlite3` un izpildi `migrate` vēlreiz (skat. [„Ja jau ir vecā `db.sqlite3`"](setup.md#ja-jau-ir-vecā-dbsqlite3)) |
| `OperationalError: no such table: testsite_photographer` (fotogrāfa profila lapās) | Pēc `git pull` nav izpildīta jaunā migrācija | Izpildi `uv run python manage.py migrate` un pārstartē serveri |
| `Error: That port is already in use.` | Serveris jau darbojas citā terminālī | Aizver to vai palaid citā portā: `runserver 8001` |

Ja problēma nav sarakstā, dodiet ziņu komandai – pievienosim risinājumu šeit.
