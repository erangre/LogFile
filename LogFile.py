"""
Created Mar 31 2016
Author: Eran Greenberg
"""

import sys, time, os
from PyQt4 import QtGui, QtCore
from epics import caput
from epics import caget
from connect_epics import epics_BG_config as ebgcfg, epics_prepare as epp
import epics_monitor
from FolderMaker import FolderMaker
import collections
from html_log import HtmlLogger

DEF_DIR = 'T:\\dac_user\\2016\\IDD_2016-1\\Test\\123'
tm_y = time.localtime().tm_year
tm_m = time.localtime().tm_mon
tm_d = time.localtime().tm_mday
DEF_FILE = 'log_' + str(tm_y) + str(tm_m).zfill(2) + str(tm_d).zfill(2) + '.txt'


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Setup App Window
        self.statusBar()
        self.setMinimumWidth(800)
        self.setWindowTitle('Log File Creator and Monitor')
        self.setWindowIcon(QtGui.QIcon('icons/google_notebook.png'))
        self.show()

        # Create Log Window
        self.log = LogWindow(self)
        self.log.move(0, 0)

        # Layout
        self.setCentralWidget(self.log)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.min_size = self.size()


class LogWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self._filter = Filter()
        self.motor_dict = {}

        self.choose_dir = DEF_DIR
        self.choose_file = DEF_FILE

        # Create Widgets
        self.label_fullpath = QtGui.QLabel(self)
        self.choose_dir_btn = QtGui.QPushButton('Choose Folder')
        self.choose_file_name_le = QtGui.QLineEdit()
        self.load_log_btn = QtGui.QPushButton('Load Log')
        self.label_start_time = QtGui.QLabel(self)
        self.label_end_time = QtGui.QLabel(self)
        self.setup_btn = QtGui.QPushButton('Setup')
        self.show_log_btn = QtGui.QPushButton('Log')
        self.comment_btn = QtGui.QPushButton('Comment')
        self.start_btn = QtGui.QPushButton('Start')
        self.stop_btn = QtGui.QPushButton('Stop')
        self.list_motor_short = QtGui.QListWidget(self)
        self.list_motor_names = QtGui.QListWidget(self)
        self.motor_load_btn = QtGui.QPushButton('Load')
        self.motor_save_btn = QtGui.QPushButton('Save')
        self.motor_remove_btn = QtGui.QPushButton('Remove')
        self.motor_clear_btn = QtGui.QPushButton('Clear')
        self.motor_add_btn = QtGui.QPushButton('Add')
        self.motor_rename_btn = QtGui.QPushButton('Rename')
        self.motor_move_up_btn = QtGui.QPushButton(u'\u2191')
        self.motor_move_dn_btn = QtGui.QPushButton(u'\u2193')
        self.collect_bg_btn = QtGui.QPushButton('Collect BG Files')
        self.create_folders_btn = QtGui.QPushButton('Create Folders')
        self.log_list = QtGui.QListWidget(self)
        self.splitter_log = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.log_table = QtGui.QTableWidget(self)
        self.view_image_btn = QtGui.QPushButton('Open Image')

        # Set Widget Properties
        self.choose_file_name_le.setText(self.choose_file)
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file)
        self.label_start_time.setText('Start Time: ')
        self.label_end_time.setText('End Time: ')
        for label_item in self.findChildren(QtGui.QLabel):
            label_item.setStyleSheet('background-color: white')
        self.setup_btn.setCheckable(True)
        self.show_log_btn.setCheckable(True)
        self.show_log_btn.hide()
        self.comment_btn.hide()
        self.comment_btn.setToolTip('Add a comment to the HTML log')
        self.stop_btn.setEnabled(False)
        self.list_motor_short.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.list_motor_names.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.motor_load_btn.setToolTip('Load does not clear the list')
        self.log_table.setColumnCount(2)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet("alternate-background-color: lightgrey;background-color: white")
        self.log_table.verticalHeader().setDefaultSectionSize(18)
        self.log_table.verticalHeader().hide()
        self.log_table.horizontalHeader().hide()

        # Set Layout
        self.vbox = QtGui.QVBoxLayout()      # Layout in vbox and hbox
        hbox_file = QtGui.QHBoxLayout()
        hbox_control = QtGui.QHBoxLayout()
        self.setup_motors_frame = QtGui.QFrame(self)
        self.setup_motors_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.grid_list_buttons = QtGui.QGridLayout()
        self.hbox_lists = QtGui.QHBoxLayout()
        vbox_log = QtGui.QVBoxLayout()
        hbox_log = QtGui.QHBoxLayout()
        self.log_frame = QtGui.QFrame(self)
        self.log_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        hbox_bottom_buttons = QtGui.QHBoxLayout()

        hbox_file.addWidget(self.label_fullpath)
        hbox_file.addStretch(1)
        hbox_file.addWidget(self.choose_dir_btn)
        hbox_file.addWidget(self.choose_file_name_le)
        hbox_file.addWidget(self.load_log_btn)

        hbox_control.addWidget(self.label_start_time)
        hbox_control.addStretch(1)
        hbox_control.addWidget(self.label_end_time)
        hbox_control.addStretch(1)
        hbox_control.addWidget(self.setup_btn)
        hbox_control.addWidget(self.comment_btn)
        hbox_control.addWidget(self.show_log_btn)
        hbox_control.addWidget(self.start_btn)
        hbox_control.addWidget(self.stop_btn)

        self.hbox_lists.addWidget(self.list_motor_short)
        self.hbox_lists.addWidget(self.list_motor_names)
        self.grid_list_buttons.addWidget(self.motor_move_up_btn, 0, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_move_dn_btn, 2, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_load_btn, 0, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_save_btn, 0, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_remove_btn, 1, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_clear_btn, 1, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_add_btn, 2, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.motor_rename_btn, 2, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.collect_bg_btn, 3, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.create_folders_btn, 3, 1, 1, 1)
        self.hbox_lists.addLayout(self.grid_list_buttons)

        self.splitter_log.addWidget(self.log_list)
        self.splitter_log.addWidget(self.log_table)
        hbox_log.addWidget(self.splitter_log)

        hbox_bottom_buttons.addWidget(self.view_image_btn)
        hbox_bottom_buttons.addStretch(1)

        vbox_log.addLayout(hbox_log)
        vbox_log.addLayout(hbox_bottom_buttons)
        self.log_frame.setLayout(vbox_log)
        self.log_frame.hide()

        self.vbox.addLayout(hbox_file)
        self.vbox.addLayout(hbox_control)
        self.setup_motors_frame.setLayout(self.hbox_lists)
        self.setup_motors_frame.hide()

        self.vbox.addWidget(self.setup_motors_frame)

        self.vbox.addWidget(self.log_frame)
        self.vbox.addStretch(1)
        self.setLayout(self.vbox)

        # Create connections
        self.choose_dir_btn.clicked.connect(self.choose_dir_btn_clicked)
        self.choose_file_name_le.returnPressed.connect(self.choose_file_name_le_changed)
        self.choose_file_name_le.installEventFilter(self._filter)
        self.load_log_btn.clicked.connect(self.load_previous_log)
        self.setup_btn.clicked.connect(self.toggle_setup_menu)
        self.show_log_btn.clicked.connect(self.toggle_show_log)
        self.comment_btn.clicked.connect(self.add_comment)
        self.start_btn.clicked.connect(self.start_logging)
        self.stop_btn.clicked.connect(self.stop_logging)
        self.motor_load_btn.clicked.connect(self.load_motor_list)
        self.motor_save_btn.clicked.connect(self.save_motor_list)
        self.motor_remove_btn.clicked.connect(self.remove_from_motor_list)
        self.motor_add_btn.clicked.connect(self.add_to_motor_list)
        self.motor_clear_btn.clicked.connect(self.clear_motor_list)
        self.motor_rename_btn.clicked.connect(self.rename_motor)
        self.list_motor_short.itemSelectionChanged.connect(self.change_names_selection)
        self.list_motor_short.doubleClicked.connect(self.rename_motor)
        self.list_motor_names.itemSelectionChanged.connect(self.change_short_selection)
        self.list_motor_names.doubleClicked.connect(self.edit_motor)
        self.motor_move_up_btn.clicked.connect(self.move_up_motors)
        self.motor_move_dn_btn.clicked.connect(self.move_dn_motors)
        self.view_image_btn.clicked.connect(self.open_image_file)
        self.collect_bg_btn.clicked.connect(self.collect_bgs)
        self.create_folders_btn.clicked.connect(self.run_create_folders_widget)

        # Setup App Window
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
        self.show()
        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.load_motor_list('base_motors.txt')

    def choose_dir_btn_clicked(self):
        CH_DIR_TEXT = 'Choose directory for saving log file'
        self.choose_dir = QtGui.QFileDialog.getExistingDirectory(self, CH_DIR_TEXT, DEF_DIR)
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file_name_le.text())

    def choose_file_name_le_changed(self):
        self.choose_file = self.choose_file_name_le.text()
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file)

    def file_name_le_change_back(self):  # in case enter wasn't pressed (to avoid accidental changes)
        self.choose_file_name_le.setText(self.choose_file)

    def load_previous_log(self):
        self.log_dict = collections.OrderedDict()
        load_log_name = QtGui.QFileDialog.getOpenFileName(self, 'Choose log file to view', '.', 'Text Files (*.txt)')
        if not load_log_name:
            msg = 'No Log File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        self.start_btn.setEnabled(False)
        self.setup_btn.setEnabled(False)
        self.choose_dir_btn.setEnabled(False)
        self.view_image_btn.setEnabled(False)
        try:
            self.log_list.itemSelectionChanged.disconnect()
        except Exception:
            pass

        self.log_list.clear()
        with open(load_log_name, 'r') as in_log_file:
            for curr_line in in_log_file:
                curr_line = curr_line.split('\n')[0]
                if 'Time' in curr_line:
                    self.headings = curr_line.split('\t')
                else:
                    line_data = curr_line.split('\t')
                    file_name = line_data[1]
                    self.log_dict[file_name] = collections.OrderedDict()
                    for col_name, col_data in zip(self.headings, line_data):
                        self.log_dict[file_name][col_name] = col_data
                    self.log_list.insertItem(0, file_name)
        if not self.log_frame.isVisible():
            self.toggle_show_log()
        self.log_list.itemSelectionChanged.connect(self.show_offline_info)

        msg = 'Loaded log file ' + load_log_name
        self.parent().statusBar().showMessage(msg)

    def toggle_setup_menu(self):
        self.setup_motors_frame.setVisible(not self.setup_motors_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        if not self.setup_motors_frame.isVisible():
            self.parent().setMinimumSize(self.parent().min_size)
            self.parent().resize(self.parent().minimumSize())

    def toggle_show_log(self):
        self.log_frame.setVisible(not self.log_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        # print self.parent().sizeHint()
        if not self.log_frame.isVisible():
            self.parent().setMinimumSize(self.parent().min_size)
            self.parent().resize(self.parent().minimumSize())

    def start_logging(self):
        f_time = time.asctime()
        self.label_start_time.setText('Start Time: ' + f_time)
        self.start_btn.setEnabled(False)
        self.load_log_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.setup_btn.hide()
        if self.setup_btn.isChecked():
            self.setup_btn.click()
        self.show_log_btn.show()
        self.comment_btn.show()
        self.choose_dir_btn.setEnabled(False)
        self.choose_file_name_le.setEnabled(False)

        full_path = self.label_fullpath.text()
        self.log_file = open(full_path, 'a')
        self.write_headings()
        self.log_file.flush()

        self.set_enabled_hbox_lists(False)
        msg = 'Started logging to: ' + full_path
        self.parent().statusBar().showMessage(msg)
        self.log_list.itemSelectionChanged.connect(self.show_selected_info)
        self.log_list.clear()

        self.base_dir = caget(epp['CCD_File_Path'], as_string=True)
        self.html_logger = HtmlLogger(self)
        self.html_logger.start_html_logger()

        self.log_monitor = epics_monitor.StartMonitors(self)

    def stop_logging(self):
        f_time = time.asctime()
        self.label_end_time.setText('End Time: ' + f_time)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.show_log_btn.isChecked():
            self.show_log_btn.click()
        self.setup_btn.show()
        self.show_log_btn.hide()
        self.choose_dir_btn.setEnabled(True)
        self.comment_btn.hide()
        self.choose_file_name_le.setEnabled(True)

        self.log_file.close()
        self.log_monitor = epics_monitor.StopMonitors(self)
        msg = 'Stopped logging!'
        self.parent().statusBar().showMessage(msg)
        self.set_enabled_hbox_lists(True)
        self.log_list.itemSelectionChanged.disconnect()
        self.log_list.clear()
        self.load_log_btn.setEnabled(True)

    def set_enabled_hbox_lists(self, enable_mode):
        for ind in range(0, self.hbox_lists.count()):
            curr_item = self.hbox_lists.itemAt(ind)
            if type(curr_item) == QtGui.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)
        for ind in range(0, self.grid_list_buttons.count()):
            curr_item = self.grid_list_buttons.itemAt(ind)
            if type(curr_item) == QtGui.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)

    def write_headings(self):
        heading = 'Day_Date_Time_Year\tFile_Name\tDirectory\tExposure_Time_(sec)\t'
        self.list_motor_short.selectAll()
        for motor in self.list_motor_short.selectedItems():
            heading = heading + motor.text() + '\t'
        heading = heading + 'Comments' + '\n'
        self.log_file.write(heading)

    def collect_bgs(self):
        msg = 'Please input background exposure time'
        exp_time, ok = QtGui.QInputDialog.getDouble(self, 'Background collection', msg, 1, 1, 10)
        # print exp_time
        # print ok
        if ok:
            self.collect_T_bg(exp_time)
            self.collect_XRD_bg(exp_time)
            print 'Background collected'

    def collect_T_bg(self, exp_time):  # Image mode 2 is background, 0 is normal
        caput(ebgcfg['ds_light'], 0, wait=True)
        caput(ebgcfg['us_light'], 0, wait=True)
        caput(ebgcfg['T_change_image_mode'], 2, wait=True)
        detector_T = caget(ebgcfg['T_detector'], as_string=True)
        if detector_T == 'PIMAX_temperature':
            caput(ebgcfg['T_PIMAX_exposure_Time'], str(exp_time), wait=True)
        elif detector_T == 'PIXIS_Temperature':
            caput(ebgcfg['T_PIXIS_exposure_Time'], str(exp_time), wait=True)
        else:
            msg = 'Incorrect T detector - T not collected'
            self.parent().statusBar().showMessage(msg)
            return
        caput(ebgcfg['T_acquire'], 1, wait=True)
        caput(ebgcfg['T_change_image_mode'], 0, wait=True)
        msg = 'Collected T background'
        self.parent().statusBar().showMessage(msg)

    def collect_XRD_bg(self, exp_time):  # Frame Type 1 is background, 0 is normal
        caput(ebgcfg['XRD_frame_type'], 1, wait=True)
        caput(ebgcfg['XRD_acquire_time'], exp_time, wait=True)
        caput(ebgcfg['XRD_acquire_start'], 1, wait=True)
        caput(ebgcfg['XRD_frame_type'], 0, wait=True)
        msg = 'Collected XRD background'
        self.parent().statusBar().showMessage(msg)

    def load_motor_list(self, file_name=None):
        if not file_name or not os.path.isfile(file_name):
            load_name = QtGui.QFileDialog.getOpenFileName(self, 'Choose file name for loading motor list', '.',
                                                          'Text Files (*.txt)')
        else:
            load_name = file_name

        if not load_name:
            msg = 'No File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        with open(load_name, 'r') as in_file:
            for motor in in_file:
                row = motor.split(',')
                self.motor_dict[row[0]] = row[-1].split('\n')[0]
                self.list_motor_short.addItem(row[0])
                self.list_motor_names.addItem(row[1].split('\n')[0])
            msg = 'Loaded motor list from ' + load_name
            self.parent().statusBar().showMessage(msg)

    def save_motor_list(self):
        save_name = QtGui.QFileDialog.getSaveFileName(self, 'Choose file name for saving motor list', '.',
                                                      'Text Files (*.txt)')
        if not save_name:
            msg = 'No File Saved'
            self.parent().statusBar().showMessage(msg)
            return
        with open(save_name, 'w') as out_file:
            self.list_motor_short.selectAll()
            for motor in self.list_motor_short.selectedItems():
                row_ind = self.list_motor_short.row(motor)
                out_line = motor.text() + ',' + self.list_motor_names.item(row_ind).text() + '\n'
                out_file.write(out_line)
            msg = 'Saved motor list to ' + save_name
            self.parent().statusBar().showMessage(msg)

    def remove_from_motor_list(self):
        for motor in self.list_motor_short.selectedItems():
            self.remove_one_motor(motor)
            msg = 'Removed ' + motor.text().split('\t')[0] + ' from motor list'
            self.parent().statusBar().showMessage(msg)

    def remove_one_motor(self, motor):
        self.list_motor_names.takeItem(self.list_motor_short.row(motor))
        self.list_motor_short.takeItem(self.list_motor_short.row(motor))
        del self.motor_dict[str(motor.text())]

    def clear_motor_list(self):
        self.list_motor_short.clear()
        self.list_motor_names.clear()
        self.motor_dict = {}
        msg = 'Motor list cleared'
        self.parent().statusBar().showMessage(msg)

    def add_to_motor_list(self):
        short_name, ok_sn = QtGui.QInputDialog.getText(self, 'Add Motor to List', 'Provide short name for motor:')
        motor_name, ok_mn = QtGui.QInputDialog.getText(self, 'Add Motor to List', 'Provide Motor address:')
        if ok_sn and ok_mn:
            self.add_one_motor(short_name, motor_name)
            msg = 'Added ' + short_name + ' to motor list'
            self.parent().statusBar().showMessage(msg)

    def add_one_motor(self, short_name, motor_name):
        self.motor_dict[str(short_name)] = str(motor_name)
        self.list_motor_short.addItem(str(short_name))
        self.list_motor_names.addItem(str(motor_name))

    def rename_motor(self):
        for motor in self.list_motor_short.selectedItems():
            old_short_name = motor.text()
            row = self.list_motor_short.row(motor)
            motor_name = self.list_motor_names.item(row).text()
            message = 'Provide new short name for motor ' + old_short_name + ':'
            short_name, ok_sn = QtGui.QInputDialog.getText(self, 'Rename motor in List', message,
                                                           QtGui.QLineEdit.Normal, old_short_name)
            if ok_sn:
                del self.motor_dict[str(old_short_name)]
                self.list_motor_short.takeItem(self.list_motor_short.row(motor))
                self.list_motor_short.insertItem(row, str(short_name))
                self.motor_dict[str(short_name)] = str(motor_name)
                msg = 'Renamed ' + old_short_name + ' to ' + short_name + ' in motor list'
                self.parent().statusBar().showMessage(msg)

    def edit_motor(self):
        for motor in self.list_motor_names.selectedItems():
            old_motor_name = motor.text()
            row = self.list_motor_names.row(motor)
            motor_short = self.list_motor_short.item(row).text()
            message = 'Provide new PV for motor ' + motor_short + ':'
            motor_name, ok_sn = QtGui.QInputDialog.getText(self, 'Change PV', message,
                                                           QtGui.QLineEdit.Normal, old_motor_name)
            if ok_sn:
                self.motor_dict[str(motor_short)] = str(motor_name)
                self.list_motor_names.takeItem(self.list_motor_names.row(motor))
                self.list_motor_names.insertItem(row, str(motor_name))
                msg = 'Updated ' + motor_short + ' from ' + old_motor_name + ' to ' + motor_name + ' in motor list'
                self.parent().statusBar().showMessage(msg)

    def move_up_motors(self):
        sorted_motors = self.sort_selected_motors_by_row()
        for motor in sorted_motors:
            row = self.list_motor_short.row(motor)
            if row == 0:
                continue
            short_name = self.list_motor_short.takeItem(row)
            motor_name = self.list_motor_names.takeItem(row)
            self.list_motor_short.insertItem(row-1, short_name)
            self.list_motor_names.insertItem(row-1, motor_name)
            self.list_motor_short.setItemSelected(self.list_motor_short.item(row-1), True)

    def move_dn_motors(self):
        sorted_motors = self.sort_selected_motors_by_row()
        for motor in reversed(sorted_motors):
            row = self.list_motor_short.row(motor)
            if row == self.list_motor_short.count()-1:
                continue
            short_name = self.list_motor_short.takeItem(row)
            motor_name = self.list_motor_names.takeItem(row)
            self.list_motor_short.insertItem(row+1, short_name)
            self.list_motor_names.insertItem(row+1, motor_name)
            self.list_motor_short.setItemSelected(self.list_motor_short.item(row+1), True)

    def sort_selected_motors_by_row(self):
        selected_motors = self.list_motor_short.selectedItems()
        temp_dict = {}
        for motor in selected_motors:
            temp_dict[self.list_motor_short.row(motor)] = motor

        temp_index = sorted(temp_dict)
        sorted_motors = []
        for index in temp_index:
            sorted_motors.append(temp_dict[index])
        return sorted_motors

    def change_names_selection(self):  # occurs when the short name selection changes
        self.list_motor_short.itemSelectionChanged.disconnect()
        self.list_motor_names.itemSelectionChanged.disconnect()
        for motor in self.list_motor_names.selectedItems():
            self.list_motor_names.setItemSelected(motor, False)
        for motor in self.list_motor_short.selectedItems():
            row_ind = self.list_motor_short.row(motor)
            self.list_motor_names.setItemSelected(self.list_motor_names.item(row_ind), True)
        self.list_motor_short.itemSelectionChanged.connect(self.change_names_selection)
        self.list_motor_names.itemSelectionChanged.connect(self.change_short_selection)

    def change_short_selection(self):  # occurs when the full motor name selection changes
        self.list_motor_short.itemSelectionChanged.disconnect()
        self.list_motor_names.itemSelectionChanged.disconnect()
        for motor in self.list_motor_short.selectedItems():
            self.list_motor_short.setItemSelected(motor, False)
        for motor in self.list_motor_names.selectedItems():
            row_ind = self.list_motor_names.row(motor)
            self.list_motor_short.setItemSelected(self.list_motor_short.item(row_ind), True)
        self.list_motor_short.itemSelectionChanged.connect(self.change_names_selection)
        self.list_motor_names.itemSelectionChanged.connect(self.change_short_selection)

    def show_selected_info(self):
        self.log_monitor.update_log_label()
        # self.resize(self.sizeHint())
        # self.parent().resize(self.parent().sizeHint())

    def show_offline_info(self):
        file_name = str(self.log_list.currentItem().text())
        for row in range(self.log_table.rowCount()):
            self.log_table.removeRow(0)
        for item in self.log_dict[file_name]:
            row_pos = self.log_table.rowCount()
            self.log_table.insertRow(row_pos)
            self.log_table.setItem(row_pos, 0, QtGui.QTableWidgetItem(item))
            self.log_table.setItem(row_pos, 1, QtGui.QTableWidgetItem(self.log_dict[file_name][item]))
        self.log_table.resizeColumnsToContents()

    def open_image_file(self):
        self.log_monitor.view_image_file()

    def run_create_folders_widget(self):
        self.folder_widget = FolderMaker(self)

    def add_comment(self):
        message = 'Please input a new comment for the HTML logger'
        new_comment, ok_sn = QtGui.QInputDialog.getText(self, 'New comment', message, QtGui.QLineEdit.Normal)
        if ok_sn:
            self.html_logger.add_comment_line(new_comment)
        pass


class Filter(QtCore.QObject):
    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QtCore.QEvent.FocusOut:
            widget.parent().file_name_le_change_back()
            return False
        else:
            return False


def main():
    pass

if __name__ == '__main__':
    main()
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
