import collections

detectors = collections.OrderedDict()

detectors['marccd2'] = {
    'name': '13MARCCD2',
    'prefix': 'XRD_',
    'monitor_signal_start': '13MARCCD2:cam1:DetectorState_RBV',
    'monitor_signal_start_value': 'Acquire',
    'monitor_signal_end': '13MARCCD2:TIFF1:WriteFile_RBV',
    'monitor_signal_end_value': 'Done',
    'track_running_tasks': True,
    'frame_type_PV': '13MARCCD2:cam1:FrameType',
    'frame_type_values': {0: 'normal',
                          1: 'background',
                          },
    'frame_type_messages': {0: 'MARCCD2 XRD',
                            1: 'MARCCD2 XRD BG',
                            },
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13MARCCD2:cam1:AcquireTime'},
    'new_file_name': {0: '13MARCCD2:TIFF1:FullFileName_RBV'},
    'comments': '{0}',
    'comments_PVs': ['13MARCCD2:AcquireSequence.STRA'],
    'comments_values': [None],
    'sleep_after_end': 0.0,
    'default_base_name': 'LaB6',
    'default_rel_dir': '',
    'soft_link': '/DAC/',
    'file_path': '13MARCCD2:TIFF1:FilePath',
    'file_name': '13MARCCD2:TIFF1:FileName',
    'file_number': '13MARCCD2:TIFF1:FileNumber',
}

detectors['pilatus3'] = {
    'name': '13PIL3',
    'prefix': 'XRD_',
    'monitor_signal_start': '13PIL3:cam1:ArrayCounter_RBV',
    'monitor_signal_start_value': None,
    'monitor_signal_end': '13PIL3:TIFF1:FullFileName_RBV',
    'monitor_signal_end_value': None,
    'monitor_signal_abort': '13PIL3:cam1:StatusMessage_RBV',
    'monitor_signal_abort_value': 'Acquisition aborted',
    'track_running_tasks': True,
    'frame_type_PV': None,
    'frame_type_values': 0,
    'frame_type_messages': {0: 'Pilatus XRD'},
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13PIL3:cam1:AcquireTime_RBV'},
    'new_file_name': {0: '13PIL3:TIFF1:FullFileName_RBV'},
    'comments': '{0}',
    'comments_PVs': ['13PIL3:AcquireSequence.STRA'],
    'comments_values': [None],
    'sleep_after_end': 0.0,
    'default_base_name': 'LaB6',
    'default_rel_dir': '',
    'soft_link': '/DAC/',
    'file_path': '13PIL3:TIFF1:FilePath',
    'file_name': '13PIL3:TIFF1:FileName',
    'file_number': '13PIL3:TIFF1:FileNumber',
}

detectors['marip2'] = {
    'name': '13MAR345_2',
    'prefix': 'XRD_',
    'monitor_signal_start': '13MAR345_2:cam1:DetectorState_RBV',
    'monitor_signal_start_value': 'Exposing',
    'monitor_signal_end': '13MAR345_2:TIFF1:WriteFile_RBV',
    'monitor_signal_end_value': 'Done',
    'track_running_tasks': True,
    'frame_type_PV': None,
    'frame_type_values': 0,
    'frame_type_messages': {0: 'MARIP2 XRD'},
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13MAR345_2:cam1:AcquireTime_RBV'},
    'new_file_name': {0: '13MAR345_2:TIFF1:FullFileName_RBV'},
    'comments': 'Pixel Size {0}. {1}',
    'comments_PVs': ['13MAR345_2:cam1:ScanResolution_RBV', '13MAR345_2:AcquireSequence.STRA'],
    'comments_values': [None, None],
    'sleep_after_end': 0.0,
    'default_base_name': 'LaB6',
    'default_rel_dir': '',
    'file_path': '13MAR345_2:TIFF1:FilePath',
    'file_name': '13MAR345_2:TIFF1:FileName',
    'file_number': '13MAR345_2:TIFF1:FileNumber',
}

detectors['lightfield'] =  {
    'name': '13IDDLF1',
    'prefix': 'T_',
    'monitor_signal_start': '13IDDLF1:cam1:Acquire',
    'monitor_signal_start_value': 'Acquire',
    'monitor_signal_end': '13IDDLF1:cam1:Acquire',
    'monitor_signal_end_value': 'Done',
    'track_running_tasks': False,
    'frame_type_PV': '13MARCCD2:cam1:FrameType',
    'frame_type_values': {0: 'normal',
                          2: 'background',
                          },
    'frame_type_messages': {0: 'T',
                            2: 'T BG',
                            },
    'new_file_name': {0: '13IDDLF1:cam1:FullFileName_RBV',
                      2: '13IDDLF1:cam1:LFBackgroundFullFile_RBV'},
    'image_type_PV': '13IDDLF1:cam1:LFExperimentName',
    'image_type_values': {0: 'PIMAX_Ruby',
                          1: 'PIMAX_temperature',
                          2: 'PIMAX_temperature_pulsed',
                          3: 'PIXIS_Raman',
                          4: 'PIXIS_Ruby',
                          5: 'PIXIS_Temperature',
                          },
    'image_type_messages': {0: 'PIMAX Ruby',
                            1: 'PIMAX T',
                            2: 'PIMAX pulsed T',
                            3: 'PIXIS Raman',
                            4: 'PIXIS Ruby',
                            5: 'PIXIS T',
                            },
    'image_type_exposure_time': {0: '13IDDLF1:cam1:LFRepGateWidth',
                                 1: '13IDDLF1:cam1:LFRepGateWidth',
                                 2: '13IDDLF1:cam1:LFRepGateWidth',
                                 3: '13IDDLF1:cam1:AcquireTime',
                                 4: '13IDDLF1:cam1:AcquireTime',
                                 5: '13IDDLF1:cam1:AcquireTime',
                                 },

    'comments': 'Filter: {0}, Laser Shutter {1}',
    'comments_PVs': ['13IDD:Unidig1Bi4.VAL', '13IDD:Unidig2Bi4.VAL'],
    'comments_values': [
        {0: 'Out',
         1: 'In',
         },
        {0: 'CLOSED',
         1: 'Open',
         }
    ],
    'sleep_after_end': 0.5,
    'default_base_name': 't',
    'default_rel_dir': 'T',
    'file_path': '13IDDLF1:cam1:FilePath',
    'file_name': '13IDDLF1:cam1:FileName',
    'file_number': '13IDDLF1:cam1:FileNumber',
}

