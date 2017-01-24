import time
try:
    from epics import caput, caget, PV, camonitor, camonitor_clear
except ImportError:
    epics = None
from connect_epics import epics_config_fixed as epcf
from connect_epics import epics_monitor_config as epmc
from connect_epics import epics_BG_config as ebgcfg
from qtpy.QtCore import *
from qtpy import QtCore
from qtpy.QtWidgets import *
from qtpy.QtGui import *
import collections
import os
import threading
from detectors import detectors


class StartMonitors(QWidget):
    log_signal = QtCore.Signal(str)

    def __init__(self, parent=None, log_dict=None):
        super(StartMonitors, self).__init__()
        self.parent = parent
        self.xrd_temp_dict = collections.OrderedDict()
        self.pxrd_temp = []
        self.pxrd_temp_dict = collections.OrderedDict()
        self.T_temp_dict = collections.OrderedDict()
        self.us_temp_dict = collections.OrderedDict()
        self.ds_temp_dict = collections.OrderedDict()
        self.ms_temp_dict = collections.OrderedDict()
        if log_dict is None:
            self.log_dict = {}
        else:
            self.log_dict = log_dict.copy()
        self.old_heading = self.parent.read_headings()
        self.running_tasks = 0
        self.xrd_start_done = True

        # connections

        self.log_signal.connect(self.signal_received)

        self.chosen_detectors = {}
        for detector in self.parent.choose_detector_menu.actions():
            if detector.isChecked():
                self.chosen_detectors[detector.text()] = {}

        for detector in self.chosen_detectors:
            self.chosen_detectors[detector]['temp_dict'] = []
            self.chosen_detectors[detector]['start_signal_function'] = self.create_start_signal_function(detector)
            camonitor(detectors[detector]['monitor_signal_start'],
                      callback=self.chosen_detectors[detector]['start_signal_function'])
            if not detectors[detector]['monitor_signal_end'] is None and \
                    not detectors[detector]['monitor_signal_end'] == detectors[detector]['monitor_signal_start']:
                self.chosen_detectors[detector]['end_signal_function'] = self.create_end_signal_function(detector)
                camonitor(detectors[detector]['monitor_signal_end'],
                          callback=self.chosen_detectors[detector]['end_signal_function'])

    def signal_received(self, sig_name):
        t0 = time.time()
        detector, phase = sig_name.rsplit('_', 1)
        frame_type_PV = detectors[detector]['frame_type_PV']

        if frame_type_PV is not None:
            frame_type = caget(frame_type_PV, as_string=False)
        else:
            frame_type = 0
        self.parent.parent().statusBar().showMessage(
            detectors[detector]['frame_type_messages'][frame_type] + ' ' + phase)
        if not frame_type == 0:
            if detectors[detector]['new_file_name'][frame_type] is None:
                return

        if phase == 'start':
            if detectors[detector]['track_running_tasks']:
                self.running_tasks += 1
            start_time = time.asctime().replace(' ', '_')
            image_type_PV = detectors[detector]['image_type_PV']
            if image_type_PV is not None:
                image_type = caget(image_type_PV, as_string=False)
            else:
                image_type = 0
            exposure_time = caget(detectors[detector]['image_type_exposure_time'][image_type], as_string=True)
            self.chosen_detectors[detector]['temp_dict'].append(self.output_line_common_start(start_time,
                                                                                              exposure_time).copy())

            if detectors[detector]['monitor_signal_end'] is None:
                new_file_name = caget(detectors[detector]['new_file_name'][frame_type], as_string=True)
                comments = self.build_comments(detector)
                self.output_line_common_end(detectors[detector]['prefix'], new_file_name, comments,
                                            self.chosen_detectors[detector]['temp_dict'][0])

        elif phase == 'end':
            if detectors[detector]['track_running_tasks']:
                self.running_tasks -= 1
            image_type_PV = detectors[detector]['image_type_PV']
            if image_type_PV is None:
                image_type = 0
            else:
                image_type = caget(image_type_PV, as_string=False)
            new_file_name = caget(detectors[detector]['new_file_name'][frame_type], as_string=True)
            comments = self.build_comments(detector)
            self.output_line_common_end(detectors[detector]['prefix'], new_file_name, comments,
                                        self.chosen_detectors[detector]['temp_dict'][0])
            del(self.chosen_detectors[detector]['temp_dict'][0])

    def build_comments(self, detector):
        comment_values = []
        for pv, val in zip(detectors[detector]['comments_PVs'], detectors[detector]['comments_values']):
            if val is None:
                comment_values.append(caget(pv, as_string=True))
            else:
                comment_index = caget(pv, as_string=False)
                comment_values.append(val[comment_index])
        return detectors[detector]['comments'].format(*comment_values)

    def output_line_common_start(self, start_time, exp_time):
        t0 = time.time()
        new_heading = self.parent.read_headings()
        if not self.old_heading == new_heading:
            self.parent.log_file.write(new_heading)
            self.old_heading = new_heading

        self.parent.set_enabled_hbox_lists(False)
        temp_dict = self.create_dict()
        temp_dict['Time'] = start_time
        temp_dict['Exp_Time'] = exp_time
        for motor in self.parent.list_motor_short.selectedItems():
            if not self.parent.motor_dict[str(motor.text())]['after']:
                m_value = caget(self.parent.motor_dict[str(motor.text())]['PV'], as_string=True)
                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_dict[str(motor.text())] = m_value
        return temp_dict

    def output_line_common_end(self, prefix, file_name, comments, temp_dict):
        temp_dict['Directory'] = file_name.replace('/', '\\').rsplit('\\', 1)[0]
        temp_dict['File_Name'] = file_name.replace('/', '\\').rsplit('\\', 1)[-1]

        for motor in self.parent.list_motor_short.selectedItems():
            if self.parent.motor_dict[str(motor.text())]['after']:
                m_value = caget(self.parent.motor_dict[str(motor.text())]['PV'], as_string=True)
                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_dict[str(motor.text())] = m_value
        temp_dict['Comments'] = comments
        new_line = ''
        for key in temp_dict:
            new_line = new_line + str(temp_dict[key]) + '\t'
        new_line = new_line + '\n'
        self.parent.log_file.write(new_line)
        self.parent.log_file.flush()
        self.parent.log_list.insertItem(0, prefix + '|' + file_name)
        self.update_log_dict(temp_dict, file_name)
        if self.running_tasks == 0:
            self.parent.set_enabled_hbox_lists(True)

    def create_start_signal_function(self, detector):
        def new_start_signal_function(*args, **kwargs):
            if detectors[detector]['monitor_signal_start_value'] is None:
                self.log_signal.emit(detector + '_start')
            else:
                if kwargs['char_value'] == detectors[detector]['monitor_signal_start_value']:
                    self.log_signal.emit(detector + '_start')
                if detectors[detector]['monitor_signal_start'] == detectors[detector]['monitor_signal_end']:
                    if kwargs['char_value'] == detectors[detector]['monitor_signal_end_value']:
                        self.log_signal.emit(detector + '_end')
        return new_start_signal_function

    def create_end_signal_function(self, detector):
        def new_end_signal_function(*args, **kwargs):
            if detectors[detector]['monitor_signal_end_value'] is None:
                self.log_signal.emit(detector + '_end')
            else:
                if kwargs['char_value'] == detectors[detector]['monitor_signal_end_value']:
                    self.log_signal.emit(detector + '_end')
        return new_end_signal_function

    def output_line_common(self, start_time, exp_time):
        new_heading = self.parent.read_headings()
        if not self.old_heading == new_heading:
            self.parent.log_file.write(new_heading)
            self.old_heading = new_heading

        self.parent.set_enabled_hbox_lists(False)
        temp_dict = self.create_dict()
        temp_dict['Time'] = start_time
        temp_dict['Exp_Time'] = exp_time
        for motor in self.parent.list_motor_short.selectedItems():
            if not self.parent.motor_dict[str(motor.text())]['after']:
                m_value = caget(self.parent.motor_dict[str(motor.text())]['PV'], as_string=True)
                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_dict[str(motor.text())] = m_value
        return temp_dict

    def create_dict(self):
        temp_dict = collections.OrderedDict()
        temp_dict['Time'] = ''
        temp_dict['File_Name'] = ''
        temp_dict['Directory'] = ''
        temp_dict['Exp_Time'] = ''
        for motor in self.parent.list_motor_short.selectedItems():
            temp_dict[str(motor.text())] = ''
        temp_dict['Comments'] = ''
        return temp_dict

    def update_log_dict(self, temp_dict, file_name):
        self.log_dict[str(file_name)] = collections.OrderedDict()
        for key in temp_dict:
            self.log_dict[str(file_name)][key] = temp_dict[key]

    def update_log_label(self):
        file_name = str(self.parent.log_list.currentItem().text())
        try:
            file_name = file_name.split('|', 1)[1]
        except IndexError:
            pass
        file_dir = file_name.replace('/', '\\').rsplit('\\', 1)[0]
        file_file = file_name.replace('/', '\\').rsplit('\\', 1)[-1]
        for row in range(self.parent.log_table.rowCount()):
            self.parent.log_table.removeRow(0)
        row_pos = self.parent.log_table.rowCount()

        for item in self.log_dict[file_name]:
            row_pos = self.parent.log_table.rowCount()
            self.parent.log_table.insertRow(row_pos)
            self.parent.log_table.setItem(row_pos, 0, QTableWidgetItem(item))
            self.parent.log_table.setItem(row_pos, 1, QTableWidgetItem(self.log_dict[file_name][item]))
        self.parent.log_table.resizeColumnsToContents()

    def view_image_file(self):
        file_name = str(self.parent.log_list.currentItem().text()).split('|', 1)
        if file_name[0] == 'IM':
            os.system("start " + file_name[-1])


class StopMonitors(object):
    def __init__(self, parent=None):
        self.parent = parent
        for detector in self.parent.choose_detector_menu.actions():
            if detector.isChecked():
                camonitor_clear(detectors[detector.text()]['monitor_signal_start'])
                if detectors[detector.text()]['monitor_signal_end'] is not None:
                    camonitor_clear(detectors[detector.text()]['monitor_signal_end'])
