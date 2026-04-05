# script_editor.py
import sys
import socket
import json
import threading
import time
import os

from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QTextCharFormat, QSyntaxHighlighter, QBrush, QFileSystemModel
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QTimer, Qt, QDir


# === ТЕМНАЯ ТЕМА ===
def apply_dark_theme(app):
    """Применение темной темы"""
    # Устанавливаем палитру для всего приложения
    dark_palette = QPalette()

    # Основные цвета
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

    # Стили для всех виджетов, включая messagebox
    app.setStyleSheet("""
        QWidget {
            background-color: #353535;
            color: white;
        }
        QPushButton {
            background-color: #454545;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
            color: white;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #252525;
        }
        QPushButton:disabled {
            background-color: #252525;
            color: #666;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #2d2d2d;
        }
        QTabBar::tab {
            background-color: #353535;
            border: 1px solid #555;
            padding: 8px;
            margin-right: 2px;
            color: white;
        }
        QTabBar::tab:selected {
            background-color: #4a4a4a;
        }
        QTabBar::tab:hover {
            background-color: #404040;
        }
        QTreeView {
            background-color: #2d2d2d;
            border: 1px solid #555;
            color: white;
        }
        QTreeView::item:selected {
            background-color: #4a4a4a;
        }
        QTreeView::item:hover {
            background-color: #404040;
        }
        QHeaderView::section {
            background-color: #353535;
            color: white;
            border: 1px solid #555;
        }
        QMenu {
            background-color: #353535;
            color: white;
            border: 1px solid #555;
        }
        QMenu::item:selected {
            background-color: #4a4a4a;
        }
        QMessageBox {
            background-color: #353535;
            color: white;
        }
        QMessageBox QLabel {
            color: white;
        }
        QMessageBox QPushButton {
            background-color: #454545;
            color: white;
            min-width: 80px;
        }
        QInputDialog {
            background-color: #353535;
            color: white;
        }
        QInputDialog QLabel {
            color: white;
        }
        QInputDialog QLineEdit {
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #555;
        }
        QFileDialog {
            background-color: #353535;
            color: white;
        }
    """)


# === ПОДСВЕТКА СИНТАКСИСА JAVASCRIPT ===
class JavaScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # Ключевые слова
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(255, 165, 0))  # оранжевый
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            'function', 'return', 'var', 'let', 'const', 'if', 'else',
            'for', 'while', 'do', 'break', 'continue', 'switch', 'case',
            'default', 'true', 'false', 'null', 'undefined', 'new', 'this'
        ]

        for word in keywords:
            pattern = f'\\b{word}\\b'
            self.add_rule(pattern, keyword_format)

        # Комментарии
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(100, 200, 100))  # зеленый
        self.add_rule('//[^\n]*', comment_format)

        # Строки
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(255, 165, 0))  # оранжевый
        self.add_rule('".*?"', string_format)
        self.add_rule("'.*?'", string_format)

        # Числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(0, 200, 255))  # голубой
        self.add_rule('\\b\\d+\\.?\\d*\\b', number_format)

        # Функции
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(255, 255, 0))  # желтый
        self.add_rule('\\b\\w+(?=\\()', function_format)

        # Специальные объекты
        special_format = QTextCharFormat()
        special_format.setForeground(QColor(255, 100, 200))  # розовый
        specials = ['state', 'game', 'Math', 'console', 'time']
        for word in specials:
            pattern = f'\\b{word}\\b'
            self.add_rule(pattern, special_format)

    def add_rule(self, pattern, format):
        import re
        self.rules.append((re.compile(pattern), format))

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)


