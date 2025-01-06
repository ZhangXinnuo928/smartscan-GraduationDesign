import sys  
import psutil  
from PyQt5.QtCore import QProcess, Qt  
from PyQt5.QtGui import QFont, QIcon  
from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,  
    QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QStatusBar, QDialog, QTextEdit, QMessageBox  
)  
import config_editor  # 导入配置文件编辑器模块  
from smartscan import smartscan  # 导入 SmartScan 类  


class ErrorLogDialog(QDialog):  
    """自定义错误日志对话框"""  
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.setWindowTitle("日志")  
        self.resize(800, 500)  

        # 布局  
        self.layout = QVBoxLayout(self)  

        # 错误日志显示区域  
        self.error_text = QTextEdit(self)  
        self.error_text.setReadOnly(True)  
        self.layout.addWidget(self.error_text)  

        # 按钮容器  
        self.button_layout = QHBoxLayout()  

        # 清空日志按钮  
        self.clear_button = QPushButton("清空日志", self)  
        self.clear_button.clicked.connect(self.clear_log)  
        self.button_layout.addWidget(self.clear_button)  

        # 关闭按钮  
        self.close_button = QPushButton("关闭", self)  
        self.close_button.clicked.connect(self.close)  
        self.button_layout.addWidget(self.close_button)  

        self.layout.addLayout(self.button_layout)  

    def append_error(self, error_message):  
        """追加错误信息到日志"""  
        self.error_text.append(error_message)  

    def clear_log(self):  
        """清空日志内容"""  
        self.error_text.clear()  


