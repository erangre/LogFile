import time
import os
import sys
import glob
from epics import caput
from epics import caget
from connect_epics import epics_prepare as epp
from qtpy import QtGui, QtCore, QtWidgets
from detectors import detectors
import collections

class FolderMaker(QtWidgets.QWidget):
    def __init__(self, parent=None, detectors=None):
        super(FolderMaker, self).__init__()
        self.caller = parent
        # self.use_marccd = use_marccd
        # self.use_pil3 = use_pil3
        self.setWindowTitle('Create folders and setup')
        self.setWindowIcon(QtGui.QIcon('icons/folder.jpg'))
        self.show()
        self.setGeometry(100, 100, 300, 200)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.chosen_detectors = collections.OrderedDict()
        for detector in detectors:
            self.chosen_detectors[detector] = DetectorSection(detector)

        # Create Widgets
        self.year_label = QtWidgets.QLabel()
        self.year_edit = QtWidgets.QLineEdit()
        self.cycle_label = QtWidgets.QLabel()
        self.cycle_edit = QtWidgets.QLineEdit()
        self.main_dir_label = QtWidgets.QLabel()
        self.main_dir_edit = QtWidgets.QLineEdit()
        self.create_btn = QtWidgets.QPushButton('Create')

        # Set Widget Properties
        self.all_time = time.localtime()
        self.year_label.setText('Year:')
        self.year_edit.setText(str(self.all_time.tm_year))
        self.cycle_label.setText('Cycle:')
        self.cycle_edit.setText(str(self.get_cycle()))
        self.main_dir_label.setText('Main Directory:')
        self.main_dir_edit.setText('GroupName')

        # Connections
        self.create_btn.clicked.connect(self.create_btn_clicked)
        self.year_edit.textChanged.connect(self.update_all_full_paths)
        self.cycle_edit.textChanged.connect(self.update_all_full_paths)
        self.main_dir_edit.textChanged.connect(self.update_all_full_paths)

        # Set Layout
        self.vbox = QtWidgets.QVBoxLayout()

        self.grid_layout_general = QtWidgets.QGridLayout()
        self.grid_layout_general.addWidget(self.year_label, 0, 0, 1, 1)
        self.grid_layout_general.addWidget(self.year_edit, 0, 1, 1, 1)
        self.grid_layout_general.addWidget(self.cycle_label, 0, 2, 1, 1)
        self.grid_layout_general.addWidget(self.cycle_edit, 0, 3, 1, 1)
        self.grid_layout_general.addWidget(self.main_dir_label, 1, 0, 1, 1)
        self.grid_layout_general.addWidget(self.main_dir_edit, 1, 1, 1, 3)
        self.grid_layout_general.setVerticalSpacing(12)

        self.vbox.addLayout(self.grid_layout_general)
        for detector in self.chosen_detectors:
            self.vbox.addWidget(self.chosen_detectors[detector])
        self.vbox.addWidget(self.create_btn)

        self.setLayout(self.vbox)

        # self.base_dir = 'T:\\dac_user\\' + self.year_edit.text() + '\\IDD_' + self.year_edit.text() + '-' + \
        #                 self.cycle_edit.text() + '\\' + self.main_dir_edit.text() + '\\'

        self.update_all_full_paths()

    def get_cycle(self):
        if 1 <= self.all_time.tm_mon <= 4:
            return 1
        elif 5 <= self.all_time.tm_mon <= 9:
            return 2
        else:
            return 3

    def update_all_full_paths(self):
        self.base_dir = 'T:\\dac_user\\' + self.year_edit.text() + '\\IDD_' + self.year_edit.text() + '-' + \
                        self.cycle_edit.text() + '\\' + self.main_dir_edit.text() + '\\'
        for detector in self.chosen_detectors:
            self.chosen_detectors[detector].base_dir = self.base_dir
            self.chosen_detectors[detector].value_changed()

    def create_btn_clicked(self):
        self.check_dirs()
        # self.update_epics()
        # if self.caller:
        #     self.caller.choose_dir = str(self.base_dir).rsplit('\\', 1)[0]
        #     self.caller.set_choose_dir_label()

    def check_dirs(self):
        base_dir = str(self.base_dir)
        self.check_one_dir(base_dir, 'Created base directory: ')

        for detector in self.chosen_detectors:
            full_path = self.chosen_detectors[detector].full_path
            path, file = os.path.split(full_path)
            self.check_one_dir(path, 'Created path for ' + detector + ': ')

        # full_dir_temperature = str(self.temperature_full_path).rsplit('\\', 1)[0]
        # full_dir_images = str(self.image_dn_full_path).rsplit('\\', 1)[0]
        # full_dir_LaB6 = str(base_dir + 'LaB6\\')
        # full_dir_patterns = str(base_dir + 'patterns\\')

        # self.check_one_dir(full_dir_temperature, 'Created T dir: ')
        # self.check_one_dir(full_dir_images, 'Created Image dir: ')
        # self.check_one_dir(full_dir_LaB6, 'Created dir for LaB6: ')
        # self.check_one_dir(full_dir_patterns, 'Created dir for integrated patterns: ')

    def check_one_dir(self, full_path, message):
        if not os.path.isdir(full_path):
            os.makedirs(full_path)
            print(message + full_path)
        else:
            print(full_path + ' already exists')

    def update_epics(self):
        full_dir_temperature = str(self.temperature_full_path).rsplit('\\', 1)[0]
        full_dir_images = str(self.image_dn_full_path).rsplit('\\', 1)[0]
        main_dir = str(self.main_dir_edit.text())
        ccd_dir = ('\\DAC\\' + main_dir).replace('\\', '/')
        if self.xrd_base_edit.text() == 'LaB6':
            ccd_dir = ccd_dir + '/LaB6'
        if self.use_marccd:
            caput(epp['CCD_File_Path'], ccd_dir)
            caput(epp['XRD_Base_Name'], str(self.xrd_base_edit.text()))
            caput(epp['XRD_Number'], str(self.xrd_num_edit.text()))
        if self.use_pil3:
            caput(epp['pXRD_File_Path'], ccd_dir)
            caput(epp['pXRD_Base_Name'], str(self.xrd_base_edit.text()))
            caput(epp['pXRD_Number'], str(self.xrd_num_edit.text()))

        caput(epp['T_File_Path'], full_dir_temperature)
        caput(epp['T_File_Name'], str(self.temperature_base_edit.text()))
        caput(epp['T_File_Number'], str(self.temperature_num_edit.text()))

        caput(epp['Image_Dn_File_Path'], full_dir_images)
        caput(epp['Image_Dn_File_Name'], str(self.image_dn_base_edit.text()))
        caput(epp['Image_Dn_Number'], str(self.image_dn_num_edit.text()))
        caput(epp['Image_Up_File_Path'], full_dir_images)
        caput(epp['Image_Up_File_Name'], str(self.image_up_base_edit.text()))
        caput(epp['Image_Up_Number'], str(self.image_up_num_edit.text()))
        caput(epp['Image_ms_File_Path'], full_dir_images)
        caput(epp['Image_ms_File_Name'], str(self.image_ms_base_edit.text()))
        caput(epp['Image_ms_Number'], str(self.image_ms_num_edit.text()))

    # def find_next_number(self, base_name):
    #     file_list = glob.glob(base_name + '*.*')
    #     fmax = 0
    #     for file in file_list:
    #         fnum = int(file.rsplit('.', 1)[0].rsplit('_', 1)[-1])
    #         if fnum > fmax:
    #             fmax = fnum
    #     return int(fmax)+1


