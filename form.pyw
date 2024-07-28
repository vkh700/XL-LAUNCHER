from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSpinBox, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, QProgressBar, QPushButton, QApplication, QMainWindow, QCheckBox, QSlider
from PyQt5.QtGui import QPixmap
import pyqt5_fugueicons as fugue

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command
from minecraft_launcher_lib.forge import install_forge_version, list_forge_versions, find_forge_version, forge_to_installed_version

from uuid import uuid1

from sys import argv, exit

import platform
import os
import subprocess
from subprocess import call
import psutil

from mojang import Client, API

import qdarkgraystyle

import webbrowser

from tkinter import messagebox


minecraft_directory = os.getenv('APPDATA') + "/XLLauncher/.minecraft"
CURRENT_DIRECTORY = os.getenv('APPDATA') + "/XLLauncher/"
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
        try:
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
                try:
                    install_forge_version(find_forge_version(self.version_id),minecraft_directory,callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })
                    call(get_minecraft_command(version=forge_to_installed_version(find_forge_version(self.version_id)), minecraft_directory=minecraft_directory, options=options))
                except Exception as ex:
                    install_forge_version(find_forge_version(self.version_id),minecraft_directory,callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })
                    call(get_minecraft_command(version="forge " + find_forge_version(self.version_id), minecraft_directory=minecraft_directory, options=options))                    
            else:   
                call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
            self.state_update_signal.emit(False)
        except Exception as ex:
            messagebox.showerror("Ошибка", ex)
            window.state_update(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(400, 400)
        self.centralwidget = QWidget(self)
        self.setWindowTitle("XL:LAUNCHER")

        if (os.path.exists(CURRENT_DIRECTORY) != True):
            os.mkdir(CURRENT_DIRECTORY)
        
        
        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(230, 127))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap(CURRENT_PROG_DIRECTORY + '/assets/title.png'))
        self.logo.setScaledContents(True)
        self.logo.move(120,0)

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.loginTitle = QLabel(self.centralwidget)
        self.loginTitle.setText('Войти в аккаунт (Майкр.):')
        self.loginTitle.move(165,90)

        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Email')
        self.username.move(170,130)
        self.username.resize(QSize(130,30))

        self.password = QLineEdit(self.centralwidget)
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        self.password.move(170,160)
        self.password.resize(QSize(130,30))

        if (os.path.isfile(CURRENT_DIRECTORY + "/passwd.dat")):
            f = open(CURRENT_DIRECTORY + "/passwd.dat", "r")
            self.password.setText(f.read())
        
        self.version_select = QComboBox(self.centralwidget)
        self.version_select.move(210,190)
        self.version_select.resize(QSize(70,30))
        
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
        self.start_progress_label.move(0,130)
        self.start_progress_label.resize(200,20)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 24)
        self.start_progress.setVisible(False)
        self.start_progress.move(0,150)
        self.start_progress.resize(150,20)
        
        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Играть!')
        self.start_button.clicked.connect(self.launch_game)
        self.start_button.move(200,220)
        self.start_button.resize(QSize(70,30))
        self.start_button.setStyleSheet("background-color: #ffa500; color : white;")

        self.game_folder = QPushButton(fugue.icon('folder'),"",self.centralwidget)
        self.game_folder.clicked.connect(self.game_folder_opn)
        self.game_folder.move(170,190)
        self.game_folder.resize(QSize(30,30))

        self.options = QPushButton(self.centralwidget)
        self.options.setText('Настройки')
        self.options.clicked.connect(self.options_opn)
        self.options.move(0,200)
        self.options.resize(QSize(90,30))
        self.options.setStyleSheet("background : rgba(0, 0, 0, 100); color:white; border-radius: 4px;") 

        self.main = QPushButton(self.centralwidget)
        self.main.setText('Главная')
        self.main.clicked.connect(self.main_opn)
        self.main.move(0,170)
        self.main.resize(QSize(90,30))
        self.main.setStyleSheet("background : rgba(0, 0, 0, 100); color:white; border-radius: 4px;") 

        self.sp = QSlider(self.centralwidget)
        print(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMaximum(round(psutil.virtual_memory().total/(1024**3)))
        self.sp.setMinimum(2)
        self.sp.setOrientation(Qt.Orientation.Horizontal)
        self.sp.move(170,120)
        self.sp.resize(QSize(150,30))
        self.sliderLabel = QLabel(self.centralwidget)
        self.sliderLabel.move(165,120)
        self.sliderLabel.setVisible(False)
        self.sliderLabel.resize(QSize(30,30))
        self.sp.valueChanged.connect(self.sliderLabel.setNum)

        self.sp.setVisible(False)

        if (os.path.isfile(CURRENT_DIRECTORY + "/ram.dat")):
            f = open(CURRENT_DIRECTORY + "/ram.dat", "r")
            self.sp.setValue(int(f.read()))

        self.forge = QCheckBox("Forge?",self.centralwidget)
        self.forge.setTristate(False)
        self.forge.move(165,160)

        if (os.path.isfile(CURRENT_DIRECTORY + "/forge.dat")):
            f = open(CURRENT_DIRECTORY + "/forge.dat", "r")
            self.forge.setChecked(bool(f.read()))

        self.optifine = QPushButton("Скачать Optifine",self.centralwidget)
        self.optifine.clicked.connect(self.download_opt)
        self.optifine.move(165,180)
        self.optifine.resize(110,21)

        self.forge.setVisible(False)
        self.optifine.setVisible(False)

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
        os.startfile(minecraft_directory)
    def options_opn(self):
        self.sp.setVisible(True)
        self.sliderLabel.setVisible(True)
        self.forge.setVisible(True)
        self.optifine.setVisible(True)
        self.version_select.setVisible(False)
        self.game_folder.setVisible(False)
        self.start_button.setVisible(False)
        self.loginTitle.setVisible(False)
        self.username.setVisible(False)
        self.password.setVisible(False)
    def main_opn(self):
        self.sp.setVisible(False)
        self.sliderLabel.setVisible(False)
        self.forge.setVisible(False)
        self.optifine.setVisible(False)
        self.version_select.setVisible(True)
        self.game_folder.setVisible(True)
        self.start_button.setVisible(True)
        self.loginTitle.setVisible(True)
        self.username.setVisible(True)
        self.password.setVisible(True)
        
        
           
    def download_opt(self):
        webbrowser.open_new_tab("https://optifine.net/downloads")
        

if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    window = MainWindow()
    window.show()

    exit(app.exec_())
