import sys, time, os
from qtpy import QtWidgets
try:
    from epics import caget
except ImportError:
    epics = None
from connect_epics import epics_prepare as epp
from PIL import Image
from fnmatch import fnmatch
import matplotlib.pyplot as plt
import shutil
import numpy as np
try:
    import thread
except ImportError:
    import _thread as thread


class HtmlLogger(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HtmlLogger, self).__init__()
        self.thumb_size = 1024, 1024
        self.parent = parent
        self.xy_file_dict = {}

        self.xy_checking = False

        self.comment_counter = 0

        # Use T folder to help with finding XRD folder
        T_folder = caget(epp['T_File_Path'], as_string=True)
        dash_ind = T_folder.find('-')
        self.xrd_base_dir = T_folder[:dash_ind+2]
        self.base_dir = str(self.parent.choose_dir)
        self.html_dir = self.base_dir.rsplit('\\')[-1]

    def start_html_logger(self):
        self.template_file = 'T:\\webdata\\13IDDLogFile\\Test\\index.html'
        self.NEWFILE = 'T:\\webdata\\13IDDLogFile\\' + self.html_dir + '\\index.html'
        self.check_one_dir(self.NEWFILE.rsplit('\\', 1)[0], 'Created directory for HTML Log File: ')
        self.check_one_dir(self.NEWFILE.rsplit('\\', 1)[0] + '\\Images', 'Created directory for HTML Log File Images: ')

        if not os.path.isfile(self.NEWFILE):
            self.template_html_log = open(self.template_file, 'r')
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
            print(message + full_path)
        else:
            print(full_path + ' already exists')

    def add_XRD(self, file_name, data):

        file_name = file_name.replace("/DAC", self.xrd_base_dir, 1)
        file_name = file_name.replace("/", "\\")

        img_src, new_file = self.generate_thumbnail_file_name(file_name)

        pattern_src = img_src.replace('.jpg', '.png')
        self.create_XRD_plot_temporary_thumbnail(pattern_src)

        new_data = 'XRD collected:' + '<br>\n'
        new_data = new_data + '<a href="' + img_src + '" target="_blank"><img src="' + img_src + \
                   '" alt="' + img_src + '" style="width:256px;"></a>' + '<a href="' + pattern_src + \
                   '" target="_blank"><img src="' + pattern_src + '" alt="' + pattern_src + '" style="height:256px;">' \
                   '</a>'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'

        self.create_new_html(file_name, new_data)
        self.update_html(file_name)
        self.create_thumbnail(file_name, new_file, True)

    def add_T(self, file_name, data):
        new_data = 'T collected:' + '\n'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'
        self.create_new_html(file_name, new_data)
        self.update_html(file_name)

    def add_image(self, file_name, data, stream):

        img_src, new_file = self.generate_thumbnail_file_name(file_name)

        new_data = stream + ' Image:' + '<br>\n'
        new_data = new_data + '<a href="' + img_src + '" target="_blank"><img src="' + img_src + \
                  '" style="width:256px;"></a>'
        new_data = new_data + self.create_table(file_name, data)
        new_data = new_data + '<hr />' + '\n'

        self.create_new_html(file_name, new_data)
        self.update_html(file_name)
        self.create_thumbnail(file_name, new_file)

    def create_table(self, file_name, data):
        short_name = file_name.rsplit('\\', 1)[-1]
        new_data = '<p><a href="#"" onclick="setTable(\'' + short_name + '\');return false">' + short_name + '</a>'
        new_data = new_data + '\n' + '<table id="' + short_name + '" style="display:none;">'
        new_data = new_data + '\n' + '<caption>' + str(file_name) + '</caption>' + '\n'
        new_data = new_data + '<th>Item</th>' + '<th>Value</ht>' + '\n'
        for key in data:
            new_data = new_data + '<tr><td>' + key + '</td><td>' + data[key] + '</td></tr>' + '\n'
        new_data = new_data + '</table>' + '\n'
        return new_data

    def create_new_html(self, file_name, new_data):
        file_name = file_name.rsplit('\\', 1)[-1]
        file_name = file_name.rsplit('.', 1)[0]
        new_file = 'T:\\webdata\\13IDDLogFile\\' + self.html_dir + '\\' + file_name + '.html'
        template_html_log = open(self.template_file, 'r')
        new_log = open(new_file, 'w')
        for line in template_html_log:
            if '<body>' in line:
                newline = '<body>\n' + new_data
            else:
                newline = line
            new_log.write(newline)
        new_log.close()
        template_html_log.close()

    def update_html(self, file_name):  # There is no way to edit a file, just make a new one and then rename
        temporary_file = 'T:\\webdata\\13IDDLogFile\\temp.html'
        file_name = file_name.rsplit('\\', 1)[-1]
        file_name = file_name.rsplit('.', 1)[0]

        html_log_file = open(self.NEWFILE, 'r')
        temporary_log = open(temporary_file, 'w')
        new_data = '<iframe src="' + file_name + '.html' + '" width="420" height="320"></iframe>' + '\n'
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
        if not self.xy_checking:
            self.xy_checking = True
            thread.start_new_thread(self.check_xy_files, ())
            sys.stdout.flush()

    def check_xy_files(self):
        time0 = time.time()
        pattern = "*.xy"
        for path, subdirs, files in os.walk(self.base_dir + '\\patterns'):
            for name in files:
                if fnmatch(name, pattern):
                    xy_file = os.path.join(path, name)
                    xy_file_mod_time = os.path.getmtime(xy_file)
                    if xy_file in self.xy_file_dict:
                        if self.xy_file_dict[xy_file] == xy_file_mod_time:
                            continue
                    self.xy_file_dict[xy_file] = xy_file_mod_time
                    self.create_XRD_plot_thumbnail(xy_file)
        print(time.time() - time0)
        self.xy_checking = False
        # for key in self.xy_file_dict:
            # print(key + '\t' + time.ctime(self.xy_file_dict[key]))

    def generate_thumbnail_file_name(self, file_name):
        new_file = self.NEWFILE.rsplit('\\', 1)[0] + '\\Images\\'
        new_file = new_file + file_name.rsplit('\\', 1)[-1].rsplit('.', 1)[0] + '.jpg'
        img_src = 'Images\\' + new_file.rsplit('\\', 1)[-1]
        img_src = img_src.replace('\\', '/')
        return img_src, new_file

    def stretch_intensity(self, ima):
        # max_i = ima.max()
        # min_i = ima.min()

        newmax_i = int(np.percentile(ima, 99.9))
        newmin_i = int(np.percentile(ima, 5))

        ind = ima < newmin_i
        ima[ind] = newmin_i
        ind = ima > newmax_i
        ima[ind] = newmax_i
        ima_new = (ima-newmin_i)*255.0/(newmax_i-newmin_i)
        return ima_new

    def create_thumbnail(self, file_name, new_file, isxrd=False):
        try:
            im = Image.open(file_name)
            if isxrd:
                im.mode = 'I'
                im = im.point(lambda i: i*(1./256)).convert('L')
                ima = np.array(im)
                imb = self.stretch_intensity(ima)
                im2 = Image.fromarray(np.uint8(imb))
                im2.thumbnail(self.thumb_size, Image.ANTIALIAS)
                im2.save(new_file, "JPEG")
            else:
                im.thumbnail(self.thumb_size, Image.ANTIALIAS)
                im.save(new_file, "JPEG")
        except (IOError, OSError):
            print("cannot create thumbnail for " + file_name)

    def create_XRD_plot_thumbnail(self, file_name):
        new_dir = self.NEWFILE.rsplit('\\', 1)[0] + '\\Images\\'
        new_file = file_name.split('.xy')[0] + '.png'
        new_file = new_dir + new_file.rsplit('\\', 1)[-1]
        file_data = open(file_name, 'r')
        tth_v = []
        intensity_v = []
        for line in file_data:
            if not line[0] == "#":
                data = line.split()
                tth_v.append(float(data[0]))
                intensity_v.append(float(data[1]))
            elif '2th_deg' in line:
                x_unit = r'$2\theta \degree$'
            elif 'q_A^-1' in line:
                x_unit = r'$q$ $(\AA^{-1})$'
            elif 'd_A' in line:
                x_unit = r'$d$ $(\AA)$'

        plt.plot(tth_v, intensity_v)
        plt.xlabel(x_unit)
        plt.ylabel('intensity')
        plt.title(file_name.rsplit('\\', 1)[-1])
        plt.savefig(new_file)
        plt.clf()

    def create_XRD_plot_temporary_thumbnail(self, file_name):
        empty_thumbnail = 'T:\\webdata\\13IDDLogFile\\empty.png'
        temp_file = 'T:\\webdata\\13IDDLogFile\\' + self.html_dir + '\\' + file_name
        if not os.path.isfile(file_name):
            shutil.copy(empty_thumbnail, temp_file)

    def add_comment_line(self, new_comment):
        self.comment_counter = self.comment_counter + 1
        new_data = '<b>Comment:</b>' + '\n'
        new_data = new_data + '<br>' + new_comment
        new_data = new_data + '<hr />' + '\n'
        file_name = 'comment' + str(self.comment_counter)
        self.create_new_html(file_name, new_data)
        self.update_html(file_name)
        pass
