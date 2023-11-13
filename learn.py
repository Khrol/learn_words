#!/usr/bin/env python3
from datetime import datetime, timedelta

from database import db_conn, select_one_value
from contextlib import closing


# ANSI escape codes for text colors
class Colors:
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'


def new_words():
    return select_one_value("SELECT word_id FROM words WHERE progress=0 ORDER BY RANDOM() LIMIT 1")


def to_repeat_words(progress, interval):
    ts_cutoff = datetime.utcnow() - interval
    return select_one_value("""
        SELECT words.word_id FROM words 
        LEFT JOIN (SELECT max(timestamp) last_at, word_id FROM results GROUP BY word_id) r on words.word_id = r.word_id
        WHERE progress=? AND r.last_at < ?
        ORDER BY RANDOM() LIMIT 1
    """, (progress, ts_cutoff))


def update_yes_progress(word_id):
    progress = select_one_value("SELECT progress FROM words WHERE word_id=?", (word_id,))
    progress += 1
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("UPDATE words SET progress=? WHERE word_id=?", (progress, word_id))
        cursor.execute("INSERT INTO results (word_id, result) VALUES (?, ?)", (word_id, True))
        db_conn.commit()


def update_no_progress(word_id):
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("UPDATE words SET progress=? WHERE word_id=?", (0, word_id))
        cursor.execute("INSERT INTO results (word_id, result) VALUES (?, ?)", (word_id, False))
        db_conn.commit()


def learn_word(word_id):
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("""
            SELECT word, translation FROM words WHERE word_id=?
        """, (word_id,))
        word, translation = cursor.fetchone()
        print(word)
        given_translation = input("Answer:").strip()
        if translation == given_translation:
            print(Colors.GREEN + "Yes" + Colors.RESET)
            update_yes_progress(word_id)
        else:
            print(Colors.RED + f"No, correct: {Colors.CYAN + translation}" + Colors.RESET)
            update_no_progress(word_id)


def words_to_learn():
    while word_id := to_repeat_words(3, timedelta(days=30)):
        yield word_id
    while word_id := to_repeat_words(2, timedelta(days=7)):
        yield word_id
    while word_id := to_repeat_words(1, timedelta(days=1)):
        yield word_id
    while word_id := new_words():
        yield word_id


if __name__ == "__main__":
    for word_id in words_to_learn():
        learn_word(word_id)
    print("No more words to learn: add new")
