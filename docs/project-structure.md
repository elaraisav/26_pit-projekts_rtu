# Projekta struktūra

Mapju un failu pārskats. Tas rāda tikai galvenos failus, lai apraksts nenovecotu pēc katra jauna faila.

```
26_pit-projekts_rtu/
├── .github/
│   ├── workflows/
│   │   └── codeql.yml       Automātiska koda drošības analīze GitHub pusē
│   └── dependabot.yml       Automātiski atkarību atjauninājumu pieprasījumi
├── chat/                    Django lietotne (app) tērzētavai: sarunas un ziņas
├── docs/                    Projekta dokumentācija (ceļveži, prasību specifikācija, projektējums, attēli)
├── photo_client_site/       Django projekta konfigurācija
├── scripts/
│   └── setup_env.py         Izveido .env ar jaunu slepeno atslēgu
├── testsite/                Django lietotne (app) ar projekta lapām
├── .env.example             Vides mainīgo paraugs
├── .gitignore               Faili, kurus Git neseko
├── LICENSE                  MIT licence
├── manage.py                Django komandas: runserver, migrate u. c.
├── mise.toml                Neobligāta mise konfigurācija
├── pyproject.toml           Projekta apraksts un atkarības
├── README.md
└── uv.lock                  Precīzas atkarību versijas (ģenerē uv, nerediģēt)
```

Pēc uzstādīšanas lokāli parādīsies arī (repozitorijā tie netiek iekļauti):

```
├── .env                     Tavi personīgie iestatījumi un atslēga
├── .venv/                   Virtuālā vide ar Python un atkarībām
└── db.sqlite3               Lokālā datubāze (izveido migrate)
```

## `photo_client_site/` – projekta konfigurācija

| Fails | Uzdevums |
|---|---|
| `settings.py` | Visi Django iestatījumi. Vērtības, kas atšķiras starp datoriem (atslēga, DEBUG, hosti), tiek ņemtas no `.env`. Iekļauj arī tērzētavas iestatījumus: `daphne`, `chat` un `CHANNEL_LAYERS`. |
| `urls.py` | Galvenā maršrutēšana: novirza pieprasījumus uz `/admin/` un uz lietotni `testsite`. |
| `asgi.py` | Ieejas punkts, kas parastos pieprasījumus nodod Django, bet WebSocket savienojumus (tērzētavu) – Channels. Tāpēc `runserver` darbojas ar Daphne. |
| `wsgi.py` | Ieejas punkts serveriem izvietošanai; lokālajā darbā nav jāmaina. |

## `testsite/` – lietotne

Šeit atrodas projekta lapas. Pagaidām tās ir maketi ar fiksētu saturu, izņemot autorizāciju, reģistrāciju un tērzētavu (sk. [README](../README.md#lapas)). Tērzētavas skati atrodas šeit (`views.py`), bet tās dati un WebSocket loģika – lietotnē `chat`.

| Ceļš | Uzdevums |
|---|---|
| `urls.py` | Lietotnes maršruti: kura adrese atver kuru lapu. |
| `views.py` | Funkcijas, kas pieņem pieprasījumu un atgriež lapu. |
| `models.py` | Datubāzes tabulu apraksts. Pagaidām tikai lietotājs `User` (lietotājvārds, unikāls e-pasts, loma: klients vai fotogrāfs). Tērzētavas tabulas ir `chat/models.py`. |
| `forms.py` | Autorizācijas un reģistrācijas formas. |
| `admin.py` | Reģistrē `User` Django administrācijas panelī (`/admin/`). |
| `templates/testsite/` | HTML veidnes (lapas). |
| `static/testsite/` | CSS, JavaScript un attēli, ko lapas ielādē. |
| `migrations/` | Datubāzes izmaiņu vēsture (pagaidām `0001_initial`). Kopīgs kods, sk. [līdzdalība](contributing.md#atkarības-un-migrācijas). |
| `tests.py`, `apps.py` | Testi (pagaidām reģistrācijas) un Django standarta konfigurācija. |

## `chat/` – tērzētava

Viena saruna katram klienta un fotogrāfa pārim. Ziņas starp atvērtajām lapām nonāk caur WebSocket (Django Channels). Skatus un adreses skat. `testsite/`, bet frontend – `testsite/static/testsite/chat.js`.

| Fails | Uzdevums |
|---|---|
| `models.py` | Tabulas `Conversation` (saruna) un `Message` (ziņa) un viens noteikums, kas drīkst tērzēt (`can_chat`: aktīvi konti, kas nav administratori). |
| `consumers.py` | WebSocket apstrāde: pārbauda, vai lietotājs ir sarunā, saglabā ziņu un nosūta to abiem dalībniekiem. |
| `routing.py` | WebSocket adrese `ws/chat/<id>/`. |
| `admin.py` | Reģistrē sarunas un ziņas `/admin/`. |
| `migrations/` | Tērzētavas tabulu izmaiņu vēsture (`0001_initial`). |

`CHANNEL_LAYERS` izmanto atmiņā strādājošu variantu (`InMemoryChannelLayer`): tas der lokālam darbam ar vienu servera procesu, bet produkcijai ar vairākiem procesiem būs jāpāriet uz `channels_redis`.

### Kā pieprasījums nonāk līdz lapai

1. Pārlūks atver adresi, piemēram, `/meklesana/`.
2. `photo_client_site/urls.py` nodod adresi lietotnei `testsite`.
3. `testsite/urls.py` atrod atbilstošo skatu (`views.meklesana`).
4. Skats atgriež veidni `templates/testsite/meklesana.html`.

Jaunu lapu pievieno ar trim soļiem: veidne, skats, ieraksts `testsite/urls.py`.

## Svarīgākie faili

- **`manage.py`** – visas Django komandas palaiž caur to: `uv run python manage.py <komanda>`.
- **`uv.lock`** – garantē, ka visiem ir vienādas atkarību versijas. To maina tikai uv komandas.
- **`.env.example`** – vides mainīgo paraugs; sīkāk [konfigurācijā](configuration.md).
