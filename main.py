import sys
from PyQt6.QtWidgets import (
    QMainWindow, QLabel, QLineEdit, QListWidget, QFileDialog
)
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QInputDialog, QMessageBox
import os
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QApplication,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer


class Database:
    """Класс для управления базой данных вопросов и паролями."""

    def __init__(self, db_name="quiz.db"):
        # Создание папки 'db', если она не существует
        self.db_folder = "db"
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        self.db_path = os.path.join(self.db_folder, db_name)
        self.connection = None
        self.cursor = None
        self.connect(self.db_path)

    def connect(self, db_name):
        """Соединение с базой данных для вопросов."""
        try:
            self.connection = sqlite3.connect(db_name)
            self.cursor = self.connection.cursor()
            self.create_tables()
            self.create_password_table()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            sys.exit(1)

    def create_tables(self):
        """Создание таблицы для вопросов, если она не существует."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    correct_answer TEXT NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать таблицы: {str(e)}")
            sys.exit(1)

    def create_password_table(self):
        """Создание таблицы для паролей, если она не существует."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY,
                    password TEXT NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать таблицу паролей: {str(e)}")
            sys.exit(1)

    def set_password(self, password):
        """Устанавливает пароль в базу данных."""
        try:
            self.cursor.execute("DELETE FROM passwords")  # Удаляем существующие записи
            self.cursor.execute("INSERT INTO passwords (password) VALUES (?)", (password,))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось установить пароль: {str(e)}")

    def get_password(self):
        """Получение пароля из базы данных."""
        try:
            self.cursor.execute("SELECT password FROM passwords")
            result = self.cursor.fetchone()
            if result is None:
                return None
            return result[0]  # Вернуть пароль, если он существует
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось получить пароль: {str(e)}")
            return None

    def get_questions(self):
        """Получение всех вопросов из базы данных."""
        try:
            self.cursor.execute("SELECT * FROM questions")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось получить вопросы: {str(e)}")
            return []

    def insert_question(self, question, correct_answer):
        """Добавление вопроса в базу данных."""
        try:
            self.cursor.execute("INSERT INTO questions (question, correct_answer) VALUES (?, ?)",
                                (question, correct_answer))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось добавить вопрос: {str(e)}")

    def delete_question(self, question_id):
        """Удаление вопроса по идентификатору."""
        try:
            self.cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось удалить вопрос: {str(e)}")

    # Доб авьте методы сохранения и загрузки вопросов из файла здесь
    def load_questions_from_txt(self, filename):
        """Загрузка вопросов из текстового файла."""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                questions = file.readlines()
                for line in questions:
                    question, correct_answer = line.strip().split(';')  # Предполагается, что данные разделены ;
                    self.insert_question(question, correct_answer)
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось загрузить вопросы: {str(e)}")

    def save_questions_to_txt(self, filename):
        """Сохранение вопросов в текстовый файл."""
        try:
            questions = self.get_questions()
            with open(filename, 'w', encoding='utf-8') as file:
                for question in questions:
                    file.write(
                        f"{question[1]};{question[2]}\n")  # Предполагается, что в строку нужно записывать вопрос и ответ
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось сохранить вопросы: {str(e)}")

    def clear_questions(self):
        """Очистка таблицы вопросов."""
        try:
            self.cursor.execute("DELETE FROM questions")
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось очистить вопросы: {str(e)}")

    def update_password(self, current_password, new_password):
        """Изменение пароля в базе данных."""
        stored_password = self.get_password()
        if stored_password is None:
            QMessageBox.warning(None, "Ошибка", "Пароль не установлен.")
            return

        if current_password != stored_password:
            QMessageBox.warning(None, "Ошибка", "Неверный текущий пароль.")
            return

        # Установка нового пароля
        self.set_password(new_password)
        QMessageBox.information(None, "Успех", "Пароль успешно изменён.")


