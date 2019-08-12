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
from widgets.LogWidgets import LogFileWidget
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
        self.pv_dict = {}
        self.log_dict = None
        self.log_file_settings = QtCore.QSettings("Logger", "LogFile")

        self.choose_dir = DEF_DIR
        self.choose_file = DEF_FILE
        self.pvs_file = ''
        self.folder_maker_settings = {}

        # self.detector = 1
        self.widget = LogFileWidget(self)
        self.widget.choose_file_name_le.setText(self.choose_file)
        self.widget.full_path_lbl.setText(self.choose_dir + '\\' + self.choose_file)
        for detector in detectors:
            action = self.widget.choose_detector_menu.addAction(detector)
            action.setCheckable(True)

        # Create connections
        self.widget.choose_dir_btn.clicked.connect(self.choose_dir_btn_clicked)
        self.widget.choose_file_name_le.returnPressed.connect(self.choose_file_name_le_changed)
        self.widget.choose_file_name_le.installEventFilter(self._filter)
        self.widget.load_log_btn.clicked.connect(self.load_previous_log)
        self.widget.reload_log_btn.clicked.connect(self.reload_previous_log)
        self.widget.setup_btn.clicked.connect(self.toggle_setup_menu)
        self.widget.show_log_btn.clicked.connect(self.toggle_show_log)
        # self.widget.comment_btn.clicked.connect(self.add_comment)
        self.widget.start_btn.clicked.connect(self.start_logging)
        self.widget.stop_btn.clicked.connect(self.stop_logging)
        self.widget.pv_load_btn.clicked.connect(self.load_pv_list)
        self.widget.pv_save_btn.clicked.connect(self.save_pv_list)
        self.widget.pv_remove_btn.clicked.connect(self.remove_from_pv_list)
        self.widget.pv_add_btn.clicked.connect(self.add_to_pv_list)
        self.widget.pv_clear_btn.clicked.connect(self.clear_pv_list)
        self.widget.pv_rename_btn.clicked.connect(self.rename_pv)
        self.widget.pv_short_name_list.itemSelectionChanged.connect(self.change_names_selection)
        self.widget.pv_short_name_list.doubleClicked.connect(self.rename_pv)
        self.widget.pv_list.itemSelectionChanged.connect(self.change_short_selection)
        self.widget.pv_list.doubleClicked.connect(self.edit_pv)
        self.widget.pv_move_up_btn.clicked.connect(self.move_up_pvs)
        self.widget.pv_move_dn_btn.clicked.connect(self.move_dn_pvs)
        self.widget.pv_toggle_after_btn.clicked.connect(self.toggle_after)
        self.widget.view_image_btn.clicked.connect(self.view_image_file)
        self.widget.create_folders_btn.clicked.connect(self.run_create_folders_widget)
        self.widget.choose_detector_menu.triggered.connect(self.widget.choose_detector_tb.click)
        self.widget.choose_detector_tb.clicked.connect(self.choose_detector_changed)

        # Setup App Window
        QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Cleanlooks'))
        self.show()
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        # self.load_config()

        if caget is None or caput is None:
            self.disable_epics()
            self.load_log_file_settings(offline=True)
        else:
            self.load_log_file_settings()

    def disable_epics(self):
        self.widget.setup_btn.setVisible(False)
        self.widget.start_btn.setVisible(False)
        self.widget.stop_btn.setVisible(False)
        self.widget.choose_detector_tb.setVisible(False)
        self.widget.start_time_lbl.setVisible(False)
        self.widget.end_time_lbl.setVisible(False)
        self.widget.full_path_lbl.setVisible(False)
        self.widget.choose_file_name_le.setVisible(False)
        self.widget.choose_dir_btn.setVisible(False)
        self.widget.create_folders_btn.setVisible(False)

    def choose_dir_btn_clicked(self):
        msg = 'Choose directory for saving log file'
        self.choose_dir = QtWidgets.QFileDialog.getExistingDirectory(self, msg, self.choose_dir)
        if self.choose_dir:
            self.set_choose_dir_label()

    def set_choose_dir_label(self):
        self.widget.full_path_lbl.setText(self.choose_dir + '\\' + self.widget.choose_file_name_le.text())

    def choose_file_name_le_changed(self):
        self.choose_file = self.widget.choose_file_name_le.text()
        self.widget.full_path_lbl.setText(self.choose_dir + '\\' + self.choose_file)

    def file_name_le_change_back(self):  # in case enter wasn't pressed (to avoid accidental changes)
        self.widget.choose_file_name_le.setText(self.choose_file)

    def load_previous_log(self, file_name=None):
        if not file_name:
            msg = 'Choose log file to view'
            load_log_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, msg, directory=self.offline_log_file,
                                                                     filter='Text Files (*.txt)')
        else:
            load_log_name = file_name

        if not load_log_name:
            msg = 'No Log File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        self.widget.start_btn.setEnabled(False)
        self.widget.setup_btn.setEnabled(False)
        self.widget.choose_dir_btn.setEnabled(False)
        # self.view_image_btn.setEnabled(False)
        self.widget.choose_detector_tb.setEnabled(False)
        self.widget.create_folders_btn.setEnabled(False)
        self.widget.setup_pvs_frame.hide()

        self.read_log_file(load_log_name)
        self.widget.reload_log_btn.show()
        self.log_file_settings.setValue('offline_log_file', load_log_name)

    def read_log_file(self, load_log_name=None):
        self.log_dict = collections.OrderedDict()
        try:
            self.widget.log_entries_list.itemSelectionChanged.disconnect()
        except Exception:
            pass

        if not load_log_name:
            msg = 'No Log File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        self.widget.log_entries_list.clear()
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
                    self.widget.log_entries_list.insertItem(0, file_name)
        if not self.widget.log_frame.isVisible():
            self.toggle_show_log()
        self.widget.log_entries_list.itemSelectionChanged.connect(self.show_offline_info)

        msg = 'Loaded log file ' + load_log_name
        self.loaded_log = load_log_name

        self.parent().statusBar().showMessage(msg)

    def reload_previous_log(self):
        self.load_previous_log(self.loaded_log)

    def toggle_setup_menu(self):
        self.widget.setup_pvs_frame.setVisible(not self.widget.setup_pvs_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        if not self.widget.setup_pvs_frame.isVisible() and not self.widget.log_frame.isVisible():
            self.parent().setMinimumHeight(self.parent().min_height)
            self.parent().resize(self.parent().width(), self.parent().minimumHeight())

    def toggle_show_log(self):
        self.widget.log_frame.setVisible(not self.widget.log_frame.isVisible())
        # self.resize(self.sizeHint())
        self.parent().resize(self.parent().sizeHint())
        # print(self.parent().sizeHint())
        if not self.widget.log_frame.isVisible() and not self.widget.setup_pvs_frame.isVisible():
            self.parent().setMinimumHeight(self.parent().min_height)
            self.parent().resize(self.parent().width(), self.parent().minimumHeight())

    def start_logging(self):
        f_time = time.asctime()
        self.widget.start_time_lbl.setText('Start Time: ' + f_time)
        self.widget.start_btn.setEnabled(False)
        self.widget.load_log_btn.setEnabled(False)
        self.widget.stop_btn.setEnabled(True)
        self.widget.show_log_btn.show()
        # self.comment_btn.show()
        # self.html_log_cb.show()
        self.widget.choose_dir_btn.setEnabled(False)
        self.widget.choose_file_name_le.setEnabled(False)
        self.widget.choose_detector_tb.setVisible(False)
        self.widget.log_entries_list.clear()

        full_path = self.widget.full_path_lbl.text()
        if os.path.isfile(full_path):
            self.read_log_file(full_path)
            try:
                self.widget.log_entries_list.itemSelectionChanged.disconnect()
            except Exception:
                pass

        self.log_file = open(full_path, 'a')
        self.write_headings()
        self.log_file.flush()

        # self.set_enabled_hbox_lists(False)
        msg = 'Started logging to: ' + full_path
        self.parent().statusBar().showMessage(msg)

        self.widget.log_entries_list.itemSelectionChanged.connect(self.show_selected_info)

        self.pvs_file = str(self.choose_file).rsplit('.')[0] + '_motors.txt'
        self.save_config()
        self.save_log_file_settings()

        # self.base_dir = caget(epp['CCD_File_Path'], as_string=True)
        # self.html_logger = HtmlLogger(self)
        # self.html_logger.start_html_logger()

        self.log_monitor = epics_monitor.StartMonitors(self, self.log_dict)
        self.widget.clear_detectors_stack_btn.clicked.connect(self.log_monitor.clear_detectors_stack_btn_clicked)

    def stop_logging(self):
        f_time = time.asctime()
        self.widget.end_time_lbl.setText('End Time: ' + f_time)
        self.widget.start_btn.setEnabled(True)
        self.widget.stop_btn.setEnabled(False)
        if self.widget.show_log_btn.isChecked():
            self.widget.show_log_btn.click()
        # self.setup_btn.show()
        self.widget.show_log_btn.hide()
        self.widget.choose_dir_btn.setEnabled(True)
        # self.widget.comment_btn.hide()
        # self.widget.html_log_cb.hide()
        self.widget.choose_file_name_le.setEnabled(True)
        self.widget.choose_detector_tb.setVisible(True)

        self.log_file.close()
        epics_monitor.StopMonitors(self)
        msg = 'Stopped logging!'
        self.parent().statusBar().showMessage(msg)
        # self.set_enabled_hbox_lists(True)
        self.widget.log_entries_list.itemSelectionChanged.disconnect()
        self.widget.log_entries_list.clear()
        self.widget.load_log_btn.setEnabled(True)
        self.set_enabled_hbox_lists(True)

    def set_enabled_hbox_lists(self, enable_mode):
        for ind in range(0, self.widget.hbox_lists.count()):
            curr_item = self.widget.hbox_lists.itemAt(ind)
            if type(curr_item) == QtWidgets.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)
        for ind in range(0, self.widget.grid_list_buttons.count()):
            curr_item = self.widget.grid_list_buttons.itemAt(ind)
            if type(curr_item) == QtWidgets.QWidgetItem:
                curr_item.widget().setEnabled(enable_mode)
        self.widget.clear_detectors_stack_btn.setEnabled(True)

    def write_headings(self):
        heading = self.read_headings()
        self.log_file.write(heading)

    def read_headings(self):
        heading = 'Day_Date_Time_Year\tFile_Name\tDirectory\tExposure_Time_(sec)\t'
        self.widget.pv_short_name_list.selectAll()
        for pv in self.widget.pv_short_name_list.selectedItems():
            heading = heading + pv.text() + '\t'
        heading = heading + 'Comments' + '\n'
        return heading

    def choose_detector_changed(self):
        self.detectors = []
        for detector in self.widget.choose_detector_menu.actions():
            if detector.isChecked():
                self.detectors.append(detector.text())

    def load_pv_list(self, file_name=None):
        if not file_name or not os.path.isfile(file_name):
            load_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose file name for loading pv list', '.',
                                                                 'Text Files (*.txt)')
        else:
            load_name = file_name

        if not load_name:
            msg = 'No File Opened'
            self.parent().statusBar().showMessage(msg)
            return

        with open(load_name, 'r') as in_file:
            for pv in in_file:
                row = pv.split(',')
                self.pv_dict[row[0]] = {}
                self.pv_dict[row[0]]['PV'] = row[1].split('\n')[0]
                if len(row) > 2:
                    self.pv_dict[row[0]]['after'] = int(row[2].split('\n')[0])
                else:
                    self.pv_dict[row[0]]['after'] = 0
                self.widget.pv_short_name_list.addItem(row[0])
                self.widget.pv_list.addItem(row[1].split('\n')[0])
                if self.pv_dict[row[0]]['after']:
                    self.widget.pv_short_name_list.item(
                        self.widget.pv_short_name_list.count()-1).setForeground(QtGui.QColor('blue'))
                    self.widget.pv_list.item(
                        self.widget.pv_list.count()-1).setForeground(QtGui.QColor('blue'))

            msg = 'Loaded pv list from ' + load_name
            self.parent().statusBar().showMessage(msg)

    def save_pv_list(self, file_name=None):
        if not file_name:
            save_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Choose file name for saving pv list', '.',
                                                                 'Text Files (*.txt)')
        else:
            save_name = file_name

        if not save_name:
            msg = 'No File Saved'
            self.parent().statusBar().showMessage(msg)
            return
        with open(save_name, 'w') as out_file:
            self.widget.pv_short_name_list.selectAll()
            for pv in self.widget.pv_short_name_list.selectedItems():
                row_ind = self.widget.pv_short_name_list.row(pv)
                out_line = str(pv.text()) + ',' + self.widget.pv_list.item(row_ind).text() + ','
                out_line = out_line + str(self.pv_dict[str(pv.text())]['after']) + '\n'
                out_file.write(out_line)
            msg = 'Saved pv list to ' + save_name
            self.parent().statusBar().showMessage(msg)

    def remove_from_pv_list(self):
        for pv in self.widget.pv_short_name_list.selectedItems():
            self.remove_one_pv(pv)
            msg = 'Removed ' + pv.text().split('\t')[0] + ' from pv list'
            self.parent().statusBar().showMessage(msg)

    def remove_one_pv(self, pv):
        self.widget.pv_list.takeItem(self.widget.pv_short_name_list.row(pv))
        self.widget.pv_short_name_list.takeItem(self.widget.pv_short_name_list.row(pv))
        del self.pv_dict[str(pv.text())]

    def clear_pv_list(self):
        self.widget.pv_short_name_list.clear()
        self.widget.pv_list.clear()
        self.pv_dict = {}
        msg = 'Motor list cleared'
        self.parent().statusBar().showMessage(msg)

    def add_to_pv_list(self):
        short_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Add PV to List', 'Provide short name for PV:')
        pv_name, ok_mn = QtWidgets.QInputDialog.getText(self, 'Add PV to List', 'Provide PV address:')
        after_msg = 'Should this PV be read after file completion?'
        after = QtWidgets.QMessageBox.question(self, 'Message', after_msg, QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if ok_sn and ok_mn:
            self.add_one_pv(short_name, pv_name, after)
            msg = 'Added ' + short_name + ' to pv list'
            self.parent().statusBar().showMessage(msg)

    def add_one_pv(self, short_name, pv_name, after):
        self.pv_dict[str(short_name)] = {}
        self.pv_dict[str(short_name)]['PV'] = str(pv_name)
        self.widget.pv_short_name_list.addItem(str(short_name))
        self.widget.pv_list.addItem(str(pv_name))
        if after == QtWidgets.QMessageBox.Yes:
            self.pv_dict[str(short_name)]['after'] = 1
            self.widget.pv_short_name_list.item(
                self.widget.pv_short_name_list.count()-1).setForeground(QtGui.QColor('blue'))
            self.widget.pv_list.item(
                self.widget.pv_list.count()-1).setForeground(QtGui.QColor('blue'))
        else:
            self.pv_dict[str(short_name)]['after'] = 0

    def rename_pv(self):
        for pv in self.widget.pv_short_name_list.selectedItems():
            old_short_name = pv.text()
            row = self.widget.pv_short_name_list.row(pv)
            pv_name = self.widget.pv_list.item(row).text()
            message = 'Provide new short name for pv ' + old_short_name + ':'
            short_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Rename pv in List', message,
                                                               QtWidgets.QLineEdit.Normal, old_short_name)
            if ok_sn:
                after = self.pv_dict[str(old_short_name)]['after']
                del self.pv_dict[str(old_short_name)]
                self.widget.pv_short_name_list.takeItem(self.widget.pv_short_name_list.row(pv))
                self.widget.pv_short_name_list.insertItem(row, str(short_name))
                self.pv_dict[str(short_name)] = {}
                self.pv_dict[str(short_name)]['PV'] = str(pv_name)
                self.pv_dict[str(short_name)]['after'] = after
                if after:
                    self.widget.pv_short_name_list.item(row).setForeground(QtGui.QColor('blue'))
                msg = 'Renamed ' + old_short_name + ' to ' + short_name + ' in pv list'
                self.parent().statusBar().showMessage(msg)

    def edit_pv(self):
        for pv in self.widget.pv_list.selectedItems():
            old_pv_name = pv.text()
            row = self.widget.pv_list.row(pv)
            pv_short = self.widget.pv_short_name_list.item(row).text()
            message = 'Provide new PV for pv ' + pv_short + ':'
            pv_name, ok_sn = QtWidgets.QInputDialog.getText(self, 'Change PV', message,
                                                            QtWidgets.QLineEdit.Normal, old_pv_name)
            if ok_sn:
                self.pv_dict[str(pv_short)]['PV'] = str(pv_name)
                self.widget.pv_list.takeItem(self.widget.pv_list.row(pv))
                self.widget.pv_list.insertItem(row, str(pv_name))
                msg = 'Updated ' + pv_short + ' from ' + old_pv_name + ' to ' + pv_name + ' in pv list'
                self.parent().statusBar().showMessage(msg)

    def toggle_after(self):
        for pv in self.widget.pv_short_name_list.selectedItems():
            row = self.widget.pv_short_name_list.row(pv)
            if self.pv_dict[str(pv.text())]['after']:
                self.pv_dict[str(pv.text())]['after'] = 0
                self.widget.pv_short_name_list.item(row).setForeground(QtGui.QColor('black'))
                self.widget.pv_list.item(row).setForeground(QtGui.QColor('black'))
            else:
                self.pv_dict[str(pv.text())]['after'] = 1
                self.widget.pv_short_name_list.item(row).setForeground(QtGui.QColor('blue'))
                self.widget.pv_list.item(row).setForeground(QtGui.QColor('blue'))

    def move_up_pvs(self):
        sorted_pvs = self.sort_selected_pvs_by_row()
        for pv in sorted_pvs:
            row = self.widget.pv_short_name_list.row(pv)
            if row == 0:
                continue
            short_name = self.widget.pv_short_name_list.takeItem(row)
            pv_name = self.widget.pv_list.takeItem(row)
            self.widget.pv_short_name_list.insertItem(row-1, short_name)
            self.widget.pv_list.insertItem(row-1, pv_name)
            self.widget.pv_short_name_list.setCurrentItem(self.widget.pv_short_name_list.item(row-1),
                                                          QtCore.QItemSelectionModel.Select)

    def move_dn_pvs(self):
        sorted_pvs = self.sort_selected_pvs_by_row()
        for pv in reversed(sorted_pvs):
            row = self.widget.pv_short_name_list.row(pv)
            if row == self.widget.pv_short_name_list.count()-1:
                continue
            short_name = self.widget.pv_short_name_list.takeItem(row)
            pv_name = self.widget.pv_list.takeItem(row)
            self.widget.pv_short_name_list.insertItem(row+1, short_name)
            self.widget.pv_list.insertItem(row+1, pv_name)
            self.widget.pv_short_name_list.setCurrentItem(self.widget.pv_short_name_list.item(row+1),
                                                          QtCore.QItemSelectionModel.Select)

    def sort_selected_pvs_by_row(self):
        selected_pvs = self.widget.pv_short_name_list.selectedItems()
        temp_dict = {}
        for pv in selected_pvs:
            temp_dict[self.widget.pv_short_name_list.row(pv)] = pv

        temp_index = sorted(temp_dict)
        sorted_pvs = []
        for index in temp_index:
            sorted_pvs.append(temp_dict[index])
        return sorted_pvs

    def change_names_selection(self):  # occurs when the short name selection changes
        self.widget.pv_short_name_list.itemSelectionChanged.disconnect()
        self.widget.pv_list.itemSelectionChanged.disconnect()
        for pv in self.widget.pv_list.selectedItems():
            self.widget.pv_list.setCurrentItem(pv, QtCore.QItemSelectionModel.Deselect)
        for pv in self.widget.pv_short_name_list.selectedItems():
            row_ind = self.widget.pv_short_name_list.row(pv)
            self.widget.pv_list.setCurrentItem(self.widget.pv_list.item(row_ind),
                                               QtCore.QItemSelectionModel.Select)
        self.widget.pv_short_name_list.itemSelectionChanged.connect(self.change_names_selection)
        self.widget.pv_list.itemSelectionChanged.connect(self.change_short_selection)

    def change_short_selection(self):  # occurs when the full pv name selection changes
        self.widget.pv_short_name_list.itemSelectionChanged.disconnect()
        self.widget.pv_list.itemSelectionChanged.disconnect()
        for pv in self.widget.pv_short_name_list.selectedItems():
            self.widget.pv_short_name_list.setCurrentItem(pv, QtCore.QItemSelectionModel.Deselect)
        for pv in self.widget.pv_list.selectedItems():
            row_ind = self.widget.pv_list.row(pv)
            self.widget.pv_short_name_list.setCurrentItem(self.widget.pv_short_name_list.item(row_ind),
                                                          QtCore.QItemSelectionModel.Select)
        self.widget.pv_short_name_list.itemSelectionChanged.connect(self.change_names_selection)
        self.widget.pv_list.itemSelectionChanged.connect(self.change_short_selection)

    def show_selected_info(self):
        self.log_monitor.update_log_label()
        # self.resize(self.sizeHint())
        # self.parent().resize(self.parent().sizeHint())

    def show_offline_info(self):
        file_name = str(self.widget.log_entries_list.currentItem().text())
        for row in range(self.widget.log_entry_table.rowCount()):
            self.widget.log_entry_table.removeRow(0)
        for item in self.log_dict[file_name]:
            row_pos = self.widget.log_entry_table.rowCount()
            self.widget.log_entry_table.insertRow(row_pos)
            self.widget.log_entry_table.setItem(row_pos, 0, QtWidgets.QTableWidgetItem(item))
            self.widget.log_entry_table.setItem(row_pos, 1, QtWidgets.QTableWidgetItem(self.log_dict[file_name][item]))
        self.widget.log_entry_table.resizeColumnsToContents()

    def view_image_file(self):
        file_name = str(self.widget.log_entries_list.currentItem().text()).split('|', 1)
        file_type = str(self.widget.log_entries_list.currentItem().text()).rsplit('.', 1)
        if file_type[-1] == 'tif':
            os.system("start " + file_name[-1])

    def run_create_folders_widget(self):
        if self.widget.start_btn.isEnabled():
            self.folder_widget = FolderMaker(parent=self, running=False, chosen_detectors=self.detectors)
        else:
            self.folder_widget = FolderMaker(parent=self, running=True, chosen_detectors=self.detectors,
                                             previous_detector_settings=self.folder_maker_settings)
        self.folder_widget.folders_created.connect(self.folders_created_emitted)

    def folders_created_emitted(self):
        if self.widget.stop_btn.isVisible():
            self.widget.stop_btn.click()
        self.widget.start_btn.click()

    def add_comment(self):
        message = 'Please input a new comment for the HTML logger'
        new_comment, ok_sn = QtWidgets.QInputDialog.getText(self, 'New comment', message, QtWidgets.QLineEdit.Normal)
        if ok_sn:
            self.html_logger.add_comment_line(new_comment)

    def load_log_file_settings(self, offline=False):
        self.offline_log_file = self.log_file_settings.value('offline_log_file', defaultValue=None)

        if offline:
            return

        self.choose_dir = self.log_file_settings.value('log_file_dir', defaultValue=self.choose_dir)
        self.choose_file = self.log_file_settings.value('log_file_name', defaultValue=self.choose_file)
        self.pvs_file = self.log_file_settings.value('pv_list_file', defaultValue='')
        self.detectors = self.log_file_settings.value('detectors', defaultValue=[])

        self.widget.choose_file_name_le.setText(self.choose_file)
        self.set_choose_dir_label()
        self.load_pv_list(self.pvs_file)

        for detector in self.widget.choose_detector_menu.actions():
            if str(detector.text()) in self.detectors:
                detector.setChecked(True)

    def save_log_file_settings(self):
        self.log_file_settings.setValue('log_file_dir', self.choose_dir)
        self.log_file_settings.setValue('log_file_name', self.choose_file)
        self.log_file_settings.setValue('pv_list_file', self.pvs_file)
        chosen_detectors = []
        for detector in self.widget.choose_detector_menu.actions():
            if detector.isChecked():
                chosen_detectors.append(detector.text())
        self.log_file_settings.setValue('detectors', chosen_detectors)
        self.save_pv_list(self.pvs_file)

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
        self.pvs_file = cfg['pv_file']
        self.detectors = cfg['detectors'].split(',')

        self.widget.choose_file_name_le.setText(self.choose_file)
        self.set_choose_dir_label()
        self.load_pv_list(self.pvs_file)
        for detector in self.choose_detector_menu.actions():
            if str(detector.text()) in self.detectors:
                detector.setChecked(True)

    def save_config(self):
        cfg_file = open('log_config.txt', 'w')

        outline = 'directory\t' + self.choose_dir + '\n'
        cfg_file.write(outline)

        outline = 'file\t' + self.choose_file + '\n'
        cfg_file.write(outline)

        outline = 'pv_file\t' + self.pvs_file + '\n'
        cfg_file.write(outline)

        selected_detectors = []
        for detector in self.widget.choose_detector_menu.actions():
            if detector.isChecked():
                selected_detectors.append(detector.text())
        selected_detectors_csv = ','.join(selected_detectors)

        outline = 'detectors\t' + selected_detectors_csv + '\n'
        cfg_file.write(outline)

        self.save_pv_list(self.pvs_file)


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
