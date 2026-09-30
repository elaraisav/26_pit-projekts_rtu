# Programmatūras izstrādes tehnoloģiju projekts

Studiju projekts: tīmekļa platforma, kurā fotogrāfi var kopīgot fotogrāfijas ar saviem klientiem.

## Tehnoloģijas

- Python 3.13, Django 6.1
- [uv](https://docs.astral.sh/uv/) – atkarību un virtuālās vides pārvaldība
- SQLite – lokālajai izstrādei
- Objektu krātuve (object storage) – fotogrāfiju glabāšanai (plānots)

## Priekšnosacījumi

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) – ja Python 3.13 nav instalēts, uv to lejupielādēs automātiski

## Uzstādīšana

```bash
cd \<direktorija-kurā-tiks-instalēts-projekts\>
git clone https://github.com/elaraisav/26_pit-projekts_rtu.git
cd 26_pit-projekts_rtu
uv sync
cp .env.example .env        # Windows cmd: copy .env.example .env
```

Ģenerē savu slepeno atslēgu un ieliec to `.env` failā vienpēdiņās (`DJANGO_SECRET_KEY='...'`):

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Izveido datubāzi:

```bash
uv run python manage.py migrate
```

## Palaišana

```bash
uv run python manage.py runserver
```

Atver <http://127.0.0.1:8000/>.

Ja viss izdevies, vajadzētu atvērties šādai lapai:

![Sākumlapas erkānuzņēmums](docs/assets/successful-first-run.png)

## Vides mainīgie

| Mainīgais | Obligāts | Apraksts |
|---|---|---|
| `DJANGO_SECRET_KEY` | jā | Katrs izstrādātājs ģenerē savu. Bez tā projekts nepalaižas. |
| `DJANGO_DEBUG` | nē | Ja nav norādīts – izslēgts. `.env.example` to lokāli ieslēdz. |
| `DJANGO_ALLOWED_HOSTS` | nē | Ar komatu atdalīts saraksts. Lokāli var atstāt tukšu. |

`.env` un `db.sqlite3` ir iekļauti `.gitignore` – tos nekad nepievieno repozitorijam.

## Izstrādes vide

- Redaktorā (VS Code, PyCharm u. c.) kā Python interpretatoru norādi `.venv` mapi.
- [mise](https://mise.jdx.dev/) lietotājiem `mise.toml` automātiski uzstāda Python, uv un `.venv` (nav obligāti).

## Projekta struktūra

```
photo_client_site/   Django projekta iestatījumi (settings.py, urls.py)
manage.py            Django komandu ieejas punkts
pyproject.toml       Atkarības
uv.lock              Precīzas atkarību versijas
.env.example         Vides mainīgo paraugs
```

## Komanda

| Vārds | Loma |
|---|---|
| … | … |

## Licence

MIT – skatīt [LICENSE](LICENSE).
