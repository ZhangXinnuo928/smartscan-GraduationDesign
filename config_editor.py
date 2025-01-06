from PyQt5.QtWidgets import (  
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,  
    QLabel, QLineEdit, QFileDialog, QScrollArea, QFormLayout, QGroupBox, QMessageBox, QSpinBox, QCheckBox, QComboBox  
)  
from PyQt5.QtCore import Qt  
import yaml  
import sys  


class ConfigEditorApp(QMainWindow):  
    def __init__(self):  
        super().__init__()  
        self.setWindowTitle("配置文件编辑器")  
        self.setGeometry(100, 100, 900, 700)  

        # 默认配置内容  
        self.default_config = self.get_default_config()  
        self.config_data = self.default_config.copy()  # 使用默认配置初始化  

        # 主布局  
        self.central_widget = QWidget()  
        self.setCentralWidget(self.central_widget)  
        self.main_layout = QVBoxLayout(self.central_widget)  

        # 文件选择部分  
        self.file_path = None  
        self.setup_file_selection()  

        # 配置文件显示部分（滚动区域）  
        self.scroll_area = QScrollArea()  
        self.scroll_area.setWidgetResizable(True)  
        self.scroll_content = QWidget()  
        self.scroll_layout = QVBoxLayout(self.scroll_content)  
        self.scroll_area.setWidget(self.scroll_content)  
        self.main_layout.addWidget(self.scroll_area)  

        # 按钮部分  
        self.setup_buttons()  

        # 显示默认配置  
        self.display_config()  

    def get_default_config(self):  
        """返回默认的配置内容"""  
        return {  
            "TCP": {  
                "host": "localhost",  
                "port": 54333,  
                "buffer_size": 8388608,  
                "timeout": 10  
            },  
            "logging": {  
                "level": "INFO",  
                "directory": None,  # 默认值为 null  
                "formatter": "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s"  
            },  
            "plots": {  
                "posterior_map_shape": [50, 50]  
            },  
            "scanning": {  
                "max_points": 999,  
                "duration": 7200,  
                "train_at": [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000],  
                "train_every": 0,  
                "normalize_values": "training",  
                "fixed_normalization": [1.0, 1.0],  
                "merge_unique_positions": True,  
                "base_error": 0.01,  
                "initial_points": "hexgrid_2D_13"  # 默认初始点类型  
            },  
            "tasks": {  
                "curvature": {  
                    "function": "curvature",  
                    "params": {  
                        "bw": 5,  
                        "c1": 0.001,  
                        "c2": 0.001,  
                        "w": 1,  
                        "roi": [[145, 190], [20, 130]]  
                    }  
                },  
                "mean": {  
                    "function": "mean",  
                    "params": {  
                        "roi": [[145, 190], [20, 130]]  
                    }  
                }  
            },  
            "acquisition_function": {  
                "function": "acquisition_function_nd",  
                "params": {  
                    "a": 1,  
                    "weights": None,  # 默认值为 null  
                    "norm": 1,  
                    "c": 0  
                }  
            },  
            "cost_function": {  
                "function": "cost_per_axis",  
                "params": {  
                    "speed": [300, 300],  
                    "weight": [100, 100]  
                }  
            },  
            "gp": {  
                "optimizer": {  
                    "output_space_dimension": 1  
                },  
                "fvgp": {  
                    "init_hyperparameters": [1000000, 100, 100, 0.5],  
                    "compute_device": "cpu",  
                    "gp_kernel_function": None,  # 默认值为 null  
                    "gp_mean_function": None,  # 默认值为 null  
                    "use_inv": False,  
                    "ram_economy": True  
                },  
                "training": {  
                    "hyperparameter_bounds": [  
                        [1000000, 1000000000],  
                        [10, 50000],  
                        [10, 50000],  
                        [0.001, 5000]  
                    ],  
                    "pop_size": 20,  
                    "max_iter": 2,  
                    "tolerance": 0.000001  
                },  
                "ask": {  
                    "n": 1,  
                    "bounds": None,  # 默认值为 null  
                    "method": "global",  
                    "pop_size": 20,  
                    "max_iter": 10,  
                    "tol": 0.000001  
                }  
            },  
            "simulator": {  
                "source_file": "D:/Users/raster2D_theta_2.h5",  
                "save_dir": "data",  
                "save_to_file": True,  
                "simulate_times": True,  
                "dwell_time": 1  
            }  
        }  

    def setup_file_selection(self):  
        """设置文件选择部分"""  
        self.file_select_layout = QHBoxLayout()  
        self.file_label = QLabel("配置文件路径:")  
        self.file_input = QLineEdit()  
        self.file_button = QPushButton("选择文件")  
        self.file_button.clicked.connect(self.select_file)  
        self.file_select_layout.addWidget(self.file_label)  
        self.file_select_layout.addWidget(self.file_input)  
        self.file_select_layout.addWidget(self.file_button)  
        self.main_layout.addLayout(self.file_select_layout)  

    def setup_buttons(self):  
        """设置按钮部分"""  
        self.button_layout = QHBoxLayout()  
        self.load_button = QPushButton("加载配置文件")  
        self.load_button.clicked.connect(self.load_config)  
        self.save_button = QPushButton("保存配置文件")  
        self.save_button.clicked.connect(self.save_config)  
        self.reset_button = QPushButton("重置为默认值")  
        self.reset_button.clicked.connect(self.reset_to_default)  
        self.button_layout.addWidget(self.load_button)  
        self.button_layout.addWidget(self.save_button)  
        self.button_layout.addWidget(self.reset_button)  
        self.main_layout.addLayout(self.button_layout)  

    def select_file(self):  
        """选择配置文件"""  
        file_path, _ = QFileDialog.getOpenFileName(self, "选择配置文件", "", "YAML 文件 (*.yaml; *.yml);;所有文件 (*)")  
        if file_path:  
            self.file_path = file_path  
            self.file_input.setText(file_path)  

    def load_config(self):  
        """加载配置文件"""  
        if not self.file_path:  
            QMessageBox.warning(self, "错误", "请先选择配置文件！")  
            return  

        try:  
            with open(self.file_path, 'r') as file:  
                self.config_data = yaml.safe_load(file)  
            self.display_config()  
            QMessageBox.information(self, "成功", "配置文件加载成功！")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"加载配置文件失败: {e}")  

    def display_config(self):  
        """在界面中显示配置文件内容"""  
        # 清空原有内容  
        for i in reversed(range(self.scroll_layout.count())):  
            widget = self.scroll_layout.itemAt(i).widget()  
            if widget:  
                widget.deleteLater()  

        # 遍历配置文件内容并生成表单  
        for section, values in self.config_data.items():  
            group_box = QGroupBox(section)  
            form_layout = QFormLayout()  

            if isinstance(values, dict):  
                self.add_nested_dict(form_layout, values, section)  
            else:  
                form_layout.addRow(QLabel("值"), self.create_editor(values, section, None))  

            group_box.setLayout(form_layout)  
            self.scroll_layout.addWidget(group_box)  

    def add_nested_dict(self, layout, nested_dict, section):  
        """递归添加嵌套字典"""  
        for key, value in nested_dict.items():  
            if isinstance(value, dict):  
                sub_group_box = QGroupBox(key)  
                sub_form_layout = QFormLayout()  
                self.add_nested_dict(sub_form_layout, value, f"{section}.{key}")  
                sub_group_box.setLayout(sub_form_layout)  
                layout.addRow(sub_group_box)  
            elif isinstance(value, list) and all(isinstance(i, list) for i in value):  
                # 处理二维列表（如 roi）  
                layout.addRow(QLabel(key), self.create_2d_list_editor(value, section, key))  
            elif isinstance(value, list):  
                # 处理一维列表（如 speed 和 weight）  
                layout.addRow(QLabel(key), self.create_1d_list_editor(value, section, key))  
            else:  
                layout.addRow(QLabel(key), self.create_editor(value, section, key))  

    def create_2d_list_editor(self, value, section, key):  
        """创建二维列表编辑器"""  
        editor = QLineEdit(", ".join(["[" + ", ".join(map(str, row)) + "]" for row in value]))  
        editor.textChanged.connect(  
            lambda val: self.update_config(  
                section,   
                key,   
                [[int(float(x)) for x in row.split(",")] for row in val.strip("[]").split("], [")]  
            )  # 转换为整数  
        )  
        return editor

    def create_1d_list_editor(self, value, section, key):  
        """创建一维列表编辑器"""  
        editor = QLineEdit(", ".join(map(str, value)))  
        editor.textChanged.connect(  
            lambda val: self.update_config(section, key, [float(x) if '.' in x else int(x) for x in val.split(",") if x.strip()])  
        )  
        return editor  

    def create_editor(self, value, section, key):  
        """根据值的类型创建合适的编辑器"""  
        if section == "scanning" and key == "initial_points":  
            # 使用下拉选择框  
            editor = QComboBox()  
            initial_point_types = [  
                "center_2D", "border_2D_8", "border_2D_16", "grid_2D_9", "grid_2D_25",  
                "hexgrid_2D_13", "hexgrid_2D_19", "center_3D", "border_3D_25", "border_3D_64",  
                "grid_3D_27", "grid_3D_125", "random_2D_50", "latin_hypercube", "sobol", "halton"  
            ]  
            editor.addItems(initial_point_types)  
            editor.setCurrentText(value)  
            editor.currentTextChanged.connect(lambda val: self.update_config(section, key, val))  
        elif isinstance(value, int):  
            editor = QSpinBox()  
            editor.setValue(value)  
            editor.setMaximum(9999999)  
            editor.valueChanged.connect(lambda val: self.update_config(section, key, val))  
        elif isinstance(value, float):  
            editor = QLineEdit(str(value))  
            editor.textChanged.connect(lambda val: self.update_config(section, key, float(val) if val else 0.0))  
        elif isinstance(value, bool):  
            editor = QCheckBox()  
            editor.setChecked(value)  
            editor.stateChanged.connect(lambda state: self.update_config(section, key, state == Qt.Checked))  
        elif value is None:  
            editor = QLineEdit("")  
            editor.setPlaceholderText("默认值：null")  
            editor.textChanged.connect(lambda val: self.update_config(section, key, None if val.strip() == "" else val))  
        elif isinstance(value, str):  
            editor = QLineEdit(value)  
            editor.textChanged.connect(lambda val: self.update_config(section, key, val))  
        else:  
            editor = QLabel(f"不支持的类型: {type(value)}")  
        return editor  

    def update_config(self, section, key, value):  
        """更新配置文件内容"""  
        keys = section.split(".")  
        config = self.config_data  
        for k in keys[:-1]:  
            config = config[k]  
        if key is None:  
            config[keys[-1]] = value  
        else:  
            config[keys[-1]][key] = value  

    def save_config(self):  
        """保存配置文件"""  
        if not self.file_path:  
            QMessageBox.warning(self, "错误", "请先选择保存路径！")  
            return  

        try:  
            with open(self.file_path, 'w') as file:  
                yaml.dump(self.config_data, file, default_flow_style=False, allow_unicode=True)  
            QMessageBox.information(self, "成功", "配置文件保存成功！")  
        except Exception as e:  
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {e}")  

    def reset_to_default(self):  
        """重置为默认配置"""  
        self.config_data = self.default_config.copy()  
        self.display_config()  


if __name__ == "__main__":  
    app = QApplication(sys.argv)  
    window = ConfigEditorApp()  
    window.show()  
    sys.exit(app.exec_())