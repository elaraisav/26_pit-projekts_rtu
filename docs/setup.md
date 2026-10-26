# Uzstādīšanas ceļvedis

Detalizēta instrukcija projekta uzstādīšanai un palaišanai. Īsā versija ir [README](../README.md) sadaļā „Ātrā palaišana". Ja kaut kas nestrādā, skat. [problēmu novēršanu](troubleshooting.md).

## 1. Nepieciešamie rīki

| Rīks | Windows | macOS | Linux |
|---|---|---|---|
| Git | `winget install --id Git.Git -e` vai [git-scm.com](https://git-scm.com/downloads) | `xcode-select --install` vai `brew install git` | distribūcijas pakotņu pārvaldnieks |
| uv | `winget install --id=astral-sh.uv -e` | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

Citi uv uzstādīšanas veidi: [uv dokumentācija](https://docs.astral.sh/uv/getting-started/installation/).

Pēc uzstādīšanas **aizver un no jauna atver termināli** (arī VS Code vai PyCharm), citādi jaunās komandas netiks atrastas. Pārbaudi:

```bash
git --version
uv --version
```

Python atsevišķi uzstādīt nav nepieciešams – `uv sync` atradīs projektā lietoto versiju un pats lejupielādēs Python 3.13, ja tā nav.

## 2. Projekta lejupielāde

Izvēlies mapi, kurā glabāsi projektu. **Windows:** neizmanto OneDrive sinhronizētas mapes (bieži tās ir *Desktop* un *Documents*) – `.venv` mapē ir tūkstošiem failu, un sinhronizācija rada kļūdas. Piemērs: `C:\dev\`.

Dažas lejupielādes iespējas:

- **Terminālis:** atver termināli izvēlētajā mapē un izpildi
  ```bash
  git clone https://github.com/elaraisav/26_pit-projekts_rtu.git
  cd 26_pit-projekts_rtu
  ```
- **VS Code:** `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`) → **Git: Clone** → ielīmē adresi `https://github.com/elaraisav/26_pit-projekts_rtu.git` → izvēlies mapi → **Open**.
- **PyCharm:** **File → New → Project from Version Control** (vai sākuma logā **Get from VCS**) → ielīmē adresi → **Clone**.
- **GitHub Desktop:** **File → Clone repository → URL** → ielīmē adresi → **Clone**.

Tālākās komandas izpildi terminālī, kas atvērts projekta mapē. VS Code un PyCharm tas ir iebūvētais terminālis (**Terminal → New Terminal** / **View → Tool Windows → Terminal**), GitHub Desktop – **Repository → Open in Terminal** (Windows: **Open in Command Prompt**).

## 3. Uzstādīšana

<details>
<summary><strong>Ja lieto mise</strong> (neobligāti – izpildi pirms uzstādīšanas komandām)</summary>

[mise](https://mise.jdx.dev/) ir rīku versiju pārvaldnieks. Projektā esošais `mise.toml` uzstāda Python 3.13 un uv, kā arī automātiski aktivizē `.venv`, kad atver projekta mapi. Ar mise uv atsevišķi uzstādīt nav nepieciešams.

Pirms mise atļauj izmantot projekta konfigurāciju, to jāapstiprina. Vispirms apskati faila saturu (Windows cmd: `type mise.toml`):

```bash
cat mise.toml
mise trust
mise install
```

</details>

```bash
uv sync
uv run python scripts/setup_env.py
uv run python manage.py migrate
```

- `uv sync` – izveido `.venv` mapi ar Python 3.13 un tieši tām atkarību versijām, kas norādītas `uv.lock`.
- `scripts/setup_env.py` – izveido `.env` failu no `.env.example` un ieraksta tajā jaunu, tikai tev piederošu slepeno atslēgu.
- `migrate` – izveido lokālo datubāzi `db.sqlite3`. Veiksmīgā gadījumā parādīsies vairākas rindas `Applying … OK`.

Virtuālā vide nav jāaktivizē – `uv run` to izmanto automātiski. Visas projekta komandas raksti ar `uv run` priekšā.

### Ja jau ir vecā `db.sqlite3`

Projekts izmanto savu lietotāja modeli (`testsite.User`), un to var izvēlēties tikai pirms pirmās `migrate`. Ja `db.sqlite3` tika izveidota pirms tam, `migrate` apstāsies ar kļūdu `InconsistentMigrationHistory` (skat. [problēmu novēršanu](troubleshooting.md)). Vecā datubāze nesatur noderīgus datus, tāpēc to var droši izdzēst un izveidot no jauna:

1. Aptur serveri, ja tas darbojas (`Ctrl+C`).
2. Izdzēs failu `db.sqlite3` projekta mapē.
3. Izveido tabulas no jauna:

```bash
uv run python manage.py migrate
```

Ja vecā datubāze tev tomēr jāsaglabā, pārvieto to uz mapi ārpus projekta, nevis pārsauc projekta mapē: kopija ar citu nosaukumu (piemēram, `db.sqlite3.bak`) Git redzētu kā neiekļautu failu, jo `.gitignore` ignorē tikai `db.sqlite3`.

### Administratora konts (neobligāti)

Lai pārskatītu lietotājus un viņu lomas, izveido administratoru (e-pasts ir obligāts, jo tam jābūt unikālam):

```bash
uv run python manage.py createsuperuser
```

Pēc servera palaišanas ieej <http://127.0.0.1:8000/admin/>.

### Ja `.env` jāizveido manuāli

`scripts/setup_env.py` to izdara automātiski. Ja tomēr vajag ar roku:

1. Nokopē `.env.example` uz `.env` (macOS/Linux/PowerShell: `cp .env.example .env`, Windows cmd: `copy .env.example .env`).
2. Ģenerē atslēgu:
   ```bash
   uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Ielīmē to `.env` failā vienpēdiņās: `DJANGO_SECRET_KEY='...'`.

`.env` rediģē ar koda redaktoru (VS Code, PyCharm, Notepad). **Neizmanto macOS TextEdit** – tas aizstāj pēdiņas ar „gudrajām" pēdiņām un var saglabāt failu RTF formātā. macOS Finder faili, kuru nosaukums sākas ar punktu, pēc noklusējuma ir paslēpti – parāda tos ar `Cmd+Shift+.`.

Vides mainīgo apraksts: [konfigurācija](configuration.md).

## 4. Palaišana

```bash
uv run python manage.py runserver
```

Terminālī parādīsies brīdinājums `WARNING: This is a development server…` – lokālajai izstrādei to var ignorēt.

Atver <http://127.0.0.1:8000/>. Ja viss izdevies, redzēsi autorizācijas lapu. Pirmo lietotāju izveido lapā `/registracija/` (pēc tam piesakies sākumlapā) vai ar `createsuperuser`. Visas lapas, izņemot autorizāciju un reģistrāciju, pieprasa pieteikšanos; bez tās notiek pāradresācija uz autorizācijas lapu.

Serveri aptur terminālī ar `Ctrl+C` (arī macOS – Control, nevis Command).

## 5. Darbs redaktorā

Redaktoram jānorāda Python interpretators no projekta `.venv` mapes, lai darbotos koda papildināšana un kļūdu pārbaude.

**VS Code**

1. Uzstādi paplašinājumu **Python** (Microsoft): **Extensions** (`Ctrl+Shift+X`) → meklē „Python".
2. Pēc `uv sync`: `Ctrl+Shift+P` → **Python: Select Interpreter** → izvēlies `.venv`.
3. Ja VS Code piedāvā **Create Environment** – atsakies. Vidi izveido `uv sync`; VS Code izveidotā vide neievērotu `uv.lock` versijas.

**PyCharm**

Jaunākās versijas atpazīst `uv.lock` un piedāvā uv vidi. Ja nē: **Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Select existing** → `.venv`. Serveri var palaist terminālī vai ar Python palaišanas konfigurāciju: skripts `manage.py`, parametri `runserver`.

`.env` failu ielādē pats `settings.py`, tāpēc redaktorā nekas papildus nav jāiestata.
