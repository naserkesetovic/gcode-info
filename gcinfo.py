# -*- coding: utf-8 -*-
#
# Naser Kesetovic
# naser.kesetovic@amm.ba
# 2021/12/24
#
# TODO: Add print finished from current timedate
# TODO: Thumnail size based upon the size from comment 
# TODO: Raw values from profile_data
# TODO: Add compressing of base64

#
# https://stackoverflow.com/questions/55369929/how-do-i-compress-base64-data-using-stringio-into-a-buffer
#


import re
import os 
import base64
import json
import math
#import pickle
import sys

import time 

from pprint import pprint
from datetime import datetime
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QAbstractItemView, QGroupBox, QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6 import uic

re_pattern = r"([.\d]+)*([a-z]+)"
seek_lines = 20 # quicky scan the file for needed info

class gcode_info(QMainWindow):
    def __init__(self, parent = None, selected_file = None, save_info = False):
        super(gcode_info, self).__init__(parent)
        self.selected_file = selected_file
        self.save_info = save_info
        self.profile_data = ""
        
        uic.loadUi(f"{os.path.dirname(__file__)}{os.path.sep}gcinfo.ui", self)
        self.init_UI()


    def init_UI(self):
        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__)}{os.path.sep}icon.png'))
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint | QtCore.Qt.WindowType.WindowCloseButtonHint)
    
        self.process_file()
        self.setWindowTitle(f"{os.path.basename(self.selected_file)}")
        
        if self.save_info:
            self.saveInfo()
        
        self.show()

    def process_file(self):
        i = 0
        total_lines = 0
        
        # thumbnail
        thumbnail_found = False
        thumbnail_begin = False
        thumbnail_size = None
        thumbnail_base64 = ""

        # profile_info
        profile_info_found = False
        profile_info_begin = False
        profile_info_size = None
        profile_info_base64 = ""
        
        with open(self.selected_file, 'r') as f:
            try:
                intro = [next(f) for x in range(seek_lines)]
            except StopIteration as e:
                #in case the file is too small.
                return
            
        for line in intro:
            if "AMM_TOTAL_LINES" in line:
                total_lines = int(line.split(' ')[-1])

        if total_lines > 0:
            with open(self.selected_file, 'r') as f:
                try:
                    gcode = [next(f) for x in range((total_lines + seek_lines))]
                except StopIteration as e:
                    # in case the file is too small.
                    return

            for line in gcode:
                if 'AMM_THUMBNAIL END' in line:
                    if thumbnail_begin:
                        thumbnail_begin = False
                        thumbnail_found = True # make sure that the data is complete!

                if thumbnail_begin:
                    thumbnail_base64 += line.strip(";").strip()

                if "AMM_THUMBNAIL BEGIN" in line:
                    # TODO: get the width, height and size
                    thumbnail_begin = True

                if "AMM_PROFILE_DATA END" in line:
                    if profile_info_begin:
                        profile_info_begin = False
                        profile_info_found = True # make sure that the data is complete!

                if profile_info_begin:
                    profile_info_base64 += line.strip(";").strip()

                if "AMM_PROFILE_DATA BEGIN" in line:
                    # TODO: get the size
                    profile_info_begin = True

            if thumbnail_found:
                pm = QPixmap()
                pm_return = pm.loadFromData(base64.b64decode(thumbnail_base64))
                if pm_return:
                    self.l_thumbnail.setPixmap(pm)
                else:
                    self.l_thumbnail.setText("Thumbnail found,\nbut damaged!")
               
            else:
                self.gThumbnail.setHidden(True)
                self.gMachine.setGeometry(QRect(10, 409, 291, 101))
                self.setFixedSize(312, 521)

            try:
                profile_data = json.loads(base64.b64decode(profile_info_base64).decode())
                self.profile_data = profile_data
                
                self.l_baseSize.setText(f"{profile_data.get('machine_width_value')} x {profile_data.get('machine_depth_value')} x {profile_data.get('machine_height_value')}mm")
                self.l_machineName.setText(f"{profile_data.get('machine_name_value')}")

                self.l_filamentAmount.setText(f"{self.round_value(profile_data.get('filament_amount'))}m")
                self.l_filamentWeight.setText(f"{self.round_value(profile_data.get('filament_weight'))}gr")

                self.l_layerHeight.setText(f"{self.round_value(profile_data.get('layer_height_value'))}{self.round_value(profile_data.get('layer_height_unit'))}")
                self.l_layerWidth.setText(f"{self.round_value(profile_data.get('line_width_value'))}{self.round_value(profile_data.get('line_width_unit'))}")
                self.l_wallThickness.setText(f"{self.round_value(profile_data.get('wall_thickness_value'))}{self.round_value(profile_data.get('wall_thickness_unit'))}")
                self.l_wallLineCount.setText(f"{self.round_value(profile_data.get('wall_line_count_value'))}")
                
                self.l_cooling.setText(f"{self.check_boolean(profile_data.get('cool_fan_enabled_value'))}")
                
                self.l_infillDensity.setText(f"{self.round_value(profile_data.get('infill_sparse_density_value'))}{self.round_value(profile_data.get('infill_sparse_density_unit'))}")
                self.l_infillPattern.setText(f"{self.round_value(profile_data.get('infill_sparse_density_value'))}")
                self.l_materialTemperature.setText(f"{self.round_value(profile_data.get('material_print_temperature_value'))}{self.round_value(profile_data.get('material_print_temperature_unit'))}")
                self.l_buildPlateTemperature.setText(f"{self.round_value(profile_data.get('material_bed_temperature_value'))}{self.round_value(profile_data.get('material_bed_temperature_unit'))}")
                self.l_printSpeed.setText(f"{self.round_value(profile_data.get('speed_print_value'))}{self.round_value(profile_data.get('speed_print_unit'))}")
                
                self.l_support.setText(f"{self.check_boolean(profile_data.get('support_enable_value'))}")
                self.l_adhesionType.setText(f"{self.round_value(profile_data.get('adhesion_type_value'))}")
                self.l_printTime.setText(f"{self.print_time(profile_data.get('print_time'))}")

                self.l_createdOn.setText(f"{self.format_timedate(profile_data.get('generated_on'))}")
                
            except:
                self.gPrint.setHidden(True)
                self.gQuality.setHidden(True)
                self.gMachine.setHidden(True)
                
                self.gThumbnail.setHidden(False)
                self.gThumbnail.setGeometry(QRect(10, 10, 290, 160))
                self.gThumbnail.setTitle("")
                self.l_thumbnail.setText("Info found,\nbut damanged!")
                
                self.setFixedSize(310, 180)


    def saveInfo(self):
        skipped_items = ['generated_on', 'filament_amount', 'filament_weight', 'job_name']
        items = []
                
        for item in self.profile_data:
            items.append(item.replace('_unit', '').replace('_value', ''))
        
        items = sorted(set(items))
        longest_item = len(max(items, key = len)) + 12

        with open(f"{self.selected_file[:-6]}_raw.txt", "w", encoding = 'utf-8') as f:
            f.write("#AMM_FILE START\n")
            f.write(f'Profile report for file "{self.selected_file}".\n')
            f.write('-----------------------------------------------------------------------------\n')
            
            for item in items:
                if item not in skipped_items:
                    value = self.profile_data.get(str(item) + '_value')
                    unit =  self.profile_data.get(str(item) + '_unit')
                    f.write(f"{item.capitalize().ljust(longest_item)}: {value} {unit}\n")
                
                else:
                    if item != 'generated_on':
                        value = self.profile_data.get(str(item))
                        unit = self.profile_data.get(str(item) + '_unit')
                        
                        if unit is not None:
                            f.write(f"{item.capitalize().ljust(longest_item)}: {value} {unit}\n")
                        else:
                            f.write(f"{item.capitalize().ljust(longest_item)}: {value}\n")

                    else:
                        value = self.profile_data.get(str(item))
                        f.write(f"{item.capitalize().ljust(longest_item)}: {self.format_timedate(value)}\n")

            f.write('-----------------------------------------------------------------------------\n')
            f.write("#AMM_FILE EOF")

    @staticmethod
    def round_value(in_value):
        try:
            value = round(float(in_value), 2)
        except:
            value = in_value

        return value


    @staticmethod
    def check_boolean(in_value):
        if str(in_value) == "true" or "True":
            return "Yes"
        return "No"


    @staticmethod
    def print_time(seconds):
        days = 60 * 60 * 24
        hours = 60 * 60
        minutes = 60

        d, reminder = divmod(int(seconds), days)
        h, reminder = divmod(reminder, hours)
        m, s = divmod(reminder, minutes)

        return f"{d} day(s), {h:02d}h:{m:02d}m"


    @staticmethod
    def format_timedate(timestamp):
        return str(datetime.fromtimestamp(timestamp).strftime("%d. %m. %Y. %H:%M"))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) <= 1:
        sys.exit()

    if len(sys.argv) == 2:
        ex = gcode_info(parent = None, selected_file = sys.argv[1])
    if len(sys.argv) == 3:
        if "--save-info" or '-s' in sys.argv:
            ex = gcode_info(parent = None, selected_file = sys.argv[2], save_info = True)
    
    sys.exit(app.exec())