class SmartScanUI(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("SmartScan 操作界面")  
        self.setGeometry(100, 100, 800, 600)  
        self.setWindowIcon(QIcon("icon.png"))  # 设置窗口图标  

        # 主布局  
        self.main_layout = QVBoxLayout()  

        # 添加标题  
        title_label = QLabel("SmartScan 操作界面")  
        title_label.setFont(QFont("Arial", 16, QFont.Bold))  
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")  
        title_label.setAlignment(Qt.AlignCenter)  
        self.main_layout.addWidget(title_label)  

        # 配置文件部分  
        config_group = QGroupBox("配置文件设置")  
        config_group.setFont(QFont("Arial", 12))  
        config_layout = QGridLayout()  

        config_label = QLabel("配置文件路径:")  
        self.config_input = QLineEdit(self)  
        self.config_button = QPushButton("选择配置文件", self)  
        self.config_button.clicked.connect(self.select_config_file)  
        self.edit_config_button = QPushButton("编辑配置文件", self)  
        self.edit_config_button.clicked.connect(self.edit_config_file)  

        config_layout.addWidget(config_label, 0, 0)  
        config_layout.addWidget(self.config_input, 0, 1, 1, 2)  
        config_layout.addWidget(self.config_button, 1, 1)  
        config_layout.addWidget(self.edit_config_button, 1, 2)  
        config_group.setLayout(config_layout)  
        self.main_layout.addWidget(config_group)  

        # 数据文件部分  
        data_group = QGroupBox("数据文件设置（仅模拟模式）")  
        data_group.setFont(QFont("Arial", 12))  
        data_layout = QGridLayout()  

        data_label = QLabel("数据文件路径:")  
        self.data_input = QLineEdit(self)  
        self.data_button = QPushButton("选择数据文件", self)  
        self.data_button.clicked.connect(self.select_data_file)  

        data_layout.addWidget(data_label, 0, 0)  
        data_layout.addWidget(self.data_input, 0, 1, 1, 2)  
        data_layout.addWidget(self.data_button, 1, 1)  
        data_group.setLayout(data_layout)  
        self.main_layout.addWidget(data_group)  

        # 扫描控制部分  
        scan_group = QGroupBox("扫描控制")  
        scan_group.setFont(QFont("Arial", 12))  
        scan_layout = QHBoxLayout()  

        self.real_scan_button = QPushButton("启动真实扫描", self)  
        self.real_scan_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")  
        self.real_scan_button.clicked.connect(self.start_real_scan)  

        self.simulation_button = QPushButton("启动模拟扫描", self)  
        self.simulation_button.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")  
        self.simulation_button.clicked.connect(self.start_simulation)  

        self.stop_button = QPushButton("停止扫描", self)  
        self.stop_button.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")  
        self.stop_button.clicked.connect(self.stop_scan)  

        self.pause_button = QPushButton("暂停扫描", self)  
        self.pause_button.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")  
        self.pause_button.clicked.connect(self.pause_or_resume_scan)  

        scan_layout.addWidget(self.real_scan_button)  
        scan_layout.addWidget(self.simulation_button)  
        scan_layout.addWidget(self.stop_button)  
        scan_layout.addWidget(self.pause_button)  
        scan_group.setLayout(scan_layout)  
        self.main_layout.addWidget(scan_group)  

        # 状态显示  
        self.status_label = QLabel("状态: 等待操作")  
        self.status_label.setFont(QFont("Arial", 10))  
        self.status_label.setStyleSheet("color: #8e44ad; margin-top: 10px;")  
        self.main_layout.addWidget(self.status_label)  

        # 设置主窗口  
        container = QWidget()  
        container.setLayout(self.main_layout)  
        self.setCentralWidget(container)  

        # 状态栏  
        self.status_bar = QStatusBar()  
        self.setStatusBar(self.status_bar)  
        self.status_bar.showMessage("欢迎使用 SmartScan！请根据提示选择配置文件和数据文件。")  

        # 初始化错误日志对话框  
        self.error_log_dialog = ErrorLogDialog(self)  

        # 初始化扫描状态  
        self._paused = False  
        self.pid = None  # 保存子进程 PID  

    def select_config_file(self):  
        file_path, _ = QFileDialog.getOpenFileName(self, "选择配置文件", "", "YAML 文件 (*.yaml; *.yml);;所有文件 (*)")  
        if file_path:  
            self.config_input.setText(file_path)  

    def edit_config_file(self):  
        config_path = self.config_input.text()  
        if config_path:  
            self.config_editor = config_editor.ConfigEditorApp()  
            self.config_editor.file_path = config_path  
            self.config_editor.file_input.setText(config_path)  
            self.config_editor.load_config()  
            self.config_editor.show()  
        else:  
            QMessageBox.warning(self, "错误", "请先选择配置文件！")  

    def select_data_file(self):  
        file_path, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "HDF5 文件 (*.h5);;所有文件 (*)")  
        if file_path:  
            self.data_input.setText(file_path)  

    def start_real_scan(self):  
        config_path = self.config_input.text()  
        if config_path:  
            self.status_label.setText("状态: 启动真实扫描中...")  
            self.process = QProcess(self)  
            self.process.start("python", ["-m", "smartscan", "--config", config_path])  
            self.pid = self.process.processId()  # 获取子进程 PID  
            self.process.readyReadStandardOutput.connect(self.read_output)  
            self.process.readyReadStandardError.connect(self.read_error)  
            self.process.finished.connect(self.process_finished)  
        else:  
            QMessageBox.warning(self, "错误", "请先选择配置文件！")  

    def start_simulation(self):  
        """启动模拟扫描"""  
        config_path = self.config_input.text()  
        data_path = self.data_input.text()  
        if config_path and data_path:  
            self.status_label.setText("状态: 启动模拟扫描中...")  
            self.simulator_process = QProcess(self)  
            self.simulator_process.start("python", ["-m", "smartscan.simulator", "-c", config_path, "-f", data_path])  
            self.pid = self.simulator_process.processId()  # 获取模拟器进程 PID  
            self.simulator_process.readyReadStandardOutput.connect(self.read_output)  
            self.simulator_process.readyReadStandardError.connect(self.read_error)  
            self.simulator_process.finished.connect(self.process_finished)  
        else:  
            QMessageBox.warning(self, "错误", "请先选择配置文件和数据文件！")  

    def pause_or_resume_scan(self):  
        if not self.pid:  
            QMessageBox.warning(self, "错误", "进程未启动或 PID 无效")  
            return  

        try:  
            p = psutil.Process(self.pid)  
            if not p.is_running():  
                QMessageBox.warning(self, "错误", "进程不存在或已结束")  
                return  

            if not self._paused:  
                p.suspend()  
                self.status_label.setText("状态: 扫描已暂停")  
                self.pause_button.setText("继续扫描")  
                self._paused = True  
            else:  
                p.resume()  
                self.status_label.setText("状态: 扫描已恢复")  
                self.pause_button.setText("暂停扫描")  
                self._paused = False  
        except psutil.NoSuchProcess:  
            QMessageBox.warning(self, "错误", "进程不存在或已结束")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"暂停或恢复扫描失败: {e}") 

    def stop_scan(self):  
        if hasattr(self, "process") and self.process.state() == QProcess.Running:  
            self.process.kill()  
            self.status_label.setText("状态: 扫描已停止")  
        elif hasattr(self, "simulator_process") and self.simulator_process.state() == QProcess.Running:  
            self.simulator_process.kill()  
            self.status_label.setText("状态: 模拟扫描已停止")  
        else:  
            QMessageBox.warning(self, "错误", "没有正在运行的扫描进程")  

    def process_finished(self):  
        self.status_label.setText("状态: 扫描已结束")  

    def read_output(self):  
        if hasattr(self, "process") and self.process.state() == QProcess.Running:  
            output = self.process.readAllStandardOutput().data().decode(errors="replace")  
            self.status_label.setText(f"状态: {output.strip()}")  
        if hasattr(self, "simulator_process") and self.simulator_process.state() == QProcess.Running:  
            output = self.simulator_process.readAllStandardOutput().data().decode(errors="replace")  
            self.status_label.setText(f"状态: {output.strip()}")  

    def read_error(self):  
        if hasattr(self, "process") and self.process.state() == QProcess.Running:  
            error = self.process.readAllStandardError().data().decode(errors="replace")  
            self.error_log_dialog.append_error(error)  
            self.error_log_dialog.show()  
        if hasattr(self, "simulator_process") and self.simulator_process.state() == QProcess.Running:  
            error = self.simulator_process.readAllStandardError().data().decode(errors="replace")  
            self.error_log_dialog.append_error(error)  
            self.error_log_dialog.show()  


if __name__ == "__main__":  
    app = QApplication(sys.argv)  
    window = SmartScanUI()  
    window.show()  
    sys.exit(app.exec_())