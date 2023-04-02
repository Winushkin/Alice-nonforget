import sqlite3


class Database:
    def __init__(self, fname: str):
        self.con = sqlite3.connect(fname, check_same_thread=False)
        self.cur = self.con.cursor()

    def create_database(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id VARCHAR UNIQUE,
        state VARCHAR,
        stage INTEGER);
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id VARCHAR,
        title VARCHAR,
        items VARCHAR);
        """)
        self.con.commit()

    def add_new_user(self, user_id: str) -> bool:
        exist_user = self.con.execute("""
        SELECT user_id FROM users WHERE user_id = ?
        """, (user_id, )).fetchone()
        if not exist_user:
            self.con.execute("""
            INSERT INTO users (user_id, state, stage) VALUES (?, 'ZERO', 0)
            """, (user_id, ))
            self.con.commit()
            return True
        return False

    def get_state(self, user_id: str) -> str:
        return self.con.execute("""
        SELECT state FROM users WHERE user_id = ?
        """, (user_id, )).fetchone()[0]

    def get_stage(self, user_id: str) -> int:
        return self.con.execute("""
        SELECT stage FROM users WHERE user_id = ?
        """, (user_id,)).fetchone()[0]

    def set_state(self, user_id: str, state: str) -> None:
        self.con.execute("""
        UPDATE users
        SET state = ?
        WHERE user_id = ?
        """, (state, user_id))

    def set_stage(self, user_id: str, stage: int) -> None:
        self.con.execute("""
        UPDATE users
        SET stage = ?
        WHERE user_id = ?
        """, (stage, user_id))

    def add_reminder(self, user_id: str, dct_: dict):
        title = dct_[user_id]["title"]
        items = "; ".join(dct_[user_id]["reminder_list"])
        data = self.con.execute("""
        SELECT * FROM reminders WHERE owner_id = ? AND title = ?
        """, (user_id, title)).fetchall()
        if not data:
            self.con.execute("""
            INSERT INTO reminders (owner_id, title, items) VALUES(?, ? ,?) 
            """, (user_id, title, items))
            self.con.commit()
        else:
            self.con.execute("""
            UPDATE reminders SET owner_id = ?, title = ?, items = ? WHERE owner_id = ? AND title = ?
            """, (user_id, title, items, user_id, title))
            self.con.commit()

    def get_reminder_items(self, user_id, title):
        try:
            return self.con.execute("""
            SELECT items FROM reminders WHERE owner_id = ? AND title = ?
            """, (user_id, title)).fetchone()[0]
        except Exception:
            return False

    def delete_reminder(self, user_id, title):
        check = self.con.execute("""
        SELECT * FROM reminders WHERE owner_id = ? AND title = ?
        """, (user_id, title)).fetchone()
        if check:
            self.con.execute("""
            DELETE FROM reminders WHERE owner_id = ? AND title = ?
            """, (user_id, title))
            self.con.commit()
            return True
        return False

    def get_reminders_with_owner(self, user_id):
        a = self.con.execute("""
        SELECT * FROM reminders WHERE owner_id = ?
        """, (user_id,)).fetchall()
        dct = list(map(lambda n: {
            "id": n[0],
            "owner_id": n[1],
            "title": n[2],
            "items": n[3]
        }, a))
        return dct

    def does_reminder_exists(self, user_id, title):
        data = self.con.execute("""
        SELECT title FROM reminders WHERE owner_id = ? AND title = ?
        """, (user_id, title)).fetchall()
        return not bool(data)