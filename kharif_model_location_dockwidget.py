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
from PyQt4.QtCore import pyqtSignal, Qt
from qgis.gui import QgsMapTool, QgsMapToolPan
from qgis.core import QgsPoint, QgsRaster, QgsMapLayerRegistry
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
		
		self.results.setHorizontalHeaderLabels([
				'Date', 'Rainfall', 'SM', 'Runoff', 'Infiltration', 'PET', 'AET', 'GW Recharge'
		])
		self.results.setVerticalHeaderLabels(['Monsoon End Summary', 'Crop End Summary'] +
		                                     ['Day ' + str(i)    for i in range(1, 366)])
		for i in range(367):
			self.results.verticalHeaderItem(i).setTextAlignment(Qt.AlignRight)
		
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
			lambda: self.on_browse(self.folder_path, 'Folder containing the data-set', folder=True)
		)
		self.input_layers = {}
		self.load_inputs_button.clicked.connect(self.load_inputs)
		self.pick_point_button.clicked.connect(self.activate_mapTool)
		self.picking_mode = False
		
		self.get_data_at_xy_button.clicked.connect(lambda: self.on_get_data_at_xy())
		
		self.rainfall_file_browse.clicked.connect(
			lambda: self.on_browse(self.rainfall_csv_filepath, 'Daily Rainfall CSV File', 'CSV files (*.csv)')
		)
		
		self.save_file_path_browse.clicked.connect(
			lambda: self.on_browse(self.save_file_path, 'Save report to file...', 'CSV files (*.csv)', save=True)
		)
		
		self.run_button.clicked.connect(self.process_run_command)
	
	def on_browse(self, lineEdit, caption, fltr='', folder=False, save=False):
		if folder:
			path = QtGui.QFileDialog.getExistingDirectory(self, caption, self.last_path)
			self.last_path = path
			# self.autofill(path)
		else:
			if save:
				path = QtGui.QFileDialog.getSaveFileName(self, caption, self.last_path)
			else:
				path = QtGui.QFileDialog.getOpenFileName(self, caption, self.last_path, fltr)
		lineEdit.setText(path)
		# if not self.folder_path.text():
		self.last_path = os.path.dirname(path)
	
	def load_inputs(self):
		if 'soil_layer' in self.input_layers:
			QgsMapLayerRegistry.instance().removeMapLayer(self.input_layers['soil_layer'])
		if 'lulc_layer' in self.input_layers:
			QgsMapLayerRegistry.instance().removeMapLayer(self.input_layers['lulc_layer'])
		if 'slope_layer' in self.input_layers:
			QgsMapLayerRegistry.instance().removeMapLayer(self.input_layers['slope_layer'])
		path = self.folder_path.text()
		self.input_layers['soil_layer'] = self.iface.addVectorLayer(os.path.join(path, 'Soil.shp'), 'Soil Cover', 'ogr')
		self.input_layers['lulc_layer'] = self.iface.addVectorLayer(os.path.join(path, 'LULC.shp'), 'Land-Use-Land-Cover', 'ogr')
		self.input_layers['slope_layer'] = self.iface.addRasterLayer(os.path.join(path, 'Slope.tif'), 'Slope')
		self.iface.mapCanvas().setExtent(self.input_layers['slope_layer'].extent())
		
		if os.path.exists(os.path.join(path, 'Rainfall.csv')):  self.rainfall_csv_filepath.setText(os.path.join(path, 'Rainfall.csv'))
		et0_dict = list(csv.DictReader(open(os.path.join(path, 'ET0.csv'))))[0]
		for month, i in zip(['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May'], range(12)):
			self.ET0.setItem(i, 0, QtGui.QTableWidgetItem(et0_dict[month]))
		#Reset picking mode for any newly loaded dataset
		self.picking_mode = False
		self.pick_point_button.setText('Pick a Point')
		self.iface.mapCanvas().setMapTool(QgsMapToolPan(self.iface.mapCanvas()))
		
	
	def activate_mapTool(self):
		if self.picking_mode:
			self.iface.mapCanvas().setMapTool(QgsMapToolPan(self.iface.mapCanvas()))
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
				self.lulc_type.setCurrentIndex(self.all_broad_lulc_types.index(dict_lulc[str(feature[Desc].lower())]))
				break
		self.slope.setText(str(self.input_layers['slope_layer'].dataProvider().identify(qgsPoint, QgsRaster.IdentifyFormatValue).results()[1]))
		self.coordinate_x.setText(str(qgsPoint.x()))
		self.coordinate_y.setText(str(qgsPoint.y()))
	
	def on_get_data_at_xy(self):
		try:
			x = float(self.coordinate_x.text())
			y = float(self.coordinate_y.text())
		except:
			return
		self.set_location_inputs(QgsPoint(x, y))
	
	def process_run_command(self):
		self.set_inputs()
		crop = Crop(self.inputs['crop_name'], self.inputs['sowing_threshold'])
		model_duration = max(crop.end_date_index, MONSOON_END_INDEX) + 1
		self.rain = self.inputs['rain'] + [0] * (model_duration - len(self.inputs['rain']))
		crop.calculate_PET(self.rain, self.inputs['et0'], model_duration)
		self.point_model = PointModel (
			self.inputs['soil_texture'],
			self.inputs['depth_value'],
			self.inputs['lulc_type'],
			self.inputs['slope'],
			crop
		)
		self.point_model.run_model(self.rain, model_duration)
		self.set_output(crop, model_duration)
		save_file_path = self.save_file_path.text()
		if save_file_path and os.path.exists(os.path.dirname(save_file_path)):
			self.output_report(crop, model_duration, save_file_path)
	
	def set_inputs(self):
		self.inputs = {}
		self.inputs['crop_name'] = self.crop.currentText()
		self.inputs['sowing_threshold'] = self.sowing_threshold.value()
		self.inputs['soil_texture'] = self.soil_texture.currentText()
		self.inputs['depth_value'] = dict_SoilDep[self.soil_depth.currentText()]
		self.inputs['lulc_type'] = self.lulc_type.currentText()
		self.inputs['rain'] = [int(float(row["Rainfall"])) for row in csv.DictReader(open(self.rainfall_csv_filepath.text()))]
		self.inputs['slope'] = float(self.slope.text())
		self.inputs['et0'] = [];    days_of_month = [30,31,31,30,31,30,31,31,28,31,30,31]
		for i in range(12):
			self.inputs['et0'] += ([float(self.ET0.item(i, 0).text())] * days_of_month[i])
		if self.coordinate_x.text() and self.coordinate_y.text():
			try:
				x = str(float(self.coordinate_x.text()))
				y = str(float(self.coordinate_y.text()))
			except:
				pass
			self.inputs['X coordinate'] = x
			self.inputs['Y coordinate'] = y
	
	def get_date_from_index(self, i):
		# Always considering an year of 365 days
		if i < 214:
			return datetime.date.fromordinal(datetime.date(2016, 12, 31).toordinal() + 151 + (i + 1)).strftime('%d %B')
		else:
			return datetime.date.fromordinal(datetime.date(2016, 12, 31).toordinal() + 365 + ((i - 214) + 1)).strftime(
				'%d %B')
	
	def set_output(self, crop, model_duration):
		self.results.setItem(0, 0, QtGui.QTableWidgetItem('30 November'))
		self.results.setItem(0, 1, QtGui.QTableWidgetItem('{}'.format(sum(self.point_model.budget.rain[:183]))))
		self.results.setItem(0, 2, QtGui.QTableWidgetItem('{:6.2f}'.format(self.point_model.budget.sm[182])))
		self.results.setItem(0, 3, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.runoff[:183]))))
		self.results.setItem(0, 4, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.infil[:183]))))
		self.results.setItem(0, 5, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(crop.PET[:183]))))
		self.results.setItem(0, 6, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.AET[:183]))))
		self.results.setItem(0, 7, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.GW_rech[:183]))))
		
		self.results.setItem(1, 0, QtGui.QTableWidgetItem(self.get_date_from_index(crop.end_date_index)))
		self.results.setItem(1, 1, QtGui.QTableWidgetItem('{}'.format(sum(self.point_model.budget.rain[:crop.end_date_index+1]))))
		self.results.setItem(1, 2, QtGui.QTableWidgetItem('{:6.2f}'.format(self.point_model.budget.sm[crop.end_date_index])))
		self.results.setItem(1, 3, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.runoff[:crop.end_date_index+1]))))
		self.results.setItem(1, 4, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.infil[:crop.end_date_index+1]))))
		self.results.setItem(1, 5, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(crop.PET[:crop.end_date_index+1]))))
		self.results.setItem(1, 6, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.AET[:crop.end_date_index+1]))))
		self.results.setItem(1, 7, QtGui.QTableWidgetItem('{:6.2f}'.format(sum(self.point_model.budget.GW_rech[:crop.end_date_index+1]))))
		for i in range(model_duration):
			self.results.setItem(i+2, 0, QtGui.QTableWidgetItem(self.get_date_from_index(i)))    # Date
			self.results.setItem(i+2, 1, QtGui.QTableWidgetItem('{}'.format(self.point_model.budget.rain[i])))    # Rain
			self.results.setItem(i+2, 2, QtGui.QTableWidgetItem('{:6.2f}'.format(float(self.point_model.budget.sm[i]))))    # SM
			self.results.setItem(i+2, 3, QtGui.QTableWidgetItem('{:6.2f}'.format(float(self.point_model.budget.runoff[i]))))    # Runoff
			self.results.setItem(i+2, 4, QtGui.QTableWidgetItem('{:6.2f}'.format(float(self.point_model.budget.infil[i]))))    # Infiltration
			self.results.setItem(i+2, 5, QtGui.QTableWidgetItem('{:6.2f}'.format(float(crop.PET[i]))))    # PET
			self.results.setItem(i+2, 6, QtGui.QTableWidgetItem('{:6.2f}'.format(float(self.point_model.budget.AET[i]))))    # AET
			self.results.setItem(i+2, 7, QtGui.QTableWidgetItem('{:6.2f}'.format(float(self.point_model.budget.GW_rech[i]))))    # GW Recharge
	
	def output_report(self, crop, model_duration, filepath):
		b = self.point_model.budget
		if 'X coordinate' in self.inputs:
			content = 'Coordinates:,X:' + self.inputs['X coordinate'] + ',Y:' + self.inputs['Y coordinate'] + '\n'
		else:
			content = ''
		content += '\n'.join([ip+','+str(ip_val) for ip, ip_val in self.inputs.items() if 'coordinate' not in ip])
		content += '\n\n' + ','.join([
			'Date', 'Rainfall', 'SM', 'Runoff', 'Infiltration', 'PET', 'AET', 'GW Recharge'
		])
		content += '\n' + ','.join(map(str, [
			'30 November(Monsoon End)', sum(b.rain[:183]),b.sm[182],sum(b.runoff[:183]),sum(b.infil[:183]),
			sum(crop.PET[:183]),sum(b.AET[:183]),sum(b.GW_rech[:183]),
		]))
		edi = crop.end_date_index
		content += '\n' + ','.join(map(str, [
			self.get_date_from_index(edi)+'(Crop End)', sum(b.rain[:edi+1]), b.sm[edi], sum(b.runoff[:edi+1]), sum(b.infil[:edi+1]),
			sum(crop.PET[:edi+1]), sum(b.AET[:edi+1]), sum(b.GW_rech[:edi+1]),
		]))
		for i in range(model_duration):
			content += '\n' + ','.join(map(str, [
				self.get_date_from_index(i), b.rain[i], b.sm[i], b.runoff[i],
				b.infil[i], crop.PET[i], b.AET[i], b.GW_rech[i],
			]))
		with open(filepath, 'w') as f:
			f.write(content)
	
	def closeEvent(self, event):
		self.closingPlugin.emit()
		event.accept()
	
class PointTool(QgsMapTool):
	def __init__(self, qgsMapCanvas, KMLDWidget):
		super(PointTool, self).__init__(qgsMapCanvas)
		self.KMLDWidget = KMLDWidget
	
	def canvasReleaseEvent(self, event):
		self.KMLDWidget.set_location_inputs(event.mapPoint())