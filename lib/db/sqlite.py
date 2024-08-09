import sqlite3
import datetime
import pytz
import json

def get_now():
    return datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d-%m-%Y')



class SqLiteBackend:

    def __init__(self):
        self._connection = sqlite3.connect('db/bot.db', check_same_thread=False)
        self.cur = _connection.cursor()


    def get_transaction_status(hash):
        cur.execute(f"SELECT hash FROM transactions WHERE hash = '{hash}'")
        result = cur.fetchone()
        if result:
            return True
        return False

    def add_v_transaction(source, hash, value, comment):
        cur.execute("INSERT INTO transactions (source, hash, value, comment) VALUES (?, ?, ?, ?)",
                    (source, hash, value, comment))
        locCon.commit()

