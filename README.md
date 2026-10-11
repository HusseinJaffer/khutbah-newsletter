# Khutbah newsletter

Add a khutbah .docx to `khutbahs/` (title line, date line, then Introduction / Topic / Conclusion).
Put `Logo.png` in `assets/`. On push, GitHub Actions runs `build.py`, which writes `YYYY-MM-DD.html`
pages and `index.html` and commits them. Test locally: `pip install -r requirements.txt` then `python build.py`.
