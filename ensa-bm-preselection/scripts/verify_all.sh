#!/usr/bin/env bash
set -euo pipefail

python --version
pip list | grep django
pip list | grep pdfplumber
pip list | grep pytesseract
if command -v tesseract >/dev/null 2>&1; then
  tesseract --version
else
  echo "tesseract not found"
fi

python manage.py migrate --check
python manage.py showmigrations
python manage.py check
python manage.py test users candidatures scoring notifications administration --verbosity=2
coverage run manage.py test
coverage report --min-coverage=70
curl -s -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","cin":"AB999999","password":"Test1234!","password_confirm":"Test1234!","nom":"Test","prenom":"User"}' | python -m json.tool#!/usr/bin/env bash
set -euo pipefail

# 1. Vérification environnement
python --version
pip list | grep django
pip list | grep pdfplumber
pip list | grep pytesseract
tesseract --version

# 2. Vérification base de données
python manage.py migrate --check
python manage.py showmigrations

# 3. Vérification modèles
python manage.py check

# 4. Tests unitaires complets
python manage.py test users candidatures scoring notifications administration --verbosity=2

# 5. Couverture de tests
coverage run manage.py test
coverage report --min-coverage=70

# 6. Vérification API (nécessite serveur démarré)
curl -s -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","cin":"AB999999","password":"Test1234!","password_confirm":"Test1234!","nom":"Test","prenom":"User"}' \
  | python -m json.tool
