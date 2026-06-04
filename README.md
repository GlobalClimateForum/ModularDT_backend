# How to run in development?

# First time
1. Python 3.14.4 required
2. Create a virtual environment `python -m venv .venv`
3. Activate the virtual environment: Linux/macOS `source .venv/bin/activate` on Windows  `.venv\Scripts\activate` or Windows PowerShell `.venv\Scripts\Activate`
4. Install required packages: `pip install -r requirements.txt`
5. Create the database and migrate it by running `python manage.py migrate` - should create db.sqlite3 file

# Run dev-Server
1. `python manage.py runserver`
