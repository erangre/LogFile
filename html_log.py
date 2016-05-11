import sys, time, os
from PyQt4 import QtGui, QtCore
from epics import caput
from epics import caget
from connect_epics import epics_BG_config as ebgcfg
import epics_monitor
from FolderMaker import FolderMaker
import collections
from PIL import Image


class HtmlLogger(object):
    def __init__(self, parent=None):
        super(HtmlLogger, self).__init__()
        self.thumb_size = 1024, 1024
        pass

    def start_html_logger(self):
        template_file = 'T:\\webdata\\13IDDLogFile\\Test\\index.html'
        self.NEWFILE = 'T:\\webdata\\13IDDLogFile\\Test\\1\\index.html'
        self.check_one_dir(self.NEWFILE.rsplit('\\', 1)[0], 'Created directory for HTML Log File: ')
        self.check_one_dir(self.NEWFILE.rsplit('\\', 1)[0] + '\\Images', 'Created directory for HTML Log File Images: ')
        self.template_html_log = open(template_file, 'r')
        self.html_log_file = open(self.NEWFILE, 'w')

        for line in self.template_html_log:
            if '<title>' in line:
                mod_line = '<title>HTML Log File Testing</title>\n'
                self.html_log_file.write(mod_line)
            elif '</body>' in line:
                mod_line = '<p>Started logging at: ' + time.asctime() + '</p>\n' + line
                self.html_log_file.write(mod_line)
            else:
                self.html_log_file.write(line)
        self.html_log_file.close()
        self.template_html_log.close()

    def check_one_dir(self, full_path, message):
        if not os.path.isdir(full_path):
            os.makedirs(full_path)
            print message + full_path
        else:
            print full_path + ' already exists'

    def add_XRD(self, file_name, data):
        new_data = 'XRD collected:' + '\n'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'
        self.update_html(new_data)

    def add_T(self, file_name, data):
        new_data = 'T collected:' + '\n'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'
        self.update_html(new_data)

    def add_image(self, file_name, data, stream):
        new_file = self.NEWFILE.rsplit('\\', 1)[0] + '\\Images\\'
        new_file = new_file + file_name.rsplit('\\', 1)[-1].rsplit('.', 1)[0] + '.jpg'
        try:
            im = Image.open(file_name)
            im.thumbnail(self.thumb_size, Image.ANTIALIAS)
            im.save(new_file, "JPEG")
        except IOError:
            print "cannot create thumbnail for " + file_name

        img_src = 'Images\\' + new_file.rsplit('\\', 1)[-1]
        new_data = stream + ' Image:' + '<br>\n'
        new_data = new_data + '<a href="' + img_src + '" target="_blank"><img src="' + img_src + \
                  '" style="width:256px;"></a>'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'

        self.update_html(new_data)

    def create_table(self, file_name, data):
        new_data = '<table>' + '\n' + '<caption>' + str(file_name) + '</caption>' + '\n'
        new_data = new_data + '<th>Item</th>' + '<th>Value</ht>' + '\n'
        for key, item in data.iteritems():
            new_data = new_data + '<tr><td>' + key + '</td><td>' + item + '</td></tr>' + '\n'
        new_data = new_data + '</table>' + '\n'
        return new_data

    def create_thumbnail(self):
        pass

    def update_html(self, new_data):
        temporary_file = 'T:\\webdata\\13IDDLogFile\\Test\\temp.html'
        html_log_file = open(self.NEWFILE, 'r')
        temporary_log = open(temporary_file, 'w')
        for line in html_log_file:
            if '<body>' in line:
                newline = '<body>\n' + new_data
            else:
                newline = line
            temporary_log.write(newline)
        temporary_log.close()
        html_log_file.close()
        os.remove(self.NEWFILE)
        os.rename(temporary_file, self.NEWFILE)
