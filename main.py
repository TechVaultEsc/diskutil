import sys
import psutil
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QColor, QPalette, QPainter, QBrush

def check_disks():
    disk_info = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            device = partition.device
            mountpoint = partition.mountpoint
            fstype = partition.fstype
            io_counters = psutil.disk_io_counters(perdisk=True).get(device, None)
            disk_info.append({
                "device": device,
                "mountpoint": mountpoint,
                "filesystem": fstype,
                "total_space": usage.total,
                "used_space": usage.used,
                "free_space": usage.free,
                "usage_percent": usage.percent,
                "read_count": io_counters.read_count if io_counters else 0,
                "write_count": io_counters.write_count if io_counters else 0,
                "read_bytes": io_counters.read_bytes if io_counters else 0,
                "write_bytes": io_counters.write_bytes if io_counters else 0,
                "read_time": io_counters.read_time if io_counters else 0,
                "write_time": io_counters.write_time if io_counters else 0,
                "read_only": partition.opts
            })
        except PermissionError:
            continue
    return disk_info

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

class DiskMonitorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.is_dragging = False

    def initUI(self):
        self.setWindowTitle("Диск Чекер")
        self.setGeometry(100, 100, 500, 450)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setFixedSize(500, 450)
        self.setStyleSheet("""
            background-color: #2f3136;
            color: white;
            font-family: 'Arial', sans-serif;
            border-radius: 10px;
        """)

        self.top_panel = QWidget(self)
        self.top_panel.setStyleSheet("background-color: #44474a; border-radius: 10px 10px 0 0;")
        self.top_panel.setFixedHeight(30)
        
        self.close_button = QPushButton("X", self.top_panel)
        self.close_button.setStyleSheet("""
            background-color: transparent;
            color: white;
            border: none;
            font-size: 16px;
            width: 30px;
            height: 30px;
            border-radius: 15px;
        """)
        self.close_button.clicked.connect(self.close)

        self.top_panel_layout = QHBoxLayout(self.top_panel)
        self.top_panel_layout.addWidget(self.close_button, alignment=Qt.AlignRight)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.top_panel)

        self.label_disk = QLabel("Выберите диск для мониторинга:")
        self.label_disk.setStyleSheet("""
            font-size: 16px; 
            margin-bottom: 20px;
            color: #7289da;
        """)
        self.layout.addWidget(self.label_disk)
        
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("""
            background-color: #44474a;
            border: 1px solid #666;
            color: white;
            font-size: 14px;
            padding: 5px;
            border-radius: 5px;
        """)
        self.comboBox.addItems(self.get_drives())
        self.layout.addWidget(self.comboBox)
        
        self.label_info = QLabel("Информация о диске")
        self.label_info.setStyleSheet("""
            font-size: 14px; 
            margin-top: 20px;
            color: #7289da;
        """)
        self.layout.addWidget(self.label_info)
        
        self.startButton = QPushButton("Начать проверку")
        self.startButton.setStyleSheet("""
            background-color: #7289da;
            color: white;
            border: none;
            padding: 10px;
            font-size: 16px;
            border-radius: 5px;
        """)
        self.startButton.setFixedSize(200, 40)
        self.startButton.clicked.connect(self.start_checking)
        self.layout.addWidget(self.startButton)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        
        self.setLayout(self.layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def get_drives(self):
        drives = [part.device for part in psutil.disk_partitions() if part.fstype != '']
        return drives

    def start_checking(self):
        self.timer.start(1000)
        self.update_info()
        self.startButton.setEnabled(False)

    def update_info(self):
        selected_disk = self.comboBox.currentText()
        disks = check_disks()
        disk_info = next((disk for disk in disks if disk['device'] == selected_disk), None)
        if disk_info:
            info = (
                f"Устройство: {disk_info['device']}\n"
                f"Точка монтирования: {disk_info['mountpoint']}\n"
                f"Файловая система: {disk_info['filesystem']}\n"
                f"Общий объем: {format_size(disk_info['total_space'])}\n"
                f"Использовано: {format_size(disk_info['used_space'])}\n"
                f"Свободно: {format_size(disk_info['free_space'])}\n"
                f"Использование: {disk_info['usage_percent']}%\n"
                f"Количество операций чтения: {disk_info['read_count']}\n"
                f"Количество операций записи: {disk_info['write_count']}\n"
                f"Чтение (байт): {format_size(disk_info['read_bytes'])}\n"
                f"Запись (байт): {format_size(disk_info['write_bytes'])}\n"
                f"Время чтения (мс): {disk_info['read_time']} мс\n"
                f"Время записи (мс): {disk_info['write_time']} мс\n"
                f"Режим работы: {'Только чтение' if 'ro' in disk_info['read_only'] else 'Чтение/Запись'}"
            )
            self.label_info.setText(info)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DiskMonitorApp()
    ex.show()
    sys.exit(app.exec_())