# === ОСНОВНОЙ РЕДАКТОР ===
class ScriptEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Madmen Script Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Соединение
        self.socket = None
        self.connected = False
        self.script_running = False

        # UI
        self.setup_ui()

        # Таймер для проверки статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(500)

        # Загружаем файлы в дерево
        self.refresh_file_tree()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # === ЛЕВАЯ ПАНЕЛЬ - ДЕРЕВО ФАЙЛОВ ===
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(200)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Заголовок с кнопками
        header_layout = QHBoxLayout()
        files_label = QLabel("📁 Файлы")
        files_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(files_label)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMaximumWidth(30)
        refresh_btn.clicked.connect(self.refresh_file_tree)
        header_layout.addWidget(refresh_btn)

        header_layout.addStretch()
        left_layout.addLayout(header_layout)

        # Дерево файлов
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())

        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))
        self.file_tree.setColumnWidth(0, 180)
        self.file_tree.setColumnHidden(1, True)  # скрываем размер
        self.file_tree.setColumnHidden(2, True)  # скрываем тип
        self.file_tree.setColumnHidden(3, True)  # скрываем дату
        self.file_tree.doubleClicked.connect(self.on_file_double_click)
        left_layout.addWidget(self.file_tree)

        # Кнопки для файлов
        file_buttons_layout = QHBoxLayout()
        new_file_btn = QPushButton("➕ Новый")
        new_file_btn.clicked.connect(self.new_file)
        file_buttons_layout.addWidget(new_file_btn)

        new_folder_btn = QPushButton("📁 Папка")
        new_folder_btn.clicked.connect(self.new_folder)
        file_buttons_layout.addWidget(new_folder_btn)

        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.clicked.connect(self.delete_item)
        file_buttons_layout.addWidget(delete_btn)

        left_layout.addLayout(file_buttons_layout)

        # === ПРАВАЯ ПАНЕЛЬ - РЕДАКТОР ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель
        top_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Connect to Main App")
        self.connect_btn.clicked.connect(self.connect_to_main)
        self.connect_btn.setMinimumWidth(150)
        top_layout.addWidget(self.connect_btn)

        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; padding: 3px;")
        top_layout.addWidget(self.status_label)

        top_layout.addStretch()
        right_layout.addLayout(top_layout)

        # Вкладки редактора
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        right_layout.addWidget(self.tab_widget)

        # Создаем первую вкладку
        self.new_tab()

        self.output_panel = QTextEdit()
        self.output_panel.setMaximumHeight(150)
        self.output_panel.setReadOnly(True)
        self.output_panel.setFont(QFont("Courier New", 10))
        self.output_panel.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ff6b6b;
                border: 1px solid #555;
                border-top: none;
            }
        """)
        right_layout.addWidget(self.output_panel)

        # Нижняя панель
        bottom_layout = QHBoxLayout()

        self.run_btn = QPushButton("▶️ Run Script")
        self.run_btn.clicked.connect(self.run_script)
        self.run_btn.setEnabled(False)
        self.run_btn.setMinimumWidth(100)
        bottom_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("⏹️ Stop Script")
        self.stop_btn.clicked.connect(self.stop_script)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(100)
        bottom_layout.addWidget(self.stop_btn)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_current_tab)
        self.save_btn.setMinimumWidth(80)
        bottom_layout.addWidget(self.save_btn)

        self.save_all_btn = QPushButton("💾 Save All")
        self.save_all_btn.clicked.connect(self.save_all_tabs)
        self.save_all_btn.setMinimumWidth(80)
        bottom_layout.addWidget(self.save_all_btn)

        self.clear_output_btn = QPushButton("🗑️ Очистить вывод")
        self.clear_output_btn.clicked.connect(self.clear_output)
        self.clear_output_btn.setMinimumWidth(120)
        bottom_layout.addWidget(self.clear_output_btn)

        bottom_layout.addStretch()
        right_layout.addLayout(bottom_layout)

        # Статус
        self.script_status = QLabel("Ready")
        self.script_status.setStyleSheet("padding: 3px; color: #aaa;")
        right_layout.addWidget(self.script_status)

        self.new_tab_btn = QPushButton("➕ Новая вкладка")
        self.new_tab_btn.clicked.connect(self.new_tab)
        self.new_tab_btn.setMinimumWidth(120)
        top_layout.addWidget(self.new_tab_btn)

        # Добавляем панели в основной layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)  # 1 - растягивается

    def show_error(self, error_message):
        """Показать ошибку в панели вывода"""
        self.output_panel.setPlainText(f"❌ Ошибка:\n{error_message}")
        self.output_panel.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ff6b6b;
                border: 1px solid #ff6b6b;
                border-top: none;
            }
        """)

    def show_success(self, message):
        """Показать успешное выполнение"""
        self.output_panel.setPlainText(f"✅ {message}")
        self.output_panel.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #6bff6b;
                border: 1px solid #6bff6b;
                border-top: none;
            }
        """)

    def clear_output(self):
        """Очистить панель вывода"""
        self.output_panel.clear()
        self.output_panel.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ff6b6b;
                border: 1px solid #555;
                border-top: none;
            }
        """)

    def new_tab(self, filename=None, content=None):
        """Создать новую вкладку"""
        # Если сейчас пустое состояние - удаляем его
        if self.tab_widget.count() == 1 and self.tab_widget.tabText(0) == "📄 Пусто":
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()
            self.tab_widget.setTabsClosable(True)

        editor = QTextEdit()
        editor.setFont(QFont("Courier New", 12))
        editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)

        # СОХРАНЯЕМ highlighter КАК АТРИБУТ EDITOR
        highlighter = JavaScriptHighlighter(editor.document())
        editor.highlighter = highlighter  # ← вот это важно!

        if content:
            editor.setText(content)
        else:
            editor.setText(self.get_default_script())

        if filename:
            tab_name = os.path.basename(filename)
            editor.setProperty("filename", filename)
        else:
            # Считаем количество безымянных вкладок
            untitled_count = 1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i).startswith("Untitled"):
                    untitled_count += 1
            tab_name = f"Untitled {untitled_count}"
            editor.setProperty("filename", None)

        index = self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index):
        """Закрыть вкладку"""
        if self.tab_widget.count() > 1:
            # Если есть больше одной вкладки - закрываем
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()
        else:
            # Если последняя вкладка - заменяем на заглушку
            self.show_empty_state()

    def show_empty_state(self):
        """Показать состояние 'нет вкладок'"""
        if self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

        # Создаем виджет-заглушку
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📄")
        icon_label.setFont(QFont("Arial", 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)

        text_label = QLabel("Нет открытых вкладок")
        text_label.setFont(QFont("Arial", 16))
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet("color: #666;")
        empty_layout.addWidget(text_label)

        sub_text = QLabel("Создайте новую вкладку или откройте файл")
        sub_text.setFont(QFont("Arial", 10))
        sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_text.setStyleSheet("color: #444;")
        empty_layout.addWidget(sub_text)

        # Кнопка для создания новой вкладки
        new_tab_btn = QPushButton("➕ Новая вкладка")
        new_tab_btn.setMaximumWidth(200)
        new_tab_btn.clicked.connect(self.new_tab)
        empty_layout.addWidget(new_tab_btn)

        self.tab_widget.addTab(empty_widget, "📄 Пусто")
        self.tab_widget.setTabsClosable(False)

    def get_current_editor(self):
        """Получить текущий редактор"""
        return self.tab_widget.currentWidget()

    def get_default_script(self):
        return """// Madmen 3D Script
function update(state, time) {
    // Вращение
    state.angle_x = Math.sin(time) * 45;
    state.angle_y = Math.cos(time) * 45;

    // Движение
    state.pos_x = 400 + Math.sin(time * 2) * 200;
    state.pos_y = 300 + Math.cos(time * 3) * 150;

    // Масштаб
    state.scale = 1 + Math.sin(time * 5) * 0.3;

    return state;
}
"""

    # === ФАЙЛОВЫЕ ОПЕРАЦИИ ===

    def refresh_file_tree(self):
        """Обновить дерево файлов"""
        self.file_model.setRootPath(QDir.rootPath())
        self.file_tree.setRootIndex(self.file_model.index(QDir.homePath()))

    def on_file_double_click(self, index):
        """Открыть файл при двойном клике"""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path) and file_path.endswith('.js'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.new_tab(file_path, content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def new_file(self):
        """Создать новый файл"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDirectory(QDir.homePath())
        dialog.setNameFilter("JS Files (*.js)")

        if dialog.exec():
            filename = dialog.selectedFiles()[0]
            if not filename.endswith('.js'):
                filename += '.js'
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.get_default_script())
                self.refresh_file_tree()
                self.new_tab(filename, self.get_default_script())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {e}")

    def new_folder(self):
        """Создать новую папку"""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("New Folder")
        dialog.setLabelText("Enter folder name:")
        dialog.setTextValue("")

        if dialog.exec():
            folder_name = dialog.textValue()
            if folder_name:
                folder_path = os.path.join(self.workspace_dir, folder_name)
                try:
                    os.makedirs(folder_path)
                    self.refresh_file_tree()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")

    def delete_item(self):
        """Удалить файл или папку"""
        indexes = self.file_tree.selectedIndexes()
        if indexes:
            file_path = self.file_model.filePath(indexes[0])

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Delete")
            msg_box.setText(f"Are you sure you want to delete {os.path.basename(file_path)}?")
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    else:
                        import shutil
                        shutil.rmtree(file_path)
                    self.refresh_file_tree()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def save_current_tab(self):
        """Сохранить текущую вкладку"""
        editor = self.get_current_editor()
        if not editor:
            return

        filename = editor.property("filename")
        if not filename:
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            dialog.setDirectory(self.workspace_dir)
            dialog.setNameFilter("JS Files (*.js)")
            dialog.setDefaultSuffix("js")

            if dialog.exec():
                filename = dialog.selectedFiles()[0]
                if not filename.endswith('.js'):
                    filename += '.js'
                editor.setProperty("filename", filename)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(filename))

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                self.refresh_file_tree()
                self.script_status.setText(f"✅ Saved: {os.path.basename(filename)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def save_all_tabs(self):
        """Сохранить все вкладки"""
        saved_count = 0
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            filename = editor.property("filename")
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(editor.toPlainText())
                    saved_count += 1
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save {filename}: {e}")

        self.refresh_file_tree()
        self.script_status.setText(f"✅ Saved {saved_count} files")

    # === СЕТЕВЫЕ ОПЕРАЦИИ ===

    def connect_to_main(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(2.0)
            self.socket.connect(('localhost', 9999))
            self.connected = True
            self.connect_btn.setText("Connected")
            self.connect_btn.setEnabled(False)
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; padding: 3px;")
            self.run_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect: {e}")

    def check_status(self):
        """Проверка статуса скрипта"""
        if not self.connected or not self.socket:
            return

        try:
            self.socket.send(json.dumps({"cmd": "get_status"}).encode())
            data = self.socket.recv(4096)
            if not data:
                return

            response = data.decode().strip()
            responses = []
            buffer = response
            while buffer:
                try:
                    obj, idx = json.JSONDecoder().raw_decode(buffer)
                    responses.append(obj)
                    buffer = buffer[idx:].strip()
                except json.JSONDecodeError:
                    break

            for msg in responses:
                if "script_running" in msg:
                    script_running = msg.get("script_running", False)

                    if script_running != self.script_running:
                        self.script_running = script_running

                        if script_running:
                            self.run_btn.setEnabled(False)
                            self.stop_btn.setEnabled(True)
                            self.script_status.setText("Script running...")
                            self.show_success("Script started successfully")
                        else:
                            self.run_btn.setEnabled(True)
                            self.stop_btn.setEnabled(False)
                            self.script_status.setText("Script stopped")

                if "error" in msg:
                    self.show_error(msg["error"])

                if msg.get("message") == "Script stopped":
                    self.script_running = False
                    self.run_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                    self.script_status.setText("Script stopped")

        except Exception as e:
            print(f"Status check error: {e}")
            self.connected = False
            self.connect_btn.setText("Connect to Main App")
            self.connect_btn.setEnabled(True)
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; padding: 3px;")
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.show_error(f"Connection lost: {e}")

    def run_script(self):
        if not self.connected:
            return

        editor = self.get_current_editor()
        if not editor:
            return

        script = editor.toPlainText()
        msg = {
            "cmd": "execute_script",
            "script": script
        }
        try:
            self.socket.send(json.dumps(msg).encode())
            self.script_status.setText("Starting script...")
            self.clear_output()
        except Exception as e:
            self.show_error(f"Failed to run script: {e}")
            QMessageBox.critical(self, "Error", f"Failed to run script: {e}")

    def stop_script(self):
        if not self.connected:
            return

        msg = {"cmd": "stop_script"}
        try:
            self.socket.send(json.dumps(msg).encode())
            self.script_status.setText("Stopping script...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop script: {e}")

    def closeEvent(self, event):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    editor = ScriptEditor()
    editor.show()
    sys.exit(app.exec())