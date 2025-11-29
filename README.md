# Aplikacja do obróbki zdjęć z wykorzystaniem GPT-5.1 (OpenAI)

Projekt indywidualny zrealizowany w Pythonie z użyciem frameworka FastAPI.

## Funkcjonalności

- wgrywanie zdjęć (JPG/PNG),
- wybór efektów:
  - czarno-białe,
  - sepia,
  - rozjaśnianie,
  - zwiększanie kontrastu,
  - kompresja (obniżenie jakości, zmniejszenie rozmiaru),
- podgląd obrazu przed i po przetworzeniu,
- generowanie krótkiego opisu przetworzonego zdjęcia z wykorzystaniem modelu GPT-5.1,
- zapis przetworzonych obrazów na dysku,
- logowanie operacji w bazie SQLite (efekt, pliki, opis, liczba tokenów).

## Uruchomienie lokalne

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# plik .env:
# OPENAI_API_KEY=sk-...

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
