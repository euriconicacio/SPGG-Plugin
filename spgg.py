# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SPGG
                                 A QGIS plugin
 Single-Point GEM Generator
                              -------------------
        begin                : 2016-10-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Eurico Nicacio - EB/UFPR
        email                : euriconicacio@ufpr.br
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from spgg_dialog import SPGGDialog
from spgg_dialog_options import SPGGDialogOptions
from spgg_dialog_proc import SPGGDialogProc
import os.path
import os
import sys
import getpass
import time
import socket
import signal
from xlrd import open_workbook
from xlwt import easyxf, Workbook
from xlutils import copy
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class SPGG:
    """QGIS Plugin Implementation."""
    global val
    global lst
    global tipo
    tipo = 100
        
    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SPGG_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = SPGGDialog()
        self.dlg3 = SPGGDialogOptions()
        self.dlg4 = SPGGDialogProc()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SPGG')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SPGG')
        self.toolbar.setObjectName(u'SPGG')
        
        

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SPGG', message)


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
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        global caminho
        a = os.environ['HOME']
        if sys.platform == "win32" or sys.platform == "win64":
            caminho = a+'\.qgis2\python\plugins\SPGG\\'
        else:
            caminho = a+'/.qgis2/python/plugins/SPGG/'
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = caminho+'icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SPGG'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SPGG'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        
        def alerta(mensagem1, mensagem2,tipo):
            msg = QMessageBox()
            if tipo == 1:
                msg.setIcon(QMessageBox.Information)
            else:
                msg.setIcon(QMessageBox.Critical)

            msg.setText(mensagem1)
            msg.setInformativeText(mensagem2)
            msg.setWindowTitle("Single-Point GEM Generator")
            msg.setStandardButtons(QMessageBox.Ok)

            retval = msg.exec_()
            return retval
    
        def muda_ext(nome_arq):
            pre, ext = os.path.splitext(nome_arq)
            if ext == ".xls":
                ext1 = ".sp0"
            else:
                ext1 = ".xls"
            os.rename(nome_arq, pre + ext1)   
        
        def fecha():
            global caminho
            if not os.path.isfile(caminho+'data.sp0'):
                muda_ext(caminho+'data.xls')
                
            self.dlg.dir.currentIndexChanged.disconnect(preenche_modelos)
            self.dlg.testar.clicked.disconnect(testa_con)
            self.dlg.fechar.clicked.disconnect(fecha)
            self.dlg.limpar.clicked.disconnect(limpa)
            self.dlg.ajuda.clicked.disconnect(ajuda)            
            self.dlg.atualizar.clicked.disconnect(atualiza_op)            
            self.dlg.addshp.clicked.disconnect(openFileNameDialog)
            self.dlg.opcoes.clicked.disconnect(opcoes)
            self.dlg.calcular.clicked.disconnect(verifica_campos)
            
            self.dlg3.selec_todas.clicked.disconnect(seleciona_todas)
            self.dlg3.remove_todas.clicked.disconnect(remove_todas)
            self.dlg3.buttonBox.button(QDialogButtonBox.Cancel).clicked.disconnect(fecha_op)
            self.dlg3.buttonBox.button(QDialogButtonBox.Ok).clicked.disconnect(anota_selec)
            self.dlg3.val_nulo.stateChanged.disconnect(checkb)
            self.dlg3.usar_col_selec.clicked.disconnect(imprime_lista)
            self.dlg3.usar_col_padrao.clicked.disconnect(imprime_lista_padrao)
                        
            self.dlg.close()
        
        def testa_con():
            try:
                host = socket.gethostbyname("www.google.com")
                s = socket.create_connection((host, 80), 2)
                alerta("Conexao de Internet OK!", "Voce possui conexao de internet e pode usufruir das funcionalidades deste programa.", 1)
                return True
            except:
                alerta("Nao ha conexao de internet!", "Voce nao possui conexao de internet e nao pode usufruir das funcionalidades deste programa.", 2)
                return False
            return True
                
        def ajuda():
            alerta("Ajuda", "Para ajuda, acesse: http://www.cienciasgeodesicas.ufpr.br/spgg/plugin/", 1)

        def le_xls(nome_arq, aba):
            wkb=open_workbook(nome_arq)
            sheet=wkb.sheet_by_index(aba)

            _matrix=[]
            for row in range (sheet.nrows):
                _row=[]
                for col in range (sheet.ncols):
                    _row.append(sheet.cell_value(row,col))
                _matrix.append(_row)
            return _matrix        
        
        def preenche_shp():
            self.dlg.shp.clear()
            canvas = self.iface.mapCanvas()
            val = []
            cont = 0
            while cont < canvas.layerCount():
                if canvas.layer(cont).geometryType() == QGis.Point:
                    if cont == 0:
                        val.append(" ")
                    val.append(canvas.layer(cont).name())
                cont = cont + 1  
            self.dlg.shp.addItems(val)
        
        def checkb():
            if self.dlg3.val.isReadOnly():
                self.dlg3.val.setReadOnly(False)
            else:
                self.dlg3.val.clear()
                self.dlg3.val.setText('0')
                self.dlg3.val.setReadOnly(True) 
            pass
        
        def imprime_lista():
            camada = self.dlg.shp.currentText()
            layer = None
            for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
                if lyr.name() == camada:
                    layer = lyr
                    break
            self.dlg3.selecionado.setText('Camada selecionada: %s' % layer.name())
            self.dlg3.listWidget.clear()
            if self.dlg3.combo_id.currentText != ' ' and self.dlg3.combo_h.currentText != ' ' and (((self.dlg3.combo_lat.currentText != ' ' and self.dlg3.combo_long.currentText != ' ') and (self.dlg3.radio_latlong.isChecked())) or (self.dlg3.radio_geom.isChecked())):
                if self.dlg3.radio_latlong.isChecked():
                    i = self.dlg3.combo_id.currentIndex()-1
                    h = self.dlg3.combo_h.currentIndex()-1
                    lat = self.dlg3.combo_lat.currentIndex()-1
                    long = self.dlg3.combo_long.currentIndex()-1

                    for f in layer.getFeatures():
                        line = 'Id %s    , Lat:  %s, Long: %s, h: %s\n' % (f[i], f[lat], f[long], f[h])
                        self.dlg3.listWidget.addItem(line)
                    self.dlg3.selecionado.setText('Camada selecionada: %s' % layer.name())
                    a = self.dlg3.listWidget.count()
                    self.dlg3.ft_exist.setText('Features existentes: %s' % str(a))
                    self.dlg3.ft_selec.setText('Features selecionadas: 0')
                else:
                    i = self.dlg3.combo_id.currentIndex()-1
                    h = self.dlg3.combo_h.currentIndex()-1

                    for f in layer.getFeatures():
                        geom = f.geometry()
                        line = 'Id %s    , Lat:  %f, Long: %f, h: %s\n' % (f[i], geom.asPoint().y(), geom.asPoint().x(), f[h])
                        self.dlg3.listWidget.addItem(line)
                    a = self.dlg3.listWidget.count()
                    self.dlg3.ft_exist.setText('Features existentes: %s' % str(a))
                    self.dlg3.ft_selec.setText('Features selecionadas: 0')
            elif not self.dlg3.radio_latlong.isChecked() and not self.dlg3.radio_geom.isChecked():
                alerta("Erro!", "Voce deve selecionar qual o formato de entrada da geometria de sua camada - 'Lat e Long separadas' ou 'Geometria'. Por favor, tente novamente", 1)
                pass
            else:
                alerta("Erro!", "Voce deve preencher todos os campos. Por favor, tente novamente", 2)
                pass
            
        def imprime_lista_padrao():
            self.dlg3.combo_id.setCurrentIndex(0)
            self.dlg3.combo_h.setCurrentIndex(0)
            self.dlg3.combo_lat.setCurrentIndex(0)
            self.dlg3.combo_long.setCurrentIndex(0)
            
            self.dlg3.grupo.setExclusive(False)
            self.dlg3.radio_latlong.setChecked(False)
            self.dlg3.radio_geom.setChecked(False)
            self.dlg3.grupo.setExclusive(True)
            
            camada = self.dlg.shp.currentText()
            layer = None
            for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
                if lyr.name() == camada:
                    layer = lyr
                    break
            self.dlg3.listWidget.clear()
            for f in layer.getFeatures():
                    line = 'Id %s    , Lat:  %s, Long: %s, h: %s\n' % (f[0],f[1], f[2], f[3])
                    self.dlg3.listWidget.addItem(line)
                
        def anota_selec():
            global lst
            global tipo
            tipo = 7
            lista = []
            for i in self.dlg3.listWidget.selectedItems():
                lista.append(str(i.text()[3:8].strip()))
            #print sorted(lista)
            self.dlg3.hide()
            lst = sorted(lista)
            if self.dlg3.radio_latlong.isChecked():
                tipo = 1
            return tipo
            
        def conta_selec():
            c = self.dlg3.listWidget.selectedItems()
            self.dlg3.ft_selec.setText('Features selecionadas: %s' % str(len(c)))
            return len(c)
        
        def seleciona_todas():
            c = self.dlg3.listWidget.count()
            for f in range(0,c):
                self.dlg3.listWidget.item(f).setSelected(True)
            self.dlg3.ft_selec.setText('Features selecionadas: %s' % str(c))
            
            return True
        
        def remove_todas():
            c = self.dlg3.listWidget.count()
            for f in range(0,c):
                self.dlg3.listWidget.item(f).setSelected(False)
            self.dlg3.ft_selec.setText('Features selecionadas: 0')
            return True
        
        def opcoes():
            global val
            global tipo
            if self.dlg.shp.currentText() == ' ' or self.dlg.shp.currentText() == '':
                alerta("Camada nao selecionada!", "Para acessar as opcoes, voce deve selecionar uma camada primeiro. Por favor, tente novamente", 2)
            else:
                self.dlg3.listWidget.clear()
                self.dlg3.combo_id.clear()
                self.dlg3.combo_h.clear()
                self.dlg3.combo_lat.clear()
                self.dlg3.combo_long.clear()
                camada = self.dlg.shp.currentText()
                layer = None
                for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
                    if lyr.name() == camada:
                        layer = lyr
                        break
                i=0
                fields = [field.name() for field in layer.pendingFields()]

                self.dlg3.combo_id.addItem(' ')
                self.dlg3.combo_h.addItem(' ')
                self.dlg3.combo_lat.addItem(' ')
                self.dlg3.combo_long.addItem(' ')
                for item in fields:
                    self.dlg3.combo_id.addItem(item)
                    self.dlg3.combo_h.addItem(item)
                    self.dlg3.combo_lat.addItem(item)
                    self.dlg3.combo_long.addItem(item)
                    

                self.dlg3.grupo.setExclusive(False)
                self.dlg3.radio_latlong.setChecked(False)
                self.dlg3.radio_geom.setChecked(False)
                self.dlg3.grupo.setExclusive(True)    
                self.dlg3.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
                
                self.dlg3.show()
                result2 = self.dlg3.exec_()
                
                if result2:
                    val = self.dlg3.val.text()
                    tipo = anota_selec()
                
        def fecha_op():
            self.dlg3.hide()
                
        def verifica_arq(filename):
            if ((filename == '') or ((filename[-3:] != 'shp'))):
                alerta("Formato de arquivo invalido!", "Somente sao aceitos arquivos shp. Por favor, tente novamente", 2)
                return False
            else:
                return True

        def openFileNameDialog():
            dlg2 = QFileDialog()
            dlg2.setFileMode(QFileDialog.AnyFile)
            if dlg2.exec_():
                filename = dlg2.selectedFiles()[0]
                
                if verifica_arq(filename):
                    layer = QgsVectorLayer(filename, "Pontos SPGG", "ogr")
                    if layer:
                        if layer.geometryType() == QGis.Point:
                            QgsMapLayerRegistry.instance().addMapLayer(layer)
                            self.iface.mapCanvas().refresh()
                            QTimer.singleShot(1000, preenche_shp)
                            self.dlg.shp.setCurrentIndex(1)
                        else:
                            alerta("Shp invalido!", "Voce deve selecionar um shp do tipo ponto. Por favor, tente novamente", 2) 
                    else:
                        alerta("Aquivo invalido!", "Arquivo inválido. Por favor, tente novamente", 2)
        
        def grava_xls(nome_arq,result,aba,tipo):
            if tipo==1:
                rb = open_workbook(nome_arq)
                r_sheet = rb.sheet_by_index(aba)
                wb = copy(rb)
                w_sheet = wb.get_sheet(aba)

                numrows = len(result)
                for i in range(numrows):
                    w_sheet.write(i, 0, result[i])

                wb.save(nome_arq)
            else:
                print (result)
                wb = Workbook()
                ws = wb.add_sheet('Resultados')

                numrows = len(result)
                numcols = len(result[0])
                for i in range(numrows):
                    for j in range(numcols):
                        ws.write(i, j, result[i][j])
                wb.save(nome_arq)
        
               
        def limpa():
            global caminho
            global tipo
            self.dlg.dir.setCurrentIndex(0)
            self.dlg.modelo.setCurrentIndex(0)
            self.dlg.func.setCurrentIndex(0)
            self.dlg.mare.setCurrentIndex(0)
            self.dlg.gzero.setCurrentIndex(0)
            self.dlg.sisref.setCurrentIndex(0)
            self.dlg.status.setText('0 de 0')
            self.dlg.shp.setCurrentIndex(0)
            self.dlg.progresso.setProperty("value", 0)
            tipo = 100
            if not os.path.isfile(caminho+'data.sp0'):
                muda_ext(caminho+'data.xls')
                
        def preenche_modelos():
            global caminho
            if not os.path.isfile(caminho+'data.xls'):
                muda_ext(caminho+'data.sp0')
            nome_arq=caminho+'data.xls'
            dire=self.dlg.dir.currentText()
            val = []
            self.dlg.modelo.clear()
            self.dlg.modelo.addItem(" ")
            if dire == " ":
                pass
            else:    
                wkb=open_workbook(nome_arq)
                sheet1=wkb.sheet_by_index(0)
                row1 =  []
                i=0
                for row in range (sheet1.nrows):
                    row1.append(sheet1.cell_value(row,0))
                    if dire == sheet1.cell_value(row,0):
                        i = row

                sheet2=wkb.sheet_by_index(1)
                row2 = []
                for row in range(sheet2.nrows):
                    row2.append(sheet2.cell_value(row,0))

                k = 0
                l = 0
                m = 0
                val = []
                while m<len(row2):
                    if row2[m] == " ":
                        k+=1
                    if k == i:
                        while l+m<len(row2):
                            if row2[l+m+1] == " ":
                                l = len(row2)
                                k = 666
                                break
                            elif l+m+1 == len(row2)-1:
                                val.append(row2[l+m+1])
                                l = len(row2)
                                k = 666
                                break
                            else:
                                val.append(row2[l+m+1])
                            l+=1
                    else:
                        m += 1
                        pass
                    if k==666:
                        break
                self.dlg.modelo.addItems(val)
                muda_ext(caminho+'data.xls')
        
        def preenche_combo():
            global caminho
            self.dlg.dir.clear()
            if not os.path.isfile(caminho+'data.sp0'):
                muda_ext(caminho+'data.xls')
            muda_ext(caminho+'data.sp0')
            a = le_xls(caminho+'data.xls',0)
            for i in range(len(a)):
                self.dlg.dir.addItems(a[i])
            
            self.dlg.modelo.clear()
            
            self.dlg.func.clear()
            a = le_xls(caminho+'data.xls',2)
            for i in range(len(a)):
                self.dlg.func.addItems(a[i])
            self.dlg.mare.clear()
            a = le_xls(caminho+'data.xls',3)
            for i in range(len(a)):
                self.dlg.mare.addItems(a[i])
            self.dlg.gzero.clear()
            a = le_xls(caminho+'data.xls',4)
            for i in range(len(a)):
                self.dlg.gzero.addItems(a[i])
            self.dlg.sisref.clear()
            a = le_xls(caminho+'data.xls',5)
            for i in range(len(a)):
                self.dlg.sisref.addItems(a[i])
            muda_ext(caminho+'data.xls')
        
        def gera_grid_ponto(dire, modelo, func, mare, gzero, sisref, lat, lon, h, grau):
            display = Display(visible=0, size=(800, 600))
            display.start()

            # Abre site
            browser = webdriver.Chrome()
            browser.get('http://icgem.gfz-potsdam.de/ICGEM/Service.html')

            # Model Directory
            model_dir = Select(browser.find_element_by_id('model_directory'))
            model_dir.select_by_visible_text(dire)

            # Model File
            model_file = Select(browser.find_element_by_id('model_file'))
            model_file.select_by_visible_text(modelo)

            # Functional
            functional = Select(browser.find_element_by_id('functional'))
            #functional.select_by_visible_text('geoid')
            functional.select_by_visible_text(func)

            # Tide System
            tide = Select(browser.find_element_by_id('tide_system'))
            #tide.select_by_visible_text('tide_free')
            tide.select_by_visible_text(mare)

            # Zero Degree Term
            zerodeg = Select(browser.find_element_by_id('zero_degree_term'))
            #zerodeg.select_by_visible_text('yes')
            zerodeg.select_by_visible_text(gzero)

            # Reference System
            ref = Select(browser.find_element_by_id('refsys'))
            #ref.select_by_visible_text('GRS80')
            ref.select_by_visible_text(sisref)

            # Grid Step
            step = browser.find_element_by_id('grid_step')
            step.clear()
            step.send_keys('1.0')

            # Longitude Limit West
            longlimit_west = browser.find_element_by_id('longlimit_west')
            longlimit_west.clear()
            longlimit_west.send_keys(str(lon))

            # Longitude Limit East
            longlimit_east = browser.find_element_by_id('longlimit_east')
            longlimit_east.clear()
            longlimit_east.send_keys(str(lon))

            # Latitude Limit South
            latlimit_south = browser.find_element_by_id('latlimit_south')
            latlimit_south.clear()
            latlimit_south.send_keys(str(lat))

            # Latitude Limit North
            latlimit_north = browser.find_element_by_id('latlimit_north')
            latlimit_north.clear()
            latlimit_north.send_keys(str(lat))
    
            # Height over Ellipsoid
            hei = browser.find_element_by_id('height_over_ell')
            hei.clear()
            hei.send_keys(str(h))

            # Maximal Degree
            max_grau = browser.find_element_by_id('max_used_degree')
            max_grau.clear()
            if grau != '9999':
                max_grau.send_keys(grau)
            else:
                max_grau.send_keys('** max degree of model **')

            # ENTER
            start = browser.find_element_by_id('start_but')
            start.send_keys(Keys.ENTER)
            # clica GRID

            element = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, 'get_but')))
            element.click()
            WebDriverWait(browser, 10).until(lambda d: len(d.window_handles) == 2)
            browser.switch_to_window(browser.window_handles[1])
            try:
                element_present = EC.presence_of_element_located((By.XPATH, '//pre'))
                WebDriverWait(browser, 30).until(element_present)
                a = browser.page_source.encode('utf-8')[-40:-21]
                browser.quit()
                display.stop()
                return float(a.strip())
            except TimeoutException:
                print("Internet issues. Please, try again.")
                return False
        
