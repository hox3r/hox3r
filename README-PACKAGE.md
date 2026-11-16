# HOX3R Profile Package

This archive contains the profile project and its local Git history for `hox3r/hox3r`.

## Branches and commit history

- `main` contains the starting profile project (`first commit`).
- `feat/monochrome-ascii-banner` contains the implementation, generated artwork, README integration, and documentation updates.

Inspect the history with:

```bash
git log --oneline --decorate --all --graph
```

## Banner design

- The supplied profile portrait is converted into a monochrome ASCII character portrait.
- White symbols assemble from the outer edges against a black background.
- A horizontal scan effect begins after the portrait assembly.
- Desktop and mobile variants are generated.
- Existing profile information and project descriptions are preserved.

## Regenerate the banner

Requires Python 3.10+ and the packages in `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_profile_hero.py
python scripts/generate_profile_hero.py --check
```

The source portrait is included in this ZIP so the banner can be regenerated locally. `assets/source/` is ignored by Git and is not included in commits. Do not force-add the original portrait to the public repository.

## Push to GitHub

The repository remote is configured as `https://github.com/hox3r/hox3r.git`. When the GitHub repository is empty, push the baseline branch first, then the feature branch:

```bash
git push -u origin main
git push -u origin feat/monochrome-ascii-banner
```

Then open a pull request with:

- Base: `main`
- Compare: `feat/monochrome-ascii-banner`
- Title: `Add monochrome ASCII profile banner`

Compare branches:

https://github.com/hox3r/hox3r/compare/main...feat/monochrome-ascii-banner
