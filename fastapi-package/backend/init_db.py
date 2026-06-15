import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    conn = psycopg2.connect("postgresql://postgres:1234@127.0.0.1:5432/postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'cinema_books_db'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE cinema_books_db")
        print("Database 'cinema_books_db' created successfully.")
    else:
        print("Database 'cinema_books_db' already exists.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_database()

    # Импорт Base и моделей из main
    from main import Base, engine, Movie, User, SessionLocal
    import bcrypt

    # Создание таблиц
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")

    db = SessionLocal()
    try:
        # Проверяем, есть ли уже фильмы в БД
        if db.query(Movie).count() == 0:
            movies_data = [
                # Қазақ тіліндегі фильмдер
                ("Дюна: Екінші бөлім", 1, 3000, 12, "Пол Атрейдес өз отбасын құртқан қастандық жасаушылардан кек алу үшін фремендермен бірігеді.", "images/posters/movie1.jpg"),
                ("Жылдам және қауіпті 10", 1, 2500, 16, "Аты аңызға айналған жарыс сагасының жалғасы. Доминик Торетто өз отбасын жаңа жаудан қорғауы керек.", "images/posters/movie2.jpg"),
                ("Джон Уик 4", 1, 2800, 18, "Джон Уик Кландар басқармасын жеңудің жолын табады, бірақ ол үшін жаңа жаумен күресуі керек.", "images/posters/movie3.jpg"),
                ("Кек алушылар: Финал", 1, 2200, 16, "Аман қалған Кек алушылар тобының мүшелері Таносқа қарсы тұру үшін жаңа жоспар құрады.", "images/posters/movie4.jpg"),
                ("Барби", 2, 2500, 12, "Барби сұлулық стандарттарына сәйкес келмегендіктен, оны Барбилендтен қуып жібереді. Енді ол шынайы әлемге саяхатқа аттанады.", "images/posters/movie5.jpg"),
                ("Келін Сабина", 2, 1500, 12, "Қалалық қыз Сабина кездейсоқ ауылға тап болып, нағыз келін болуды үйренуге мәжбүр болады.", "images/posters/movie6.jpg"),
                ("Үйде жалғыз қалғанда", 2, 1200, 6, "Сегіз жасар Кевин Рождество мерекесінде үйде жалғыз қалып, өз үйін ұрылардан қорғайды.", "images/posters/movie7.jpg"),
                ("Оппенгеймер", 3, 3500, 16, "Атом бомбасын жасаушы, көрнекті американдық физик Роберт Оппенгеймердің өмірбаяны мен тарихи шешімдері.", "images/posters/movie8.jpg"),
                ("Интерстеллар", 3, 2000, 12, "Зерттеушілер тобы адамзатқа жаңа ғаламшар табу үшін ғарыштағы құрт тесігі арқылы қауіпті саяхатқа аттанады.", "images/posters/movie9.jpg"),
                ("Джокер", 3, 2500, 18, "Готэм, 1980 жылдардың басы. Сәтсіз комедиант Артур Флек біртіндеп есінен адасып, қылмыс әлеміне енеді.", "images/posters/movie10.jpg"),
                
                # Русский язык
                ("Дюна: Часть вторая", 1, 3000, 12, "Пол Атрейдес объединяется с фременами, чтобы отомстить заговорщикам, уничтожившим его семью.", "images/posters/movie1.jpg"),
                ("Форсаж 10", 1, 2500, 16, "Продолжение культовой гоночной саги. Доминику Торетто предстоит защитить свою семью от нового врага.", "images/posters/movie2.jpg"),
                ("Джон Уик 4", 1, 2800, 18, "Джон Уик находит способ одержать победу над Правлением Кланов, но для этого ему предстоит сразиться с новым врагом.", "images/posters/movie3.jpg"),
                ("Мстители: Финал", 1, 2200, 16, "Оставшиеся в живых члены команды Мстителей и их союзники разрабатывают новый план, чтобы противостоять Таносу.", "images/posters/movie4.jpg"),
                ("Барби", 2, 2500, 12, "Барби выгоняют из Барбиленда, потому что она не соответствует его нормам красоты. Она отправляется в реальный мир.", "images/posters/movie5.jpg"),
                ("Келинка Сабина", 2, 1500, 12, "Городская девушка Сабина случайно попадает в аул, где ей приходится учиться быть настоящей келин.", "images/posters/movie6.jpg"),
                ("Один дома", 2, 1200, 6, "Восьмилетний Кевин остается один дома на Рождество и защищает свой дом от грабителей.", "images/posters/movie7.jpg"),
                ("Оппенгеймер", 3, 3500, 16, "История жизни американского физика Роберта Оппенгеймера, создателя первой атомной бомбы.", "images/posters/movie8.jpg"),
                ("Интерстеллар", 3, 2000, 12, "Группа исследователей отправляется сквозь кротовую нору, чтобы найти новую планету для спасения человечества.", "images/posters/movie9.jpg"),
                ("Джокер", 3, 2500, 18, "Готэм, начало 1980-х годов. Комик-неудачник Артур Флек постепенно погружается в безумие и становится преступником.", "images/posters/movie10.jpg")
            ]
            for title, genre, price, age, desc, img in movies_data:
                db.add(Movie(title=title, genre=genre, ticket_price=price, age_rating=age, description=desc, poster_path=img))
            print("Movies seeded.")

        # Добавляем тестового пользователя
        if db.query(User).filter(User.username == "user1").count() == 0:
            h_pwd = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
            db.add(User(username="user1", password_hash=h_pwd, full_name="Иван Петров"))
            print("Test user 'user1' seeded.")

        db.commit()
        print("Database fully initialized and seeded.")
    finally:
        db.close()
