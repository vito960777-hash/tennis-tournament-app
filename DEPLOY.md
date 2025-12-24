# Інструкція з деплою на Render

## Підготовка

1. Створіть акаунт на [Render.com](https://render.com) (безкоштовно)
2. Підключіть свій GitHub акаунт до Render

## Деплой

### Варіант 1: З GitHub (рекомендовано)

1. Створіть новий репозиторій на GitHub
2. Додайте файли проекту до репозиторію:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/tennis-tournament.git
git push -u origin main
```

3. Перейдіть на [Render Dashboard](https://dashboard.render.com/)
4. Натисніть "New +" → "Web Service"
5. Підключіть ваш GitHub репозиторій
6. Render автоматично виявить `render.yaml` і налаштує все

### Варіант 2: Вручну

1. Перейдіть на [Render Dashboard](https://dashboard.render.com/)
2. Натисніть "New +" → "Web Service"
3. Виберіть "Public Git repository"
4. Вставте URL вашого репозиторію
5. Налаштування:
   - **Name**: tennis-tournament (або на ваш вибір)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Environment Variables:
   - `ADMIN_PASSWORD`: ваш пароль адміністратора (замість `tennis2024`)
   - `SECRET_KEY`: будь-який випадковий рядок для безпеки
7. Натисніть "Create Web Service"

## Після деплою

Ваш додаток буде доступний за адресою типу:
```
https://tennis-tournament-XXXX.onrender.com
```

### Використання

1. **Для глядачів**: просто відкрийте лінк - вони зможуть переглядати турнір в реальному часі
2. **Для адміна**:
   - Натисніть "Адмін вхід"
   - Введіть пароль (за замовчуванням `tennis2024`, але краще змініть в environment variables)
   - Тепер ви можете створювати турніри та вводити результати

### Важливо!

- Безкоштовний план Render засинає після 15 хвилин неактивності
- При першому запиті після сну буде затримка ~30 секунд
- Турнір зберігається в пам'яті, тому після перезапуску сервера дані будуть втрачені
- Для постійного зберігання потрібно додати базу даних (можна зробити пізніше)

## Зміна пароля адміна

В Render Dashboard:
1. Перейдіть у ваш Web Service
2. Вкладка "Environment"
3. Знайдіть `ADMIN_PASSWORD`
4. Змініть значення
5. Збережіть (сервіс автоматично перезапуститься)

## Оновлення додатка

Просто зробіть push в GitHub:
```bash
git add .
git commit -m "Update"
git push
```

Render автоматично задеплоїть нову версію!