class DetectorSection(QtWidgets.QGroupBox):
    def __init__(self, detector,  parent=None):
        super(DetectorSection, self).__init__(parent)
        self.detector = detector
        self.base_dir = ''
        self.create_widgets()
        self.set_widget_properties()
        self.setup_connections()
        self.set_layout()
        self.set_initial_parameters()
        self.value_changed()

    def create_widgets(self):
        self.update_label = QtWidgets.QLabel('Auto Update?')
        self.update_cb = QtWidgets.QCheckBox()
        self.detector_label = QtWidgets.QLabel()
        self.rel_dir_edit = QtWidgets.QLineEdit()
        self.base_name_edit = QtWidgets.QLineEdit()
        self.num_edit = QtWidgets.QLineEdit()
        self.full_path_label = QtWidgets.QLabel()

    def set_widget_properties(self):
        self.detector_label.setText(self.detector + ' directory / basename / #:')
        self.rel_dir_edit.setText(detectors[self.detector].get('default_rel_dir', ''))
        self.base_name_edit.setText(detectors[self.detector].get('default_base_name', ''))
        self.num_edit.setText('1')
        self.update_cb.setChecked(True)

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

    def set_initial_parameters(self):
        pass

    def value_changed(self):
        if not self.sender() == self.rel_dir_edit and str(self.base_name_edit.text()) == 'LaB6':
            self.rel_dir_edit.setText('LaB6')
        # current_dir = self.base_dir + '\\' + str(self.rel_dir_edit.text()) + '\\'
        current_dir = os.path.join(self.base_dir, str(self.rel_dir_edit.text()))
        if not self.sender() == self.num_edit:
            next_num = self.find_next_number(str(current_dir + self.base_name_edit.text() + '_'))
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
        # self.full_path = self.base_dir + self.rel_dir_edit.text() + '\\' + \
        #                                  self.base_name_edit.text() + '_' + \
        #                                  str(self.num_edit.text()).zfill(3)
        self.full_path = os.path.join(self.base_dir, str(self.rel_dir_edit.text()),
                                      str(self.base_name_edit.text()) + '_' + str(self.num_edit.text()).zfill(3))

        self.full_path_label.setText(self.full_path)


def main():
    pass

if __name__ == '__main__':
    main()
    app = QtWidgets.QApplication(sys.argv)
    main_window = FolderMaker()
    sys.exit(app.exec_())
