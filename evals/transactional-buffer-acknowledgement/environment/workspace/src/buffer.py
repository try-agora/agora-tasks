import sqlite3


class Buffer:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
        )
        self.db.commit()

    def append(self, payload):
        with self.db:
            return self.db.execute(
                "INSERT INTO entries(payload) VALUES (?)", (payload,)
            ).lastrowid

    def pending(self):
        return self.db.execute("SELECT id, payload FROM entries ORDER BY id").fetchall()

    def close(self):
        self.db.close()

    def acknowledge(self, ids):
        with self.db:
            self.db.execute("DELETE FROM entries")
