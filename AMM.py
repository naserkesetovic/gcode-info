# -*- coding: utf-8 -*-
#
# Naser Kesetovic
# naser.kesetovic@outlook.ba
# 2021/12/23
# 
#
import os
import sys

import base64
import json 
import time

from UM.Logger import Logger
from UM.Application import Application
from UM.Qt.Duration import DurationFormat

from cura.Snapshot import Snapshot
from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderManager import ExtruderManager

from PyQt5.QtCore import QByteArray, QIODevice, QBuffer

from ..Script import Script

line_size = 78

values_to_obtain_general = [
    'layer_height',
    'line_width',
    'infill_sparse_density',
    'material_print_temperature',
    'material_bed_temperature',
    'speed_print',
    'support_enable',
    'adhesion_type'
    ]

values_to_obtain = [
    # general machine info
    'machine_name',
    'machine_width',
    'machine_height',
    'machine_depth',

    # quality
    'layer_height',
    'layer_height_0',
    'line_width',
    'wall_line_width',

    # walls
    'wall_thickness',
    'wall_line_count',

    #top/bottom
    'top_layers',
    'bottom_layers',

    #infill
    'infill_sparse_density',
    'infill_pattern',
    'infill_line_distance',

    #material
    'material_print_temperature',
    'material_print_temperature_layer_0',
    'material_bed_temperature',
    'material_bed_temperature_layer_0',

    #speed
    'speed_print',
    'speed_infill',
    'speed_ironing',
    'speed_layer_0',
    'speed_support',

    #travel
    'retraction_enable',
    'retraction_amount',

    #cooling
    'cool_fan_enabled',
    'cool_fan_speed',
    'cool_fan_speed_0',
    'cool_min_layer_time',

    #support
    'support_enable',
    'support_type',
    'support_pattern',
    'support_wall_count',

    #build plate adhesion
    'adhesion_type',
    'raft_extra_margin',
    'brim_width',
    'brim_gap',
    'brim_line_count',
    'brim_outside_only',
    'skirt_line_count',
    'skirt_distance',
    ]


