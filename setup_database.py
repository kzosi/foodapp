import sqlite3

def setup_database():
    conn = sqlite3.connect('meals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            included_ingredients TEXT,
            excluded_ingredients TEXT,
            meal_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
