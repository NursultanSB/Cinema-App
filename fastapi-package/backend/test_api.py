import requests
import datetime
import io

API_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== ЗАПУСК ТЕСТОВ REST API ===\n")
    
    # 1. Тест соединения
    print("Тест 1: Проверка доступности API...")
    r = requests.get(f"{API_URL}/test")
    assert r.status_code == 200, "API недоступно"
    assert r.json()["database"] == "Connected successfully", "Ошибка БД"
    print("=> OK (API доступно, БД подключена)\n")

    # Уникальный логин для тестов
    test_username = f"testuser_{int(datetime.datetime.now().timestamp())}"
    test_password = "testpassword123"
    test_fullname = "Тестовый Пользователь"
    
    # 2. Регистрация
    print("Тест 2: Регистрация нового пользователя...")
    payload = {
        "username": test_username,
        "password": test_password,
        "full_name": test_fullname
    }
    r = requests.post(f"{API_URL}/api/register", json=payload)
    assert r.status_code == 201, f"Ошибка регистрации: {r.text}"
    print("=> OK (Пользователь зарегистрирован)\n")

    # 3. Регистрация с дубликатом имени
    print("Тест 3: Регистрация с существующим логином...")
    r = requests.post(f"{API_URL}/api/register", json=payload)
    assert r.status_code == 400, "Должна быть ошибка 400 для дубликата"
    print("=> OK (Ошибка 400 получена)\n")

    # 4. Авторизация (Вход)
    print("Тест 4: Вход пользователя...")
    payload_login = {
        "username": test_username,
        "password": test_password
    }
    r = requests.post(f"{API_URL}/api/login", json=payload_login)
    assert r.status_code == 200, f"Ошибка входа: {r.text}"
    token = r.json().get("token")
    assert token is not None, "Токен не получен"
    print("=> OK (Вход успешен, токен получен)\n")

    headers = {"Authorization": f"Bearer {token}"}

    # 5. Просмотр фильмов
    print("Тест 5: Получение списка фильмов...")
    r = requests.get(f"{API_URL}/api/movies")
    assert r.status_code == 200, "Ошибка получения фильмов"
    movies = r.json()
    assert len(movies) > 0, "Список фильмов пуст"
    print(f"=> OK (Получено фильмов: {len(movies)})\n")
    
    # Запомним ID первого фильма для покупки
    target_movie = movies[0]
    movie_id = target_movie["id"]
    movie_price = target_movie["ticket_price"]
    print(f"Выбран фильм: ID {movie_id} с ценой {movie_price}")

    # 6. Фильтрация фильмов
    print("Тест 6: Фильтрация и сортировка фильмов...")
    # Фильтр по жанру 1 (Боевик) и сортировка по возрастанию цены
    r = requests.get(f"{API_URL}/api/movies?genre=1&sort=price_asc")
    assert r.status_code == 200
    filtered_movies = r.json()
    for m in filtered_movies:
        assert m["genre"] == 1, "Жанр должен быть равен 1"
    # Проверим сортировку по цене
    if len(filtered_movies) > 1:
        assert filtered_movies[0]["ticket_price"] <= filtered_movies[1]["ticket_price"], "Сортировка по цене неверная"
    print("=> OK (Фильтрация и сортировка работают)\n")

    # 7. Покупка билета с неверной датой (в прошлом)
    print("Тест 7: Валидация покупки (дата в прошлом)...")
    past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    ticket_payload = {
        "movie_id": movie_id,
        "show_date": past_date,
        "quantity": 1
    }
    r = requests.post(f"{API_URL}/api/tickets", json=ticket_payload, headers=headers)
    assert r.status_code == 400, "Должна быть ошибка 400 для прошедшей даты"
    print("=> OK (Валидация прошедшей даты работает)\n")

    # 8. Покупка билета с неверным количеством (0)
    print("Тест 8: Валидация покупки (количество < 1)...")
    ticket_payload["show_date"] = datetime.date.today().isoformat()
    ticket_payload["quantity"] = 0
    r = requests.post(f"{API_URL}/api/tickets", json=ticket_payload, headers=headers)
    assert r.status_code == 422 or r.status_code == 400, "Должна быть ошибка валидации для количества 0"
    print("=> OK (Валидация количества билетов работает)\n")

    # 9. Успешная покупка билета
    print("Тест 9: Успешная покупка 3 билетов...")
    ticket_payload["quantity"] = 3
    r = requests.post(f"{API_URL}/api/tickets", json=ticket_payload, headers=headers)
    assert r.status_code == 201, f"Ошибка покупки: {r.text}"
    ticket_id = r.json()["ticket_id"]
    expected_total = movie_price * 3
    assert r.json()["total_price"] == expected_total, f"Итоговая цена не совпадает. Ожидалось: {expected_total}, Получено: {r.json()['total_price']}"
    print(f"=> OK (Билет {ticket_id} куплен, общая стоимость {expected_total} tenge)\n")

    # 10. Просмотр профиля и списка билетов
    print("Тест 10: Получение профиля пользователя...")
    r = requests.get(f"{API_URL}/api/profile", headers=headers)
    assert r.status_code == 200, "Ошибка получения профиля"
    profile = r.json()
    assert profile["username"] == test_username, "Имя пользователя не совпадает"
    assert len(profile["tickets"]) > 0, "Билеты не найдены в профиле"
    my_ticket = profile["tickets"][0]
    assert my_ticket["id"] == ticket_id, "ID билета не совпадает"
    assert my_ticket["status"] == "active", "Статус билета должен быть active"
    print("=> OK (Профиль и билеты отображаются корректно)\n")

    # 11. Загрузка аватара
    print("Тест 11: Загрузка аватарки профиля...")
    avatar_data = b"fake-jpeg-image-content"
    files = {"file": ("avatar.jpg", io.BytesIO(avatar_data), "image/jpeg")}
    r = requests.post(f"{API_URL}/api/profile/avatar", files=files, headers=headers)
    assert r.status_code == 200, f"Ошибка загрузки аватара: {r.text}"
    avatar_path = r.json()["avatar_path"]
    assert avatar_path.startswith("/static/avatars/"), "Путь аватара неверный"
    
    # Проверим, что файл скачивается
    r_check = requests.get(f"{API_URL}{avatar_path}")
    assert r_check.status_code == 200, "Аватар не доступен для скачивания"
    print(f"=> OK (Аватар успешно загружен и доступен: {avatar_path})\n")

    # 12. Возврат билета
    print("Тест 12: Оформление возврата билета...")
    r = requests.post(f"{API_URL}/api/tickets/{ticket_id}/refund", headers=headers)
    assert r.status_code == 200, f"Ошибка возврата: {r.text}"
    assert r.json()["status"] == "refunded", "Статус должен измениться на refunded"
    
    # Проверка статуса в профиле
    r = requests.get(f"{API_URL}/api/profile", headers=headers)
    assert r.json()["tickets"][0]["status"] == "refunded", "Статус билета в профиле должен быть refunded"
    print("=> OK (Билет возвращен, статус изменен на refunded)\n")

    print("=== ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ===")

if __name__ == "__main__":
    run_tests()
