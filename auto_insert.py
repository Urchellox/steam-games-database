import time
import random
import mysql.connector  

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1801",
    database="games"
)
cursor = conn.cursor()

while True:
    user_id = random.randint(1, 1000)
    app_id = random.randint(10, 500)
    hours = round(random.uniform(0.5, 20.0), 2)
    helpful = random.randint(0, 50)
    funny = random.randint(0, 20)
    is_recommended = random.choice(['True', 'False'])
    date = "2025-10-13"
    
    cursor.execute("""
        INSERT INTO recommendations (app_id, user_id, hours, helpful, funny, is_recommended, date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (app_id, user_id, hours, helpful, funny, is_recommended, date))
    
    conn.commit()
    print("Inserted new recommendation...")
    time.sleep(10)
