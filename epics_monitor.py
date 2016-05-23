import time
from epics import caput, caget, PV, camonitor, camonitor_clear
from connect_epics import epics_config_fixed as epcf
from connect_epics import epics_monitor_config as epmc
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import collections
import os


class StartMonitors(QWidget):
    def __init__(self, parent=None):
        super(StartMonitors, self).__init__()
        self.parent = parent
        self.xrd_temp_dict = collections.OrderedDict()
        self.T_temp_dict = collections.OrderedDict()
        self.us_temp_dict = collections.OrderedDict()
        self.ds_temp_dict = collections.OrderedDict()
        self.ms_temp_dict = collections.OrderedDict()
        self.log_dict = {}

        # connections
        self.xrd_emit = MySignals('XRD_signal', self.parent.motor_dict)
        self.xrd_end_emit = MySignals('XRD_end', self.parent.motor_dict)
        self.T_emit = MySignals('T_signal', self.parent.motor_dict)
        self.T_end_emit = MySignals('T_end', self.parent.motor_dict)
        self.ds_emit = MySignals('ds_signal', self.parent.motor_dict)
        self.us_emit = MySignals('us_signal', self.parent.motor_dict)
        self.ms_emit = MySignals('ms_signal', self.parent.motor_dict)

        self.connect(self.xrd_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.xrd_end_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.T_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.T_end_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.ds_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.us_emit, SIGNAL("new_info(QString)"), self.output_line)
        self.connect(self.ms_emit, SIGNAL("new_info(QString)"), self.output_line)

        # signals to monitor
        camonitor(epmc['XRD_clicked'], callback=self.xrd_signal)
        camonitor(epmc['T_clicked'], callback=self.temp_signal)
        camonitor(epmc['DS_saved'], callback=self.ds_signal)
        camonitor(epmc['US_saved'], callback=self.us_signal)
        camonitor(epmc['MS_saved'], callback=self.ms_signal)

    def xrd_signal(self, **kwargs):
        print 'XRD'
        print kwargs['char_value']
        if kwargs['char_value'] == 'Acquire':
            self.xrd_emit.start()
        elif kwargs['char_value'] == 'Done':
            self.xrd_end_emit.start()

    def temp_signal(self, **kwargs):
        print 'T'
        print kwargs['char_value']
        if kwargs['char_value'] == 'Acquire':
            self.T_emit.start()
        elif kwargs['char_value'] == 'Done':
            self.T_end_emit.start()

    def ds_signal(self, **kwargs):
        print 'DS'
        print kwargs['char_value']
        if kwargs['char_value'] == 'Done':
            self.ds_emit.start()

    def us_signal(self, **kwargs):
        print 'US'
        print kwargs['char_value']
        if kwargs['char_value'] == 'Done':
            self.us_emit.start()

    def ms_signal(self, **kwargs):
        print 'MS'
        print kwargs['char_value']
        if kwargs['char_value'] == 'Done':
            self.ms_emit.start()

    # for XRD and T signals, there is a start time and Done time.
    def output_line(self, sig_name):
        if sig_name == 'XRD_signal':
            self.old_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            self.parent.parent().statusBar().showMessage('XRD Collecting')
            self.xrd_start_done = False
            self.xrd_start_time = time.asctime().replace(' ', '_')
            exp_time = caget(epcf['XRD_exp_t'], as_string=True)
            common_info, self.xrd_temp_dict = self.output_line_common(self.xrd_start_time, exp_time)
            self.xrd_new_line = exp_time + '\t' + common_info
            self.xrd_start_done = True
        elif sig_name == 'XRD_end':
            self.parent.parent().statusBar().showMessage('XRD Collected')
            while not self.xrd_start_done:
                pass
            start_time = time.time()
            new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            while self.old_xrd_file_name == new_xrd_file_name:
                new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
                if time.time() - start_time > 1:
                    break
            new_xrd_file_name = caget(epcf['XRD_file_name'], as_string=True)
            xrd_comments = caget(epcf['XRD_comment'], as_string=True)
            self.output_line_common_end(self.xrd_new_line, new_xrd_file_name, self.xrd_start_time, xrd_comments, 'XRD_',
                                        self.xrd_temp_dict)
            self.parent.html_logger.add_XRD(new_xrd_file_name, self.xrd_temp_dict)
        elif sig_name == 'T_signal':
            self.parent.parent().statusBar().showMessage('T Collecting')
            self.T_start_done = False
            self.T_start_time = time.asctime().replace(' ', '_')
            self.T_start_done = True
        elif sig_name == 'T_end':
            self.parent.parent().statusBar().showMessage('T Collected')
            while not self.T_start_done:
                pass
            detector_T = caget(epcf['T_detector'], as_string=True)
            if detector_T == 'PIMAX_temperature':
                exp_time = caget(epcf['T_exp_t_PIMAX'], as_string=True)
            elif detector_T == 'PIXIS_Temperature':
                exp_time = caget(epcf['T_exp_t_PIXIS'], as_string=True)
            common_info, self.T_temp_dict = self.output_line_common(self.T_start_time, exp_time)
            self.T_new_line = exp_time + '\t' + common_info
            new_T_file_name = caget(epcf['T_file_name'], as_string=True)
            T_comments = self.temperature_comments()
            self.output_line_common_end(self.T_new_line, new_T_file_name, self.T_start_time, T_comments, 'T_',
                                        self.T_temp_dict)
            self.parent.html_logger.add_T(new_T_file_name, self.T_temp_dict)
        elif sig_name == 'ds_signal':
            self.parent.parent().statusBar().showMessage('Downstream Image Collected')
            self.ds_start_time = time.asctime().replace(' ', '_')
            new_ds_file_name = caget(epcf['image_ds_file_name'], as_string=True)
            exp_time = caget(epcf['ds_exp_t'], as_string=True)
            common_info, self.ds_temp_dict = self.output_line_common(self.ds_start_time, exp_time)
            im_comments = self.image_comments('ds')
            self.ds_new_line = exp_time + '\t' + common_info
            self.output_line_common_end(self.ds_new_line, new_ds_file_name, self.ds_start_time, im_comments, 'IM_',
                                        self.ds_temp_dict)
            self.parent.html_logger.add_image(new_ds_file_name, self.ds_temp_dict, 'DS')
        elif sig_name == 'us_signal':
            self.parent.parent().statusBar().showMessage('Upstream Image Collected')
            self.us_start_time = time.asctime().replace(' ', '_')
            new_us_file_name = caget(epcf['image_us_file_name'], as_string=True)
            exp_time = caget(epcf['us_exp_t'], as_string=True)
            common_info, self.us_temp_dict = self.output_line_common(self.us_start_time, exp_time)
            im_comments = self.image_comments('us')
            self.us_new_line = exp_time + '\t' + common_info
            self.output_line_common_end(self.us_new_line, new_us_file_name, self.us_start_time, im_comments, 'IM_',
                                        self.us_temp_dict)
            self.parent.html_logger.add_image(new_us_file_name, self.us_temp_dict, 'US')
        elif sig_name == 'ms_signal':
            self.parent.parent().statusBar().showMessage('Microscope Image Collected')
            self.ms_start_time = time.asctime().replace(' ', '_')
            new_ms_file_name = caget(epcf['image_ms_file_name'], as_string=True)
            exp_time = caget(epcf['ms_exp_t'], as_string=True)
            common_info, self.ms_temp_dict = self.output_line_common(self.ms_start_time, exp_time)
            im_comments = self.image_comments('ms')
            self.ms_new_line = exp_time + '\t' + common_info
            self.output_line_common_end(self.ms_new_line, new_ms_file_name, self.ms_start_time, im_comments, 'IM_',
                                        self.ms_temp_dict)
            self.parent.html_logger.add_image(new_ms_file_name, self.ms_temp_dict, 'MS')

    def output_line_common(self, start_time, exp_time):
            temp_dict = collections.OrderedDict()
            temp_new_line = ''
            temp_dict['Time'] = start_time
            temp_dict['Exp_Time'] = exp_time
            for motor in self.parent.list_motor_short.selectedItems():
                m_value = caget(self.parent.motor_dict[str(motor.text())], as_string=True)
                if m_value == '-2.27e-13':
                    m_value = '0'
                temp_new_line = temp_new_line + m_value + '\t'
                temp_dict[str(motor.text())] = m_value
            return temp_new_line, temp_dict

    def output_line_common_end(self, new_line, file_name, start_time, comments, prefix, temp_dict):
        file_dir = file_name.replace('/', '\\').rsplit('\\', 1)[0]
        file_file = file_name.replace('/', '\\').rsplit('\\', 1)[-1]
        new_line = file_file + '\t' + file_dir + '\t' + new_line
        new_line = start_time + '\t' + new_line + comments + '\n'
        self.parent.log_file.write(new_line)
        self.parent.log_file.flush()
        self.parent.log_list.insertItem(0, prefix + file_name)
        temp_dict['Comments'] = comments
        self.update_log_dict(temp_dict, file_name)

    def update_log_dict(self, temp_dict, file_name):
        self.log_dict[str(file_name)] = collections.OrderedDict()
        for key, value in temp_dict.iteritems():
            self.log_dict[str(file_name)][key] = value

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
        self.parent.log_table.insertRow(row_pos)
        self.parent.log_table.setItem(row_pos, 0, QTableWidgetItem('File'))
        self.parent.log_table.setItem(row_pos, 1, QTableWidgetItem(file_file))
        self.parent.log_table.insertRow(row_pos+1)
        self.parent.log_table.setItem(row_pos+1, 0, QTableWidgetItem('Directory'))
        self.parent.log_table.setItem(row_pos+1, 1, QTableWidgetItem(file_dir))

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
        camonitor_clear(epmc['XRD_clicked'])
        camonitor_clear(epmc['T_clicked'])
        camonitor_clear(epmc['DS_saved'])
        camonitor_clear(epmc['US_saved'])
        camonitor_clear(epmc['MS_saved'])


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