detectors['us_visual'] = {
    'name': '13IDD_PG1',
    'prefix': 'IM_',
    'monitor_signal_start': '13IDD_PG1:TIFF1:WriteFile_RBV',
    'monitor_signal_start_value': 'Done',
    'monitor_signal_end': None,
    'monitor_signal_end_value': None,
    'track_running_tasks': False,
    'frame_type_PV': None,
    'frame_type_values': 0,
    'frame_type_messages': {0: 'US Image', },
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13IDD_PG1:cam1:AcquireTime',
                                 },
    'new_file_name': {0: '13IDD_PG1:TIFF1:FullFileName_RBV',
                      },
    'comments': 'Gain: {0}, DS Light: {1}:{2}, US Light: {3}:{4}',
    'comments_PVs': ['13IDD_PG1:cam1:GainValAbs',
                     '13IDD:Unidig1Bo22',
                     '13IDD:DAC2_2.VAL',
                     '13IDD:Unidig1Bo20',
                     '13IDD:DAC2_1.VAL',
                     ],
    'comments_values': [None,
                        {0: 'OFF',
                         1: 'ON'
                         },
                        None,
                        {0: 'OFF',
                         1: 'ON'
                         },
                        None
                        ],
    'sleep_after_end': 0.0,
    'default_base_name': 'us_image',
    'default_rel_dir': 'images',
    'file_path': '13IDD_PG1:TIFF1:FilePath',
    'file_name': '13IDD_PG1:TIFF1:FileName',
    'file_number': '13IDD_PG1:TIFF1:FileNumber',
}

detectors['ds_visual'] = {
    'name': '13IDD_PG2',
    'prefix': 'IM_',
    'monitor_signal_start': '13IDD_PG2:TIFF1:WriteFile_RBV',
    'monitor_signal_start_value': 'Done',
    'monitor_signal_end': None,
    'monitor_signal_end_value': None,
    'track_running_tasks': False,
    'frame_type_PV': None,
    'frame_type_values': 0,
    'frame_type_messages': {0: 'DS Image', },
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13IDD_PG2:cam1:AcquireTime',
                                 },
    'new_file_name': {0: '13IDD_PG2:TIFF1:FullFileName_RBV',
                      },
    'comments': 'Gain: {0}, DS Light: {1}:{2}, US Light: {3}:{4}',
    'comments_PVs': ['13IDD_PG2:cam1:GainValAbs',
                     '13IDD:Unidig1Bo22',
                     '13IDD:DAC2_2.VAL',
                     '13IDD:Unidig1Bo20',
                     '13IDD:DAC2_1.VAL',
                     ],
    'comments_values': [None,
                        {0: 'OFF',
                         1: 'ON'
                         },
                        None,
                        {0: 'OFF',
                         1: 'ON'
                         },
                        None
                        ],
    'sleep_after_end': 0.0,
    'default_base_name': 'ds_image',
    'default_rel_dir': 'images',
    'file_path': '13IDD_PG2:TIFF1:FilePath',
    'file_name': '13IDD_PG2:TIFF1:FileName',
    'file_number': '13IDD_PG2:TIFF1:FileNumber',
}

detectors['ms_visual'] = {
    'name': '13IDD_PG3',
    'prefix': 'IM_',
    'monitor_signal_start': '13IDD_PG3:TIFF1:WriteFile_RBV',
    'monitor_signal_start_value': 'Done',
    'monitor_signal_end': None,
    'monitor_signal_end_value': None,
    'track_running_tasks': False,
    'frame_type_PV': None,
    'frame_type_values': 0,
    'frame_type_messages': {0: 'MS Image', },
    'image_type_PV': None,
    'image_type_values': 0,
    'image_type_exposure_time': {0: '13IDD_PG3:cam1:AcquireTime',
                                 },
    'new_file_name': {0: '13IDD_PG3:TIFF1:FullFileName_RBV',
                      },
    'comments': 'Gain: {0}, Zoom: {1}',
    'comments_PVs': ['13IDD_PG3:cam1:GainValAbs', '13IDD:m14.RBV'],
    'comments_values': [None, None],
    'sleep_after_end': 0.0,
    'default_base_name': 'ms_image',
    'default_rel_dir': 'images',
    'file_path': '13IDD_PG3:TIFF1:FilePath',
    'file_name': '13IDD_PG3:TIFF1:FileName',
    'file_number': '13IDD_PG3:TIFF1:FileNumber',
}