class AMM(Script):
    def __init__(self):
        super().__init__()
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        self.application = CuraApplication.getInstance()
        '''
        extruders_stack = ExtruderManager.getInstance().getMachineExtruders(global_stack.getId())
        extruders = list(Application.getInstance().getGlobalContainerStack().extruders.values())
        Material profile: extruders[0].qualityChanges.getMetaData().get('name', '')
        Material: extruders[0].material.getMetaData().get('material', '')
        Quality: extruders[0].quality.getMetaData().get('name', '')
        '''

    def _getPropertyValue(self, property_name):
        return self.global_stack.getProperty(property_name, 'value')


    def _getPropertyName(self, property_name):
        return self.global_stack.getProperty(property_name, 'name')


    def _getPropertyUnit(self, property_name):
        return str(self.global_stack.getProperty(property_name, 'unit'))


    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail snapshot...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")


    def _encodeSnapshot(self, snapshot):
        Logger.log("d", "Encoding thumbnail image...")
        try:
            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.ReadWrite)
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "PNG")
            base64_bytes = base64.b64encode(thumbnail_buffer.data())
            base64_message = base64_bytes.decode('ascii')
            thumbnail_buffer.close()
            return base64_message
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")


    def _convertSnapshotToGcode(self, encoded_snapshot, width, height, chunk_size=78):
        Logger.log('d', 'Converting thumbnail data to GCode')
        gcode = []

        encoded_snapshot_length = len(encoded_snapshot)
        gcode.append(f'; AMM_THUMBNAIL BEGIN {width} {height} {encoded_snapshot_length}')

        chunks = ["; {}".format(encoded_snapshot[i:i+chunk_size])
            for i in range(0, len(encoded_snapshot), chunk_size)]

        gcode.extend(chunks)
        gcode.append("; AMM_THUMBNAIL END")
        return gcode


    def _getProfileValues(self):
        data = {}

        for value in values_to_obtain:
            #data[f'{value}_name'] = self._getPropertyName(value)
            data[f'{value}_value'] = self._getPropertyValue(value)
            data[f'{value}_unit'] = self._getPropertyUnit(value)

        data['print_time'] = self.application.getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.Seconds)
        data['print_time_unit'] = "s"
        data['job_name'] = self.application.getPrintInformation().jobName
        data['filament_amount'] = self.application.getPrintInformation().materialLengths[0]
        data['filament_amount_unit'] = "m"
        data['filament_weight'] = self.application.getPrintInformation().materialWeights[0]
        data['filament_weight_unit'] = "gr"
        data['generated_on'] = time.time()

        return data


    def _getProfileValuesInReadableFormat(self):
        data = []
        longest_len = len(max(values_to_obtain_general, key = len)) + 6
        data.append("; AMM_SHORT_PROFILE BEGIN")
        for value in values_to_obtain_general:
            data.append(f"; {value.replace('_', ' ').capitalize().ljust(longest_len)}: {self._getPropertyValue(value)} {self._getPropertyUnit(value)}")

        data.append(f"; {'Print time:'.ljust(longest_len)}: {self._getPrintTime(str(self.application.getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.Seconds)))} s")
        data.append(f"; {'Filament amount:'.ljust(longest_len)}: {self.application.getPrintInformation().materialLengths[0]} m")
        data.append(f"; {'Filament weight:'.ljust(longest_len)}: {self.application.getPrintInformation().materialWeights[0]} gr")
        data.append(f"; {'Generated on:'.ljust(longest_len)}: {time.strftime('%d. %m. %Y. - %H:%M', time.localtime(time.time()))}")
        data.append("; AMM_SHORT_PROFILE END")
        
        return data


    def _encodeProfileData(self, profile_data):
        encoded_data = base64.b64encode(json.dumps(profile_data).encode()).decode()
        # to return: json.loads(base64.b64decode(return_data).decode())
        # alternative is to use pickle
        #encoded_data = base64.b64encode(pickle.dumps(profile_data, pickle.HIGHEST_PROTOCOL)).decode()
        return encoded_data


    def _convertProfileDataToGCode(self, encoded_profile_data, chunk_size = 78):
        Logger.log('d', 'Converting profile data to GCode')
        gcode = []
        encoded_profile_data_length = len(encoded_profile_data)
        gcode.append(f'; AMM_PROFILE_DATA BEGIN {encoded_profile_data_length}')

        chunks = ["; {}".format(encoded_profile_data[i:i+chunk_size])
                    for i in range(0, len(encoded_profile_data), chunk_size)]

        gcode.extend(chunks)
        gcode.append("; AMM_PROFILE_DATA END")
        return gcode


    def _getPrintTime(self, seconds):
        days = 60 * 60 * 24
        hours = 60 * 60
        minutes = 60

        d, reminder = divmod(int(seconds), days)
        h, reminder = divmod(reminder, hours)
        m, s = divmod(reminder, minutes)

        return f"{d} day(s), {h:02d}h:{m:02d}m"


    def getSettingDataString(self):
        return """{
            "name": "AMM Post Processing Script",
            "key": "AMM",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "width":
                {
                    "label": "Thumbnail width",
                    "description": "Width of the generated thumbnail",
                    "unit": "px",
                    "type": "int",
                    "default_value": 128,
                    "minimum_value": "32",
                    "minimum_value_warning": "64",
                    "maximum_value_warning": "512"
                },
                "height":
                {
                    "label": "Thumbnail height",
                    "description": "Height of the generated thumbnail",
                    "unit": "px",
                    "type": "int",
                    "default_value": 128,
                    "minimum_value": "0",
                    "minimum_value_warning": "64",
                    "maximum_value_warning": "512"
                }
            }
        }"""


    def execute(self, data):
        thumbnail_width = self.getSettingValueByKey("width")
        thumbnail_height = self.getSettingValueByKey("height")

        snapshot = self._createSnapshot(thumbnail_width, thumbnail_height)
        profile_data = self._getProfileValues()
        profile_data_short = self._getProfileValuesInReadableFormat()
        

        if snapshot:
            encoded_snapshot = self._encodeSnapshot(snapshot)
            encoded_snapshot_gcode = self._convertSnapshotToGcode(encoded_snapshot, thumbnail_width, thumbnail_height, line_size)

        if profile_data:
            encoded_profile_data = self._encodeProfileData(profile_data)
            encoded_profile_data_gcode = self._convertProfileDataToGCode(encoded_profile_data, line_size)

        for layer in data:
            layer_index = data.index(layer)
            lines = data[layer_index].split('\n')

            for line in lines:
                if line.startswith(";Generated with Cura"):
                    line_index = lines.index(line)
                    insert_index = line_index + 1
                    if snapshot:
                        total_lines = f'; AMM_TOTAL_LINES {len(encoded_profile_data_gcode) + len(encoded_snapshot_gcode) + len(profile_data_short) + 5}'
                        lines[insert_index:insert_index] = [';', total_lines, ';', *profile_data_short, ';', *encoded_snapshot_gcode, '; ', *encoded_profile_data_gcode, ';']
                    else:
                        total_lines = f'; AMM_TOTAL_LINES {len(encoded_profile_data_gcode) + len(profile_data_short) + 2}'
                        lines[insert_index:insert_index] = [';', total_lines, ';', *profile_data_short, ';', *encoded_profile_data_gcode, ';']
                    break

            final_lines = '\n'.join(lines)
            data[layer_index] = final_lines

        return data
