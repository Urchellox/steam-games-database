import mysql.connector
from mysql.connector import connect, Error
from tabulate import tabulate

def shorten(text, length=40):
    text = str(text)
    return text if len(text) <= length else text[:length-3] + "..."

queries = [
    (
        "Список игр с описанием (короткое описание + жанры)",
        """
        SELECT s.name, d.short_description, s.genres
        FROM steam s
        JOIN steam_description_data d ON s.appid = d.steam_appid
        LIMIT 10;
        """
    ),
    (
        "Трейлеры игр",
        """
        SELECT s.name, m.movies
        FROM steam s
        JOIN steam_media_data m ON s.appid = m.steam_appid
        WHERE m.movies IS NOT NULL AND m.movies <> ''
        LIMIT 15;
        """
    ),
    (
        "Топ-5 игр по положительным отзывам + их среднее время игры",
        """
        SELECT s.name, s.positive_ratings, s.average_playtime
        FROM steam s
        ORDER BY s.positive_ratings DESC
        LIMIT 5;
        """
    ),
    (
        "Средняя цена игр по издателям (только если у издателя больше 5 игр)",
        """
        SELECT s.publisher, AVG(s.price) AS avg_price, COUNT(*) AS total_games
        FROM steam s
        GROUP BY s.publisher
        HAVING COUNT(*) > 5
        ORDER BY avg_price DESC;
        """
    ),
    (
        "Количество игр по жанрам и средняя оценка (positive - negative)",
        """
        SELECT s.genres, COUNT(*) AS game_count, 
               AVG(s.positive_ratings - s.negative_ratings) AS avg_score
        FROM steam s
        GROUP BY s.genres
        ORDER BY avg_score DESC
        LIMIT 10;
        """
    ),
    (
        "Названия игр и их системные требования для ПК",
        """
        SELECT s.name, r.pc_requirements
        FROM steam s
        JOIN steam_requirements_data r ON s.appid = r.steam_appid
        LIMIT 10;
        """
    ),
    (
        "Список игр с медианным временем игры и поддержкой (сайт поддержки)",
        """
        SELECT s.name, s.median_playtime, sup.website
        FROM steam s
        JOIN steam_support_info sup ON s.appid = sup.steam_appid
        WHERE s.median_playtime > 100
        ORDER BY s.median_playtime DESC
        LIMIT 10;
        """
    ),
    (
        "Количество отзывов по каждой игре + процент положительных рекомендаций",
        """
        SELECT s.name, COUNT(r.review_id) AS total_reviews,
        SUM(CASE WHEN r.is_recommended = 'true' THEN 1 ELSE 0 END) * 100.0 / COUNT(r.review_id) AS positive_percent
        FROM steam s
        JOIN recommendations r ON s.appid = r.app_id
        GROUP BY s.name
        ORDER BY positive_percent DESC;
        """
    ),
    (
        "Самые дорогие sci fi игры",
        """
        SELECT s.name, s.price, t.sci_fi
        FROM steam s
        JOIN steamspy_tag_data t ON s.appid = t.appid
        WHERE t.sci_fi > 0
        ORDER BY s.price DESC
        LIMIT 10;
        """
    ),
    (
        "Топ-5 разработчиков по количеству игр и среднему времени игры",
        """
        SELECT s.developer, COUNT(*) AS game_count, AVG(s.average_playtime) AS avg_playtime
        FROM steam s
        GROUP BY s.developer
        ORDER BY game_count DESC
        LIMIT 5;
        """
    ),
]

try:
    with connect(
        host="localhost",
        user=input("Имя пользователя: "),
        password=input("Пароль: "),
        database="games",
    ) as connection:
        with connection.cursor() as cursor:
            for i, (title, query) in enumerate(queries, start=1):
                print(f"\n=== Запрос {i}: {title} ===\n")
                cursor.execute(query)
                headers = [col[0] for col in cursor.description]
                result = cursor.fetchall()
                result = [[shorten(cell) for cell in row] for row in result]
                if result:
                    print(tabulate(result, headers=headers, tablefmt="fancy_grid"))
                else:
                    print("Нет данных.")
                    
except Error as e:
    print("Ошибка:", e)