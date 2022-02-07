import sys
from PySide6.QtWidgets import *

class Survey(QWidget):
    def __init__(self):
        super().__init__()

        self.label_values = ['Start Location', 'Bearing', 'Region Length', 'Path Width', 'Path Count', 'Layer Count']
        self.labels = []
        self.fields = []

        for i in self.label_values:
            self.labels.append(QLabel(i))

        for i in range(len(self.label_values)):
            self.fields.append(QLineEdit())

        layout = QGridLayout()
        for i in range(len(self.label_values)):
            layout.addWidget(self.labels[i], i, 0)
            layout.addWidget(self.fields[i], i, 1)

        self.setLayout(layout)

class Destination(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel('Location')
        self.field = QLineEdit()

        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.field, 0, 1)

        self.setLayout(layout)

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.mission_objectives = []

        self.create_mission_tab()
        self.create_testing_tab()

        layout = QGridLayout()
        self.setLayout(layout)

        tabs = QTabWidget()

        tabs.addTab(self._mission_tab, 'Mission')
        tabs.addTab(self._testing_tab, 'Testing')

        layout.addWidget(tabs, 0, 0)

        self.setWindowTitle('MOANA')

    def create_mission_tab(self):
        self._mission_tab = QWidget()

        self.add_objective_button = QPushButton('Add Objective')
        self.add_destination_button = QPushButton('Add Destination')
        self.start_mission_button = QPushButton('Start Mission')

        self.add_objective_button.clicked.connect(self.add_objective)
        self.add_destination_button.clicked.connect(self.add_destination)

        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.add_objective_button)
        sub_layout.addWidget(self.add_destination_button)

        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.start_mission_button)

        self._mission_layout = layout
        self._mission_tab.setLayout(self._mission_layout)

    def create_testing_tab(self):
        self._testing_tab = QWidget()

        comp1_label = QLabel('Heading Control')
        comp1_field = QLineEdit()
        comp1_button = QPushButton('Test')

        comp2_label = QLabel('Pitch Control')
        comp2_field = QLineEdit()
        comp2_button = QPushButton('Test')

        comp3_label = QLabel('Thruster Control')
        comp3_field = QLineEdit()
        comp3_button = QPushButton('Test')

        layout = QGridLayout()
        layout.addWidget(comp1_label, 0, 0)
        layout.addWidget(comp1_field, 0, 1)
        layout.addWidget(comp1_button, 0, 2)
        layout.addWidget(comp2_label, 1, 0)
        layout.addWidget(comp2_field, 1, 1)
        layout.addWidget(comp2_button, 1, 2)
        layout.addWidget(comp3_label, 2, 0)
        layout.addWidget(comp3_field, 2, 1)
        layout.addWidget(comp3_button, 2, 2)

        self._testing_layout = layout
        self._testing_tab.setLayout(self._testing_layout)

    def add_objective(self):
        self.mission_objectives.append(Survey())
        self._mission_layout.insertWidget(len(self.mission_objectives) - 1, self.mission_objectives[-1])

    def add_destination(self):
        self.mission_objectives.append(Destination())
        self._mission_layout.insertWidget(len(self.mission_objectives) - 1, self.mission_objectives[-1])

if __name__ == '__main__':
    app = QApplication()
    window = Window()
    window.show()

    sys.exit(app.exec())