import time
import os
import sys
import glob
try:
    from epics import caput
    from epics import caget
except ImportError:
    epics = None
from qtpy import QtGui, QtCore, QtWidgets
from detectors import detectors
import collections


class FolderMaker(QtWidgets.QWidget):
    def __init__(self, parent=None, running=False, chosen_detectors=None, previous_detector_settings=None):
        super(FolderMaker, self).__init__()
        self.folder_maker_settings = QtCore.QSettings("Logger", "FolderMaker")
        self.caller = parent
        self.log_running = running
        self.setWindowTitle('Create folders and setup')
        self.setWindowIcon(QtGui.QIcon('icons/folder.jpg'))
        self.show()
        self.setGeometry(100, 100, 300, 200)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        if previous_detector_settings is None:
            self.new_settings = collections.OrderedDict()
            for detector in chosen_detectors:
                self.new_settings[detector] = None
        else:
            self.new_settings = previous_detector_settings

        self.chosen_detectors = collections.OrderedDict()
        for detector in chosen_detectors:
            self.chosen_detectors[detector] = DetectorSection(detector, self.new_settings[detector])

        # Create Widgets
        self.advanced_settings_gb = AdvancedSettingsSection()
        self.main_dir_label = QtWidgets.QLabel('Group Name:')
        self.main_dir_edit = QtWidgets.QLineEdit()
        self.full_path_header = QtWidgets.QLabel('Full Path:')
        self.full_path_label = QtWidgets.QLabel()
        self.show_advanced_settings_btn = QtWidgets.QPushButton('Advanced')
        self.create_btn = QtWidgets.QPushButton('Create')

        # Set Widget Properties
        self.all_time = time.localtime()
        self.advanced_settings_gb.hide()
        self.show_advanced_settings_btn.setCheckable(True)

        if previous_detector_settings is None:
            self.main_dir_edit.setText('GroupName')
            self.advanced_settings_gb.year_edit.setText(str(self.all_time.tm_year))
            self.advanced_settings_gb.cycle_edit.setText(str(self.get_cycle()))
        else:
            self.main_dir_edit.setText(previous_detector_settings['general']['base_dir'])
            self.advanced_settings_gb.year_edit.setText(previous_detector_settings['general']['year'])
            self.advanced_settings_gb.cycle_edit.setText(previous_detector_settings['general']['cycle'])

        # Connections
        self.create_btn.clicked.connect(self.create_btn_clicked)
        self.main_dir_edit.textChanged.connect(self.update_all_full_paths)
        self.advanced_settings_gb.advancedSettingsChanged.connect(self.update_all_full_paths)
        self.show_advanced_settings_btn.clicked.connect(self.show_advanced_settings_btn_clicked)

        # Set Layout
        self.vbox = QtWidgets.QVBoxLayout()

        self.grid_layout_general = QtWidgets.QGridLayout()
        self.grid_layout_general.addWidget(self.main_dir_label, 0, 0, 1, 1)
        self.grid_layout_general.addWidget(self.main_dir_edit, 0, 1, 1, 3)
        self.grid_layout_general.addWidget(self.full_path_header, 1, 0, 1, 1)
        self.grid_layout_general.addWidget(self.full_path_label, 1, 1, 1, 3)
        self.grid_layout_general.addWidget(self.show_advanced_settings_btn, 2, 0, 1, 1)
        self.grid_layout_general.setVerticalSpacing(12)

        self.vbox.addLayout(self.grid_layout_general)
        self.vbox.addWidget(self.advanced_settings_gb)
        for detector in self.chosen_detectors:
            self.vbox.addWidget(self.chosen_detectors[detector])
        self.vbox.addWidget(self.create_btn)

        self.setLayout(self.vbox)
        self.load_folder_maker_settings()
        self.update_all_full_paths()

    def get_cycle(self):
        if 1 <= self.all_time.tm_mon <= 4:
            return 1
        elif 5 <= self.all_time.tm_mon <= 9:
            return 2
        else:
            return 3

    def update_all_full_paths(self):
        root_dir = self.advanced_settings_gb.root_format_edit.text().format(
            year=self.advanced_settings_gb.year_edit.text(),
            cycle=self.advanced_settings_gb.cycle_edit.text()
        )
        self.base_dir = os.path.join(root_dir, self.main_dir_edit.text())
        self.full_path_label.setText(self.base_dir)

        for detector in self.chosen_detectors:
            if self.chosen_detectors[detector].update_cb.isChecked():
                self.chosen_detectors[detector].base_dir = self.base_dir
                self.chosen_detectors[detector].value_changed()

    def show_advanced_settings_btn_clicked(self):
        if self.advanced_settings_gb.isVisible():
            self.advanced_settings_gb.hide()
        else:
            self.advanced_settings_gb.show()

    def create_btn_clicked(self):
        self.check_and_make_dirs()
        self.update_epics()
        self.update_detector_settings()
        self.save_folder_maker_settings()
        if not self.log_running:
            self.caller.choose_file_name_le.setText('log_' +
                                                    str(time.localtime().tm_year) + '_' +
                                                    str(time.localtime().tm_mon).zfill(2) + '_' +
                                                    str(time.localtime().tm_mday).zfill(2) +
                                                    '.txt')
            self.caller.choose_dir = str(self.base_dir).rsplit('\\', 1)[0]
            self.caller.set_choose_dir_label()

        self.caller.folder_maker_settings = self.new_settings.copy()

    def check_and_make_dirs(self):
        base_dir = str(self.base_dir)
        self.check_and_make_one_dir(base_dir, 'Created base directory: ')

        for detector in self.chosen_detectors:
            full_path = self.chosen_detectors[detector].full_path
            path, file = os.path.split(full_path)
            self.check_and_make_one_dir(path, 'Created path for ' + detector + ': ')

    def check_and_make_one_dir(self, full_path, message):
        if not os.path.isdir(full_path):
            os.makedirs(full_path)
            print(message + full_path)
        else:
            print(full_path + ' already exists')

    def update_epics(self):
        for detector in self.chosen_detectors:
            soft_link = detectors[detector].get('soft_link', False)
            if not soft_link:
                full_path = self.chosen_detectors[detector].full_path
                path, file = os.path.split(full_path)
                file = file.rsplit('_', 1)[0]
            else:
                main_dir = str(self.main_dir_edit.text())
                rel_dir = str(self.chosen_detectors[detector].rel_dir_edit.text())
                path = (soft_link + main_dir + '\\' + rel_dir).replace('\\', '/')
                file = str(self.chosen_detectors[detector].base_name_edit.text())
            number = str(self.chosen_detectors[detector].num_edit.text())

            caput(detectors[detector]['file_path'], path)
            caput(detectors[detector]['file_name'], file)
            caput(detectors[detector]['file_number'], number)

    def update_detector_settings(self):
        for detector in self.chosen_detectors:
            self.new_settings[detector] = {}
            self.new_settings[detector]['detector_name'] = detector
            self.new_settings[detector]['base_dir'] = self.chosen_detectors[detector].base_dir
            self.new_settings[detector]['update_toggle'] = self.chosen_detectors[detector].update_cb.isChecked()
            # self.new_settings[detector]['detector_label'] = self.chosen_detectors[detector].detector_label.text()
            self.new_settings[detector]['rel_dir_edit'] = self.chosen_detectors[detector].rel_dir_edit.text()
            self.new_settings[detector]['base_name_edit'] = self.chosen_detectors[detector].base_name_edit.text()
            self.new_settings[detector]['num_edit'] = self.chosen_detectors[detector].num_edit.text()
            self.chosen_detectors[detector].update_path()
        self.new_settings['general'] = {}
        self.new_settings['general']['base_dir'] = self.main_dir_edit.text()
        self.new_settings['general']['year'] = self.advanced_settings_gb.year_edit.text()
        self.new_settings['general']['cycle'] = self.advanced_settings_gb.cycle_edit.text()

    def load_folder_maker_settings(self):
        year = self.folder_maker_settings.value('year', defaultValue=None)
        if year is None:
            self.advanced_settings_gb.year_edit.setText(self.all_time.tm_year)
        else:
            self.advanced_settings_gb.year_edit.setText(year)

        cycle = self.folder_maker_settings.value('cycle', defaultValue=None)
        if cycle is None:
            self.advanced_settings_gb.cycle_edit.setText(self.get_cycle())
        else:
            self.advanced_settings_gb.cycle_edit.setText(cycle)

        root_dir_format = self.folder_maker_settings.value('root_dir_format', defaultValue=None)
        if root_dir_format is None:
            self.advanced_settings_gb.root_format_edit.setText('')
        else:
            self.advanced_settings_gb.root_format_edit.setText(root_dir_format)

    def save_folder_maker_settings(self):
        self.folder_maker_settings.setValue('year', self.advanced_settings_gb.year_edit.text())
        self.folder_maker_settings.setValue('cycle', self.advanced_settings_gb.cycle_edit.text())
        self.folder_maker_settings.setValue('root_dir_format', self.advanced_settings_gb.root_format_edit.text())