####################################################################################################################
        def gera_modelos(camada, dire, modelo, func, mare, gzero, sisref, grau):
            self.dlg4.show()
            j = 0
            layer = None
            i = self.dlg3.combo_id.currentIndex()
            for lyr in QgsMapLayerRegistry.instance().mapLayers().values():
                if lyr.name() == camada:
                    layer = lyr
                    break
            k = layer.featureCount()
            geo = ["" for x in range(k)]
            self.dlg.status.setText("0 de "+str(layer.featureCount()))
            
            for f in layer.getFeatures():
                if str(f[i]) in lst:
                    geo[j]= float(gera_grid_ponto(dire,modelo,func,mare,gzero,sisref,f[1],f[2],f[3],grau))
                    #geo[j] = str((j+1)*37)
                else:
                    geo[j] = str(val)
                self.dlg.progresso.setValue(j*100/k)
                self.dlg.status.setText(str(j+1)+" de "+str(layer.featureCount()))
                j+=1
            
            self.dlg.progresso.setValue(100)
            
            for item in geo:
                print item
            
            res = layer.dataProvider().addAttributes([QgsField("func", QVariant.Double)])
            
            fields = [field.name() for field in layer.pendingFields()]
            j = len(fields)
            
            k=0
            for feature in layer.getFeatures():
                fid = int(feature.id())
                layer.startEditing()
                layer.changeAttributeValue(fid, j, geo[k])
                layer.commitChanges()
                k+=1
            self.dlg4.hide()
            alerta("Processamento finalizado!", "Visualize os resultados obtidos acessando a tabela de atributos da camada.", 1)

        
        def verifica_campos():
            if (self.dlg.dir.currentText() != ' ') and (self.dlg.modelo.currentText() != ' ') and (self.dlg.modelo.currentText() != '-') and (self.dlg.func.currentText() != ' ') and (self.dlg.mare.currentText() != ' ') and (self.dlg.gzero.currentText() != ' ') and (self.dlg.sisref.currentText() != ' ') and (self.dlg.shp.currentText() != ' '):
                if tipo == 100:
                    alerta("Erro!", "Voce deve editar as opcoes da camada.", 2)
                else:
                    gera_modelos(self.dlg.shp.currentText(), self.dlg.dir.currentText(), self.dlg.modelo.currentText(), self.dlg.func.currentText(), self.dlg.mare.currentText(), self.dlg.gzero.currentText(), self.dlg.sisref.currentText(), self.dlg.grau.value())
            else:
                alerta("Ha campos nao preenchidos!", "Voce deve preencher todos os campos para gerar os modelos.", 2)
                pass
            
        def atualiza_op():
            global caminho
            reply = QMessageBox()
            reply.setIcon(QMessageBox.Question)
            reply.setText("Tem certeza que deseja atualizar as opcoes do formulario? ")
            reply.setInformativeText("Isto pode levar varios minutos.")
            reply.setWindowTitle("Single-Point GEM Generator")
            reply.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            retval = reply.exec_()
            if retval == QMessageBox.Yes:
                if(testa_con()):
                    muda_ext(caminho+'data.sp0')
                    grava_xls(caminho+'data.xls',le_combo('model_directory'),0,1)
                    grava_xls(caminho+'data.xls',le_combo('model_file'),1,1)
                    grava_xls(caminho+'data.xls',le_combo('functional'),2,1)
                    grava_xls(caminho+'data.xls',le_combo('tide_system'),3,1)
                    grava_xls(caminho+'data.xls',le_combo('zero_degree_term'),4,1)
                    grava_xls(caminho+'data.xls',le_combo('refsys'),5,1)
                    preenche_combo()
                    muda_ext(caminho+'data.xls')
                    alerta("OPCOES ATUALIZADAS!", "As opções de geração de modelos foram atualizadas com sucesso!", 1)
                    return True
                else:
                    return False
            else:
                return False
        
        limpa()
        try: self.dlg.dir.currentIndexChanged.disconnect() 
        except Exception: pass
        try: self.dlg.testar.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.fechar.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.limpar.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.ajuda.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.atualizar.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.addshp.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.opcoes.clicked.disconnect() 
        except Exception: pass
        try: self.dlg.calcular.clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.selec_todas.clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.remove_todas.clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.listWidget.itemClicked.disconnect() 
        except Exception: pass
        try: self.dlg3.buttonBox.button(QDialogButtonBox.Cancel).clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.buttonBox.button(QDialogButtonBox.Ok).clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.val_nulo.stateChanged.disconnect() 
        except Exception: pass
        try: self.dlg3.usar_col_selec.clicked.disconnect() 
        except Exception: pass
        try: self.dlg3.usar_col_padrao.clicked.disconnect() 
        except Exception: pass
        
        self.dlg.dir.currentIndexChanged.connect(preenche_modelos)
        self.dlg.testar.clicked.connect(testa_con)
        self.dlg.fechar.clicked.connect(fecha)
        self.dlg.limpar.clicked.connect(limpa)
        self.dlg.ajuda.clicked.connect(ajuda)            
        self.dlg.atualizar.clicked.connect(atualiza_op)
        self.dlg.addshp.clicked.connect(openFileNameDialog)
        self.dlg.opcoes.clicked.connect(opcoes)
        self.dlg.calcular.clicked.connect(verifica_campos)
        
        self.dlg3.selec_todas.clicked.connect(seleciona_todas)
        self.dlg3.remove_todas.clicked.connect(remove_todas)
        self.dlg3.listWidget.itemClicked.connect(conta_selec)
        self.dlg3.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(fecha_op)
        self.dlg3.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(anota_selec)
        self.dlg3.val_nulo.stateChanged.connect(checkb)
        self.dlg3.usar_col_selec.clicked.connect(imprime_lista)
        self.dlg3.usar_col_padrao.clicked.connect(imprime_lista_padrao)

        # show the dialog
        self.dlg.show()
        
        signal.signal(signal.SIGINT, fecha)
        signal.signal(signal.SIGTERM, fecha)
        
        global caminho
        a = os.environ['HOME']
        if sys.platform == "win32" or sys.platform == "win64":
            caminho = a+'\.qgis2\python\plugins\SPGG\\'
        else:
            caminho = a+'/.qgis2/python/plugins/SPGG/'
        
        if (testa_con()):
            if os.path.isfile(caminho+'data.sp0') or os.path.isfile(caminho+'data.xls'):
                global val
                global lst
                val = 0
                preenche_combo()
                preenche_shp()
            else:
                alerta("ERRO!", "Um dos arquivos de configuracao do SPGG foi corrompido! Desinstale e instale o plugin para poder utiliza-lo.", 2)
        else:
            fecha()
        

        
        
        
        
        
                
        
        
        
        
        
