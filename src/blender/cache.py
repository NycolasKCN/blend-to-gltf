import sqlite3
from pathlib import Path

# Nome do arquivo de banco de dados SQLite
DB_NAME = "cache.db"

def init_db() -> None:
    """
    Inicializa o banco de dados e cria a tabela de cache se ela não existir.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                glosa TEXT PRIMARY KEY,
                file_path TEXT NOT NULL
            )
        """)
        conn.commit()

def check_cache(glosa: str) -> str | None:
    """
    Retorna o caminho em cache associado à glosa, ou None se não existir.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM cache WHERE glosa = ?", (glosa,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
    return None

def register_cache(glosa: str, file: Path) -> None:
    """
    Registra ou atualiza o caminho do arquivo para uma determinada glosa no cache.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # O 'INSERT OR REPLACE' garante que glosas repetidas atualizem o caminho existente
        cursor.execute(
            "INSERT OR REPLACE INTO cache (glosa, file_path) VALUES (?, ?)",
            (glosa, str(file))
        )
        conn.commit()