class AdvancedSettingsSection(QtWidgets.QGroupBox):

    advancedSettingsChanged = QtCore.Signal()

    def __init__(self):
        super(AdvancedSettingsSection, self).__init__()
        self.create_widgets()
        self.setup_connections()
        self.set_layout()

    def create_widgets(self):
        self.year_label = QtWidgets.QLabel('Year')
        self.year_edit = QtWidgets.QLineEdit()
        self.cycle_label = QtWidgets.QLabel('Cycle')
        self.cycle_edit = QtWidgets.QLineEdit()
        self.root_format_label = QtWidgets.QLabel('Root Format')
        self.root_format_edit = QtWidgets.QLineEdit()

    def setup_connections(self):
        self.year_edit.editingFinished.connect(self.emit_advanced_settings_changed)
        self.cycle_edit.editingFinished.connect(self.emit_advanced_settings_changed)
        self.root_format_edit.editingFinished.connect(self.emit_advanced_settings_changed)

    def set_layout(self):
        self.grid_layout_section = QtWidgets.QGridLayout()
        self.grid_layout_section.addWidget(self.year_label, 0, 0, 1, 1)
        self.grid_layout_section.addWidget(self.year_edit, 0, 1, 1, 1)
        self.grid_layout_section.addWidget(self.cycle_label, 0, 2, 1, 1)
        self.grid_layout_section.addWidget(self.cycle_edit, 0, 3, 1, 1)
        self.grid_layout_section.addWidget(self.root_format_label, 1, 0, 1, 1)
        self.grid_layout_section.addWidget(self.root_format_edit, 1, 1, 1, 3)
        self.grid_layout_section.setVerticalSpacing(12)
        self.setLayout(self.grid_layout_section)

    def emit_advanced_settings_changed(self):
        self.advancedSettingsChanged.emit()


