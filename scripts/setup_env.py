"""Create .env from .env.example with a freshly generated secret key."""
from pathlib import Path

from django.core.management.utils import get_random_secret_key

root = Path(__file__).resolve().parent.parent
env = root / '.env'
if env.exists():
    raise SystemExit('.env already exists, not overwriting it.')

text = (root / '.env.example').read_text(encoding='utf-8')
if "DJANGO_SECRET_KEY=''" not in text:
    raise SystemExit(".env.example has no DJANGO_SECRET_KEY='' line to fill in.")
text = text.replace("DJANGO_SECRET_KEY=''", f"DJANGO_SECRET_KEY='{get_random_secret_key()}'")
env.write_text(text, encoding='utf-8')
print('Created .env with a new DJANGO_SECRET_KEY.')
