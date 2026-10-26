# Līdzdalība projektā

Kā komandā strādājam ar Git un GitHub. Vides uzstādīšana: [uzstādīšanas ceļvedis](setup.md).

## Pamatnoteikumi

- Uz `main` zaru tieši nerakstām. Izmaiņas nonāk tajā tikai ar pull request (PR).
- Katram PR vajadzīgs **viens apstiprinājums no cita komandas locekļa** (ne PR autora). Ja apstiprinājuma nav iespējams iegūt, PR var sapludināt repozitorija īpašnieks.
- Viens PR – viena skaidri nosaucama izmaiņa. Mazi PR tiek pārskatīti ātrāk.

## Zaru nosaukumi

Izmantojam standarta prefiksus:

| Prefikss | Kam | Piemērs |
|---|---|---|
| `feature/` | jauna funkcionalitāte | `feature/image-storage-transfer` |
| `fix/` | kļūdas labojums | `fix/login-form-method` |
| `refactor/` | koda pārstrukturēšana vai pārsaukšana bez uzvedības maiņas | `refactor/english-identifiers` |
| `docs/` | dokumentācija | `docs/readme-restructure` |
| `chore/` | uzkopšana, atkarības, konfigurācija | `chore/remove-temp-codeql-stub` |

Nosaukumu raksta angļu valodā, ar defisēm.

## Darba gaita

1. Atjauno lokālo `main`:

```bash
git switch main
```

```bash
git pull --ff-only
```

2. Izveido zaru:

```bash
git switch -c feature/mans-zars
```

3. Veic izmaiņas, pārbaudi, ka vietne startē un lapas atveras:

```bash
uv run python manage.py runserver
```

4. Saglabā izmaiņas:

```bash
git add <faili>
```

```bash
git commit -m "Short description of the change"
```

5. Nosūti zaru uz GitHub:

```bash
git push -u origin feature/mans-zars
```

6. GitHub vietnē atver pull request uz `main`, īsi apraksti, ko mainīji un kāpēc, un palūdz kādu no komandas to pārskatīt.
7. Pēc apstiprinājuma un sapludināšanas atjauno `main`:

```bash
git switch main
```

```bash
git pull --ff-only
```

8. Ja darbs zarā ir pabeigts, izdzēs lokālo zaru:

```bash
git branch -d feature/mans-zars
```

Sapludinot PR, GitHub piedāvā izdzēst arī attālināto zaru. Dzēs to tikai tad, ja darbs zarā ir pabeigts; ja funkcionalitāte ir nepabeigta un zarā turpināsi strādāt, atstāj gan attālināto, gan lokālo zaru. Turpinot strādāt, vispirms ievelc jaunāko `main` zarā un tad atver jaunu PR.

## Commit ziņojumi

- Vēlams angļu valodā; latviešu valodā arī ir pieņemami.
- Pirmā rinda īsa un konkrēta, kas izdarīts: `Add photographer profile model`, nevis `fix`.
- Vienā commit – viena loģiska izmaiņa.

## Kods

- Kods (mainīgo, funkciju, failu un klašu nosaukumi, komentāri) tiek rakstīts angļu valodā.
- Daļa esošā koda ir latviski (piemēram, lapu un veidņu nosaukumi); to pārveidosim vēlāk, nevis pa vienam, lai nerastos konflikti.
- Lietotāja redzamie teksti (veidnēs) paliek latviski – to prasa projekta prasības.

## Atkarības un migrācijas

- Pakotnes pievieno tikai ar `uv add`; `pyproject.toml` un `uv.lock` iekļauj tajā pašā commit. Sīkāk: [konfigurācija](configuration.md#atkarību-pārvaldība).
- Migrāciju faili ir kopīgs kods. Ja divi cilvēki paralēli maina modeļus, migrācijas var konfliktēt. Pirms `makemigrations` izpildi `git pull` un paziņo komandai, ka maini modeļus.
- Ja PR maina lietotāja modeli vai citādi neļauj turpināt ar esošo `db.sqlite3`, to norāda PR aprakstā, un pēc sapludināšanas paziņo komandai, ka jāatjauno datubāze ([sīkāk](setup.md#ja-jau-ir-vecā-dbsqlite3)).
- `.env` un `db.sqlite3` nekad nepievieno repozitorijam.

## Dependabot

Dependabot automātiski atver PR ar atkarību atjauninājumiem. Mazos (labojumu) atjauninājumus var sapludināt pēc apstiprinājuma; ja otrais PR konfliktē ar pirmo, komentārā uzraksti `@dependabot rebase`. `uv.lock` konfliktus ar roku nelabo.

## Pārskatīšana (review)

Pārskatītājs pārbauda, vai:

- izmaiņa dara to, ko apraksta PR;
- vietne startē un skartās lapas atveras;
- repozitorijā nav nejauši pievienotu failu (`.env`, `db.sqlite3`, `.venv`);
- CodeQL pārbaude ir zaļa.
