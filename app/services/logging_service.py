import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "logs.db"

# CENNIK OPENAI (orientacyjny, w USD)
# GPT-4o: $2.50 / 1M input, $10.00 / 1M output
# DALL-E 3: $0.040 / obraz (standard)
PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "dall-e-3": {"image": 0.040},
    "unknown": {"input": 0, "output": 0}
}

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Pozwala odwoływać się do kolumn po nazwie
    return conn

def init_db():
    """Tworzy tabelę i aktualizuje schemat jeśli brakuje kolumny 'model'."""
    conn = _get_conn()
    cur = conn.cursor()
    
    # 1. Tworzenie tabeli (jeśli nie istnieje)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT,
            result_filename TEXT,
            effect TEXT,
            ai_description TEXT,
            tokens_in INTEGER,
            tokens_out INTEGER,
            created_at TEXT,
            model TEXT
        )
        """
    )
    
    # 2. Migracja: Sprawdź czy kolumna 'model' istnieje, jak nie to dodaj (dla starych baz)
    cur.execute("PRAGMA table_info(operations)")
    columns = [info[1] for info in cur.fetchall()]
    if "model" not in columns:
        print(">>> Aktualizacja bazy: Dodawanie kolumny 'model'...")
        cur.execute("ALTER TABLE operations ADD COLUMN model TEXT")
        # Uzupełnij stare rekordy domyślnie
        cur.execute("UPDATE operations SET model = 'gpt-4o' WHERE effect != 'dall-e-3'")
        cur.execute("UPDATE operations SET model = 'dall-e-3' WHERE effect = 'dall-e-3'")
    
    conn.commit()
    conn.close()

def log_operation(
    original_filename: str,
    result_filename: str,
    effect: str,
    ai_description: str,
    tokens_in: int,
    tokens_out: int,
    model: str = "gpt-4o"
):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO operations (
            original_filename, result_filename, effect, 
            ai_description, tokens_in, tokens_out, created_at, model
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            original_filename, result_filename, effect, ai_description,
            tokens_in, tokens_out, datetime.now().isoformat(timespec="seconds"), model
        ),
    )
    conn.commit()
    conn.close()

def calculate_cost(row):
    """Oblicza koszt dla pojedynczego wiersza."""
    model = row["model"] if row["model"] else "gpt-4o"
    effect = row["effect"]
    
    cost = 0.0
    
    # Logika dla DALL-E
    if "dall-e" in model.lower() or effect == "dall-e-3":
        cost = PRICING["dall-e-3"]["image"]
        
    # Logika dla GPT (tekst/vision)
    else:
        # Jeśli nie znamy modelu, zakładamy gpt-4o
        prices = PRICING.get(model, PRICING["gpt-4o"])
        t_in = row["tokens_in"] or 0
        t_out = row["tokens_out"] or 0
        cost = (t_in * prices["input"]) + (t_out * prices["output"])
        
    return cost

def get_logs():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM operations ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    
    logs_data = []
    total_cost = 0.0
    
    for row in rows:
        cost = calculate_cost(row)
        total_cost += cost
        
        logs_data.append({
            "created_at": row["created_at"],
            "original_filename": row["original_filename"],
            "result_filename": row["result_filename"],
            "effect": row["effect"],
            "ai_description": row["ai_description"],
            "tokens_in": row["tokens_in"],
            "tokens_out": row["tokens_out"],
            "model": row["model"] if row["model"] else "gpt-4o", # fallback dla starych logów
            "cost": cost
        })
        
    return logs_data, total_cost