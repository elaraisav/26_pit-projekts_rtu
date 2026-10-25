# Konfigurācija

Kā projekts nolasa iestatījumus un kā pārvaldīt atkarības.

## Vides mainīgie

Iestatījumi, kas atšķiras starp datoriem, glabājas `.env` failā projekta saknē (paraugs – `.env.example`). Failu ielādē `settings.py`.

| Mainīgais | Obligāts | Apraksts |
|---|---|---|
| `DJANGO_SECRET_KEY` | jā | Katrs izstrādātājs ģenerē savu. Bez tā projekts nepalaižas. |
| `DJANGO_DEBUG` | nē | Ja nav norādīts – izslēgts. `.env.example` to lokāli ieslēdz. |
| `DJANGO_ALLOWED_HOSTS` | nē | Ar komatu atdalīts saraksts. Lokāli var atstāt tukšu. |

`.env` un `db.sqlite3` ir iekļauti `.gitignore` – tos nekad nepievieno repozitorijam. Atslēga nav jādala ar citiem: katram sava.

`.env` izveide: [uzstādīšanas ceļvedis](setup.md#3-uzstādīšana).

## Atkarību pārvaldība

Pakotnes pievieno un noņem tikai ar uv – tas vienlaikus atjauno `pyproject.toml` un `uv.lock`:

```bash
uv add <pakotne>
```

```bash
uv remove <pakotne>
```

Abus failus (`pyproject.toml` un `uv.lock`) iekļauj vienā commit ar kodu, kas pakotni izmanto. Pēc `git pull` citi atjauno savu vidi ar:

```bash
uv sync
```

**Neizmanto `pip install` vai `uv pip install`** – tie uzstāda pakotni tikai tavā datorā un to nekur nepieraksta, tāpēc citiem projekts nestrādās.

`uv.lock` maina tikai uv komandas, nevis ar roku. Dependabot automātiski veido pull request ar atjauninātām versijām (`.github/dependabot.yml`).
