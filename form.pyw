from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSpinBox, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, QProgressBar, QPushButton, QApplication, QMainWindow, QCheckBox
from PyQt5.QtGui import QPixmap

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command
from minecraft_launcher_lib.forge import install_forge_version, list_forge_versions, find_forge_version, forge_to_installed_version

from uuid import uuid1

from subprocess import call
from sys import argv, exit

import platform

import os

from mojang import Client, API

import psutil

import qdarkgraystyle

import webbrowser

minecraft_directory = "%appdata%/XLLauncher/.minecraft"
CURRENT_DIRECTORY = "%appdata%/XLLauncher/"
CURRENT_PROG_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str, str, bool, int, bool)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    version_id = ''
    username = ''
    usernameRl = ''
    password = ''
    uuid = ''
    memory = 1
    license = False
    forge = False

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username, password, license, memory, forge):
        self.version_id = version_id
        self.username = username
        self.password = password
        self.license = license
        self.memory = memory
        self.forge = forge
    
    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):

        f = open(CURRENT_DIRECTORY + "/plr.dat", "w")
        f.write(self.username)
        f.close()
        f = open(CURRENT_DIRECTORY + "/ver.dat", "w")
        f.write(self.version_id)
        f.close()
        f = open(CURRENT_DIRECTORY + "/passwd.dat", "w")
        f.write(self.password)
        f.close()
        f = open(CURRENT_DIRECTORY + "/ram.dat", "w")
        f.write(str(self.memory))
        f.close()
        f = open(CURRENT_DIRECTORY + "/forge.dat", "w")
        f.write(str(self.forge))
        f.close()

        self.state_update_signal.emit(True)

        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory, callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })
        
        client = Client(self.username, self.password)
        token = client.bearer_token
        self.usernameRl = client.get_profile().name
        api = API()
        self.uuid = api.get_uuid(self.usernameRl)

        options = {
            'username': self.usernameRl,
            'uuid': self.uuid,
            'token': token
        }
        options["jvmArguments"] = ["-Xmx" + str(self.memory) + "G", "-Xms" + str(self.memory) + "G"]

        if (self.forge):
            install_forge_version(find_forge_version(self.version_id),minecraft_directory,callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })
            call(get_minecraft_command(version="forge " + find_forge_version(self.version_id), minecraft_directory=minecraft_directory, options=options))
        else:   
            call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
        self.state_update_signal.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(300, 283)
        self.centralwidget = QWidget(self)
        self.setWindowTitle("XL:LAUNCHER")
        
        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(256, 127))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap(CURRENT_PROG_DIRECTORY + '/assets/title.png'))
        self.logo.setScaledContents(True)

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Email')

        self.password = QLineEdit(self.centralwidget)
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)

        if (os.path.isfile(CURRENT_DIRECTORY + "/passwd.dat")):
            f = open(CURRENT_DIRECTORY + "/passwd.dat", "r")
            self.password.setText(f.read())
        
        self.version_select = QComboBox(self.centralwidget)
        
        for version in get_version_list():
            self.version_select.addItem(version['id'])
        
        if (os.path.isfile(CURRENT_DIRECTORY + "/ver.dat")):
            f = open(CURRENT_DIRECTORY + "/ver.dat", "r")
            self.version_select.setCurrentText(f.read())

        if (os.path.isfile(CURRENT_DIRECTORY + "/plr.dat")):
            f = open(CURRENT_DIRECTORY + "/plr.dat", "r")
            self.username.setText(f.read())

        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 24)
        self.start_progress.setVisible(False)
        
        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Играть!')
        self.start_button.clicked.connect(self.launch_game)

        self.game_folder = QPushButton(self.centralwidget)
        self.game_folder.setText('Папка с игрой')
        self.game_folder.clicked.connect(self.game_folder_opn)

        self.options = QPushButton(self.centralwidget)
        self.options.setText('Настройки')
        self.options.clicked.connect(self.options_opn)

        self.sp = QSpinBox(self.centralwidget)
        print(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMaximum(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMinimum(2)

        self.sp.setVisible(False)

        if (os.path.isfile(CURRENT_DIRECTORY + "/ram.dat")):
            f = open(CURRENT_DIRECTORY + "/ram.dat", "r")
            self.sp.setValue(int(f.read()))

        self.buttonopts = QHBoxLayout()
        self.buttonopts.addWidget(self.start_button)
        self.buttonopts.addWidget(self.game_folder)
        self.buttonopts.addWidget(self.options)

        self.forge = QCheckBox("Forge?",self.centralwidget)
        self.forge.setTristate(False)

        if (os.path.isfile(CURRENT_DIRECTORY + "/forge.dat")):
            f = open(CURRENT_DIRECTORY + "/forge.dat", "r")
            self.forge.setChecked(bool(f.read()))

        self.optifine = QPushButton("Скачать Optifine",self.centralwidget)
        self.optifine.clicked.connect(self.download_opt)

        self.forge.setVisible(False)
        self.optifine.setVisible(False)

        self.veropts = QHBoxLayout()
        self.veropts.addWidget(self.forge)
        self.veropts.addWidget(self.optifine)
        
        self.vertical_layout = QVBoxLayout(self.centralwidget)
        self.vertical_layout.setContentsMargins(15, 15, 15, 15)
        self.vertical_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vertical_layout.addItem(self.titlespacer)
        self.vertical_layout.addWidget(self.username)
        self.vertical_layout.addWidget(self.password)
        self.vertical_layout.addWidget(self.version_select)
        self.vertical_layout.addWidget(self.sp)
        self.vertical_layout.addItem(self.progress_spacer)
        self.vertical_layout.addWidget(self.start_progress_label)
        self.vertical_layout.addWidget(self.start_progress)
        self.vertical_layout.addItem(self.veropts)
        self.vertical_layout.addItem(self.buttonopts)

        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.setCentralWidget(self.centralwidget)
    
    def licenseChange(self):
        self.username.setText("")

    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.username.setDisabled(value)
        self.password.setDisabled(value)
        self.version_select.setDisabled(value)
        self.sp.setDisabled(value)
        self.forge.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)
    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)
    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text(), self.password.text(), True, self.sp.value(), self.forge.isChecked())
        self.launch_thread.start()
    def game_folder_opn(self):
        if (platform.system() == "Windows"):
            import subprocess
            subprocess.run(['explorer', minecraft_directory])
        if ("Linux" in platform.system()):
            import subprocess
            subprocess.run(['xdg-open', minecraft_directory])
        if (platform.system() == "Darwin"):
            import subprocess
            subprocess.run(['open', minecraft_directory])
    def options_opn(self):
        if (self.sp.isVisible()):
            self.sp.setVisible(False)
        else:
            self.sp.setVisible(True)
        if (self.forge.isVisible()):
            self.forge.setVisible(False)
        else:
            self.forge.setVisible(True)
        if (self.optifine.isVisible()):
            self.optifine.setVisible(False)
        else:
            self.optifine.setVisible(True)
    def download_opt(self):
        webbrowser.open_new_tab("https://optifine.net/downloads")
        

if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    window = MainWindow()
    window.show()

    exit(app.exec_())
