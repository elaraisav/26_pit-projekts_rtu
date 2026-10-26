# Programmatūras izstrādes tehnoloģiju projekts

Rīgas Tehniskās Universitātes (RTU) kursa projekts: tīmekļa platformas **makets**, kurā fotogrāfi var kopīgot fotogrāfijas ar saviem klientiem, bet klienti - viegli atrast sev piemērotus fotogrāfus.

Platformā pašlaik ir īstenotas sekojošās funkcionalitātes:
- Pilnīgi: autorizācija, reģistrācija un izrakstīšanās;
- Daļēji: (TODO);
- Statiski (fiksēts saturs): pārējās lapas (skat. tabulu zemāk).

## Ātrā palaišana

Nepieciešami [Git](https://git-scm.com/downloads) un [uv](https://docs.astral.sh/uv/getting-started/installation/) (sīkāk – [uzstādīšanas ceļvedis](docs/setup.md)).

```bash
git clone https://github.com/elaraisav/26_pit-projekts_rtu.git
cd 26_pit-projekts_rtu
uv sync
uv run python scripts/setup_env.py
uv run python manage.py migrate
uv run python manage.py runserver
```

Pēc tam atver <http://127.0.0.1:8000/> – redzēsi autorizācijas lapu. Pirmo lietotāju izveido lapā `/registracija/`.

`scripts/setup_env.py` izveido `.env` failu ar jaunu slepeno atslēgu; bez tā serveris nestartēsies.

> [!NOTE]
> Ja jau ir vecā `db.sqlite3` no laika pirms autorizācijas, `migrate` beigsies ar kļūdu. Izdzēs `db.sqlite3` (tajā nav noderīgu datu) un izpildi `migrate` vēlreiz – skat. [uzstādīšanas ceļvedi](docs/setup.md#ja-jau-ir-vecā-dbsqlite3). Administratora kontu izveido ar `uv run python manage.py createsuperuser`.

> [!IMPORTANT]
> Pakotnes pievieno tikai ar `uv add <pakotne>`, nekad ar `pip install` – citādi tās netiks pierakstītas `pyproject.toml` un `uv.lock`, un citiem projekts nestrādās.

## Tehnoloģijas

- [Python](https://www.python.org/) 3.13+ – programmēšanas valoda.
- [Django](https://www.djangoproject.com/) 6.1 – tīmekļa ietvars: lapas, maršruti, datubāzes piekļuve.
- [uv](https://docs.astral.sh/uv/) – Python versijas, virtuālās vides un atkarību pārvaldība.
- [SQLite](https://sqlite.org/) – lokālā datubāze (Django noklusējums).
- [Silo](https://hub.docker.com/r/pgsty/silo) Docker konteinerī – objektu krātuve (object storage) attēliem, savietojama ar S3 (**plānots**).

## Lapas

| Adrese | Lapa | Statuss |
|---|---|---|
| `/` | Autorizācija | darbojas |
| `/registracija/` | Reģistrācija | darbojas |
| `/registracija/nosutita/` | Paziņojums „Verifikācija nosūtīta uz epastu" | darbojas |
| `/logout/` | Izrakstīšanās (tikai `POST`, poga lapā) | darbojas |
| `/sakumlapa/` | Sākumlapa | makets |
| `/meklesana/` | Fotogrāfu meklēšana un rezultāti | makets |
| `/profils/` | Klienta profils (paša skats) | makets |
| `/profils_fotogr/` | Fotogrāfa profils (paša skats; pagaidām pieejams tikai ar pagaidu pogu sākumlapā) | makets |
| `/profils_fotogr_klienta/` | Fotogrāfa profils (klienta skats) | makets |
| `/profila_regid/` | Profila rediģēšana (`regid` = rediģēt) | makets |
| `/portfolio_regid/` | Portfolio rediģēšana | makets |

Statuss „makets" nozīmē, ka lapa rāda fiksētu saturu un nesaglabā datus. Statuss „darbojas" nozīmē, ka lapa strādā ar reāliem datiem. Statuss tiks mainīts, kad lapa sāks strādāt ar reāliem datiem.

Visas lapas, izņemot `/`, `/registracija/` un `/registracija/nosutita/`, pieprasa pieteikšanos.

## Dokumentācija

- [Uzstādīšanas ceļvedis](docs/setup.md) – rīki, projekta lejupielāde, pirmā palaišana, darbs redaktorā.
- [Problēmu novēršana](docs/troubleshooting.md) – biežākās kļūdas un risinājumi.
- [Konfigurācija](docs/configuration.md) – vides mainīgie (`.env`) un atkarību pārvaldība ar uv.
- [Projekta struktūra](docs/project-structure.md) – mapes, svarīgākie faili un maršrutēšana.
- [Līdzdalība projektā](docs/contributing.md) – zari, pull request un darba kārtība komandā.
- [Sistēmas prasību specifikācija](docs/requirements-specification.md) – ko sistēmai jādara un kādi ir ierobežojumi.
- [Sistēmas projektējums](docs/system-design.md) – moduļi, datubāze, ekrāni un lēmumu tabulas.

## Komanda

| Vārds  | Uzvārds        |
|---|---|
| Elans  | Raitums-Šāvējs |
| Aigars | Gerasimčiks    |
| Artūrs | Helmanis       |
| Marta  | Stašāne        |
| Anna   | Stašāne        |

## Licence

MIT – skatīt [LICENSE](LICENSE).

## Par mākslīgā intelekta izmantošanu

Projekta izstrādē, tostarp dokumentācijas (`README.md`, `docs/`) un koda sagatavošanā, plaši izmantojam mākslīgā intelekta (MI) rīkus. MI netiek izmantots kā aizstājējs komandas darbam: darbs tiek veikts pa soļiem, rezultāti tiek pārbaudīti, un daļu darba veicam pašu rokām.

Uzstādīšana operētājsistēmās Windows un macOS nav pārbaudīta, tāpēc to darbību nevaram garantēt. Ja radusies problēma ar instrukcijām, skriptiem vai kļūdu paziņojumiem, lūdzu, dodiet ziņu – risināsim.
