import time
import os
import sys
import glob
from epics import caput
from epics import caget
from connect_epics import epics_prepare as epp
from PyQt4 import QtGui, QtCore


class FolderMaker(QtGui.QWidget):
    def __init__(self, parent=None):
        super(FolderMaker, self).__init__()
        self.caller = parent
        self.setWindowTitle('Create folders and setup')
        self.setWindowIcon(QtGui.QIcon('icons/folder.jpg'))
        self.show()
        self.setGeometry(100, 100, 300, 200)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

        # Create Widgets
        self.year_label = QtGui.QLabel()
        self.year_edit = QtGui.QLineEdit()
        self.cycle_label = QtGui.QLabel()
        self.cycle_edit = QtGui.QLineEdit()
        self.main_dir_label = QtGui.QLabel()
        self.main_dir_edit = QtGui.QLineEdit()
        self.xrd_label = QtGui.QLabel()
        self.xrd_base_edit = QtGui.QLineEdit()
        self.xrd_num_edit = QtGui.QLineEdit()
        self.xrd_full_path_label = QtGui.QLabel()
        self.temperature_label = QtGui.QLabel()
        self.temperature_dir_edit = QtGui.QLineEdit()
        self.temperature_base_edit = QtGui.QLineEdit()
        self.temperature_num_edit = QtGui.QLineEdit()
        self.temperature_full_path_label = QtGui.QLabel()
        self.image_dir_label = QtGui.QLabel()
        self.image_dir_edit = QtGui.QLineEdit()
        self.image_dn_label = QtGui.QLabel()
        self.image_dn_base_edit = QtGui.QLineEdit()
        self.image_dn_num_edit = QtGui.QLineEdit()
        self.image_up_label = QtGui.QLabel()
        self.image_up_base_edit = QtGui.QLineEdit()
        self.image_up_num_edit = QtGui.QLineEdit()
        self.image_ms_label = QtGui.QLabel()
        self.image_ms_base_edit = QtGui.QLineEdit()
        self.image_ms_num_edit = QtGui.QLineEdit()
        self.image_dn_full_path_label = QtGui.QLabel()
        self.image_up_full_path_label = QtGui.QLabel()
        self.image_ms_full_path_label = QtGui.QLabel()
        self.create_btn = QtGui.QPushButton('Create')

        # Set Widget Properties
        self.all_time = time.localtime()
        self.year_label.setText('Year:')
        self.year_edit.setText(str(self.all_time.tm_year))
        self.cycle_label.setText('Cycle:')
        self.cycle_edit.setText(str(self.get_cycle()))
        self.main_dir_label.setText('Main Directory:')
        self.main_dir_edit.setText('GroupName')

        self.xrd_label.setText('XRD basename / #:')
        self.xrd_base_edit.setText('LaB6')
        self.xrd_num_edit.setText('1')

        self.temperature_label.setText('Temperature Directory / basename / #')
        self.temperature_dir_edit.setText('T')
        self.temperature_base_edit.setText('r')
        self.temperature_num_edit.setText('1')

        self.image_dir_label.setText('Image Directory:')
        self.image_dir_edit.setText('Images')
        self.image_dn_label.setText('Downstream basename / #')
        self.image_dn_base_edit.setText('ds_image')
        self.image_dn_num_edit.setText('1')
        self.image_up_label.setText('Upstream basename / #')
        self.image_up_base_edit.setText('us_image')
        self.image_up_num_edit.setText('1')
        self.image_ms_label.setText('Microscope basename / #')
        self.image_ms_base_edit.setText('ms_image')
        self.image_ms_num_edit.setText('1')

        # Connections
        self.create_btn.clicked.connect(self.create_btn_clicked)
        self.year_edit.textChanged.connect(self.update_all_full_paths)
        self.cycle_edit.textChanged.connect(self.update_all_full_paths)
        self.main_dir_edit.textChanged.connect(self.update_all_full_paths)
        self.xrd_base_edit.textChanged.connect(self.xrd_changed)
        self.xrd_num_edit.textChanged.connect(self.xrd_changed)
        self.temperature_dir_edit.textChanged.connect(self.temperature_changed)
        self.temperature_base_edit.textChanged.connect(self.temperature_changed)
        self.temperature_num_edit.textChanged.connect(self.temperature_changed)
        self.image_dir_edit.textChanged.connect(self.image_changed)
        self.image_dn_base_edit.textChanged.connect(self.image_changed)
        self.image_up_base_edit.textChanged.connect(self.image_changed)
        self.image_dn_num_edit.textChanged.connect(self.image_changed)
        self.image_up_num_edit.textChanged.connect(self.image_changed)
        self.image_ms_base_edit.textChanged.connect(self.image_changed)
        self.image_ms_num_edit.textChanged.connect(self.image_changed)

        # Set Layout
        self.grid_layout_folders = QtGui.QGridLayout()
        self.grid_layout_folders.addWidget(self.year_label, 0, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.year_edit, 0, 1, 1, 1)
        self.grid_layout_folders.addWidget(self.cycle_label, 0, 2, 1, 1)
        self.grid_layout_folders.addWidget(self.cycle_edit, 0, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.main_dir_label, 1, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.main_dir_edit, 1, 1, 1, 3)

        self.grid_layout_folders.addWidget(self.xrd_label, 2, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.xrd_base_edit, 2, 1, 1, 2)
        self.grid_layout_folders.addWidget(self.xrd_num_edit, 2, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.xrd_full_path_label, 3, 0, 1, 4)

        self.grid_layout_folders.addWidget(self.temperature_label, 4, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.temperature_dir_edit, 4, 1, 1, 1)
        self.grid_layout_folders.addWidget(self.temperature_base_edit, 4, 2, 1, 1)
        self.grid_layout_folders.addWidget(self.temperature_num_edit, 4, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.temperature_full_path_label, 5, 0, 1, 4)

        self.grid_layout_folders.addWidget(self.image_dir_label, 6, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.image_dir_edit, 6, 1, 1, 2)
        self.grid_layout_folders.addWidget(self.image_dn_label, 7, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.image_dn_base_edit, 7, 1, 1, 2)
        self.grid_layout_folders.addWidget(self.image_dn_num_edit, 7, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.image_dn_full_path_label, 8, 0, 1, 4)
        self.grid_layout_folders.addWidget(self.image_up_label, 9, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.image_up_base_edit, 9, 1, 1, 2)
        self.grid_layout_folders.addWidget(self.image_up_num_edit, 9, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.image_up_full_path_label, 10, 0, 1, 4)
        self.grid_layout_folders.addWidget(self.image_ms_label, 11, 0, 1, 1)
        self.grid_layout_folders.addWidget(self.image_ms_base_edit, 11, 1, 1, 2)
        self.grid_layout_folders.addWidget(self.image_ms_num_edit, 11, 3, 1, 1)
        self.grid_layout_folders.addWidget(self.image_ms_full_path_label, 12, 0, 1, 4)

        self.grid_layout_folders.addWidget(self.create_btn, 13, 0, 1, 4)

        self.grid_layout_folders.setVerticalSpacing(12)
        self.setLayout(self.grid_layout_folders)

        self.base_dir = 'T:\\dac_user\\' + self.year_edit.text() + '\\IDD_' + self.year_edit.text() + '-' + \
                        self.cycle_edit.text() + '\\' + self.main_dir_edit.text() + '\\'

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
        self.xrd_changed()
        self.temperature_changed()
        self.image_changed()
        # self.update_xrd_path()
        # self.update_temperature_path()
        # self.update_images_path()

    def xrd_changed(self):
        if not self.sender() == self.xrd_num_edit:
            next_num = self.find_next_number(str(self.base_dir + self.xrd_base_edit.text() + '_'))
            self.xrd_num_edit.setText(str(next_num))
        self.update_xrd_path()

    def temperature_changed(self):
        temperature_dir = self.base_dir + '\\' + self.temperature_dir_edit.text() + '\\'
        if not self.sender() == self.temperature_num_edit:
            next_num = self.find_next_number(str(temperature_dir + self.temperature_base_edit.text() + '_'))
            self.temperature_num_edit.setText(str(next_num))
        self.update_temperature_path()

    def image_changed(self):
        image_dir = self.base_dir + '\\' + self.image_dir_edit.text() + '\\'
        if self.sender() == self.image_dir_edit or self.sender() == self.main_dir_edit:
            next_num = self.find_next_number(str(image_dir + self.image_up_base_edit.text() + '_'))
            self.image_up_num_edit.setText(str(next_num))
            next_num = self.find_next_number(str(image_dir + self.image_dn_base_edit.text() + '_'))
            self.image_dn_num_edit.setText(str(next_num))
            next_num = self.find_next_number(str(image_dir + self.image_ms_base_edit.text() + '_'))
            self.image_ms_num_edit.setText(str(next_num))
        elif self.sender() == self.image_dn_base_edit:
            next_num = self.find_next_number(str(image_dir + self.image_dn_base_edit.text() + '_'))
            self.image_dn_num_edit.setText(str(next_num))
        elif self.sender() == self.image_up_base_edit:
            next_num = self.find_next_number(str(image_dir + self.image_up_base_edit.text() + '_'))
            self.image_up_num_edit.setText(str(next_num))
        elif self.sender() == self.image_ms_base_edit:
            next_num = self.find_next_number(str(image_dir + self.image_ms_base_edit.text() + '_'))
            self.image_ms_num_edit.setText(str(next_num))
        self.update_images_path()

    def update_xrd_path(self):
        self.xrd_full_path = self.base_dir + self.xrd_base_edit.text() + '_' + str(self.xrd_num_edit.text()).zfill(3)
        self.xrd_full_path_label.setText(self.xrd_full_path)

    def update_temperature_path(self):
        self.temperature_full_path = self.base_dir + self.temperature_dir_edit.text() + '\\' + \
                                     self.temperature_base_edit.text() + '_' + \
                                     str(self.temperature_num_edit.text()).zfill(3)
        self.temperature_full_path_label.setText(self.temperature_full_path)

    def update_images_path(self):
        self.image_dn_full_path = self.base_dir + self.image_dir_edit.text() + '\\' + \
                                     self.image_dn_base_edit.text() + '_' + str(self.image_dn_num_edit.text()).zfill(3)
        self.image_dn_full_path_label.setText(self.image_dn_full_path)

        self.image_up_full_path = self.base_dir + self.image_dir_edit.text() + '\\' + \
                                     self.image_up_base_edit.text() + '_' + str(self.image_up_num_edit.text()).zfill(3)
        self.image_up_full_path_label.setText(self.image_up_full_path)

        self.image_ms_full_path = self.base_dir + self.image_dir_edit.text() + '\\' + \
                                     self.image_ms_base_edit.text() + '_' + str(self.image_ms_num_edit.text()).zfill(3)
        self.image_ms_full_path_label.setText(self.image_ms_full_path)

    def create_btn_clicked(self):
        self.check_dirs()
        self.update_epics()
        if self.caller:
            self.caller.choose_dir = str(self.base_dir).rsplit('\\', 1)[0]
            self.caller.set_choose_dir_label()

    def check_dirs(self):
        base_dir = str(self.base_dir)
        full_dir_temperature = str(self.temperature_full_path).rsplit('\\', 1)[0]
        full_dir_images = str(self.image_dn_full_path).rsplit('\\', 1)[0]
        full_dir_LaB6 = str(base_dir + 'LaB6\\')
        full_dir_patterns = str(base_dir + 'patterns\\')

        self.check_one_dir(base_dir, 'Created base directory: ')
        self.check_one_dir(full_dir_temperature, 'Created T dir: ')
        self.check_one_dir(full_dir_images, 'Created Image dir: ')
        self.check_one_dir(full_dir_LaB6, 'Created dir for LaB6: ')
        self.check_one_dir(full_dir_patterns, 'Created dir for integrated patterns: ')

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

        caput(epp['CCD_File_Path'], ccd_dir)
        caput(epp['XRD_Base_Name'], str(self.xrd_base_edit.text()))
        caput(epp['XRD_Number'], str(self.xrd_num_edit.text()))
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

    def find_next_number(self, base_name):
        file_list = glob.glob(base_name + '*.*')
        fmax = 0
        for file in file_list:
            fnum = file.rsplit('.', 1)[0].rsplit('_', 1)[-1]
            if fnum > fmax:
                fmax = fnum
        return int(fmax)+1


def main():
    pass

if __name__ == '__main__':
    main()
    app = QtGui.QApplication(sys.argv)
    main_window = FolderMaker()
    sys.exit(app.exec_())