class DetectorSection(QtWidgets.QGroupBox):
    def __init__(self, detector, parameters=None, parent=None):
        super(DetectorSection, self).__init__(parent)
        self.detector = detector
        if parameters is None:
            self.base_dir = ''
        else:
            self.base_dir = parameters['base_dir']
        self.create_widgets()
        self.set_widget_properties(parameters)
        self.setup_connections()
        self.set_layout()
        self.value_changed()

    def create_widgets(self):
        self.update_label = QtWidgets.QLabel('Link to basedir?')
        self.update_cb = QtWidgets.QCheckBox()
        self.detector_label = QtWidgets.QLabel()
        self.rel_dir_edit = QtWidgets.QLineEdit()
        self.base_name_edit = QtWidgets.QLineEdit()
        self.num_edit = QtWidgets.QLineEdit()
        self.full_path_label = QtWidgets.QLabel()

    def set_widget_properties(self, parameters=None):
        if parameters is None:
            self.rel_dir_edit.setText(detectors[self.detector].get('default_rel_dir', ''))
            self.base_name_edit.setText(detectors[self.detector].get('default_base_name', ''))
            self.num_edit.setText('1')
            self.update_cb.setChecked(True)
        else:
            self.detector = parameters['detector_name']
            self.rel_dir_edit.setText(parameters['rel_dir_edit'])
            self.base_name_edit.setText(parameters['base_name_edit'])
            self.num_edit.setText(parameters['num_edit'])
            self.update_cb.setChecked(parameters['update_toggle'])
        self.detector_label.setText("<b>" + self.detector + "</b>" + ' directory / basename / #:')
        self.full_path_label_font = QtGui.QFont()
        self.full_path_label_font.setBold(True)
        self.full_path_label.setFont(self.full_path_label_font)

    def setup_connections(self):
        self.rel_dir_edit.textChanged.connect(self.value_changed)
        self.base_name_edit.textChanged.connect(self.value_changed)
        self.num_edit.textChanged.connect(self.value_changed)

    def set_layout(self):
        self.grid_layout_section = QtWidgets.QGridLayout()
        self.grid_layout_section.addWidget(self.update_label, 0, 0, 1, 1)
        self.grid_layout_section.addWidget(self.update_cb, 0, 1, 1, 1)
        self.grid_layout_section.addWidget(self.detector_label, 1, 0, 1, 1)
        self.grid_layout_section.addWidget(self.rel_dir_edit, 1, 1, 1, 1)
        self.grid_layout_section.addWidget(self.base_name_edit, 1, 2, 1, 1)
        self.grid_layout_section.addWidget(self.num_edit, 1, 3, 1, 1)
        self.grid_layout_section.addWidget(self.full_path_label, 2, 0, 1, 4)
        self.grid_layout_section.setVerticalSpacing(12)
        self.setLayout(self.grid_layout_section)

    def value_changed(self):
        if not self.sender() == self.rel_dir_edit and str(self.base_name_edit.text()) == 'LaB6':
            self.rel_dir_edit.setText('LaB6')
        current_dir = os.path.join(self.base_dir, str(self.rel_dir_edit.text()))
        if not self.sender() == self.num_edit:
            next_num = self.find_next_number(str(current_dir + '\\' + self.base_name_edit.text() + '_'))
            self.num_edit.setText(str(next_num))
        self.update_path()

    def find_next_number(self, base_name):
        file_list = glob.glob(base_name + '*.*')
        fmax = 0
        for file in file_list:
            fnum = int(file.rsplit('.', 1)[0].rsplit('_', 1)[-1])
            if fnum > fmax:
                fmax = fnum
        return int(fmax)+1

    def update_path(self):
        self.full_path = os.path.join(self.base_dir, str(self.rel_dir_edit.text()),
                                      str(self.base_name_edit.text()) + '_' + str(self.num_edit.text()).zfill(3))

        self.full_path_label.setText(self.full_path)
        if os.path.isdir(self.full_path.rsplit('\\', 1)[0]):
            self.full_path_label.setStyleSheet("QLabel {color:green}")
        else:
            self.full_path_label.setStyleSheet("QLabel {color:red}")


def main():
    pass

if __name__ == '__main__':
    main()
    app = QtWidgets.QApplication(sys.argv)
    main_window = FolderMaker()
    sys.exit(app.exec_())
