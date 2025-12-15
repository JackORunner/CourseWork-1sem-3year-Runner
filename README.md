# CourseWork-1sem-3year-Runner
Course Work Bihun FeI-34

Інструкція по запуску проекту та опис файлів
Структура проекту:
•	Program/main.py — Точка входу в додаток. Ініціалізує Flet, налаштовує маршрутизацію та тему.
•	Program/database.py — Клас Database. Відповідає за всі операції з SQLite.
•	Program/ai_engine.py — Клас AIEngine. Відповідає за комунікацію з Google Gemini API.
•	Program/views/ — Папка з файлами інтерфейсу (library_view.py, study_view.py, settings_view.py).
•	Program/build/ — Папка що створюється внаслідок компіляції .apk файлу
Інструкція із запуску:
1.	Клонуйте репозиторій
2.	Встановіть Python версії 3.10 або вище.
3.	Встановіть необхідні бібліотеки командою: pip install flet requests google-generativeai. Та згалані бібліотеки в файлах з вимогами
4.	Встановіть Flutter SDK та Android SDK
5.	Переконайтеся в встановленні через команду flutter doctor
6.	Запустіть додаток: python Program/main.py.
7.	При першому запуску перейдіть у вкладку "Settings" та введіть ваш API ключ Google Gemini.
Примітка щодо збірки APK: Для збірки під Android використовуйте команду: flet build apk --include-packages requests,google-generativeai Логіка нормалізації шляхів у main.py автоматично відпрацює при запуску на пристрої. Також для налагодження використовуйте adb.
