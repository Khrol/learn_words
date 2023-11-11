from database import init_db, db_conn
from contextlib import closing


def add_word(word, translation):
    with closing(db_conn.cursor()) as cursor:
        insert_query = "INSERT INTO words (word, translation) VALUES (?, ?)"
        cursor.execute(insert_query, (word, translation))
        db_conn.commit()


if __name__ == "__main__":
    init_db()
    more_words = True
    while more_words:
        word = input("Enter word:").strip()
        translation = input("Translation:").strip()
        add_word(word, translation)
        more_words = input("More words? (y/n)") == "y"
