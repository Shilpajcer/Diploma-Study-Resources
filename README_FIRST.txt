DIPLOMA STUDY HUB — PHASE 2

OPEN IN VS CODE
1. Extract this ZIP file.
2. In VS Code choose File > Open Folder. Select the diploma-study-hub folder.
3. Open Terminal > New Terminal.
4. Run these commands one by one (Windows PowerShell):

   py -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python manage.py check
   python manage.py migrate
   python manage.py runserver

5. Open http://127.0.0.1:8000/ in your browser.

If PowerShell blocks activation, run this once in the same terminal:
   Set-ExecutionPolicy -Scope Process Bypass
Then activate again.

NOTES
- This is Phase 2 only: homepage + coming-soon routes + development sample data.
- Sample subject codes and resource entries are fake placeholders, not official DTE content.
- SQLite is temporary for this phase; MySQL is planned for a later phase.
- Keep the feature flags in config/settings/base.py set to False for now.
- Do not deploy this development configuration to production.
