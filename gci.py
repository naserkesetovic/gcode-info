# -*- coding: utf-8 -*-
#
# Naser Kesetovic
# naser.kesetovic@amm.ba
# 2021/12/22
#
#
import re
import os 
import base64
import sys

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QAbstractItemView, QGroupBox, QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QRect
from PyQt6 import uic

re_pattern = r"([.\d]+)*([a-z]+)"
total_num_of_lines = 300

class gcode_info(QMainWindow):
    def __init__(self, parent = None, selected_file = None):
        super(gcode_info, self).__init__(parent)
        self.selected_file = selected_file
        uic.loadUi(f"{os.path.dirname(__file__)}{os.path.sep}gci.ui", self)
        self.init_UI()
        
    def init_UI(self):
        self.setWindowIcon(QIcon(f'{os.path.dirname(__file__)}{os.path.sep}icon.png'))
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint | QtCore.Qt.WindowType.WindowCloseButtonHint)
    
        self.process_file(self.selected_file)
        self.setWindowTitle(f"{os.path.basename(self.selected_file)}")
       
        self.show()

    def process_file(self, selected_file):
        i = 0
        thumbnail_found = False 
        thumbnail_begin = False
        thumbnail_size = None
        thumbnail = ""
        
        with open(selected_file, 'r') as file:
            try:
                gcode = [next(file) for x in range(total_num_of_lines)] 
            except StopIteration as e:
                return 
            
        for line in gcode:
            current_line = line.strip().split('\t')
            if "Base:" in line:
                base_size = current_line[-1]
                self.l_baseSize.setText(base_size)

            if "Machine:" in line:
                machine_name = current_line[-1]
                self.l_machineName.setText(machine_name)
                
            if "Print time:" in line:
                print_time = current_line[-1]
                self.l_printTime.setText(print_time)

            if "Filament amount:" in line:
                filament_amount = self.extract_and_round_value(current_line[-1])
                self.l_filamentAmount.setText(f'{filament_amount[0]} {filament_amount[1]}')

            if "Filament weight:" in line:
                filament_weight = self.extract_and_round_value(current_line[-1])
                self.l_filamentWeight.setText(f'{filament_weight[0]} {filament_weight[1]}')

            if "Layer height:" in line:
                layer_height = self.extract_and_round_value(current_line[-1])
                self.l_layerHeight.setText(f'{layer_height[0]} {layer_height[1]}')

            if "Line width:" in line:
                layer_width = self.extract_and_round_value(current_line[-1])
                self.l_layerWidth.setText(f'{layer_width[0]} {layer_width[1]}')

            if "Wall thickness" in line:
                wall_thickness = current_line[-1]
                self.l_wallThickness.setText(wall_thickness)
                
            if "Wall line count" in line:
                wall_line_count = current_line[-1]
                self.l_wallLineCount.setText(wall_line_count)

            if "Cooling" in line:
                cooling = current_line[-1]
                if cooling == "True":
                    self.l_cooling.setText("Yes")
                else:
                    self.l_cooling.setText("No")
                
            if "Top/Bottom line width:" in line:
                top_bottom_line_width = self.extract_and_round_value(current_line[-1])

            if "Infill density:" in line:
                infill_density = current_line[-1]
                self.l_infillDensity.setText(f'{infill_density} %')

            if "Infill pattern:" in line:
                infill_pattern = current_line[-1]
                self.l_infillPattern.setText(infill_pattern)

            if "Material temperature:" in line:
                material_temperature = current_line[-1].encode('ascii', errors = 'ignore').decode()
                self.l_materialTemperature.setText(f'{material_temperature[:-1]} °C')

            if "Build plate temperature:" in line:
                build_plate_temperature = current_line[-1].encode('ascii', errors = 'ignore').decode()
                self.l_buildPlateTemperature.setText(f'{build_plate_temperature[:-1]} °C')

            if "Print speed:" in line:
                print_speed = self.extract_and_round_value(current_line[-1])
                self.l_printSpeed.setText(f'{print_speed[0]} {print_speed[1]}')

            if "Generate support:" in line:
                support = current_line[-1]
                if support == "True":
                    self.l_support.setText("Yes")
                else:
                    self.l_support.setText("No")

            if "Support type:" in line:
                support_type = current_line[-1]

            if "Adhesion type" in line:
                adhesion_type = current_line[-1]
                self.l_adhesionType.setText(adhesion_type)

            if "Generated on:" in line:
                created_on = gcode[i + 1].strip(';').strip()
                self.l_createdOn.setText(created_on)

            if "thumbnail end" in line:
                thumbnail_begin = False
                
            if thumbnail_begin:
                thumbnail += line.strip(";").strip()
                
            if "thumbnail begin" in line:
                thumbnail_found = True
                thumbnail_begin = True
                
            i += 1
        
        if thumbnail_found:
            pm = QPixmap()
            pm.loadFromData(base64.b64decode(thumbnail))
            self.l_thumbnail.setPixmap(pm)
            
    @staticmethod
    def extract_and_round_value(in_value):
        re_finds = re.match(re_pattern, in_value.replace('[', '').replace(']', ''), re.I)
        try:
            value = round(float(re_finds.groups()[0]), 2)
            unit = re_finds.groups()[1]
        except:
            value = 0
            unit = ''

        return value, unit


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) <= 1:
        sys.exit()
        
    ex = gcode_info(parent = None, selected_file = sys.argv[1])
    
    sys.exit(app.exec())
