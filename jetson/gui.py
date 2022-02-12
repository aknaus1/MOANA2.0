import sys
from PySide6.QtWidgets import *
from guitransmit import MYSSH

class Window(QWidget):
    ssh = MYSSH

    def __init__(self):
        super().__init__()

        self.mission_objectives = []

        self.create_mission_tab()
        self.create_high_testing_tab()
        self.create_low_testing_tab()

        layout = QGridLayout()
        self.setLayout(layout)

        tabs = QTabWidget()

        tabs.addTab(self._mission_tab, 'Mission')
        tabs.addTab(self._high_testing_tab, 'High Level Testing')
        tabs.addTab(self._low_testing_tab, 'Low Level Testing')

        layout.addWidget(tabs, 0, 0)

        self.setFixedHeight(600)
        self.setFixedWidth(600)

        self.setWindowTitle('MOANA')

    def create_mission_tab(self):
        self._mission_tab = QWidget()

        label_values = ['Bearing', 'Path Length', 'Path Width', 'Path Count', 'Layer Count']
        mission_labels = []
        self.mission_fields = []

        for i in label_values:
            mission_labels.append(QLabel(i))

        for i in range(len(label_values)):
            self.mission_fields.append(QLineEdit())

        sub_layout = QGridLayout()
        for i in range(len(label_values)):
            sub_layout.addWidget(mission_labels[i], i, 0)
            sub_layout.addWidget(self.mission_fields[i], i, 1)

        self.start_mission_button = QPushButton('Send Mission Command')

        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.start_mission_button)

        self.start_mission_button.clicked.connect(self.start_mission)

        self._mission_layout = layout
        self._mission_tab.setLayout(self._mission_layout)

    def create_high_testing_tab(self):
        self._high_testing_tab = QWidget()

        pc_title = QLabel('Pitch Control')
        self.pc_button = QPushButton('Send')
        pc_lab1 = QLabel('Pitch angle command')
        self.pc_field1 = QLineEdit()
        pc_lab2 = QLabel('KPp')
        self.pc_field2 = QLineEdit()
        pc_lab3 = QLabel('Thrust command')
        self.pc_field3 = QLineEdit()

        pc_layout = QGridLayout()
        pc_layout.addWidget(pc_title, 0, 0)
        pc_layout.addWidget(self.pc_button, 0, 1)
        pc_layout.addWidget(pc_lab1, 1, 0)
        pc_layout.addWidget(self.pc_field1, 1, 1)
        pc_layout.addWidget(pc_lab2, 2, 0)
        pc_layout.addWidget(self.pc_field2, 2, 1)
        pc_layout.addWidget(pc_lab3, 3, 0)
        pc_layout.addWidget(self.pc_field3, 3, 1)
        
        hc_title = QLabel('Heading Control')
        self.hc_button = QPushButton('Send')
        hc_lab1 = QLabel('Heading command')
        self.hc_field1 = QLineEdit()
        hc_lab2 = QLabel('KPh')
        self.hc_field2 = QLineEdit()

        hc_layout = QGridLayout()
        hc_layout.addWidget(hc_title, 0, 0)
        hc_layout.addWidget(self.hc_button, 0, 1)
        hc_layout.addWidget(hc_lab1, 1, 0)
        hc_layout.addWidget(self.hc_field1, 1, 1)
        hc_layout.addWidget(hc_lab2, 2, 0)
        hc_layout.addWidget(self.hc_field2, 2, 1)
        
        dc_title = QLabel('Depth Control')
        self.dc_button = QPushButton('Send')
        dc_lab1 = QLabel('Depth command')
        self.dc_field1 = QLineEdit()
        dc_lab2 = QLabel('KPp')
        self.dc_field2 = QLineEdit()
        dc_lab3 = QLabel('KPd')
        self.dc_field3 = QLineEdit()

        dc_layout = QGridLayout()
        dc_layout.addWidget(dc_title, 0, 0)
        dc_layout.addWidget(self.dc_button, 0, 1)
        dc_layout.addWidget(dc_lab1, 1, 0)
        dc_layout.addWidget(self.dc_field1, 1, 1)
        dc_layout.addWidget(dc_lab2, 2, 0)
        dc_layout.addWidget(self.dc_field2, 2, 1)
        dc_layout.addWidget(dc_lab3, 3, 0)
        dc_layout.addWidget(self.dc_field3, 3, 1)

        sc_title = QLabel('Speed Control')
        self.sc_button = QPushButton('Send')
        sc_lab1 = QLabel('Speed command')
        self.sc_field1 = QLineEdit()

        sc_layout = QGridLayout()
        sc_layout.addWidget(sc_title, 0, 0)
        sc_layout.addWidget(self.sc_button, 0, 1)
        sc_layout.addWidget(sc_lab1, 1, 0)
        sc_layout.addWidget(self.sc_field1, 1, 1)

        layout = QVBoxLayout()
        layout.addLayout(pc_layout)
        layout.addLayout(hc_layout)
        layout.addLayout(dc_layout)
        layout.addLayout(sc_layout)

        self.pc_button.clicked.connect(self.pc_command)
        self.hc_button.clicked.connect(self.hc_command)
        self.dc_button.clicked.connect(self.dc_command)
        self.sc_button.clicked.connect(self.sc_command)

        self._high_testing_layout = layout
        self._high_testing_tab.setLayout(self._high_testing_layout)

    def create_low_testing_tab(self):
        self._low_testing_tab = QWidget()

        mc_title = QLabel('Mass Slider Control')
        self.mc_button = QPushButton('Send')
        mc_lab1 = QLabel('Mass slider position command')
        self.mc_field1 = QLineEdit()

        mc_layout = QGridLayout()
        mc_layout.addWidget(mc_title, 0, 0)
        mc_layout.addWidget(self.mc_button, 0, 1)
        mc_layout.addWidget(mc_lab1, 1, 0)
        mc_layout.addWidget(self.mc_field1, 1, 1)
        
        rc_title = QLabel('Rudder Control')
        self.rc_button = QPushButton('Send')
        rc_lab1 = QLabel('Rudder angle command')
        self.rc_field1 = QLineEdit()

        rc_layout = QGridLayout()
        rc_layout.addWidget(rc_title, 0, 0)
        rc_layout.addWidget(self.rc_button, 0, 1)
        rc_layout.addWidget(rc_lab1, 1, 0)
        rc_layout.addWidget(self.rc_field1, 1, 1)
        
        tc_title = QLabel('Thruster Control')
        self.tc_button = QPushButton('Send')
        tc_lab1 = QLabel('Thrust force')
        self.tc_field1 = QLineEdit()

        tc_layout = QGridLayout()
        tc_layout.addWidget(tc_title, 0, 0)
        tc_layout.addWidget(self.tc_button, 0, 1)
        tc_layout.addWidget(tc_lab1, 1, 0)
        tc_layout.addWidget(self.tc_field1, 1, 1)

        ac_title = QLabel('Data collection')
        self.ac_button = QPushButton('Send')
        ac_lab1 = QLabel('Length of time')
        self.ac_field1 = QLineEdit()

        ac_layout = QGridLayout()
        ac_layout.addWidget(ac_title, 0, 0)
        ac_layout.addWidget(self.ac_button, 0, 1)
        ac_layout.addWidget(ac_lab1, 1, 0)
        ac_layout.addWidget(self.ac_field1, 1, 1)

        layout = QVBoxLayout()
        layout.addLayout(mc_layout)
        layout.addLayout(rc_layout)
        layout.addLayout(tc_layout)
        layout.addLayout(ac_layout)

        self.mc_button.clicked.connect(self.mc_command)
        self.rc_button.clicked.connect(self.rc_command)
        self.tc_button.clicked.connect(self.tc_command)
        self.ac_button.clicked.connect(self.ac_command)

        self._low_testing_layout = layout
        self._low_testing_tab.setLayout(self._low_testing_layout)

    # send mission command
    def start_mission(self):
        print('start mission')
        print(self.mission_fields[0].text())
        print(self.mission_fields[1].text())
        print(self.mission_fields[2].text())
        print(self.mission_fields[3].text())
        print(self.mission_fields[4].text())
        self.ssh.mission(self.mission_fields[0], self.mission_fields[1], self.mission_fields[2], self.mission_fields[3], self.mission_fields[4])

    # send pitch control command
    def pc_command(self):
        print('pitch control')
        print(self.pc_field1.text())
        print(self.pc_field2.text())
        print(self.pc_field3.text())
        self.ssh.setPitch(self.pc_field1)

    # send heading control command
    def hc_command(self):
        print('heading control')
        print(self.hc_field1.text())
        print(self.hc_field2.text())
        self.ssh.setHeading(self.hc_field1)
    
    # send depth control command
    def dc_command(self):
        print('depth control')
        print(self.dc_field1.text())
        print(self.dc_field2.text())
        print(self.dc_field3.text())
        self.ssh.setDepth(self.dc_field1)

    # send speed control command
    def sc_command(self):
        print('speed control')
        print(self.sc_field1.text())
        self.ssh.setThrust(self.sc_field1)

    # send mass slider control command
    def mc_command(self):
        print('mass slider control')
        print(self.mc_field1.text())
        self.ssh.setStepper(self.mc_field1)

    # send rudder control command
    def rc_command(self):
        print('rudder control')
        print(self.rc_field1.text())
        self.ssh.setYaw(self.rc_field1)
    
    # send thrust control command
    def tc_command(self):
        print('thrust control')
        print(self.tc_field1.text())
        self.ssh.setThrust(self.tc_field1)

    # send data collection command
    def ac_command(self):
        print('data collection')
        print(self.ac_field1.text())
        self.ssh.startDataCollection(self.ac_field1)


if __name__ == '__main__':
    app = QApplication()
    window = Window()
    window.show()

    sys.exit(app.exec())
