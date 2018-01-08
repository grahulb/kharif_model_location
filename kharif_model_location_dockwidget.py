# -*- coding: utf-8 -*-
"""
/***************************************************************************
 KharifModelPointDockWidget
                                 A QGIS plugin
 Evaluate Kharif Model at a Location
                             -------------------
        begin                : 2018-01-07
        git sha              : $Format:%H$
        copyright            : (C) 2018 by IITB
        email                : sohoni@cse.iitb.ac.in
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os, csv, datetime

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from qgis.gui import QgsMapTool
from qgis.core import QgsRaster
from kharif_model_point_model import PointModel, Crop
from constants_dicts_lookups import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
	os.path.dirname(__file__), 'kharif_model_location_dockwidget_base.ui'))


class KharifModelPointDockWidget(QtGui.QDockWidget, FORM_CLASS):
	
	closingPlugin = pyqtSignal()
	
	def __init__(self, parent=None, iface=None):
		"""Constructor."""
		super(KharifModelPointDockWidget, self).__init__(parent)
		# Set up the user interface from Designer.
		# After setupUI you can access any designer object by doing
		# self.<objectname>, and you can use autoconnect slots - see
		# http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
		# #widgets-and-dialogs-with-auto-connect
		self.setupUi(self)
		
		self.iface = iface
		self.all_textures = dict_SoilProperties.keys();  self.all_textures.remove('soil type')
		self.soil_texture.addItems(self.all_textures)
		self.all_depths = dict_SoilDep.keys()
		self.soil_depth.addItems(self.all_depths)
		self.all_broad_lulc_types = dict_lulc.values();  self.all_broad_lulc_types.remove('water')
		self.lulc_type.addItems(self.all_broad_lulc_types)
		self.crop.addItems(dict_crop.keys() + dict_LULC_pseudo_crop.keys())
		
		self.last_path = ''
		self.folder_path_browse.clicked.connect(
			lambda: self.on_browse(self.folder_path, 'Folder containing the data-set', folder=True))
		self.load_inputs_button.clicked.connect(self.load_inputs)
		self.pick_point_button.clicked.connect(self.activate_mapTool)
		self.picking_mode = False
		
		self.rainfall_file_browse.clicked.connect(
			lambda: self.on_browse(self.rainfall_csv_filepath, 'Daily Rainfall CSV File', 'CSV files (*.csv)'))
		
		self.run_button.clicked.connect(self.process_run_command)
	
	def on_browse(self, lineEdit, caption, fltr='', folder=False, save=False):
		if folder:
			if save:
				path = QtGui.QFileDialog.getSaveFileName(self, caption, self.last_path, '.png')
			else:
				path = QtGui.QFileDialog.getExistingDirectory(self, caption, self.last_path)
				self.last_path = path
				# self.autofill(path)
		else:
			path = QtGui.QFileDialog.getOpenFileName(self, caption, self.last_path, fltr)
		lineEdit.setText(path)
		# if not self.folder_path.text():
		self.last_path = os.path.dirname(path)
	
	def load_inputs(self):
		path = self.folder_path.text()
		self.input_layers = {}
		self.input_layers['soil_layer'] = self.iface.addVectorLayer(os.path.join(path, 'Soil.shp'), 'Soil Cover', 'ogr')
		self.input_layers['lulc_layer'] = self.iface.addVectorLayer(os.path.join(path, 'LULC.shp'), 'Land-Use-Land-Cover', 'ogr')
		self.input_layers['slope_layer'] = self.iface.addRasterLayer(os.path.join(path, 'Slope.tif'), 'Slope')
		
		if os.path.exists(os.path.join(path, 'Rainfall.csv')):  self.rainfall_csv_filepath.setText(os.path.join(path, 'Rainfall.csv'))
		i = 0
		for row in csv.DictReader(open(os.path.join(path, 'ET0_file.csv'))):
			self.ET0.setItem(i, 0, QtGui.QTableWidgetItem(row["ET0"]))
			i += 1
	
	def activate_mapTool(self):
		if self.picking_mode:
			self.pointTool = None
			self.pick_point_button.setText('Pick a Point')
			self.picking_mode = False
		else:
			if (self.input_layers['soil_layer'] is None
				or self.input_layers['lulc_layer'] is None
				or self.input_layers['slope_layer'] is None):   return
			self.pointTool = PointTool(self.iface.mapCanvas(), self)
			self.iface.mapCanvas().setMapTool(self.pointTool)
			self.pick_point_button.setText('Disable picking')
			self.picking_mode = True
	
	def set_location_inputs(self, qgsPoint):
		for feature in self.input_layers['soil_layer'].getFeatures():
			if feature.geometry().contains(qgsPoint):
				self.soil_texture.setCurrentIndex(self.all_textures.index(feature[TEX].lower()))
				self.soil_depth.setCurrentIndex(self.all_depths.index(feature[Depth].lower()))
				break
		for feature in self.input_layers['lulc_layer'].getFeatures():
			if feature.geometry().contains(qgsPoint):
				self.lulc_type.setCurrentIndex(self.all_broad_lulc_types.index(dict_lulc[feature[Desc].lower()]))
				break
		self.slope.setText(str(self.input_layers['slope_layer'].dataProvider().identify(qgsPoint, QgsRaster.IdentifyFormatValue).results()[1]))
	
	def process_run_command(self):
		self.set_inputs()
		crop = Crop(self.inputs['crop_name'], self.inputs['sowing_threshold'])
		model_duration = max(crop.end_date_index, MONSOON_END_INDEX) + 1
		self.rain = self.inputs['rain'] + [0] * (model_duration - len(self.inputs['rain']))
		crop.calculate_PET(self.rain, self.inputs['et0'], model_duration)
		self.point_model = PointModel   (
											self.inputs['soil_texture'],
											self.inputs['depth_value'],
											self.inputs['lulc_type'],
											self.inputs['slope'],
											crop
										)
		self.point_model.run_model(self.rain, model_duration)
		self.set_output(crop, model_duration)
	
	def set_inputs(self):
		self.inputs = {}
		self.inputs['crop_name'] = self.crop.currentText()
		self.inputs['sowing_threshold'] = self.sowing_threshold.value()
		self.inputs['soil_texture'] = self.soil_texture.currentText()
		self.inputs['depth_value'] = dict_SoilDep[self.soil_depth.currentText()]
		self.inputs['lulc_type'] = self.lulc_type.currentText()
		self.inputs['rain'] = [int(row["Rainfall"]) for row in csv.DictReader(open(self.rainfall_csv_filepath.text()))]
		self.inputs['slope'] = float(self.slope.text())
		self.inputs['et0'] = [];    days_of_month = [30,31,31,30,31,30,31,31,28,31,30,31]
		for i in range(12):
			self.inputs['et0'] += ([float(self.ET0.item(i, 0).text())] * days_of_month[i])
	
	def set_output(self, crop, model_duration):
		def get_date_from_index(i):
			# Always considering an year of 365 days
			if i < 214:
				return datetime.date.fromordinal(datetime.date(2016, 12, 31).toordinal() + 151 + (i+1)).strftime('%d %B')
			else:
				return datetime.date.fromordinal(datetime.date(2016, 12, 31).toordinal() + 365 + ((i-214)+1)).strftime('%d %B')
		for i in range(model_duration):
			self.results.setItem(i, 0, QtGui.QTableWidgetItem(get_date_from_index(i)))    # Date
			self.results.setItem(i, 1, QtGui.QTableWidgetItem(str(self.rain[i])))    # Rain
			self.results.setItem(i, 2, QtGui.QTableWidgetItem(str(self.point_model.budget.sm[i])))    # SM
			self.results.setItem(i, 3, QtGui.QTableWidgetItem(str(self.point_model.budget.runoff[i])))    # Runoff
			self.results.setItem(i, 4, QtGui.QTableWidgetItem(str(self.point_model.budget.infil[i])))    # Infiltration
			self.results.setItem(i, 5, QtGui.QTableWidgetItem(str(crop.PET[i])))    # PET
			self.results.setItem(i, 6, QtGui.QTableWidgetItem(str(self.point_model.budget.AET[i])))    # AET
			self.results.setItem(i, 7, QtGui.QTableWidgetItem(str(self.point_model.budget.GW_rech[i])))    # GW Recharge
	
	def closeEvent(self, event):
		self.closingPlugin.emit()
		event.accept()
	
class PointTool(QgsMapTool):
	def __init__(self, qgsMapCanvas, KMLDWidget):
		super(PointTool, self).__init__(qgsMapCanvas)
		self.KMLDWidget = KMLDWidget
	
	def canvasReleaseEvent(self, event):
		self.KMLDWidget.set_location_inputs(event.mapPoint())