from qtpy import QtGui, QtCore, QtWidgets


class LogFileWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LogFileWidget, self).__init__(parent)

        # Create Widgets

        self.label_fullpath = QtWidgets.QLabel()
        self.choose_dir_btn = QtWidgets.QPushButton('Choose Folder')
        self.choose_file_name_le = QtWidgets.QLineEdit()
        self.load_log_btn = QtWidgets.QPushButton('Load Log')
        self.reload_log_btn = QtWidgets.QPushButton('Reload Log')
        self.label_start_time = QtWidgets.QLabel('Start Time: ')
        self.label_end_time = QtWidgets.QLabel('End Time: ')
        self.setup_btn = QtWidgets.QPushButton('Setup')
        self.show_log_btn = QtWidgets.QPushButton('Log')
        self.comment_btn = QtWidgets.QPushButton('Comment')
        # self.html_log_cb = QtWidgets.QCheckBox('HTML Log')
        self.choose_detector_tb = QtWidgets.QToolButton()
        self.create_folders_btn = QtWidgets.QPushButton('Create Folders')
        self.start_btn = QtWidgets.QPushButton('Start')
        self.stop_btn = QtWidgets.QPushButton('Stop')

        self.list_pv_short = QtWidgets.QListWidget()
        self.list_pv_names = QtWidgets.QListWidget()
        self.pv_load_btn = QtWidgets.QPushButton('Load')
        self.pv_save_btn = QtWidgets.QPushButton('Save')
        self.pv_remove_btn = QtWidgets.QPushButton('Remove')
        self.pv_clear_btn = QtWidgets.QPushButton('Clear')
        self.pv_add_btn = QtWidgets.QPushButton('Add')
        self.pv_rename_btn = QtWidgets.QPushButton('Rename')
        self.pv_move_up_btn = QtWidgets.QPushButton(u'\u2191')
        self.pv_move_dn_btn = QtWidgets.QPushButton(u'\u2193')
        self.pv_toggle_after_btn = QtWidgets.QPushButton('Before/After')
        self.clear_detectors_stack_btn = QtWidgets.QPushButton('Clear detectors')

        self.log_list = QtWidgets.QListWidget(self)
        self.splitter_log = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.log_table = QtWidgets.QTableWidget(self)
        self.view_image_btn = QtWidgets.QPushButton('Open Image')

        # Set Widget Properties

        for label_item in self.findChildren(QtWidgets.QLabel):
            label_item.setStyleSheet('background-color: white')

        self.setup_btn.setCheckable(True)
        self.show_log_btn.setCheckable(True)
        self.reload_log_btn.hide()
        self.show_log_btn.hide()
        self.comment_btn.hide()
        # self.comment_btn.setToolTip('Add a comment to the HTML log')
        # self.html_log_cb.setChecked(False)
        # self.html_log_cb.hide()
        # self.html_log_cb.setToolTip('Enable logging to HTML file')
        self.choose_detector_tb.setText('Detectors')
        self.choose_detector_menu = QtWidgets.QMenu()
        self.choose_detector_tb.setMenu(self.choose_detector_menu)
        self.choose_detector_tb.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        self.stop_btn.setEnabled(False)
        self.list_pv_short.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_pv_names.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.pv_load_btn.setToolTip('Load does not clear the list')
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
        self.setup_pvs_frame = QtWidgets.QFrame(self)
        self.setup_pvs_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
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
        # hbox_file.addWidget(self.html_log_cb)
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
        hbox_control.addWidget(self.create_folders_btn)
        hbox_control.addWidget(self.show_log_btn)
        hbox_control.addWidget(self.start_btn)
        hbox_control.addWidget(self.stop_btn)

        self.hbox_lists.addWidget(self.list_pv_short)
        self.hbox_lists.addWidget(self.list_pv_names)
        self.grid_list_buttons.addWidget(self.pv_move_up_btn, 0, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_move_dn_btn, 2, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_load_btn, 0, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_save_btn, 0, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_remove_btn, 1, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_clear_btn, 1, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_add_btn, 2, 1, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_rename_btn, 2, 2, 1, 1)
        self.grid_list_buttons.addWidget(self.pv_toggle_after_btn, 1, 0, 1, 1)
        self.grid_list_buttons.addWidget(self.clear_detectors_stack_btn, 3, 2, 1, 1)
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
        self.setup_pvs_frame.setLayout(self.hbox_lists)
        self.setup_pvs_frame.hide()

        self.vbox.addWidget(self.setup_pvs_frame)

        self.vbox.addWidget(self.log_frame)
        # self.vbox.addStretch(1)
        parent.setLayout(self.vbox)
