# Projekta struktūra

Mapju un failu pārskats. Tas rāda tikai galvenos failus, lai apraksts nenovecotu pēc katra jauna faila.

```
26_pit-projekts_rtu/
├── .github/
│   ├── workflows/
│   │   └── codeql.yml       Automātiska koda drošības analīze GitHub pusē
│   └── dependabot.yml       Automātiski atkarību atjauninājumu pieprasījumi
├── chat/                    Django lietotne (app) tērzētavai: sarunas, maksājuma pieprasījumi un attēlu komplekti
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
├── db.sqlite3               Lokālā datubāze (izveido migrate)
└── media/                   Augšupielādētie faili: portfolio attēli un tērzētavas attēlu komplekti
```

## `photo_client_site/` – projekta konfigurācija

| Fails | Uzdevums |
|---|---|
| `settings.py` | Visi Django iestatījumi. Vērtības, kas atšķiras starp datoriem (atslēga, DEBUG, hosti), tiek ņemtas no `.env`. Iekļauj arī tērzētavas iestatījumus: `daphne`, `chat` un `CHANNEL_LAYERS`, kā arī augšupielādēto failu iestatījumus `MEDIA_URL` un `MEDIA_ROOT` (mape `media/`). |
| `urls.py` | Galvenā maršrutēšana: novirza pieprasījumus uz `/admin/` un uz lietotni `testsite`; ja `DEBUG` ir ieslēgts, atdod arī augšupielādētos failus no `/media/`. |
| `asgi.py` | Ieejas punkts, kas parastos pieprasījumus nodod Django, bet WebSocket savienojumus (tērzētavu) – Channels. Tāpēc `runserver` darbojas ar Daphne. |
| `wsgi.py` | Ieejas punkts serveriem izvietošanai; lokālajā darbā nav jāmaina. |

## `testsite/` – lietotne

Šeit atrodas projekta lapas. Pagaidām tās ir maketi ar fiksētu saturu, izņemot autorizāciju, reģistrāciju, tērzētavu, fotogrāfa profila aprakstu un portfolio (sk. [README](../README.md#lapas)). Tērzētavas skati atrodas šeit (`views.py`), bet tās dati un WebSocket loģika – lietotnē `chat`.

| Ceļš | Uzdevums |
|---|---|
| `urls.py` | Lietotnes maršruti: kura adrese atver kuru lapu. |
| `views.py` | Funkcijas, kas pieņem pieprasījumu un atgriež lapu. Šeit ir arī portfolio pārvaldība (pievienošana, rediģēšana, dzēšana) un tērzētavas skati (sarunas, jaunas sarunas sākšana, ziņu atjaunošana, attēlu augšupielāde). |
| `models.py` | Datubāzes tabulu apraksts. Lietotājs `User` (lietotājvārds, unikāls e-pasts, loma: klients vai fotogrāfs), `Photographer` (fotogrāfa profils, pieejams kā `user.profile`; apraksts līdz 250 rakstzīmēm) un `PortfolioImage` (fotogrāfa portfolio attēls: fails, nosaukums, kategorija un apraksts; pieejams kā `profile.portfolio_images`). Tērzētavas tabulas ir `chat/models.py`. |
| `forms.py` | Autorizācijas, reģistrācijas, fotogrāfa profila (`PhotographerForm`) un portfolio attēla (`PortfolioImageForm`; attēls līdz 10 MB) formas. |
| `admin.py` | Reģistrē `User` un `Photographer` Django administrācijas panelī (`/admin/`). |
| `templates/testsite/` | HTML veidnes (lapas). |
| `static/testsite/` | CSS, JavaScript un attēli, ko lapas ielādē. |
| `migrations/` | Datubāzes izmaiņu vēsture (`0001_initial` līdz `0004`; tostarp portfolio attēli). Kopīgs kods, sk. [līdzdalība](contributing.md#atkarības-un-migrācijas). |
| `tests.py`, `apps.py` | Testi (reģistrācijas un fotogrāfa profila) un Django standarta konfigurācija. |

## `chat/` – tērzētava

Viena saruna katram klienta un fotogrāfa pārim. Ziņas starp atvērtajām lapām nonāk caur WebSocket (Django Channels). Ziņu veidi ir trīs: teksts, maksājuma pieprasījums un attēlu komplekts. Skatus un adreses skat. `testsite/`, bet frontend – `testsite/static/testsite/chat.js`.

| Fails | Uzdevums |
|---|---|
| `models.py` | Tabulas `Conversation` (saruna), `Message` (ziņa: teksts, maksājuma pieprasījums vai attēlu komplekts) un `MessageImage` (viens komplekta attēls: sīktēls un priekšskatījums), noteikums, kas drīkst tērzēt (`can_chat`: aktīvi konti, kas nav administratori), un noteikums, kad var augšupielādēt attēlus (`open_payment_for_upload`: jaunākais pieprasījums ir apmaksāts un tam vēl nav komplekta). |
| `consumers.py` | WebSocket apstrāde: pārbauda, vai lietotājs ir sarunā, saglabā ziņu un nosūta to abiem dalībniekiem. Darbības: `message` (teksts), `payment` un `cancel_payment` (fotogrāfs pieprasa un atceļ maksājumu), `pay` (klients apmaksā; demonstrācija). |
| `forms.py` | `PaymentRequestForm` – pārbauda maksājuma pieprasījuma summu (vismaz 0,01, divas zīmes aiz komata). |
| `uploads.py` | Attēlu komplekta apstrāde: pārbauda failus (līdz 10 JPG vai PNG, katrs līdz 10 MB), izveido zip ar oriģināliem un katram attēlam sīktēlu un priekšskatījumu. Augšupielādes skats `chat_upload_images` atrodas `testsite/views.py`. |
| `signals.py` | Dzēš komplekta failus (zip, sīktēlus, priekšskatījumus), kad datubāzē tiek dzēsti to ieraksti. |
| `routing.py` | WebSocket adrese `ws/chat/<id>/`. |
| `admin.py` | Reģistrē sarunas un ziņas `/admin/`. |
| `tests.py` | Tērzētavas testi: attēlu augšupielāde (`UploadTests`) un maksājumu darbības WebSocket (`PaymentConsumerTests`). |
| `migrations/` | Tērzētavas tabulu izmaiņu vēsture (`0001_initial` līdz `0003_batch_uploads`). |

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
