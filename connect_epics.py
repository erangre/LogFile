"""
List of EPICS controllers to read/write/monitor
"""

epics_config_fixed = {
    'XRD_file_name': '13MARCCD2:TIFF1:FullFileName_RBV',
    'T_file_name': '13IDDLF1:cam1:FullFileName_RBV',
    'XRD_comment': '13MARCCD2:AcquireSequence.STRA',
    'image_ds_file_name': '13IDD_PG2:TIFF1:FullFileName_RBV',
    'image_us_file_name': '13IDD_PG1:TIFF1:FullFileName_RBV',
    'image_ms_file_name': '13IDD_PG3:TIFF1:FullFileName_RBV',
    'XRD_exp_t': '13MARCCD2:cam1:AcquireTime',
    'T_detector': '13IDDLF1:cam1:LFExperimentName_RBV',
    'T_exp_t_PIMAX': '13IDDLF1:cam1:LFRepGateWidth',
    'T_exp_t_PIXIS': '13IDDLF1:cam1:AcquireTime',
    'T_filter': '13IDD:Unidig1Bi4.VAL',
    'T_shutter': '13IDD:Unidig2Bi4.VAL',
    'ds_exp_t': '13IDD_PG2:cam1:AcquireTime',
    'us_exp_t': '13IDD_PG1:cam1:AcquireTime',
    'ds_gain': '13IDD_PG2:cam1:GainValAbs',
    'us_gain': '13IDD_PG1:cam1:GainValAbs',
    'ds_light_sw': '13IDD:Unidig1Bo22',
    'us_light_sw': '13IDD:Unidig1Bo20',
    'ds_light_int': '13IDD:DAC2_2.VAL',
    'us_light_int': '13IDD:DAC2_1.VAL',
    'ms_exp_t': '13IDD_PG3:cam1:AcquireTime',
    'ms_gain': '13IDD_PG3:cam1:GainValAbs',
    'ms_zoom': '13IDD:m14.RBV',
}

epics_monitor_config = {
    'XRD_clicked': '13MARCCD2:cam1:Acquire',
    'T_clicked': '13IDDLF1:cam1:Acquire',
    'DS_saved': '13IDD_PG2:TIFF1:WriteFile_RBV',
    'US_saved': '13IDD_PG1:TIFF1:WriteFile_RBV',
    'MS_saved': '13IDD_PG3:TIFF1:WriteFile_RBV',
}

epics_BG_config = {
    'T_change_image_mode': '13IDDLF1:cam1:ImageMode',
    'T_PIMAX_exposure_Time': '13IDDLF1:cam1:LFRepGateWidth',
    'T_PIXIS_exposure_Time': '13IDDLF1:cam1:AcquireTime',
    'T_detector': '13IDDLF1:cam1:LFExperimentName_RBV',
    'T_acquire': '13IDDLF1:cam1:Acquire',
    'us_light': '13IDD:Unidig1Bo20',
    'ds_light': '13IDD:Unidig1Bo22',
    'XRD_frame_type': '13MARCCD2:cam1:FrameType',
    'XRD_acquire_time': '13MARCCD2:cam1:AcquireTime',
    'XRD_acquire_start': '13MARCCD2:cam1:Acquire',
}

epics_prepare = {
    'CCD_File_Path': '13MARCCD2:TIFF1:FilePath',
    'XRD_Base_Name': '13MARCCD2:TIFF1:FileName',
    'XRD_Number': '13MARCCD2:TIFF1:FileNumber',
    'Image_Up_File_Path': '13IDD_PG1:TIFF1:FilePath',
    'Image_Up_File_Name': '13IDD_PG1:TIFF1:FileName',
    'Image_Up_Number': '13IDD_PG1:TIFF1:FileNumber',
    'Image_Up_Final_Name': '13IDD_PG1:TIFF1:FullFileName_RBV',
    'Image_Dn_File_Path': '13IDD_PG2:TIFF1:FilePath',
    'Image_Dn_File_Name': '13IDD_PG2:TIFF1:FileName',
    'Image_Dn_Number': '13IDD_PG2:TIFF1:FileNumber',
    'Image_Dn_Final_Name': '13IDD_PG2:TIFF1:FullFileName_RBV',
    'T_File_Path': '13IDDLF1:cam1:FilePath',
    'T_File_Name': '13IDDLF1:cam1:FileName',
    'T_File_Number': '13IDDLF1:cam1:FileNumber',
    'T_Final_Name': '13IDDLF1:cam1:FullFileName_RBV',
    'Image_ms_File_Path': '13IDD_PG3:TIFF1:FilePath',
    'Image_ms_File_Name': '13IDD_PG3:TIFF1:FileName',
    'Image_ms_Number': '13IDD_PG3:TIFF1:FileNumber',
    'Image_ms_Final_Name': '13IDD_PG3:TIFF1:FullFileName_RBV',
}

# Obsolete
"""
epics_config = {
    'T_ds': '13IDD:ds_las_temp.VAL',
    'T_int_ds': '13IDD:dn_t_int',
    'T_us': '13IDD:us_las_temp.VAL',
    'T_int_us': '13IDD:up_t_int',
    'laser_power_ds': '13IDD:Laser2OutputPower',
    'laser_percent_ds': '13IDD:DAC2_4.VAL',
    'laser_power_us': '13IDD:Laser1OutputPower',
    'laser_percent_us': '13IDD:DAC2_3.VAL',
    'DAC_hor': '13IDD:m81.RBV',
    'DAC_ver': '13IDD:m83.RBV',
    'DAC_focus': '13IDD:m82.RBV',
    'DAC_omega': '13IDD:m96.LVIO',
    'DET_pos_z': '13IDD:m84.RBV',
    'DET_pos_x': '13IDD:m8.RBV',
    'XRD_shutter': '13IDD:Unidig1Bi11.VAL',
    'lasers_shutter': '13IDD:Unidig2Bi4.VAL',
    'lasers_filter': '13IDD:Unidig1Bi4.VAL',
    'xray_energy': '13IDA:CDEn:E_RBV',
    'APS_current': 'S:SRcurrentAI.VAL',
    'T_Hutch': 'G:AHU:FP5088Ai.VAL',
    'delay': '13IDD:BNC1:P3:Delay',
    'T1': '13Keithley2:DMM1Ch1_calc.VAL',
    'T2': '13Keithley2:DMM1Ch2_calc.VAL',
    'T3': '13Keithley2:DMM1Ch3_calc.VAL',
    'T4': '13Keithley2:DMM1Ch4_calc.VAL',
    'Soller_x': '13IDD:m93.RBV',
    'Soller_z': '13IDD:m94.RBV',
    'Soller_th': '13IDD:m95.RBV',
}
"""
