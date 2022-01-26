# -*- coding: utf-8 -*-
"""
/***************************************************************************
 autoliterator
                                 A QGIS plugin
 automatic numbering of polygons
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Travin Alexzander
        email                : Alexzander721@mail.ru
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, qVersion, QVariant, QBasicTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import *
from qgis.core import (QgsApplication,
                       QgsProject,
                       QgsFeature,
                       QgsExpression,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsFeatureRenderer,
                       QgsGeometry,
                       QgsVectorDataProvider,
                       QgsVectorLayer,
                       QgsMapLayer,
                       QgsMapLayerType,
                       QgsWkbTypes,
                       QgsPalLayerSettings,
                       QgsVectorLayerSimpleLabeling,
                       QgsGeometry,
                       )
from .resources import *
from .auto_numbering_dockwidget import autoliteratorDockWidget
import os.path


class autoliterator:

    def __init__(self, iface):
        self.iface = iface
        self.dockwidget = autoliteratorDockWidget()
        self.instance = QgsProject.instance()
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'auto_numbering_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&automatic numbering plugin')
        self.toolbar = self.iface.addToolBar(u'autoliterator')
        self.toolbar.setObjectName(u'autoliterator')
        self.first_start = None

        self.pluginIsActive = False
        self.timer = QBasicTimer()
        self.step = 0

    def tr(self, message):
        return QCoreApplication.translate('autoliterator', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/auto_numbering/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'automatic numbering'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def onClosePlugin(self):
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False

    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&automatic numbering plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        self.first_start = True
        if not self.pluginIsActive:
            self.pluginIsActive = True
        self.dockwidget.closingPlugin.connect(self.onClosePlugin)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.recording.setChecked(False)
        self.dockwidget.create.setChecked(True)
        self.dockwidget.lineEdit.setDisabled(False)
        self.dockwidget.lineEdit.setText("№")
        self.dockwidget.comboBox_3.setDisabled(True)
        self.dockwidget.progressBar.setValue(0)
        if len(self.instance.mapLayers().values()) > 0:
            self.choice_layer()
            self.choice_field()
        self.dockwidget.comboBox.currentIndexChanged.connect(self.choice_field)
        self.dockwidget.all.clicked.connect(self.clik)
        self.dockwidget.only.clicked.connect(self.clik)
        self.dockwidget.recording.clicked.connect(self.clik)
        self.dockwidget.create.clicked.connect(self.clik_create)
        self.dockwidget.Run.clicked.connect(self.start)
        self.dockwidget.Cancel.clicked.connect(self.cl)
        self.dockwidget.show()

    # close plugin
    def cl(self):
        self.iface.removeDockWidget(self.dockwidget)
        self.pluginIsActive = False

    # add layers in comboBox
    def choice_layer(self):
        self.dockwidget.comboBox.clear()
        for layer in self.instance.mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.dockwidget.comboBox.addItem(layer.name(), layer)

    # add fields in comboBox
    def choice_field(self):
        self.dockwidget.comboBox_2.clear()
        self.dockwidget.comboBox_3.clear()
        slayer = self.dockwidget.comboBox.itemData(self.dockwidget.comboBox.currentIndex())
        if slayer is not None:
            [self.dockwidget.comboBox_2.addItem(field.name()) for field in slayer.fields()]
            [self.dockwidget.comboBox_3.addItem(field.name()) for field in slayer.fields()]

    def start(self):
        if self.first_start:
            self.progressbar()
            self.startProgress()
            slayer = self.dockwidget.comboBox.itemData(self.dockwidget.comboBox.currentIndex())
            selectedfield = self.dockwidget.comboBox_2.currentText()
            findx = slayer.dataProvider().fieldNameIndex(f"{selectedfield}")
            lst = []
            self.create_field(slayer)
            # numbering all objects in layer
            # unifying field is not used
            if self.dockwidget.all.isChecked():
                slayer.selectAll()
                for feature in slayer.getFeatures():
                    self.change(slayer, feature)
                self.numbering(slayer)
            # numbering selected objects in layer
            # unifying field is used
            elif self.dockwidget.only.isChecked():
                for feature in slayer.getFeatures():
                    self.change(slayer, feature)
                self.numbering(slayer)
            # standard numbering
            # unifying field is used
            elif self.dockwidget.all.isChecked() == False or self.dockwidget.only.isChecked() == False:
                for feature in slayer.getFeatures():
                    lst.append(feature.attributes()[findx])
                    self.change(slayer, feature)
                # enumeration of all objects by their unifying feature
                for number in list(set(lst)):
                    slfeats = f"{selectedfield}={number}"
                    slayer.selectByExpression(f'{slfeats}')
                    self.numbering(slayer)
            slayer.removeSelection()
            slayer.dataProvider().deleteAttributes([slayer.dataProvider().fieldNameIndex("sm_max")])
            slayer.updateFields()
            self.style(slayer)
            self.first_start = False
        else:
            pass

    def create_field(self, slayer):
        if self.dockwidget.create.isChecked():
            slayer.dataProvider().addAttributes([QgsField(self.dockwidget.lineEdit.text(), QVariant.Int)])
        slayer.dataProvider().addAttributes([QgsField("sm_max", QVariant.Double)])

    def ndx(self, slayer):
        if self.dockwidget.create.isChecked():
            ndx = slayer.dataProvider().fieldNameIndex(str(self.dockwidget.lineEdit.text()))
            return ndx
        elif self.dockwidget.recording.isChecked():
            ndx = slayer.dataProvider().fieldNameIndex(str(self.dockwidget.comboBox_3.currentText()))
            return ndx

    # adding to the field the max Y value of each objects
    def change(self, slayer, feature):
        indx = slayer.dataProvider().fieldNameIndex("sm_max")
        geom = feature.geometry()
        ymax = geom.boundingBox().toString().split(',')[2]
        sm = float(ymax)
        slayer.dataProvider().changeAttributeValues(
            {feature.id(): {indx: sm}})

    # sorting max Y values from highest to lowest and numbering
    def numbering(self, slayer):
        selected = slayer.selectedFeatures()
        indx = slayer.dataProvider().fieldNameIndex("sm_max")
        slayer.startEditing()
        self.timerEvent()
        srtfeat = sorted(selected, key=lambda feat: feat[indx], reverse=True)
        [slayer.changeAttributeValue(val.id(), self.ndx(slayer), int(i)) for i, val in
         enumerate(srtfeat, start=1)]
        slayer.commitChanges()

    def clik(self):
        self.first_start = True
        if self.dockwidget.all.isChecked():
            self.dockwidget.only.setDisabled(True)
            self.dockwidget.comboBox_2.setDisabled(True)
        if not self.dockwidget.all.isChecked():
            self.dockwidget.only.setDisabled(False)
            self.dockwidget.comboBox_2.setDisabled(False)
        if self.dockwidget.only.isChecked():
            self.dockwidget.all.setDisabled(True)
            self.dockwidget.comboBox_2.setDisabled(True)
        if not self.dockwidget.only.isChecked():
            self.dockwidget.all.setDisabled(False)
        if self.dockwidget.recording.isChecked():
            self.dockwidget.create.setChecked(False)
            self.dockwidget.lineEdit.setDisabled(True)
            self.dockwidget.comboBox_3.setDisabled(False)
        if not self.dockwidget.recording.isChecked():
            self.dockwidget.create.setChecked(True)
            self.dockwidget.lineEdit.setDisabled(False)
            self.dockwidget.comboBox_3.setDisabled(True)

    def clik_create(self):
        self.first_start = True
        if self.dockwidget.create.isChecked():
            self.dockwidget.recording.setChecked(False)
            self.dockwidget.lineEdit.setDisabled(False)
            self.dockwidget.comboBox_3.setDisabled(True)
        if not self.dockwidget.create.isChecked():
            self.dockwidget.recording.setChecked(True)
            self.dockwidget.lineEdit.setDisabled(True)
            self.dockwidget.comboBox_3.setDisabled(False)

    # enabling leLabels upon completion of the algorithm
    def style(self, slayer):
        labelSettings = QgsPalLayerSettings()
        if self.dockwidget.create.isChecked():
            labelSettings.fieldName = f"{self.dockwidget.lineEdit.text()}"
        elif self.dockwidget.recording.isChecked():
            labelSettings.fieldName = f"{self.dockwidget.comboBox_3.currentText()}"
        slayer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))
        slayer.setLabelsEnabled(True)
        self.dockwidget.progressBar.setValue(100)

    def progressbar(self):
        self.step = 0
        self.dockwidget.progressBar.setValue(0)

    def startProgress(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(90, self.dockwidget.progressBar)

    def timerEvent(self):
        if self.step >= 90:
            self.timer.stop()
            return

        self.step += 1
        self.dockwidget.progressBar.setValue(self.step)