class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Программа для проверки знаний")
        self.setGeometry(0, 0, 1920, 1080)

        self.database = Database()
        self.results_database = ResultsDatabase()
        self.test_duration = 60

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(400, 50, 500, 50)

        student_button = QPushButton("Ученик")
        teacher_button = QPushButton("Учитель")

        font_size = "font-size: 24px; padding: 20px;"
        student_button.setStyleSheet(font_size)
        teacher_button.setStyleSheet(font_size)

        student_button.clicked.connect(self.name_lastname)
        teacher_button.clicked.connect(self.ask_password)

        layout.addWidget(student_button)
        layout.addWidget(teacher_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def keyPressEvent(self, event):
        """Закрытие приложения при нажатии Esc"""
        if event.key() == Qt.Key.Key_Escape:
            quit()  # Закрываем приложение

    def name_lastname(self):
        """Запрос имени и фамилии ученика"""
        name, ok = QInputDialog.getText(self, "Имя", "Введите свое имя:")
        if ok and name.split():
            self.show_student_window(name)
        else:
            QMessageBox.warning(self, "Ошибка", "Вы не ввели имя.")

    def show_student_window(self, student_name):
        """Показать окно ученика."""
        self.student_window = StudentWindow(self.database, self.results_database, self, self.test_duration,
                                            student_name)
        self.student_window.show()
        self.close()

    def show_set_password_window(self):
        """Открытие окна для установки пароля"""
        new_password, ok = QInputDialog.getText(self, "Установка пароля", "Введите новый пароль:")
        if ok and new_password:
            self.database.set_password(new_password)  # Устанавливаем новый пароль
            QMessageBox.information(self, "Успех", "Пароль успешно установлен.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пароль не установлен.")

    def ask_password(self):
        """Запрос пароля для доступа к окну учителя"""
        stored_password = self.database.get_password()

        if stored_password is None:
            # Если пароль не установлен, перенаправить на окно для установки пароля
            self.show_set_password_window()
        else:
            # Если пароль установлен, запрашиваем его у пользователя
            password, ok = QInputDialog.getText(self, "Пароль", "Введите пароль:")
            if ok and password == stored_password:
                self.show_admin_window()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный пароль.")

    def show_admin_window(self):
        """Показать окно для учителя."""
        self.teacher_window = Admin(self.database, self)
        self.teacher_window.show()
        self.close()


class StudentWindow(QWidget):
    def __init__(self, database, results_database, parent, duration, student_name):
        super().__init__()
        self.database = database
        self.results_database = results_database
        self.parent = parent
        self.student_name = student_name
        self.quiz_ended = False
        self.duration = duration

        self.setWindowTitle("Ученик")
        self.setGeometry(0, 0, 1920, 1080)
        self.showFullScreen()

        # Создаем виджеты
        self.question_text_edit = QTextEdit(self)
        self.question_text_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.question_text_edit.setStyleSheet("font-size: 40px; font-weight: bold;")
        self.question_text_edit.setReadOnly(True)

        self.answer_input = QLineEdit(self)
        self.answer_input.setPlaceholderText("Введите ваш ответ...")

        self.submit_button = QPushButton("Ответить", self)
        self.submit_button.setFixedWidth(650)
        self.back_button = QPushButton("Назад", self)
        self.back_button.setFixedWidth(150)

        self.correct_answer_counter = QLabel("Правильные ответы: 0", self)
        self.correct_answer_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.correct_answer_counter.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.timer_label = QLabel(f"Оставшееся время: {self.format_time(self.duration)}", self)
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.score = 0
        self.questions = self.database.get_questions()
        self.current_question_index = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        if self.questions:
            self.load_question()
        else:
            QMessageBox.warning(self, "Ошибка", "Нет доступных вопросов для теста!")

        self.initUI()

    def keyPressEvent(self, event):
        """Закрытие приложения при нажатии Esc"""
        if event.key() == Qt.Key.Key_Escape:
            quit()

    def format_time(self, seconds):
        """Форматирование времени"""
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02}:{seconds:02}"

    def update_timer(self):
        if self.duration > 0:
            self.duration -= 1
            self.timer_label.setText(f"Оставшееся время: {self.format_time(self.duration)}")
        else:
            self.duration = 0  # Обнуляем таймер
            self.timer.stop()  # Останавливаем таймер
            self.end_quiz()  # Завершение викторины

    def initUI(self):
        layout = QVBoxLayout()

        font_size = "font-size: 14px; padding: 10px;"
        self.submit_button.setStyleSheet(font_size)

        layout.addWidget(self.question_text_edit)
        layout.addWidget(self.correct_answer_counter)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.back_button)

        self.submit_button.clicked.connect(self.check_answer)
        self.back_button.clicked.connect(self.go_back)

        self.setLayout(layout)

    def load_question(self):
        """Загрузка следующего вопроса"""
        if self.current_question_index < len(self.questions):
            question_number = self.current_question_index + 1
            question_text = self.questions[self.current_question_index][1]
            self.question_text_edit.setPlainText(f"Вопрос {question_number}: {question_text}")
            self.answer_input.clear()
        else:
            self.end_quiz()

    def check_answer(self):
        """Проверка ответа пользователя"""
        answer = self.answer_input.text()
        correct_answer = self.questions[self.current_question_index][2] if self.current_question_index < len(
            self.questions) else None

        if answer == '':
            QMessageBox.information(self, "Ошибка!", 'Вы не ввели ответ ')
        elif correct_answer:
            if answer.strip().lower() == correct_answer.strip().lower():
                self.score += 1
                self.correct_answer_counter.setText(f"Правильные ответы: {self.score}")
            else:
                QMessageBox.warning(self, "Неправильно!", f"Правильный ответ: {correct_answer}")

        self.current_question_index += 1

        if self.current_question_index < len(self.questions):
            self.load_question()
        else:
            self.duration = 0  # Обнуляем таймер до завершения викторины
            self.end_quiz()

    def end_quiz(self):
        """Завершение викторины"""
        if self.quiz_ended:
            return

        self.quiz_ended = True
        grade = self.calculate_grade(self.score)
        self.results_database.insert_result(self.student_name, self.score)
        QMessageBox.information(self, "Викторина завершена!",
                                f"Ваш результат: {self.score} из {len(self.questions)}.\nВаша оценка: {grade}.")
        self.close()
        self.parent.show()

    def calculate_grade(self, score):
        """Подсчёт оценки"""
        total_questions = len(self.questions)
        if total_questions == 0:
            return "Нет вопросов"

        if score >= total_questions * 0.75:
            return "Отлично\n оценка 5"
        elif score >= total_questions * 0.5:
            return "Хорошо\n оценка 4"
        elif score >= total_questions * 0.25:
            return "Удовлетворительно\n оценка 3"
        else:
            return "Неудовлетворительно\n оценка 2"

    def go_back(self):
        """Возврат к главному окну"""
        self.duration = 0  # Обнуляем таймер перед возвратом
        self.parent.show()
        self.close()


