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


def new_words(exclude):
    return select_one_value(f"""
    SELECT word_id FROM words WHERE progress=0 AND word_id NOT IN ({','.join(['?' for _ in exclude])}) 
    ORDER BY RANDOM() LIMIT 1
    """, exclude)


def to_repeat_words(progress, interval, exclude):
    ts_cutoff = datetime.utcnow() - interval
    return select_one_value(f"""
        SELECT words.word_id FROM words 
        LEFT JOIN (SELECT max(timestamp) last_at, word_id FROM results GROUP BY word_id) r on words.word_id = r.word_id
        WHERE progress=? AND r.last_at < ? AND words.word_id NOT IN ({','.join(['?' for _ in exclude])})
        ORDER BY RANDOM() LIMIT 1
    """, [progress, ts_cutoff] + exclude)


def update_yes_progress(word_id):
    progress = select_one_value("SELECT progress FROM words WHERE word_id=?", (word_id,))
    progress += 1
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("UPDATE words SET progress=?, last_learned_at=CURRENT_TIMESTAMP WHERE word_id=?",
                       (progress, word_id))
        cursor.execute("INSERT INTO results (word_id, result) VALUES (?, ?)",
                       (word_id, True))
        db_conn.commit()


def update_no_progress(word_id):
    with closing(db_conn.cursor()) as cursor:
        cursor.execute("UPDATE words SET progress=?, last_learned_at=CURRENT_TIMESTAMP WHERE word_id=?",
                       (0, word_id))
        cursor.execute("INSERT INTO results (word_id, result) VALUES (?, ?)",
                       (word_id, False))
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
            return True
        else:
            print(Colors.RED + f"No, correct: {Colors.CYAN + translation}" + Colors.RESET)
            update_no_progress(word_id)
            return False


def words_to_learn(exclude):
    if word_id := to_repeat_words(6, timedelta(days=32), exclude):
        return word_id
    if word_id := to_repeat_words(5, timedelta(days=16), exclude):
        return word_id
    if word_id := to_repeat_words(4, timedelta(days=8), exclude):
        return word_id
    if word_id := to_repeat_words(3, timedelta(days=4), exclude):
        return word_id
    if word_id := to_repeat_words(2, timedelta(days=2), exclude):
        return word_id
    if word_id := to_repeat_words(1, timedelta(days=1), exclude):
        return word_id
    if word_id := new_words(exclude):
        return word_id
    return None


TO_LEARN_AMOUNT = 10


if __name__ == "__main__":
    to_learn = []
    while (word_id := words_to_learn(to_learn)) and len(to_learn) < 10:
        to_learn.append(word_id)
    while to_learn:
        to_repeat = []
        for word_id in to_learn:
            if not learn_word(word_id):
                to_repeat.append(word_id)
        to_learn = to_repeat
    left = []
    while word_id := words_to_learn(left):
        left.append(word_id)
    if left:
        print(f"Left {len(left)} to learn")
    else:
        print("No more words to learn: add new")
