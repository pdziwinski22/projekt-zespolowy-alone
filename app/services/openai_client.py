from pathlib import Path
from typing import Tuple
import base64
import os
from openai import OpenAI
import logging
from dotenv import load_dotenv  # Biblioteka do czytania .env

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# 1. Znajdź ścieżkę do pliku .env (cofamy się o 2 katalogi z services/ do głównego)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"

# 2. Załaduj zmienne
load_dotenv(dotenv_path=env_path)

# 3. Pobierz klucz
api_key = os.getenv("OPENAI_API_KEY")

# Sprawdzenie czy klucz istnieje (dla bezpieczeństwa)
if not api_key:
    logger.error("BRAK KLUCZA API! Sprawdź plik .env")
    # Możemy ustawić pusty, ale zapytania się nie udadzą
    api_key = ""

# Inicjalizacja klienta
client = OpenAI(api_key=api_key)

def encode_image(image_path: Path) -> str:
    """Konwertuje obraz na base64 dla API OpenAI"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Błąd odczytu pliku {image_path}: {e}")
        return ""

def describe_image(image_path: Path, mode: str = "standard") -> Tuple[str, int, int]:
    if not api_key:
        return "Błąd: Brak konfiguracji klucza API w pliku .env", 0, 0

    base64_image = encode_image(image_path)
    if not base64_image:
        return "Błąd: Nie udało się odczytać pliku zdjęcia.", 0, 0
    
    # Konfiguracja promptów
    if mode == "medical":
        system_prompt = (
            "Jesteś zaawansowanym asystentem medycznym AI. "
            "Przeprowadź profesjonalną analizę widocznego obrazu (RTG, TK, skóra, urazy). "
            "Zidentyfikuj widoczne struktury anatomiczne i ewentualne anomalie. "
            "Używaj fachowej terminologii medycznej, ale wyjaśnij ją w nawiasie prostym językiem. "
            "WAŻNE: Na końcu dodaj disclaimer: 'To jest analiza AI, a nie porada lekarska. Skonsultuj się z lekarzem.'"
        )
        user_prompt = "Dokonaj analizy medycznej tego zdjęcia."
        max_tokens = 600
    else:
        system_prompt = "Jesteś asystentem opisującym zdjęcia. Odpowiadasz krótko, po polsku."
        user_prompt = "Opisz to zdjęcie."
        max_tokens = 200

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",  # Model Vision
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                },
            ],
            max_tokens=max_tokens,
        )
        
        msg = completion.choices[0].message
        text = msg.content.strip()
        usage = completion.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0

        return text, tokens_in, tokens_out

    except Exception as e:
        logger.exception("Błąd OpenAI Vision")
        return f"Błąd API: {str(e)}", 0, 0

def generate_image_dalle(prompt: str) -> str:
    if not api_key:
        return "" # Zwracamy pusty ciąg, obsługa błędu w UI

    try:
        print(f">>> Generowanie DALL-E: {prompt}")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        logger.exception("Błąd DALL-E")
        print(f"BŁĄD DALL-E: {e}")
        return ""