class Admin(QWidget):
    """Окно для учителя с административными правами."""

    def __init__(self, database, parent):
        super().__init__()
        self.database = database
        self.parent = parent

        self.setWindowTitle("Админ")
        self.setGeometry(100, 100, 400, 300)
        self.showFullScreen()

        # Кнопки интерфейса
        self.submit_button = QPushButton("Проверить результаты учеников", self)
        self.delete_button = QPushButton("Изменение вопросов", self)
        self.set_time_button = QPushButton("Установить время теста", self)
        self.change_password_button = QPushButton("Изменить пароль", self)  # Кнопка изменения пароля
        self.back_button = QPushButton("Назад", self)

        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна учителя"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(400, 10, 500, 50)

        # Добавление кнопок в макет
        layout.addWidget(self.submit_button)
        layout.addWidget(self.set_time_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.change_password_button)  # Добавление кнопки изменения пароля
        layout.addWidget(self.back_button)

        font_size = "font-size: 24px; padding: 20px;"
        self.submit_button.setStyleSheet(font_size)
        self.set_time_button.setStyleSheet(font_size)
        self.delete_button.setStyleSheet(font_size)
        self.change_password_button.setStyleSheet(font_size)  # Стилизация кнопки изменения пароля
        self.back_button.setStyleSheet(font_size)

        self.setLayout(layout)

        # Подключение кнопок к их функциям
        self.back_button.clicked.connect(self.go_back)
        self.delete_button.clicked.connect(self.show_correct_window)
        self.set_time_button.clicked.connect(self.ask_time)
        self.submit_button.clicked.connect(self.show_results_window)
        self.change_password_button.clicked.connect(self.change_password)  # Подключение кнопки

    def keyPressEvent(self, event):
        """Закрытие приложения при нажатии Esc"""
        if event.key() == Qt.Key.Key_Escape:
            quit()

    def show_results_window(self):
        """Показать окно с результатами учеников."""
        self.results_window = ResultsWindow(self.database, self.parent.results_database, self)
        self.results_window.show()
        self.close()

    def change_password(self):
        """Функция для изменения пароля."""
        current_password, ok1 = QInputDialog.getText(self, "Изменение пароля", "Введите текущий пароль:")
        if not ok1 or current_password == "":
            QMessageBox.warning(self, "Ошибка", "Вы должны ввести текущий пароль.")
            return

        new_password, ok2 = QInputDialog.getText(self, "Изменение пароля", "Введите новый пароль:")
        if ok2 and new_password != "":
            print(f"Текущий пароль: {current_password}, Новый пароль: {new_password}")
            self.database.update_password(current_password, new_password)
        else:
            QMessageBox.warning(self, "Ошибка", "Вы должны ввести новый пароль.")

    def go_back(self):
        """Возврат к главному окну."""
        self.parent.show()
        self.close()

    def show_correct_window(self):
        """Показать окно учителя."""
        self.correct_window = TeacherWindow(self.database, self)
        self.correct_window.show()
        self.close()

    def ask_time(self):
        """Запрос времени для теста у учителя."""
        time, ok = QInputDialog.getInt(self, "Установить время теста", "Введите время в минутах:", value=1, min=1)
        if ok:
            duration = time * 60
            self.parent.test_duration = duration
            QMessageBox.information(self, "Успех", f"Время теста установлено на {time} минут(ы).")


