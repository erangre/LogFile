"""
Created Mar 31 2016
Author: Eran Greenberg
"""

import sys, time, os
from qtpy import QtGui, QtCore, QtWidgets
try:
    from epics import caput
    from epics import caget
except ImportError:
    caput = None
    caget = None
import epics_monitor
from FolderMaker import FolderMaker
from detectors import detectors
import collections
# from html_log import HtmlLogger
try:
    import thread
except ImportError:
    import _thread as thread

DEF_DIR = 'T:\\dac_user\\2016\\IDD_2016-1\\Test\\123'
tm_y = time.localtime().tm_year
tm_m = time.localtime().tm_mon
tm_d = time.localtime().tm_mday
DEF_FILE = 'log_' + str(tm_y) + str(tm_m).zfill(2) + str(tm_d).zfill(2) + '.txt'


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()

        # Setup App Window
        self.statusBar()
        # self.setMinimumWidth(800)
        self.setWindowTitle('Log File Creator and Monitor')
        self.setWindowIcon(QtGui.QIcon('icons/google_notebook.png'))
        self.show()

        # Create Log Window
        self.log = LogWindow(self)
        self.log.move(0, 0)

        # Layout
        self.setCentralWidget(self.log)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.min_height = self.height()


class LogWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self._filter = Filter()
        self.motor_dict = {}
        self.log_dict = None
        self.log_file_settings = QtCore.QSettings("Logger", "LogFile")

        self.choose_dir = DEF_DIR
        self.choose_file = DEF_FILE
        self.motors_file = ''
        self.folder_maker_settings = {}

        # self.detector = 1

        # Create Widgets
        self.label_fullpath = QtWidgets.QLabel(self)
        self.choose_dir_btn = QtWidgets.QPushButton('Choose Folder')
        self.choose_file_name_le = QtWidgets.QLineEdit()
        self.load_log_btn = QtWidgets.QPushButton('Load Log')
        self.reload_log_btn = QtWidgets.QPushButton('Reload Log')
        self.label_start_time = QtWidgets.QLabel(self)
        self.label_end_time = QtWidgets.QLabel(self)
        self.setup_btn = QtWidgets.QPushButton('Setup')
        self.show_log_btn = QtWidgets.QPushButton('Log')
        self.comment_btn = QtWidgets.QPushButton('Comment')
        self.html_log_cb = QtWidgets.QCheckBox('HTML Log')
        self.choose_detector_tb = QtWidgets.QToolButton()
        self.start_btn = QtWidgets.QPushButton('Start')
        self.stop_btn = QtWidgets.QPushButton('Stop')
        self.list_motor_short = QtWidgets.QListWidget(self)
        self.list_motor_names = QtWidgets.QListWidget(self)
        self.motor_load_btn = QtWidgets.QPushButton('Load')
        self.motor_save_btn = QtWidgets.QPushButton('Save')
        self.motor_remove_btn = QtWidgets.QPushButton('Remove')
        self.motor_clear_btn = QtWidgets.QPushButton('Clear')
        self.motor_add_btn = QtWidgets.QPushButton('Add')
        self.motor_rename_btn = QtWidgets.QPushButton('Rename')
        self.motor_move_up_btn = QtWidgets.QPushButton(u'\u2191')
        self.motor_move_dn_btn = QtWidgets.QPushButton(u'\u2193')
        self.motor_toggle_after_btn = QtWidgets.QPushButton('Before/After')
        self.create_folders_btn = QtWidgets.QPushButton('Create Folders')
        self.log_list = QtWidgets.QListWidget(self)
        self.splitter_log = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.log_table = QtWidgets.QTableWidget(self)
        self.view_image_btn = QtWidgets.QPushButton('Open Image')

        # Set Widget Properties
        self.choose_file_name_le.setText(self.choose_file)
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file)
        self.label_start_time.setText('Start Time: ')
        self.label_end_time.setText('End Time: ')
        for label_item in self.findChildren(QtWidgets.QLabel):
            label_item.setStyleSheet('background-color: white')
        self.setup_btn.setCheckable(True)
        self.show_log_btn.setCheckable(True)
        self.reload_log_btn.hide()
        self.show_log_btn.hide()
        self.comment_btn.hide()
        self.comment_btn.setToolTip('Add a comment to the HTML log')
        self.html_log_cb.setChecked(False)
        self.html_log_cb.hide()
        self.html_log_cb.setToolTip('Enable logging to HTML file')
        self.choose_detector_tb.setText('Detectors')
        self.choose_detector_menu = QtWidgets.QMenu()
        for detector in detectors:
            action = self.choose_detector_menu.addAction(detector)
            action.setCheckable(True)
        self.choose_detector_tb.setMenu(self.choose_detector_menu)
        self.choose_detector_tb.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        self.stop_btn.setEnabled(False)
        self.list_motor_short.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_motor_names.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.motor_load_btn.setToolTip('Load does not clear the list')
        self.log_table.setColumnCount(2)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet("alternate-background-color: lightgrey;background-color: white")
        self.log_table.verticalHeader().setDefaultSectionSize(18)
        self.log_table.verticalHeader().hide()
        self.log_table.horizontalHeader().hide()

        # Set Layout
        self.vbox = QtWidgets.QVBoxLayout()      # Layout in vbox and hbox
        hbox_file = QtWidgets.QHBoxLayout()
        hbox_control = QtWidgets.QHBoxLayout()
        self.setup_motors_frame = QtWidgets.QFrame(self)
        self.setup_motors_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.grid_list_buttons = QtWidgets.QGridLayout()
        self.hbox_lists = QtWidgets.QHBoxLayout()
        vbox_log = QtWidgets.QVBoxLayout()
        hbox_log = QtWidgets.QHBoxLayout()
        self.log_frame = QtWidgets.QFrame(self)
        self.log_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        hbox_bottom_buttons = QtWidgets.QHBoxLayout()

        hbox_file.addWidget(self.label_fullpath)
        hbox_file.addStretch(1)
        hbox_file.addWidget(self.setup_btn)
        hbox_file.addWidget(self.html_log_cb)
        hbox_file.addWidget(self.choose_dir_btn)
        hbox_file.addWidget(self.choose_file_name_le)
        hbox_file.addWidget(self.reload_log_btn)
        hbox_file.addWidget(self.load_log_btn)

        hbox_control.addWidget(self.label_start_time)
        hbox_control.addStretch(1)
        hbox_control.addWidget(self.label_end_time)
        hbox_control.addStretch(1)
        hbox_control.addWidget(self.choose_detector_tb)
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
        self.grid_list_buttons.addWidget(self.motor_toggle_after_btn, 1, 0, 1, 1)
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
        # self.vbox.addStretch(1)
        self.setLayout(self.vbox)

        # Create connections
        self.choose_dir_btn.clicked.connect(self.choose_dir_btn_clicked)
        self.choose_file_name_le.returnPressed.connect(self.choose_file_name_le_changed)
        self.choose_file_name_le.installEventFilter(self._filter)
        self.load_log_btn.clicked.connect(self.load_previous_log)
        self.reload_log_btn.clicked.connect(self.reload_previous_log)
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
        self.motor_toggle_after_btn.clicked.connect(self.toggle_after)
        self.view_image_btn.clicked.connect(self.open_image_file)
        self.create_folders_btn.clicked.connect(self.run_create_folders_widget)
        self.choose_detector_menu.triggered.connect(self.choose_detector_tb.click)
        self.choose_detector_tb.clicked.connect(self.choose_detector_changed)

        # Setup App Window
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Cleanlooks'))
        self.show()
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.load_config()
        self.load_log_file_settings()
        if caget == None or caput == None:
            self.disable_epics()

    def disable_epics(self):
        self.setup_btn.setVisible(False)
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.choose_detector_tb.setVisible(False)
        self.label_start_time.setVisible(False)
        self.label_end_time.setVisible(False)
        self.label_fullpath.setVisible(False)
        self.choose_file_name_le.setVisible(False)
        self.choose_dir_btn.setVisible(False)

    def choose_dir_btn_clicked(self):
        CH_DIR_TEXT = 'Choose directory for saving log file'
        self.choose_dir, _ = QtWidgets.QFileDialog.getExistingDirectory(self, CH_DIR_TEXT, self.choose_dir)
        if self.choose_dir:
            self.set_choose_dir_label()

    def set_choose_dir_label(self):
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file_name_le.text())

    def choose_file_name_le_changed(self):
        self.choose_file = self.choose_file_name_le.text()
        self.label_fullpath.setText(self.choose_dir + '\\' + self.choose_file)

    def file_name_le_change_back(self):  # in case enter wasn't pressed (to avoid accidental changes)
        self.choose_file_name_le.setText(self.choose_file)

    def load_previous_log(self, file_name=None):
        if not file_name:
            msg = 'Choose log file to view'
            load_log_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, msg, '.', 'Text Files (*.txt)')
        else:
            load_log_name = file_name

        if not load_log_name:
            msg = 'No Log File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        self.start_btn.setEnabled(False)
        self.setup_btn.setEnabled(False)
        self.choose_dir_btn.setEnabled(False)
        self.view_image_btn.setEnabled(False)
        self.choose_detector_tb.setEnabled(False)
        self.setup_motors_frame.hide()

        self.read_log_file(load_log_name)
        self.reload_log_btn.show()

    def read_log_file(self, load_log_name=None):
        self.log_dict = collections.OrderedDict()
        try:
            self.log_list.itemSelectionChanged.disconnect()
        except Exception:
            pass

        if not load_log_name:
            msg = 'No Log File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        self.log_list.clear()
        with open(load_log_name, 'r') as in_log_file:
            for curr_line in in_log_file:
                curr_line = curr_line.split('\n')[0]
                if 'Time' in curr_line:
                    self.headings = curr_line.split('\t')
                else:
                    line_data = curr_line.split('\t')
                    file_name = line_data[2] + '\\' + line_data[1]
                    self.log_dict[file_name] = collections.OrderedDict()
                    for col_name, col_data in zip(self.headings, line_data):
                        self.log_dict[file_name][col_name] = col_data
                    self.log_list.insertItem(0, file_name)
        if not self.log_frame.isVisible():
            self.toggle_show_log()
        self.log_list.itemSelectionChanged.connect(self.show_offline_info)

        msg = 'Loaded log file ' + load_log_name
        self.loaded_log = load_log_name

        self.parent().statusBar().showMessage(msg)

    def reload_previous_log(self):
        self.load_previous_log(self.loaded_log)

    def toggle_setup_menu(self):
        self.setup_motors_frame.setVisible(not self.setup_motors_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        if not self.setup_motors_frame.isVisible() and not self.log_frame.isVisible():
            self.parent().setMinimumHeight(self.parent().min_height)
            self.parent().resize(self.parent().width(), self.parent().minimumHeight())

    def toggle_show_log(self):
        self.log_frame.setVisible(not self.log_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        # print(self.parent().sizeHint())
        if not self.log_frame.isVisible() and not self.setup_motors_frame.isVisible():
            self.parent().setMinimumHeight(self.parent().min_height)
            self.parent().resize(self.parent().width(), self.parent().minimumHeight())

    def start_logging(self):
        f_time = time.asctime()
        self.label_start_time.setText('Start Time: ' + f_time)
        self.start_btn.setEnabled(False)
        self.load_log_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.show_log_btn.show()
        # self.comment_btn.show()
        # self.html_log_cb.show()
        self.choose_dir_btn.setEnabled(False)
        self.choose_file_name_le.setEnabled(False)
        self.choose_detector_tb.setVisible(False)
        self.log_list.clear()

        full_path = self.label_fullpath.text()
        if os.path.isfile(full_path):
            self.read_log_file(full_path)
            try:
                self.log_list.itemSelectionChanged.disconnect()
            except Exception:
                pass

        self.log_file = open(full_path, 'a')
        self.write_headings()
        self.log_file.flush()

        # self.set_enabled_hbox_lists(False)
        msg = 'Started logging to: ' + full_path
        self.parent().statusBar().showMessage(msg)

        self.log_list.itemSelectionChanged.connect(self.show_selected_info)

        self.motors_file = str(self.choose_file).rsplit('.')[0] + '_motors.txt'
        self.save_config()
        self.save_log_file_settings()

        # self.base_dir = caget(epp['CCD_File_Path'], as_string=True)
        # self.html_logger = HtmlLogger(self)
        # self.html_logger.start_html_logger()

        self.log_monitor = epics_monitor.StartMonitors(self, self.log_dict)

    def stop_logging(self):
        f_time = time.asctime()
        self.label_end_time.setText('End Time: ' + f_time)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.show_log_btn.isChecked():
            self.show_log_btn.click()
        # self.setup_btn.show()
        self.show_log_btn.hide()
        self.choose_dir_btn.setEnabled(True)
        self.comment_btn.hide()
        self.html_log_cb.hide()
        self.choose_file_name_le.setEnabled(True)
        self.choose_detector_tb.setVisible(True)

        self.log_file.close()
        epics_monitor.StopMonitors(self)
        msg = 'Stopped logging!'
        self.parent().statusBar().showMessage(msg)
        # self.set_enabled_hbox_lists(True)
        self.log_list.itemSelectionChanged.disconnect()
        self.log_list.clear()
        self.load_log_btn.setEnabled(True)
        self.set_enabled_hbox_lists(True)

    def set_enabled_hbox_lists(self, enable_mode):
        for ind in range(0, self.hbox_lists.count()):
            curr_item = self.hbox_lists.itemAt(ind)
            if type(curr_item) == QtWidgets.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)
        for ind in range(0, self.grid_list_buttons.count()):
            curr_item = self.grid_list_buttons.itemAt(ind)
            if type(curr_item) == QtWidgets.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)

    def write_headings(self):
        heading = self.read_headings()
        self.log_file.write(heading)

    def read_headings(self):
        heading = 'Day_Date_Time_Year\tFile_Name\tDirectory\tExposure_Time_(sec)\t'
        self.list_motor_short.selectAll()
        for motor in self.list_motor_short.selectedItems():
            heading = heading + motor.text() + '\t'
        heading = heading + 'Comments' + '\n'
        return heading

    def choose_detector_changed(self):
        self.detectors = []
        for detector in self.choose_detector_menu.actions():
            if detector.isChecked():
                self.detectors.append(detector.text())

    def load_motor_list(self, file_name=None):
        if not file_name or not os.path.isfile(file_name):
            load_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose file name for loading motor list', '.',
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
                self.motor_dict[row[0]] = {}
                self.motor_dict[row[0]]['PV'] = row[1].split('\n')[0]
                if len(row) > 2:
                    self.motor_dict[row[0]]['after'] = int(row[2].split('\n')[0])
                else:
                    self.motor_dict[row[0]]['after'] = 0
                self.list_motor_short.addItem(row[0])
                self.list_motor_names.addItem(row[1].split('\n')[0])
                if self.motor_dict[row[0]]['after']:
                    self.list_motor_short.item(self.list_motor_short.count()-1).setForeground(QtGui.QColor('blue'))
                    self.list_motor_names.item(self.list_motor_names.count()-1).setForeground(QtGui.QColor('blue'))

            msg = 'Loaded motor list from ' + load_name
            self.parent().statusBar().showMessage(msg)

    def save_motor_list(self, file_name=None):
        if not file_name:
            save_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Choose file name for saving motor list', '.',
                                                          'Text Files (*.txt)')
        else:
            save_name = file_name

        if not save_name:
            msg = 'No File Saved'
            self.parent().statusBar().showMessage(msg)
            return
        with open(save_name, 'w') as out_file:
            self.list_motor_short.selectAll()
            for motor in self.list_motor_short.selectedItems():
                row_ind = self.list_motor_short.row(motor)
                out_line = str(motor.text()) + ',' + self.list_motor_names.item(row_ind).text() + ','
                out_line = out_line + str(self.motor_dict[str(motor.text())]['after']) + '\n'
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
        short_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Add Motor to List', 'Provide short name for motor:')
        motor_name, ok_mn = QtWidgets.QInputDialog.getText(self, 'Add Motor to List', 'Provide Motor address:')
        after_msg = 'Should this PV be read after file completion?'
        after = QtWidgets.QMessageBox.question(self, 'Message', after_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if ok_sn and ok_mn:
            self.add_one_motor(short_name, motor_name, after)
            msg = 'Added ' + short_name + ' to motor list'
            self.parent().statusBar().showMessage(msg)

    def add_one_motor(self, short_name, motor_name, after):
        self.motor_dict[str(short_name)] = {}
        self.motor_dict[str(short_name)]['PV'] = str(motor_name)
        self.list_motor_short.addItem(str(short_name))
        self.list_motor_names.addItem(str(motor_name))
        if after == QtWidgets.QMessageBox.Yes:
            self.motor_dict[str(short_name)]['after'] = 1
            self.list_motor_short.item(self.list_motor_short.count()-1).setForeground(QtGui.QColor('blue'))
            self.list_motor_names.item(self.list_motor_names.count()-1).setForeground(QtGui.QColor('blue'))
        else:
            self.motor_dict[str(short_name)]['after'] = 0

    def rename_motor(self):
        for motor in self.list_motor_short.selectedItems():
            old_short_name = motor.text()
            row = self.list_motor_short.row(motor)
            motor_name = self.list_motor_names.item(row).text()
            message = 'Provide new short name for motor ' + old_short_name + ':'
            short_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Rename motor in List', message,
                                                           QtWidgets.QLineEdit.Normal, old_short_name)
            if ok_sn:
                after = self.motor_dict[str(old_short_name)]['after']
                del self.motor_dict[str(old_short_name)]
                self.list_motor_short.takeItem(self.list_motor_short.row(motor))
                self.list_motor_short.insertItem(row, str(short_name))
                self.motor_dict[str(short_name)] = {}
                self.motor_dict[str(short_name)]['PV'] = str(motor_name)
                self.motor_dict[str(short_name)]['after'] = after
                if after:
                    self.list_motor_short.item(row).setForeground(QtGui.QColor('blue'))
                msg = 'Renamed ' + old_short_name + ' to ' + short_name + ' in motor list'
                self.parent().statusBar().showMessage(msg)

    def edit_motor(self):
        for motor in self.list_motor_names.selectedItems():
            old_motor_name = motor.text()
            row = self.list_motor_names.row(motor)
            motor_short = self.list_motor_short.item(row).text()
            message = 'Provide new PV for motor ' + motor_short + ':'
            motor_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Change PV', message,
                                                           QtWidgets.QLineEdit.Normal, old_motor_name)
            if ok_sn:
                self.motor_dict[str(motor_short)]['PV'] = str(motor_name)
                self.list_motor_names.takeItem(self.list_motor_names.row(motor))
                self.list_motor_names.insertItem(row, str(motor_name))
                msg = 'Updated ' + motor_short + ' from ' + old_motor_name + ' to ' + motor_name + ' in motor list'
                self.parent().statusBar().showMessage(msg)

    def toggle_after(self):
        for motor in self.list_motor_short.selectedItems():
            row = self.list_motor_short.row(motor)
            if self.motor_dict[str(motor.text())]['after']:
                self.motor_dict[str(motor.text())]['after'] = 0
                self.list_motor_short.item(row).setForeground(QtGui.QColor('black'))
                self.list_motor_names.item(row).setForeground(QtGui.QColor('black'))
            else:
                self.motor_dict[str(motor.text())]['after'] = 1
                self.list_motor_short.item(row).setForeground(QtGui.QColor('blue'))
                self.list_motor_names.item(row).setForeground(QtGui.QColor('blue'))

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
            self.list_motor_short.setCurrentItem(self.list_motor_short.item(row-1), QtCore.QItemSelectionModel.Select)

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
            self.list_motor_short.setCurrentItem(self.list_motor_short.item(row+1), QtCore.QItemSelectionModel.Select)

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
            self.list_motor_names.setCurrentItem(motor, QtCore.QItemSelectionModel.Deselect)
        for motor in self.list_motor_short.selectedItems():
            row_ind = self.list_motor_short.row(motor)
            self.list_motor_names.setCurrentItem(self.list_motor_names.item(row_ind), QtCore.QItemSelectionModel.Select)
        self.list_motor_short.itemSelectionChanged.connect(self.change_names_selection)
        self.list_motor_names.itemSelectionChanged.connect(self.change_short_selection)

    def change_short_selection(self):  # occurs when the full motor name selection changes
        self.list_motor_short.itemSelectionChanged.disconnect()
        self.list_motor_names.itemSelectionChanged.disconnect()
        for motor in self.list_motor_short.selectedItems():
            self.list_motor_short.setCurrentItem(motor, QtCore.QItemSelectionModel.Deselect)
        for motor in self.list_motor_names.selectedItems():
            row_ind = self.list_motor_names.row(motor)
            self.list_motor_short.setCurrentItem(self.list_motor_short.item(row_ind), QtCore.QItemSelectionModel.Select)
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
            self.log_table.setItem(row_pos, 0, QtWidgets.QTableWidgetItem(item))
            self.log_table.setItem(row_pos, 1, QtWidgets.QTableWidgetItem(self.log_dict[file_name][item]))
        self.log_table.resizeColumnsToContents()

    def open_image_file(self):
        self.log_monitor.view_image_file()

    def run_create_folders_widget(self):
        if self.start_btn.isEnabled():
            self.folder_widget = FolderMaker(parent=self, running=False, chosen_detectors=self.detectors)
        else:
            self.folder_widget = FolderMaker(parent=self, running=True, chosen_detectors=self.detectors,
                                             previous_detector_settings=self.folder_maker_settings)

    def add_comment(self):
        message = 'Please input a new comment for the HTML logger'
        new_comment, ok_sn = QtWidgets.QInputDialog.getText(self, 'New comment', message, QtWidgets.QLineEdit.Normal)
        if ok_sn:
            self.html_logger.add_comment_line(new_comment)

    def load_log_file_settings(self):
        self.choose_dir = self.log_file_settings.value('log_file_dir', defaultValue=self.choose_dir)
        self.choose_file = self.log_file_settings.value('log_file_name', defaultValue=self.choose_file)
        self.motors_file = self.log_file_settings.value('pv_list_file', defaultValue='')
        self.detectors = self.log_file_settings.value('detectors', defaultValue=[])

        self.choose_file_name_le.setText(self.choose_file)
        self.set_choose_dir_label()
        self.load_motor_list(self.motors_file)

        for detector in self.choose_detector_menu.actions():
            if str(detector.text()) in self.detectors:
                detector.setChecked(True)

    def save_log_file_settings(self):
        self.log_file_settings.setValue('log_file_dir', self.choose_dir)
        self.log_file_settings.setValue('log_file_name', self.choose_file)
        self.log_file_settings.setValue('pv_list_file', self.motors_file)
        chosen_detectors = []
        for detector in self.choose_detector_menu.actions():
            if detector.isChecked():
                chosen_detectors.append(detector.text())
        self.log_file_settings.setValue('detectors', chosen_detectors)
        self.save_motor_list(self.motors_file)

    def load_config(self):
        cfg = {}
        try:
            cfg_file = open('log_config.txt', 'r')
        except IOError:
            print('No configuration file, using program defaults')
            return
        for line in cfg_file:
            cfg[line.split()[0]] = line.split()[1]

        self.choose_file = cfg['file']
        self.choose_dir = cfg['directory']
        self.motors_file = cfg['motor_file']
        self.detectors = cfg['detectors'].split(',')

        self.choose_file_name_le.setText(self.choose_file)
        self.set_choose_dir_label()
        self.load_motor_list(self.motors_file)
        for detector in self.choose_detector_menu.actions():
            if str(detector.text()) in self.detectors:
                detector.setChecked(True)

    def save_config(self):
        cfg_file = open('log_config.txt', 'w')

        outline = 'directory\t' + self.choose_dir + '\n'
        cfg_file.write(outline)

        outline = 'file\t' + self.choose_file + '\n'
        cfg_file.write(outline)

        outline = 'motor_file\t' + self.motors_file + '\n'
        cfg_file.write(outline)

        selected_detectors = []
        for detector in self.choose_detector_menu.actions():
            if detector.isChecked():
                selected_detectors.append(detector.text())
        selected_detectors_csv = ','.join(selected_detectors)

        outline = 'detectors\t' + selected_detectors_csv + '\n'
        cfg_file.write(outline)

        self.save_motor_list(self.motors_file)


class Filter(QtCore.QObject):
    def eventFilter(self, widget, event):
        # FocusOut event
        if event.type() == QtCore.QEvent.FocusOut:
            widget.parent().file_name_le_change_back()
            return False
        else:
            return False

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import traceback


def excepthook(exc_type, exc_value, traceback_obj):
    """
    Global function to catch unhandled exceptions. This function will result in an error dialog which displays the
    error information.

    :param exc_type: exception type
    :param exc_value: exception value
    :param traceback_obj: traceback object
    :return:
    """

    traceback.print_exception(exc_type, exc_value, traceback_obj)

sys.excepthook = excepthook


def main():
    pass

if __name__ == '__main__':
    main()
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
