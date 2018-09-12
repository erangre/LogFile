import time
try:
    from epics import caput, caget, PV, camonitor, camonitor_clear
except ImportError:
    epics = None

from qtpy import QtCore
from qtpy.QtWidgets import *
import collections
import os
from detectors import detectors


class StartMonitors(QWidget):
    log_signal = QtCore.Signal(str)
    abort_signal = QtCore.Signal(str)

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
        self.id = 0

        # connections

        self.log_signal.connect(self.signal_received)
        self.abort_signal.connect(self.abort_signal_received)

        self.chosen_detectors = {}
        for detector in self.parent.choose_detector_menu.actions():
            if detector.isChecked():
                self.chosen_detectors[detector.text()] = {}

        for detector in self.chosen_detectors:
            self.chosen_detectors[detector]['temp_dict'] = []
            # self.chosen_detectors[detector]['aborted_id_list'] = []
            self.chosen_detectors[detector]['start_signal_function'] = self.create_start_signal_function(detector)
            camonitor(detectors[detector]['monitor_signal_start'],
                      callback=self.chosen_detectors[detector]['start_signal_function'])
            if not detectors[detector]['monitor_signal_end'] is None and \
                    not detectors[detector]['monitor_signal_end'] == detectors[detector]['monitor_signal_start']:
                self.chosen_detectors[detector]['end_signal_function'] = self.create_end_signal_function(detector)
                camonitor(detectors[detector]['monitor_signal_end'],
                          callback=self.chosen_detectors[detector]['end_signal_function'])
            if not detectors[detector].get('monitor_signal_abort', None) is None:
                self.chosen_detectors[detector]['abort_signal_function'] = self.create_abort_signal_function(detector)
                camonitor(detectors[detector]['monitor_signal_abort'],
                          callback=self.chosen_detectors[detector]['abort_signal_function'])

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
            # First clean up aborted signals
            # (this caused problems like an endless loop sometimes)
            # num_aborted = len(self.chosen_detectors[detector]['aborted_id_list'])
            # while num_aborted > 0:
            #     if self.chosen_detectors[detector]['temp_dict'][0]['id'] in \
            #             self.chosen_detectors[detector]['aborted_id_list']:
            #         print(detector + ': ' + str(len(self.chosen_detectors[detector]['temp_dict'])))
            #         del self.chosen_detectors[detector]['temp_dict'][0]
            #         self.running_tasks -= 1
            #         num_aborted -= 1

            # Now deal with new signal
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
                del (self.chosen_detectors[detector]['temp_dict'][0])

        elif phase == 'end' and len(self.chosen_detectors[detector]['temp_dict']) > 0:
            delay = detectors[detector].get('delay_before_end', None)
            if delay:
                time.sleep(delay)

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
            # try:
            #     del(self.chosen_detectors[detector]['aborted_id_list'][0])
            # except IndexError:
            #     pass
            del(self.chosen_detectors[detector]['temp_dict'][0])
            pvs_to_clear = detectors[detector].get('end_clear_pvs', None)
            if pvs_to_clear:
                for pv in pvs_to_clear:
                    caput(pv, '', wait=True)
        print(str(time.time() - t0))

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
        # t0 = time.time()
        self.id += 1
        new_heading = self.parent.read_headings()
        if not self.old_heading == new_heading:
            self.parent.log_file.write(new_heading)
            self.old_heading = new_heading

        self.parent.set_enabled_hbox_lists(False)
        temp_dict = self.create_dict()
        temp_dict['id'] = self.id
        temp_dict['Time'] = start_time
        temp_dict['Exp_Time'] = exp_time
        for motor in self.parent.list_motor_short.selectedItems():
            if not self.parent.motor_dict[str(motor.text())]['after']:
                # t1 = time.time()
                m_value = caget(self.parent.motor_dict[str(motor.text())]['PV'])
                if type(m_value) is not str:
                    if abs(m_value) < 1:
                        m_value = '{:.3g}'.format(m_value)
                    else:
                        m_value = '{:.3f}'.format(m_value)

                # print(time.time()-t1, ' for ', self.parent.motor_dict[str(motor.text())]['PV'])
                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_dict[str(motor.text())] = m_value
        return temp_dict

    def output_line_common_end(self, prefix, file_name, comments, temp_dict):
        temp_dict['Directory'] = file_name.replace('/', '\\').rsplit('\\', 1)[0]
        temp_dict['File_Name'] = file_name.replace('/', '\\').rsplit('\\', 1)[-1]

        for motor in self.parent.list_motor_short.selectedItems():
            if self.parent.motor_dict[str(motor.text())]['after']:
                m_value = caget(self.parent.motor_dict[str(motor.text())]['PV'])
                if type(m_value) is not str:
                    if abs(m_value) < 1:
                        m_value = '{:.3g}'.format(m_value)
                    else:
                        m_value = '{:.3f}'.format(m_value)

                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_dict[str(motor.text())] = m_value
        temp_dict['Comments'] = comments
        new_line = ''
        for key in temp_dict:
            if not key == 'id':
                new_line = new_line + str(temp_dict[key]) + '\t'
        new_line = new_line + '\n'
        self.parent.log_file.write(new_line)
        self.parent.log_file.flush()
        self.parent.log_list.insertItem(0, prefix + '|' + file_name)
        self.update_log_dict(temp_dict, file_name)
        if self.running_tasks == 0:
            self.parent.set_enabled_hbox_lists(True)

    def abort_signal_received(self, sig_name):
        detector, phase = sig_name.rsplit('_', 1)
        if phase == 'abort':
            # self.chosen_detectors[detector]['aborted_id_list'] = []
            while len(self.chosen_detectors[detector]['temp_dict']) > 0:
                del self.chosen_detectors[detector]['temp_dict'][0]
                self.running_tasks -= 1
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

    def create_abort_signal_function(self, detector):
        def new_abort_signal_function(*args, **kwargs):
            if kwargs['char_value'] in detectors[detector]['monitor_signal_abort_value']:
                self.abort_signal.emit(detector + '_abort')

        return new_abort_signal_function

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

    def clear_detectors_stack_btn_clicked(self):
        for detector in self.chosen_detectors:
            while len(self.chosen_detectors[detector]['temp_dict']) > 0:
                print(detector + ': ' + str(len(self.chosen_detectors[detector]['temp_dict'])))
                # del self.chosen_detectors[detector]['aborted_id_list'][0]
                del self.chosen_detectors[detector]['temp_dict'][0]
        self.running_tasks = 0
        self.parent.set_enabled_hbox_lists(True)


class StopMonitors(object):
    def __init__(self, parent=None):
        self.parent = parent
        for detector in self.parent.choose_detector_menu.actions():
            if detector.isChecked():
                camonitor_clear(detectors[detector.text()]['monitor_signal_start'])
                if detectors[detector.text()]['monitor_signal_end'] is not None:
                    camonitor_clear(detectors[detector.text()]['monitor_signal_end'])