class ResultsDatabase:
    """Класс для управления базой данных результатов."""

    def __init__(self, db_name="results.db"):
        self.db_folder = "db"
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        self.db_path = os.path.join(self.db_folder, db_name)
        self.connection = None
        self.cursor = None
        self.connect(self.db_path)

    def connect(self, db_name):
        """Соединение с базой данных для результатов."""
        try:
            self.connection = sqlite3.connect(db_name)
            self.cursor = self.connection.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных результатов: {str(e)}")
            sys.exit(1)

    def create_tables(self):
        """Создание таблицы для результатов, если она не существует."""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    score INTEGER NOT NULL
                )
            """)
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать таблицу результатов: {str(e)}")
            sys.exit(1)

    def insert_result(self, name, score):
        """Сохранение результата ученика в базе данных."""
        try:
            self.cursor.execute("INSERT INTO results (name, score) VALUES (?, ?)", (name, score))
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось сохранить результат: {str(e)}")

    def get_results(self):
        """Получение всех результатов из базы данных."""
        try:
            self.cursor.execute("SELECT name, score FROM results")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось получить результаты: {str(e)}")
            return []

    def clear_results(self):
        """Очистка базы данных результатов."""
        try:
            self.cursor.execute("DELETE FROM results")
            self.connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось очистить результаты: {str(e)}")

    def close(self):
        """Закрытие соединения с базой данных результатов."""
        if self.cursor is not None:
            self.cursor.close()
        if self.connection is not None:
            self.connection.close()


class ResultsWindow(QWidget):
    def __init__(self, database, results_database, parent):
        super().__init__()
        self.database = database
        self.results_database = results_database
        self.parent = parent
        self.setWindowTitle("Результаты учеников")
        self.setGeometry(100, 100, 400, 300)
        self.results_list = QListWidget(self)
        self.showFullScreen()

        self.back_button = QPushButton("Назад", self)
        self.clear_button = QPushButton("Очистка", self)
        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна с результатами"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Результаты учеников:"))
        layout.addWidget(self.results_list)
        layout.addWidget(self.back_button)
        layout.addWidget(self.clear_button)
        font_size = "font-size: 24px; padding: 20px;"
        self.back_button.setStyleSheet(font_size)
        self.clear_button.setStyleSheet(font_size)
        self.setLayout(layout)
        self.load_results()
        self.back_button.clicked.connect(self.go_back)
        self.clear_button.clicked.connect(self.clear)

    def load_results(self):
        """Загрузка результатов учеников из базы данных"""
        self.results_list.clear()
        try:
            results = self.results_database.get_results()
            if not results:
                QMessageBox.information(self, "Информация", "Нет доступных результатов.")
            for name, score in results:
                self.results_list.addItem(f"{name}: {score} баллов")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить результаты: {str(e)}")

    def clear(self):
        """Очистка базы данных результатов"""
        try:
            self.results_database.clear_results()
            self.load_results()
            QMessageBox.information(self, "Очистка", "Результаты очищены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось очистить результаты: {str(e)}")

    def go_back(self):
        """Возврат к главному окну."""
        self.parent.show()
        self.close()

    def keyPressEvent(self, event):
        """Закрытие приложения при нажатии Esc"""
        if event.key() == Qt.Key.Key_Escape:
            quit()  # Закрываем приложение


class TeacherWindow(QWidget):
    """Окно для управления вопросами."""

    def __init__(self, database, parent):
        super().__init__()
        self.database = database
        self.parent = parent

        self.setWindowTitle("Учитель")
        self.setGeometry(100, 100, 400, 300)
        self.showFullScreen()

        self.question_input = QLineEdit(self)
        self.answer_input = QLineEdit(self)
        self.submit_button = QPushButton("Добавить вопрос", self)
        self.delete_button = QPushButton("Удалить вопрос", self)
        self.delete_all_button = QPushButton("Удалить все вопросы", self)
        self.load_button = QPushButton("Загрузить вопросы из файла", self)  # Кнопка для загрузки
        self.save_button = QPushButton("Сохранить вопросы в файл", self)  # Кнопка для сохранения
        self.back_button = QPushButton("Назад", self)
        self.question_list = QListWidget(self)

        self.initUI()

        # Загрузка вопросов из базы данных
        self.load_questions()

    def initUI(self):
        """Инициализация пользовательского интерфейса окна учителя"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите вопрос:"))
        layout.addWidget(self.question_input)
        layout.addWidget(QLabel("Введите правильный ответ:"))
        layout.addWidget(self.answer_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(QLabel("Список вопросов:"))
        layout.addWidget(self.question_list)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.delete_all_button)
        layout.addWidget(self.load_button)  # Добавлено
        layout.addWidget(self.save_button)  # Добавлено
        layout.addWidget(self.back_button)

        font_size = "font-size: 24px; padding: 20px;"
        self.back_button.setStyleSheet(font_size)
        self.load_button.setStyleSheet(font_size)  # Стили для кнопки загрузки
        self.save_button.setStyleSheet(font_size)  # Стили для кнопки сохранения
        self.delete_all_button.setStyleSheet(font_size)
        self.delete_button.setStyleSheet(font_size)
        self.submit_button.setStyleSheet(font_size)

        self.submit_button.clicked.connect(self.add_question)
        self.delete_button.clicked.connect(self.delete_question)
        self.delete_all_button.clicked.connect(self.delete_all_questions)
        self.back_button.clicked.connect(self.go_back)
        self.load_button.clicked.connect(self.load_questions_from_file)  # Связываем
        self.save_button.clicked.connect(self.save_questions_to_file)  # Связываем

        self.setLayout(layout)

    def load_questions_from_file(self):
        """Загрузка вопросов из выбранного текстового файла."""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Text Files (*.txt)")
        if filename:
            self.database.load_questions_from_txt(filename)
            QMessageBox.information(self, "Успех", "Вопросы загружены из файла!")
            self.load_questions()  # Обновляем список вопросов после загрузки

    def save_questions_to_file(self):
        """Сохранение вопросов в выбранный текстовый файл."""
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Text Files (*.txt)")
        if filename:
            self.database.save_questions_to_txt(filename)
            QMessageBox.information(self, "Успех", "Вопросы сохранены в файл!")

    def delete_all_questions(self):
        """Удаление всех вопросов из базы данных."""
        self.database.clear_questions()
        self.load_questions()

    def load_questions(self):
        """Загрузка вопросов из базы данных в список."""
        self.question_list.clear()
        questions = self.database.get_questions()
        for q in questions:
            self.question_list.addItem(f"{q[1]} | {q[2]}")  # Показываем вопрос и ответ

    def add_question(self):
        """Добавление нового вопроса."""
        question = self.question_input.text()
        answer = self.answer_input.text()

        if question and answer:
            self.database.insert_question(question, answer)
            self.load_questions()
            self.question_input.clear()
            self.answer_input.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Вопрос и ответ должны быть заполнены!")

    def delete_question(self):
        """Удаление выбранного вопроса из базы данных."""
        selected_item = self.question_list.currentItem()
        if selected_item:
            question_text = selected_item.text().split(" | ")[0]  # Получаем текст вопроса
            question_id = self.database.get_questions()[self.question_list.currentRow()][0]
            self.database.delete_question(question_id)
            self.load_questions()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите вопрос для удаления.")

    def keyPressEvent(self, event):
        """Закрытие приложения при нажатии Esc"""
        if event.key() == Qt.Key.Key_Escape:
            quit()  # Закрываем приложение

    def go_back(self):
        """Возврат к главному окну."""
        self.parent.show()  # Показываем родительское окно (главное окно)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    database = Database()  # Создание базы данных
    parent = QuizApp()  # Создание главного окна
    parent.database = database  # Передача базы данных
    parent.show()  # Показать главное окно
    sys.exit(app.exec())
