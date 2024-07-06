from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSpinBox, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, QProgressBar, QPushButton, QApplication, QMainWindow, QCheckBox
from PyQt5.QtGui import QPixmap

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command

from uuid import uuid1

from subprocess import call
from sys import argv, exit

import platform

import os

from mojang import Client, API

import psutil

import qdarkgraystyle

minecraft_directory = ".xllauncher"
CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str, str, bool, int)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    version_id = ''
    username = ''
    usernameRl = ''
    password = ''
    uuid = ''
    memory = 1
    license = False

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username, password, license, memory):
        self.version_id = version_id
        self.username = username
        self.password = password
        self.license = license
        self.memory = memory
    
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

        f = open("plr.dat", "w")
        f.write(self.username)
        f.close()
        f = open("ver.dat", "w")
        f.write(self.version_id)
        f.close()
        f = open("passwd.dat", "w")
        f.write(self.password)
        f.close()
        f = open("ram.dat", "w")
        f.write(self.memory)
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
        self.logo.setPixmap(QPixmap(CURRENT_DIRECTORY + '/assets/title.png'))
        self.logo.setScaledContents(True)

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Email')

        self.password = QLineEdit(self.centralwidget)
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)

        if (os.path.isfile("passwd.dat")):
            f = open("passwd.dat", "r")
            self.password.setText(f.read())
        
        self.version_select = QComboBox(self.centralwidget)
        
        for version in get_version_list():
            self.version_select.addItem(version['id'])
        
        if (os.path.isfile("ver.dat")):
            f = open("ver.dat", "r")
            self.version_select.setCurrentText(f.read())

        if (os.path.isfile("plr.dat")):
            f = open("plr.dat", "r")
            self.username.setText(f.read())

        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 24)
        self.start_progress.setVisible(False)
        
        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('PLAY!')
        self.start_button.clicked.connect(self.launch_game)

        self.game_folder = QPushButton(self.centralwidget)
        self.game_folder.setText('Game Folder')
        self.game_folder.clicked.connect(self.game_folder_opn)

        self.sp = QSpinBox(self.centralwidget)
        print(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMaximum(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMinimum(2)

        if (os.path.isfile("ram.dat")):
            f = open("ram.dat", "r")
            self.sp.setText(f.read())

        self.buttonopts = QHBoxLayout()
        self.buttonopts.addWidget(self.start_button)
        self.buttonopts.addWidget(self.game_folder)
        
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
        self.license.setDisabled(value)
        self.version_select.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)
    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)
    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text(), self.password.text(), self.license.isChecked(), self.sp.value())
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
        

if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    window = MainWindow()
    window.show()

    exit(app.exec_())
