import sqlite3

DB_NAME = "second.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS user_info")

    cursor.execute("""
     CREATE TABLE IF NOT EXISTS user_info(
            user_id TEXT,
            api_key TEXT PRIMARY KEY,
            total_tokens_used INTEGER DEFAULT 0,
            tier TEXT,
            vllm_lora_id INT
            )
    """)

    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin1", "this-123", 0, "free", 1))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin2", "this-124", 0, "free", 2))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin3", "this-125", 0, "premium", 3))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin4", "this-126", 0, "free", 4))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin5", "this-127", 0, "premium", 5))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin6", "that-128", 0, "premium", 1))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin7", "that-129", 0, "premium", 2))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin8", "that-130", 0, "premium", 3))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin9", "that-131", 0, "premium", 4))
    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?, ?)", ("admin0", "that-132", 0, "premium", 5))

    conn.commit()
    conn.close()

def create_new_user(user_id: str, api_key: str, tier: str = "premium", lora_id: int = 1):
    """Inserts a new user into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_info (user_id, api_key, total_tokens_used, tier, vllm_lora_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, api_key, 0, tier, lora_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_user_tokens(user_id, no_of_tokens):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE user_info SET total_tokens_used = total_tokens_used + ? WHERE user_id=?",
        (no_of_tokens, user_id)
    )

    conn.commit()
    conn.close()

def add_user_info(user_id, api_key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO user_info VALUES(?, ?, ?, ?)", 
                   (user_id, api_key, 0, "free"))
    conn.commit()
    conn.close()

def check_used_tokens(api_key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT total_tokens_used, tier FROM user_info WHERE api_key=?", (api_key,))

    result = cursor.fetchone()
    conn.close()

    return result

def check_user_info(api_key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM user_info WHERE api_key=?", (api_key, ))
    result = cursor.fetchone()

    conn.close()

    return result is not None

def get_user_id(api_key):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM user_info WHERE api_key=?", (api_key,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    return None
