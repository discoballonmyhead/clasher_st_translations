# The translations repo

Holds the spreadsheet and turns it into the language packs the app downloads.
Nothing here needs the Flutter project.

```
translations.xlsx                  the sheet: one row per key, one column per language
langpack.py                        turns the sheet into the packs
languages.json                     optional: column header -> code, if the sheet has no Languages tab
dist/                              built output, not committed
  lang_vi.zip  lang_ja.zip  …      one per language, each holding translations.json
  app_language_constants.dart      copy into the app when you next build
.github/workflows/…                commit the sheet -> packs built and uploaded
```

## What langpack.py does

Reads the sheet, works out a language code for each language column, checks the
translations against the English, and writes one `lang_<code>.zip` per language.
Each zip holds a single `translations.json` of `{"key": "text"}`.

The app's `LanguageDownloadService` lists the assets on the latest release of
this repo, keeps the ones named `lang_*.zip`, and reads each size from GitHub.
So a language is live the moment its zip is on the release: no app build, and
people on older builds get it too.

English is never packed. It ships inside the app as `defaultEnglishTranslations`,
and any key a pack is missing falls back to it.

It also writes `app_language_constants.dart` next to the zips. That is the only
piece the app itself needs updating for: it carries the native name and flag for
each code. Until you ship it, a new language still works but shows as its code.

## By hand

```
pip install openpyxl

python langpack.py                      a window: pick the sheet, press Check, then Pack
python langpack.py --write              uses the single .xlsx here
python langpack.py --list               just show the languages and their codes
python langpack.py --write --strict     refuse to write if placeholders do not match

cd dist
gh release upload latest lang_*.zip --clobber
```

`--registry ../clasher_st/lib/core/constants/app_language_constants.dart` also
drops the Dart file straight into the app, if it is checked out beside this repo.

## Or let CI do it

Push a change to the sheet on `main` and the workflow builds the packs, creates
the `latest` release if it is missing, and uploads them. The Dart file comes out
as a run artifact called `app_language_constants`.

## Adding a language

1. Add a column to the sheet: `Korean`, or `Korean (ko)` to set the code yourself.
2. Translate it. Empty cells fall back to English, so a half-done column is fine.
3. Commit, or run `python langpack.py --write` and upload `dist/lang_ko.zip`.
4. Next time you build the app, copy in the new `app_language_constants.dart`.

If a column header is not recognised, the run stops and names it rather than
guessing a code. Give it one in a `Languages` tab in the workbook:

| Column | Code | Name | Country |
|---|---|---|---|
| Vietnamese (North) | vi | Tiếng Việt (Miền Bắc) | VN |
| Vietnamese (South) | vi-south | Tiếng Việt (Miền Nam) | VN |

or in `languages.json`:

```json
{ "Vietnamese (South)": ["vi-south", "Tiếng Việt (Miền Nam)", "VN"] }
```

A code is permanent once published: the app stores downloaded packs under it.
