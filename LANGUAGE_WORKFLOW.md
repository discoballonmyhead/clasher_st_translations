# Adding a language, start to finish

Four steps. Nothing to rebuild, no app release.

```
1. Add a column to the sheet          "Korean"  (or "Korean (ko)")
2. Translate it (or part of it)        empty cells fall back to English
3. python tools/langpack.py            pick the sheet, press Pack
4. Upload the new lang_ko.zip          gh release upload latest lang_ko.zip --clobber
```

The app lists whatever `lang_*.zip` sits on the latest release of the
translations repo, so Korean appears in the picker as soon as the zip is up.
People already on an older build see it too.

Step 3 also rewrites `lib/core/constants/app_language_constants.dart` so the
picker has the native name and flag for the new code. That one file does need a
build to reach people — until then the picker shows `KO` with a best-guess flag,
which still works. So: upload the zip whenever you like, ship the registry with
your next release.

## How a column becomes a code

The code is the whole contract: the zip is `lang_<code>.zip`, the app stores the
pack under `<code>`, and `LanguageRegistry` looks it up by `<code>`. So the tool
never guesses one. It resolves the column header in this order:

1. a **`Languages` tab** in the workbook — the one to use when you want control:

   | Column | Code | Name | Country |
   |---|---|---|---|
   | Vietnamese (North) | vi | Tiếng Việt (Miền Bắc) | VN |
   | Vietnamese (South) | vi-south | Tiếng Việt (Miền Nam) | VN |

2. a `languages.json` beside the .xlsx: `{"Vietnamese (South)": ["vi-south", "Tiếng Việt (Miền Nam)", "VN"]}`
3. a code in brackets: `Bengali (bn)`, `Chinese (zh-TW)`
4. a header that is already a code: `th`, `zh-TW`
5. the built-in table of language names in `langpack.py` — `Japanese`, `Malay`,
   `Filipino`, `Indonesian`, `Vietnamese (North)`, `Vietnamese (South)` and about
   fifty more

Brackets only count as a code when they look like one, so `Vietnamese (North)`
is read as a name (rule 5) and `Bengali (bn)` as a code (rule 3).

If a column matches none of these, the run **stops** and names the column. That
is deliberate: a made-up code would ship a pack the app can never match.

## Your current set

| Sheet column | Code | Pack | Shows in the picker as |
|---|---|---|---|
| English | `en` | *not packed, built into the app* | English |
| Vietnamese (North) | `vi` | `lang_vi.zip` | Tiếng Việt (Miền Bắc) |
| Vietnamese (South) | `vi-south` | `lang_vi-south.zip` | Tiếng Việt (Miền Nam) |
| Japanese | `ja` | `lang_ja.zip` | 日本語 |
| Malay | `ms` | `lang_ms.zip` | Bahasa Melayu |
| Filipino | `fil` | `lang_fil.zip` | Filipino |
| Indonesian | `id` | `lang_id.zip` | Bahasa Indonesia |

Two of these are worth a look before you publish, because **a code cannot be
changed later without orphaning what people already downloaded**:

- **`vi-south`** is not a standard language tag; there is no official subtag for
  southern Vietnamese. It is fine as an app-internal code (the app treats codes
  as opaque strings) and it reads well as a file name. If you would rather be
  strict, use `vi-VN-x-south` — change the one line in the `Languages` tab or in
  `KNOWN` in `langpack.py` and re-run. Do it before the first upload.
- **`fil`** is the right code for Filipino. Your old registry had `tl`
  (Tagalog). They are not the same thing and `tl` is deprecated for this use, so
  the generated registry uses `fil`.

## What the tool checks before writing

- **Placeholders match the English.** `Welcome back, {name}` translated as
  `Chào mừng, {ten}` would print the literal `{ten}` in the app. Every
  `{placeholder}` missing or invented is reported with its key and language.
- **`%s` counts match**, for the 40 or so strings that still use that style.
- **Stray `{` or `}`** that is not a placeholder.
- **Coverage**, per language, as a percentage of the sheet.

Problems are reported and the pack is still written, because a half-right pack
is better than none: the app falls back to English for any key the pack lacks.
Use `--strict` (or the checkbox) to refuse to write instead — that is what to
use in CI.

## The whole sheet, however it is laid out

Every tab whose first column header is `Key` is read and merged. `Read me`,
`Progress`, `Changes` and anything else is ignored, as are the grey columns
(`Constant`, `Section`, `Placeholders`, `Notes`). So the 21-tab workbook from
round 33 and a single wide sheet both work; the 21-tab one merges to 1,825 keys.

A key that appears twice keeps its first value and is reported.

## Commands

```
python tools/langpack.py                                   the window
python tools/langpack.py --xlsx sheet.xlsx                 check, write nothing
python tools/langpack.py --xlsx sheet.xlsx --list           just the languages
python tools/langpack.py --xlsx sheet.xlsx --write
python tools/langpack.py --xlsx sheet.xlsx --write \
    --registry lib/core/constants/app_language_constants.dart
python tools/langpack.py --xlsx sheet.xlsx --write --only ja --only ms
python tools/langpack.py --xlsx sheet.xlsx --write --strict      for CI
```

The packs are byte-for-byte reproducible: the same sheet gives the same zip, so
a release asset only changes when the words did.

## What the app does with them

Already built, nothing to change beyond the two files in this zip:

- `LanguageDownloadService.fetchLanguageManifest()` lists the release assets,
  keeps the ones named `lang_*.zip`, drops `en`, and reads each size straight
  from GitHub — one call, no probing.
- `downloadLanguage(code)` re-resolves the asset, downloads it, pulls
  `translations.json` out of the zip, and deletes the zip.
- `TranslationService` keeps the decoded map in Hive under the code, caches the
  manifest for 24 hours with a stale fallback when offline, and falls back
  key by key: active language → built-in English → the key itself.

So a language that is only 60% translated behaves correctly: the translated keys
appear in that language, the rest in English.
