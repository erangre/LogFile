import time
from epics import caput, caget, PV, camonitor, camonitor_clear
from connect_epics import epics_config_fixed as epcf
from connect_epics import epics_monitor_config as epmc
from connect_epics import epics_BG_config as ebgcfg
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
import os


class StartMonitors(QWidget):
    def __init__(self, parent=None):
        super(StartMonitors, self).__init__()
        self.parent = parent
        self.xrd_temp_dict = collections.OrderedDict()
        self.pxrd_temp = []
        self.pxrd_temp_dict = collections.OrderedDict()
        self.T_temp_dict = collections.OrderedDict()
        self.us_temp_dict = collections.OrderedDict()
        self.ds_temp_dict = collections.OrderedDict()
        self.ms_temp_dict = collections.OrderedDict()
        self.log_dict = {}
        self.old_heading = self.parent.read_headings()
        self.running_tasks = 0
        self.xrd_start_done = True

        # connections
        self.xrd_emit = MySignals('XRD_signal', self.parent.motor_dict)
        self.xrd_end_emit = MySignals('XRD_end', self.parent.motor_dict)
        self.pxrd_emit = MySignals('pXRD_signal', self.parent.motor_dict)
        self.pxrd_end_emit = MySignals('pXRD_end', self.parent.motor_dict)
        # self.pxrd_abort_emit = MySignals('pXRD_abort', self.parent.motor_dict)
        self.T_emit = MySignals('T_signal', self.parent.motor_dict)
        self.T_end_emit = MySignals('T_end', self.parent.motor_dict)
        self.ds_emit = MySignals('ds_signal', self.parent.motor_dict)
        self.us_emit = MySignals('us_signal', self.parent.motor_dict)
        self.ms_emit = MySignals('ms_signal', self.parent.motor_dict)
        self.pec_xrd_emit = MySignals('pec_XRD_signal', self.parent.motor_dict)
        self.pec_xrd_end_emit = MySignals('pec_XRD_end', self.parent.motor_dict)

        self.connect(self.xrd_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.xrd_end_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.pxrd_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.pxrd_end_emit, SIGNAL("new_info(QString)"), self.output_line)
        # self.connect(self.pxrd_abort_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.T_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.T_end_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.ds_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.us_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.ms_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.pec_xrd_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.pec_xrd_end_emit, SIGNAL("new_info(QString)"), self.output_line)

        # signals to monitor
        # camonitor(epmc['XRD_clicked'], callback=self.xrd_signal)
        if not self.parent.detector == 4:
            camonitor(epmc['T_clicked'], callback=self.temp_signal)
            camonitor(epmc['DS_saved'], callback=self.ds_signal)
            camonitor(epmc['US_saved'], callback=self.us_signal)
            camonitor(epmc['MS_saved'], callback=self.ms_signal)
        if self.parent.detector == 1 or self.parent.detector == 3:
            camonitor(epmc['XRD_file_write'], callback=self.xrd_file_signal)
            camonitor(epmc['XRD_detector_state'], callback=self.xrd_signal)
        if self.parent.detector == 2 or self.parent.detector == 3:
            camonitor(epmc['pilatus_new_frame'], callback=self.pxrd_frame_signal)
            camonitor(epmc['pilatus_tiff_written'], callback=self.pxrd_tiff_write_signal)
            camonitor(epmc['pilatus_status'], callback=self.pxrd_status_signal)
        if self.parent.detector == 4:
            camonitor(epmc['pec_file_write'], callback=self.pec_xrd_file_signal)
            camonitor(epmc['pec_detector_state'], callback=self.pec_xrd_signal)

    def xrd_signal(self, **kwargs):
        if kwargs['char_value'] == 'Acquire':
            self.xrd_emit.start()

    def xrd_file_signal(self, **kwargs):
        if kwargs['char_value'] == 'Done':
            self.xrd_end_emit.start()

    def pec_xrd_signal(self, **kwargs):
        if kwargs['char_value'] == 'Acquire':
            self.pec_xrd_emit.start()

    def pec_xrd_file_signal(self, **kwargs):
        if kwargs['char_value'] == 'Done':
            self.pec_xrd_end_emit.start()

    def pxrd_frame_signal(self, **kwargs):
        print('New pilatus frame #' + str(kwargs['char_value']))
        self.pxrd_emit.start()

    def pxrd_tiff_write_signal(self, **kwargs):
        print('New pilatus Tiff file: ' + kwargs['char_value'])
        self.pxrd_end_emit.start()

    def pxrd_status_signal(self, **kwargs):
        if kwargs['char_value'] == "Acqusition aborted":
            self.running_tasks-=len(self.pxrd_temp)
            self.pxrd_temp = []

    def temp_signal(self, **kwargs):
        if kwargs['char_value'] == 'Acquire':
            self.T_emit.start()
        elif kwargs['char_value'] == 'Done':
            self.T_end_emit.start()

    def ds_signal(self, **kwargs):
        if kwargs['char_value'] == 'Done':
            self.ds_emit.start()

    def us_signal(self, **kwargs):
        if kwargs['char_value'] == 'Done':
            self.us_emit.start()

    def ms_signal(self, **kwargs):
        if kwargs['char_value'] == 'Done':
            self.ms_emit.start()

    # for XRD and T signals, there is a start time and Done time.
    def output_line(self, sig_name):
        if sig_name == 'XRD_signal':
            if caget(ebgcfg['XRD_frame_type'], as_string=False) == 0:  # normal frame
                self.running_tasks += 1
            else:  # background file
                return
            self.old_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            self.parent.parent().statusBar().showMessage('XRD Collecting')
            self.xrd_start_done = False
            self.xrd_start_time = time.asctime().replace(' ', '_')
            exp_time = caget(epcf['XRD_exp_t'], as_string=True)
            self.xrd_temp_dict = self.output_line_common(self.xrd_start_time, exp_time)
            self.xrd_start_done = True
        elif sig_name == 'XRD_end':
            self.parent.parent().statusBar().showMessage('XRD Collected')
            while not self.xrd_start_done:
                pass
            start_time = time.time()
            new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            while self.old_xrd_file_name == new_xrd_file_name:
                new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
                if time.time() - start_time > 5:
                    break
            self.running_tasks -= 1
            new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            xrd_comments = caget(epcf['XRD_comment'], as_string=True)
            self.output_line_common_end(new_xrd_file_name, xrd_comments, 'XRD_', self.xrd_temp_dict)
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_XRD(new_xrd_file_name, self.xrd_temp_dict)
        elif sig_name == 'pXRD_signal':
            self.running_tasks += 1
            self.parent.parent().statusBar().showMessage('XRD Collecting on Pilatus')
            self.pxrd_start_time = time.asctime().replace(' ', '_')
            exp_time = caget(epcf['pXRD_exp_t'], as_string=True)
            self.pxrd_temp.append(self.output_line_common(self.pxrd_start_time, exp_time).copy())
        elif sig_name == 'pXRD_end':
            self.parent.parent().statusBar().showMessage('XRD Collected on Pilatus')
            self.running_tasks -= 1
            new_pxrd_file_name = caget(epcf['pXRD_file_name'], as_string=True)
            pxrd_comments = caget(epcf['pXRD_comment'], as_string=True)
            self.output_line_common_end(new_pxrd_file_name, pxrd_comments, 'pXRD_', self.pxrd_temp[0])
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_XRD(new_pxrd_file_name, self.pxrd_temp[0])
            del self.pxrd_temp[0]

        elif sig_name == 'T_signal':
            self.running_tasks += 1
            self.parent.parent().statusBar().showMessage('T Collecting')
            self.T_start_done = False
            self.T_start_time = time.asctime().replace(' ', '_')
            detector_T = caget(epcf['T_detector'], as_string=True)  # moved this whole part including output_common
                                                                    # from the T_end. make sure it works.
            if detector_T == 'PIMAX_temperature':
                exp_time = caget(epcf['T_exp_t_PIMAX'], as_string=True)
            elif detector_T == 'PIXIS_Temperature':
                exp_time = caget(epcf['T_exp_t_PIXIS'], as_string=True)
            else:
                exp_time = caget(epcf['T_exp_t_PIXIS'], as_string=True)  # CHECK THIS
            self.T_temp_dict = self.output_line_common(self.T_start_time, exp_time)
            self.T_start_done = True
        elif sig_name == 'T_end':
            self.parent.parent().statusBar().showMessage('T Collected')
            while not self.T_start_done:
                pass
            self.running_tasks -= 1
            if caget(ebgcfg['T_change_image_mode']) == 2:
                new_T_file_name = caget(epcf['T_BG_file_name'], as_string=True)
            else:
                new_T_file_name = caget(epcf['T_file_name'], as_string=True)
            T_comments = self.temperature_comments()
            time.sleep(0.5)
            self.output_line_common_end(new_T_file_name, T_comments, 'T_', self.T_temp_dict)
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_T(new_T_file_name, self.T_temp_dict)
        elif sig_name == 'ds_signal':
            self.parent.parent().statusBar().showMessage('Downstream Image Collected')
            self.ds_start_time = time.asctime().replace(' ', '_')
            new_ds_file_name = caget(epcf['image_ds_file_name'], as_string=True)
            exp_time = caget(epcf['ds_exp_t'], as_string=True)
            self.ds_temp_dict = self.output_line_common(self.ds_start_time, exp_time)
            im_comments = self.image_comments('ds')
            self.output_line_common_end(new_ds_file_name, im_comments, 'IM_', self.ds_temp_dict)
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_image(new_ds_file_name, self.ds_temp_dict, 'DS')
        elif sig_name == 'us_signal':
            self.parent.parent().statusBar().showMessage('Upstream Image Collected')
            self.us_start_time = time.asctime().replace(' ', '_')
            new_us_file_name = caget(epcf['image_us_file_name'], as_string=True)
            exp_time = caget(epcf['us_exp_t'], as_string=True)
            self.us_temp_dict = self.output_line_common(self.us_start_time, exp_time)
            im_comments = self.image_comments('us')
            self.output_line_common_end(new_us_file_name, im_comments, 'IM_', self.us_temp_dict)
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_image(new_us_file_name, self.us_temp_dict, 'US')
        elif sig_name == 'ms_signal':
            self.parent.parent().statusBar().showMessage('Microscope Image Collected')
            self.ms_start_time = time.asctime().replace(' ', '_')
            new_ms_file_name = caget(epcf['image_ms_file_name'], as_string=True)
            exp_time = caget(epcf['ms_exp_t'], as_string=True)
            self.ms_temp_dict = self.output_line_common(self.ms_start_time, exp_time)
            im_comments = self.image_comments('ms')
            self.output_line_common_end(new_ms_file_name, im_comments, 'IM_', self.ms_temp_dict)
            if self.parent.html_log_cb.isChecked():
                self.parent.html_logger.add_image(new_ms_file_name, self.ms_temp_dict, 'MS')
        elif sig_name == 'pec_XRD_signal':
            if caget(ebgcfg['pec_XRD_frame_type'], as_string=False) == 0:  # normal frame
                self.running_tasks += 1
            else:  # background file
                return
            self.old_xrd_file_name = caget(epcf['pec_XRD_file_name'], as_string=True)
            self.parent.parent().statusBar().showMessage('pec XRD Collecting')
            self.xrd_start_done = False
            self.xrd_start_time = time.asctime().replace(' ', '_')
            exp_time = caget(epcf['pec_XRD_exp_t'], as_string=True)
            self.xrd_temp_dict = self.output_line_common(self.xrd_start_time, exp_time)
            self.xrd_start_done = True
        elif sig_name == 'pec_XRD_end':
            self.parent.parent().statusBar().showMessage('pec XRD Collected')
            while not self.xrd_start_done:
                pass
            start_time = time.time()
            new_xrd_file_name = caget(epcf['pec_XRD_file_name'], as_string=True)
            while self.old_xrd_file_name == new_xrd_file_name:
                new_xrd_file_name = caget(epcf['pec_XRD_file_name'], as_string=True)
                if time.time() - start_time > 5:
                    break
            self.running_tasks -= 1
            new_xrd_file_name = caget(epcf['pec_XRD_file_name'], as_string=True)
            xrd_comments = caget(epcf['pec_XRD_comment'], as_string=True)
            self.output_line_common_end(new_xrd_file_name, xrd_comments, 'XRD_', self.xrd_temp_dict)
            # if self.parent.html_log_cb.isChecked():
            #     self.parent.html_logger.add_XRD(new_xrd_file_name, self.xrd_temp_dict)

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

    def output_line_common_end(self, file_name, comments, prefix, temp_dict):
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
        self.parent.log_list.insertItem(0, prefix + file_name)
        self.update_log_dict(temp_dict, file_name)
        if self.running_tasks == 0:
            self.parent.set_enabled_hbox_lists(True)

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

    def temperature_comments(self):
        Tfilter = caget(epcf['T_filter'], as_string=False)
        if Tfilter:
            T_comment = 'In'
        else:
            T_comment = 'Out'
        T_comment = 'Filter: ' + T_comment
        Tshutter = caget(epcf['T_shutter'], as_string=False)
        if Tshutter:
            T_comment = T_comment + ', Laser Shutter: Open'
        else:
            T_comment = T_comment + ', Laser Shutter: CLOSED'
        return T_comment

    def image_comments(self, stream):
        im_comments = 'Gain: '
        if stream == 'ds':
            im_comments = im_comments + caget(epcf['ds_gain'], as_string=True) + ', '
        elif stream == 'us':
            im_comments = im_comments + caget(epcf['us_gain'], as_string=True) + ', '
        elif stream == 'ms':
            im_comments = im_comments + caget(epcf['ms_gain'], as_string=True) + ', '
            zoom_state = caget(epcf['ms_zoom'], as_string=True)
            im_comments = im_comments + 'Zoom: ' + zoom_state
            return im_comments
        ds_on_off = self.on_off(caget(epcf['ds_light_sw'], as_string=False))
        us_on_off = self.on_off(caget(epcf['us_light_sw'], as_string=False))
        im_comments = im_comments + 'DS Light: ' + ds_on_off + ':' + caget(epcf['ds_light_int'], as_string=True)
        im_comments = im_comments + ', US Light: ' + us_on_off + ':' + caget(epcf['us_light_int'], as_string=True)
        return im_comments

    def on_off(self, zero_one):
        if zero_one:
            return 'ON'
        else:
            return 'OFF'

    def update_log_label(self):
        file_name = str(self.parent.log_list.currentItem().text())
        file_name = file_name.split('_', 1)[1]
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
        file_name = str(self.parent.log_list.currentItem().text()).split('_', 1)
        if file_name[0] == 'IM':
            os.system("start " + file_name[-1])


class StopMonitors(object):
    def __init__(self, parent=None):
        # camonitor_clear(epmc['XRD_clicked'])
        camonitor_clear(epmc['T_clicked'])
        camonitor_clear(epmc['DS_saved'])
        camonitor_clear(epmc['US_saved'])
        camonitor_clear(epmc['MS_saved'])
        camonitor_clear(epmc['XRD_file_write'])
        camonitor_clear(epmc['XRD_detector_state'])


class MySignals(QThread):
    def __init__(self, signal_name, motor_names):
        # super(MySignals, self).__init__()  # Replaced by next line
        QThread.__init__(self)
        self.signal_name = signal_name
        self.motor_names = motor_names

    def __del__(self):
        self.wait()

    def run(self):
        self.emit(SIGNAL('new_info(QString)'), self.signal_name)
