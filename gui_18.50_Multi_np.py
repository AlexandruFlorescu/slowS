import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from autobahn.twisted.websocket  import WebSocketClientFactory, WebSocketClientProtocol, connectWS
import json
import pandas as pd
import OPMMData_v4 as opd
import PandasModel as pdmodel
import PandasModel_R as pdrmodel
import io
import csv
import pexpect
import inspect
import numpy as np
#from datetime import datetime, timedelta
#import paramiko

# http://eli.thegreenplace.net/2011/05/26/code-sample-socket-client-based-on-twisted-with-pyqt
# https://stackoverflow.com/questions/3142705/is-there-a-websocket-client-implemented-for-python

global morphGUI
morphGUI = None
activePlugins=["OptionTrader.OT01","OptionTrader.OT02","OptionPricer.OP01","OrderForwarder.OF01","LoggerServer"]
guiNo = 1

class MyClientProtocol(WebSocketClientProtocol):

    #def sendMessage(self, msg):
    #    msg = {k: str(v) for k, v in msg.iteritems()}
    #    self.sendMessage(msg)

    def onMessage(self, msg, binary):
    	print inspect.stack()[0][3], 'START'
        morphGUI.onMessage(msg)
        
    def onOpen(self):
    	print inspect.stack()[0][3], 'START'
        print ("Connected")
        morphGUI.listWidget.insertItem(0,"Connected")
        morphGUI.onConnection(self)

    def onClose(self, wasClean, code, reason):
    	print inspect.stack()[0][3], 'START'
        print ("Disconnected", wasClean, code, reason)
        morphGUI.listWidget.insertItem(0,"Disconnected")
        morphGUI.onDisconnection()

class MorphGUI(QtWidgets.QMainWindow):
    def __init__(self, reactor):
    	print inspect.stack()[0][3], 'START'
        QtWidgets.QMainWindow.__init__(self)
        ## Read csvs for inital values
        path = "~/GUI_17/csvs/"
        self.opmmData = opd.OPMMData(path)
        ## GUI setup
        self.setupGUI()
        self.client = None
        self.reactor = reactor
        #self.setupConnection()

    def setupConnection(self):
    	print inspect.stack()[0][3], 'START'
        self.factory = WebSocketClientFactory("ws://49.248.124.188:5005")
        self.factory.protocol = MyClientProtocol
        print ("Trying to connect")
        self.connector = connectWS(self.factory)

    def onConnection(self, client):
    	print inspect.stack()[0][3], 'START'
        assert self.client is None
        self.client = client
        plugins = activePlugins[guiNo-1] + "," + activePlugins[2] + "," + activePlugins[4] #+ "," + activePlugins[4]
        testMsg = json.dumps( {"MsgType":"Connect", "guiName": "GUI_" + str(guiNo), "plugins": plugins}, sort_keys=True)

        #testMsg = json.dumps( {'MsgType':'XX'}, sort_keys=True )
        self.client.sendMessage(testMsg.encode('utf8'))
        stopmsg = {}
        stopmsg['MsgType'] = 'UMSG'
        stopmsg["activePlugin"] = activePlugins[guiNo -1]
        stopmsg["value"] = '0'        
        stopmsg = {k: str(v) for k, v in stopmsg.items()}
        self.client.sendMessage(json.dumps(stopmsg).encode('utf8'))

        
    def onMessage(self, msg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(msg, typ='series')

        if data["MsgType"] == "Connect":
            print ("Received connect msg")        
        elif data['MsgType'] == 'InstrumentData':
            self.onInstrumentDataMessage(msg)
        elif data['MsgType'] == 'PortfolioData':
            self.onPortfolioDataMessage(msg)
        elif data['MsgType'] == 'TradeData':
            self.onTradeDataMessage(msg)
        elif data['MsgType'] == 'PortfolioInfo':
            self.onPfInfoMessage(msg)
        #elif data['MsgType'] == 'OrderNewRequest':
        #    self.onOrderRequestMessage(msg)
        #elif data['MsgType'] == 'OrderModifyRequest':
        #    self.onOrderRequestMessage(msg)
        #elif data['MsgType'] == 'OrderCancelRequest':
        #    self.onOrderRequestMessage(msg)
        #elif data['MsgType'] == 'OrderAck':
        #    self.onOrderRespMessage(msg)
        #elif data['MsgType'] == 'OrderCancel':
        #    self.onOrderRespMessage(msg)
        #elif data['MsgType'] == 'OrderCancelReject':
        #    self.onOrderRespMessage(msg)
        #elif data['MsgType'] == 'OrderReject':
        #    self.onOrderRespMessage(msg)
        #elif data['MsgType'] == 'OrderFill':
        #    self.onOrderRespMessage(msg)
        elif data['MsgType'] == 'Alert':
            self.onAlertMessage(msg)
        #else:
            #print ("Unexpected message type!!!!!!")
            #print ("Received message", msg)
        assert self.client is not None
        #print "Received message", msg

    def onDisconnection(self):
    	print inspect.stack()[0][3], 'START'
        assert self.client is not None
        self.client = None

    def setupGUI(self):
    	print inspect.stack()[0][3], 'START'
        self.setWindowTitle("Parameter Input Screen")
        self.resize(1200, 1200)
        self.showMaximized()
        self.centralwidget = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.tabWidget  = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setStyleSheet("QTabBar::tab {height: 20px}")

        ## Setup tabs (below methods put everything in self.tabWidget
        self.setupMonitorTab()
        self.setupAuxTab()
        
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.tabWidget.setCurrentIndex(0)
        self.setCentralWidget(self.centralwidget)

    def setupMonitorTab(self):
    	print inspect.stack()[0][3], 'START'
        self.Monitor    = QtWidgets.QWidget()
        self.mgridLayout = QtWidgets.QGridLayout(self.Monitor)
        
        ## Portfolios
        self.pfTable   = QtWidgets.QTableView(self.Monitor)
        self.pfTable.setMouseTracking(False)
        self.pfModel   = pdmodel.PandasModel(self.opmmData.pfData)
        self.pfModel.dataChanged.connect(self.onPfItemChange)
        self.pfTable.setModel(self.pfModel)
        self.pfTable.setMinimumHeight(175)
        self.pfTable.resizeColumnsToContents()        
        self.pfTable.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.pfTable.setColumnWidth(0,25)
        self.pfTable.setColumnWidth(1,25)
        self.pfTable.setColumnWidth(3,80)
        self.pfTable.setColumnWidth(4,80)
        self.pfTable.setColumnWidth(7,10)
        self.pfTable.setColumnWidth(8,60)
        self.pfTable.setColumnWidth(9,60)
        self.pfTable.setColumnWidth(11,10)
        self.pfTable.setColumnWidth(17,10)
        self.pfTable.setColumnWidth(18,60)
        self.pfTable.setColumnWidth(19,60)
        self.pfTable.setAlternatingRowColors(True)      
        self.pfTable.setStyleSheet("alternate-background-color: rgba(100,100,255,25); background-color: white; font: 12px")        
        self.pfTable.setShowGrid(False)
        self.pfTable.setColumnHidden(2,True) 
        self.pfTable.setColumnHidden(5,True) 
        self.pfTable.setColumnHidden(10,True)     
        self.pfTable.setColumnHidden(14,True)     
        self.pfTable.resizeRowsToContents()
        self.pfTable.horizontalHeader().setSectionResizeMode(2)        
        self.pfTable.verticalHeader().setSectionResizeMode(2)
        self.mgridLayout.addWidget(self.pfTable,0,0,4,8)
       
        
        ## Buttons
        self.startButton = QtWidgets.QPushButton('Start All')
        self.startButton.clicked.connect(self.StartAll)
        self.mgridLayout.addWidget(self.startButton,0,8,1,2)
        
        self.stopButton = QtWidgets.QPushButton('Stop All')
        self.stopButton.clicked.connect(self.StopAll)
        self.mgridLayout.addWidget(self.stopButton,1,8,1,2)
        
        self.saveButton = QtWidgets.QPushButton('Save')
        #self.saveButton.clicked.connect(self.SaveAll)
        self.mgridLayout.addWidget(self.saveButton,2,8,1,1)
         
        self.clearButton = QtWidgets.QPushButton('Clear')
        self.clearButton.clicked.connect(self.ClearAll)
        self.mgridLayout.addWidget(self.clearButton,2,9,1,1)
         
        self.clearButton = QtWidgets.QPushButton('Check All')
        self.clearButton.clicked.connect(self.CheckAll)
        self.mgridLayout.addWidget(self.clearButton,3,8,1,2)       
        
        ### Instruments Read Only
        self.insRdTable  = QtWidgets.QTableView(self.Monitor)
        self.insRdModel  = pdrmodel.PandasModel(self.opmmData.insrData)
        self.insRdTable.setModel(self.insRdModel)
        self.insRdTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        #self.insRdTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        insSelectionModel = self.insRdTable.selectionModel()
        insSelectionModel.selectionChanged.connect(self.onInsSelect)
        self.insRdTable.setMinimumHeight(1350)  
        self.insRdTable.setAlternatingRowColors(True)
        self.insRdTable.setStyleSheet("alternate-background-color: rgba(100,100,100,15); background-color: white; font: 11px")
        self.insRdTable.setShowGrid(False)
        self.insRdTable.setColumnHidden(2,True)
        self.insRdTable.setColumnHidden(11,True)
        self.insRdTable.setColumnHidden(19,True)
        self.insRdTable.setColumnHidden(25,True)
        self.insRdTable.setColumnHidden(26,True)
        self.insRdTable.setColumnHidden(27,True)
        self.insRdTable.setColumnHidden(28,True)
        self.insRdTable.setColumnHidden(29,True)
        self.insRdTable.setColumnHidden(30,True)
        self.insRdTable.setColumnHidden(31,True)
        self.insRdTable.setColumnHidden(32,True)
        self.insRdTable.resizeColumnsToContents()
        for i in range(11,21):
            self.insRdTable.setColumnWidth(i,55)
        for i in range(0,self.insRdModel.rowCount()):
            self.insRdTable.setRowHidden(i,True)
            self.insRdTable.setRowHeight(i,20)
        self.insRdTable.setColumnWidth(0,20)
        self.insRdTable.setColumnWidth(1,40)
        self.insRdTable.setColumnWidth(5,10)
        self.insRdTable.setColumnWidth(13,10)
        self.insRdTable.setColumnWidth(16,10)
        self.insRdTable.setColumnWidth(22,10)
        self.insRdTable.resizeRowsToContents()
        self.insRdTable.horizontalHeader().setSectionResizeMode(2)        
        self.insRdTable.verticalHeader().setSectionResizeMode(2)        
        self.mgridLayout.addWidget(self.insRdTable,4,0,1,10)



        ### Instruments Params Dynamic
        self.insParTable  = QtWidgets.QTableView(self.Monitor)
        self.insParModel  = pdmodel.PandasModel(self.opmmData.insData,
                                             self.opmmData.minInsData,
                                             self.opmmData.maxInsData)
        self.insParModel.dataChanged.connect(self.onInsItemChange)
        self.insParTable.setModel(self.insParModel)
        for i in range(0,self.insParModel.rowCount()):
            self.insParTable.setRowHidden(i,True)
            self.insParTable.setRowHeight(i,20)
        self.insParTable.setStyleSheet("font: 11px")
        self.insParTable.resizeColumnsToContents()
        self.insParTable.setColumnWidth(0,25)
        self.insParTable.setColumnWidth(5,60)
        self.insParTable.setColumnWidth(17,50)
        self.insParTable.setColumnHidden(1,True)
        self.insParTable.setColumnHidden(2,True)
        self.insParTable.setColumnHidden(6,True)
        self.insParTable.setColumnHidden(7,True)
        self.insParTable.setColumnHidden(18,True)
        self.insParTable.setColumnHidden(19,True)
        self.insParTable.setColumnHidden(20,True)
        self.insParTable.setColumnHidden(21,True)
        self.insParTable.resizeRowsToContents()
        self.insParTable.horizontalHeader().setSectionResizeMode(2)        
        self.insParTable.verticalHeader().setSectionResizeMode(2)
        self.insParTable.setMinimumHeight(10)  
        self.mgridLayout.addWidget(self.insParTable,5,0,1,10)


        ### PF Params Dynamic
        self.pfParamsTable  = QtWidgets.QTableView(self.Monitor)
        self.pfParamsModel  = pdmodel.PandasModel(self.opmmData.globalParams.data,
                                                  self.opmmData.minGlobalParams.data,
                                                  self.opmmData.maxGlobalParams.data)
        self.pfParamsModel.dataChanged.connect(self.onPfParamChange)
        self.pfParamsTable.setModel(self.pfParamsModel)
        self.pfParamsTable.setMinimumHeight(10)    
        self.pfParamsTable.setColumnHidden(0,True)
        self.pfParamsTable.setColumnHidden(8,True)        
        for i in range(0,self.pfParamsModel.rowCount()):
            self.pfParamsTable.setRowHidden(i,True)
            self.pfParamsTable.setRowHeight(i,20)   
        self.pfParamsTable.setStyleSheet("font: 11px")
        self.pfParamsTable.resizeColumnsToContents()
        self.pfParamsTable.setColumnWidth(1,25)        
        self.pfParamsTable.resizeRowsToContents()
        self.pfParamsTable.horizontalHeader().setSectionResizeMode(2)        
        self.pfParamsTable.verticalHeader().setSectionResizeMode(2)        
        self.mgridLayout.addWidget(self.pfParamsTable,6,0,1,5)


        ### Hedging Params Dynamic
        self.hedgingParamsTable        = QtWidgets.QTableView(self.Monitor)
        self.hedgingParamsModel        = pdmodel.PandasModel(self.opmmData.hedgingParams.data,
                                                      self.opmmData.minHedgingParams.data,
                                                      self.opmmData.maxHedgingParams.data)
        self.hedgingParamsModel.dataChanged.connect(self.onHedgingParamChange)
        self.hedgingParamsTable.setModel(self.hedgingParamsModel)
        self.hedgingParamsTable.setMinimumHeight(10)
        for i in range(0,self.hedgingParamsModel.rowCount()):
            self.hedgingParamsTable.setRowHidden(i,True)
            self.hedgingParamsTable.setRowHeight(i,20) 
        self.hedgingParamsTable.setStyleSheet("font: 11px")
        self.hedgingParamsTable.resizeColumnsToContents()
        self.hedgingParamsTable.setColumnWidth(1,25)        
        self.hedgingParamsTable.resizeRowsToContents()
        self.hedgingParamsTable.horizontalHeader().setSectionResizeMode(2)        
        self.hedgingParamsTable.verticalHeader().setSectionResizeMode(2)
        self.hedgingParamsTable.setColumnHidden(0,True)  
        #self.hedgingParamsTable.setColumnHidden(3,True)                
        self.mgridLayout.addWidget(self.hedgingParamsTable,7,0,1,5)
        
        
        ### Vol Curve Dynamic
        self.vcTable        = QtWidgets.QTableView(self.Monitor)
        self.vcModel        = pdmodel.PandasModel(self.opmmData.volCurve.data,
                                                  self.opmmData.minVolCurve.data,
                                                  self.opmmData.maxVolCurve.data)
        self.vcModel.dataChanged.connect(self.onVolCurveChange)
        self.vcTable.setModel(self.vcModel)
        self.vcTable.setMinimumHeight(10)    
        for i in range(0,self.vcModel.rowCount()):
            self.vcTable.setRowHidden(i,True)
            self.vcTable.setRowHeight(i,20) 
        self.vcTable.setStyleSheet("font: 11px")
        self.vcTable.resizeColumnsToContents()
        self.vcTable.resizeRowsToContents()
        self.vcTable.setColumnWidth(1,25)        
        self.vcTable.horizontalHeader().setSectionResizeMode(2)        
        self.vcTable.verticalHeader().setSectionResizeMode(2)
        self.vcTable.setColumnHidden(0,True)     
        self.mgridLayout.addWidget(self.vcTable,8,0,1,5)


        ## Trades List
        self.tradeList = QtWidgets.QListWidget(self.Monitor)
        self.tradeList.setMinimumHeight(20)
        self.mgridLayout.addWidget(self.tradeList,6,5,3,5)
        
        
        ## Alert monitor
        self.listWidget = QtWidgets.QListWidget(self.Monitor)
        self.listWidget.setMinimumHeight(30)
        self.mgridLayout.addWidget(self.listWidget,9,0,1,10)
        
        self.gridLayout.addWidget(self.Monitor)
        self.tabWidget.addTab(self.Monitor, "Monitor")

    def setupAuxTab(self):
    	print inspect.stack()[0][3], 'START'
        self.Aux    = QtWidgets.QWidget()
        self.agridLayout = QtWidgets.QGridLayout(self.Aux)
        
        
        self.insHdTable  = QtWidgets.QTableView(self.Aux)
        self.insRdModel  = pdrmodel.PandasModel(self.opmmData.insrData)
        self.insHdTable.setModel(self.insRdModel)
        self.insHdTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        #self.insHdTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        insHidingModel = self.insHdTable.selectionModel()
        insHidingModel.selectionChanged.connect(self.onHdSelect)
        self.insHdTable.setMinimumHeight(800)  
        self.insHdTable.setAlternatingRowColors(True)
        self.insHdTable.setStyleSheet("alternate-background-color: rgba(100,100,100,15); background-color: white; font: 12px")
        self.insHdTable.setShowGrid(False)
        self.insHdTable.setColumnHidden(2,True)
        self.insHdTable.resizeColumnsToContents()
        for i in range(15,27):
            self.insHdTable.setColumnHidden(i,True)
        self.insHdTable.setColumnWidth(0,25)
        #self.insHdTable.setColumnWidth(1,40)
        self.insHdTable.resizeRowsToContents()
        self.insHdTable.horizontalHeader().setSectionResizeMode(2)        
        self.insHdTable.verticalHeader().setSectionResizeMode(2)        
        self.agridLayout.addWidget(self.insHdTable,1,0,1,4)
        
        ## Aux Buttons
        self.unhidePosn = QtWidgets.QPushButton('Unhide Positions')
        self.unhidePosn.clicked.connect(self.UnhidePosn)
        self.agridLayout.addWidget(self.unhidePosn,0,0,1,1)
        
        #self.stopButton = QtWidgets.QPushButton('Stop All')
        #self.stopButton.clicked.connect(self.StopAll)
        #self.mgridLayout.addWidget(self.stopButton,1,8,1,2)
        
        self.tabWidget.addTab(self.Aux, "AuxTab")

    def onPfItemChange(self, item):
    	print inspect.stack()[0][3], 'START'
        if (item.column() == 0):
            self.onPfStateChange(item)
        else:
            print ("Don't change pf level data, it's read only!!")

    def onPfStateChange(self, item):
    	print inspect.stack()[0][3], 'START'
        data = {}
        data['MsgType'] = 'StateChange'
        data['portfolioId'] = (self.pfModel._data.iloc[item.row()]).portfolioId
        data['instrumentId'] = 0
        data["activePlugin"] = (self.pfModel._data.iloc[item.row()]).activePlugin
        if self.pfModel._data.iloc[item.row()].activePlugin == self.pfModel._data.iloc[item.row()].activePlugin: 
            if self.pfModel._data.iloc[item.row(), 0].checkState() == QtCore.Qt.Checked:
                data['state'] = '4'#'Trading'
                data = {k: str(v) for k, v in data.items()}
                self.client.sendMessage(json.dumps(data).encode('utf8'))
            else:
                data['state'] = '1'#'Active'
                data = {k: str(v) for k, v in data.items()}
                self.client.sendMessage(json.dumps(data).encode('utf8'))
        
    def onInsItemChange(self, item):
    	print inspect.stack()[0][3], 'START'
        #print ("Instrument level change")
        if (item.column() == 0):
            self.onInstrumentStateChange(item)
        else:
            rowIndex = item.row()
            msgType = "OptionParams"
            cols = ["MsgType","portfolioId","instrumentId","quoteBidQty","quoteAskQty","priceCorrection","volCorrection","deltaRetreat","vegaRetreat","deltaSpread","vegaSpread","multiplier","maxOpBuyQty","maxOpSellQty","maxOpNetQty","maxOpBuyValue","maxOpSellValue","spreadTolerance","taxCorrection","minDelta","strikeLimit"]
            tmp = self.insParModel._data.iloc[rowIndex]
            dataToSend = tmp[cols]
            dataToSend['MsgType'] = msgType
            dataToSend["activePlugin"] = (self.insRdModel._data.iloc[item.row()]).activePlugin
            dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
            self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))


    def onInsSelect(self, itemSelect,itemDeselect):
    	print inspect.stack()[0][3], 'START'
        if not itemDeselect.isEmpty():
            indexDeSel = itemDeselect[0]
            rowIndex2 = indexDeSel.top()
            pfDeSelected = (self.insRdModel._data[rowIndex2,0]) -1

            self.vcTable.setRowHidden(pfDeSelected,True)
            self.hedgingParamsTable.setRowHidden(pfDeSelected,True)
            self.pfParamsTable.setRowHidden(pfDeSelected,True)
            self.insParTable.setRowHidden(rowIndex2,True)

        if not itemSelect.isEmpty():
            indexSel = itemSelect[0]
            rowIndex = indexSel.top()
            pfSelected = (self.insRdModel._data[rowIndex,0]) -1

            self.vcTable.setRowHidden(pfSelected,False)
            self.hedgingParamsTable.setRowHidden(pfSelected,False)
            self.pfParamsTable.setRowHidden(pfSelected,False)
            self.insParTable.setRowHidden(rowIndex,False)

    def onHdSelect(self, itemSelect):
    	print inspect.stack()[0][3], 'START'
        if not itemSelect.isEmpty():
            indexSel = itemSelect[0]
            rowIndex = indexSel.top()
            self.insHdTable.setRowHidden(rowIndex,True)
            self.insRdTable.setRowHidden(rowIndex,False)
            

    def onInstrumentStateChange(self, item):
    	print inspect.stack()[0][3], 'START'
        dataToSend = {}
        dataToSend['MsgType'] = 'StateChange'
        dataToSend['portfolioId'] = str((self.insRdModel._data.iloc[item.row()]).portfolioId)
        dataToSend['instrumentId'] = str((self.insRdModel._data.iloc[item.row()]).instrumentId)
        dataToSend["activePlugin"] = str((self.insRdModel._data.iloc[item.row()]).activePlugin)
        if self.insRdModel._data.iloc[item.row()].activePlugin == self.insRdModel._data.iloc[item.row()].activePlugin: 
            if self.insParModel._data.iloc[item.row(), 0].checkState() == QtCore.Qt.Checked:
                dataToSend['state'] = '4'#'Trading'
                dataToSend = {k: str(v) for k, v in dataToSend.items()}
                self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
            else:
                dataToSend['state'] = '1'#'Active'
                dataToSend = {k: str(v) for k, v in dataToSend.items()}
                self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
                self.insRdTable.setRowHidden(item.row(),True)
                self.insRdTable.clearSelection()
                self.insHdTable.setRowHidden(item.row(),False)            
        
    def onVolCurveChange(self, item):
    	print inspect.stack()[0][3], 'START'
        #print ("Vol curve change")
        rowIndex = item.row()
        msgType = "VolCurve"
        cols = ["MsgType", "portfolioId", "atmStrike", "atmVol", "skew", "leftCurve", "leftRange","rightCurve", "rightRange"]
        tmp = self.vcModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = activePlugins[2]
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
        #msgType = "GlobalParams"
        #cols = ["MsgType", "portfolioId", "maxBuyQty", "maxSellQty", "maxBuyValue", "maxSellValue", "maxDelta","maxVega", "maxGamma", "minPnl"]
        #tmp = self.pfParamsModel._data.iloc[rowIndex]
        #dataToSend = tmp[cols]
        #dataToSend['MsgType'] = msgType
        #dataToSend["activePlugin"] = activePlugins[0]
        #dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        #self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))
        
    def onPfParamChange(self, item):
    	print inspect.stack()[0][3], 'START'
        #print ("Global param change")
        rowIndex = item.row()
        msgType = "GlobalParams"
        cols = ["MsgType", "portfolioId", "maxBuyQty", "maxSellQty", "maxBuyValue", "maxSellValue", "maxDelta","maxVega", "maxGamma", "minPnl"]
        tmp = self.pfParamsModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = (self.pfModel._data.iloc[item.row()]).activePlugin
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))

    def onHedgingParamChange(self, item):
    	print inspect.stack()[0][3], 'START'
        #print ("Hedging param change")
        rowIndex = item.row()
        msgType = "HedgingParams"
        cols =  ["MsgType","portfolioId","hedgeDelta","targetDelta","maxBid","maxAsk","tolerance","offset"]
        tmp = self.hedgingParamsModel._data.iloc[rowIndex]
        dataToSend = tmp[cols]
        dataToSend['MsgType'] = msgType
        dataToSend["activePlugin"] = (self.pfModel._data.iloc[item.row()]).activePlugin
        dataToSend = {k: str(v) for k, v in dataToSend.iteritems()}
        self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))

    def onPortfolioDataMessage(self, jsonMsg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(jsonMsg, typ='series')
        pfId = int(data['portfolioId'])
        self.pfModel.updateRow(pfId, data)
        self.pfTable.model().layoutChanged.emit()

    def onPfInfoMessage(self, jsonMsg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(jsonMsg, typ='series')
        pfId = int(data['portfolioId'])
        self.pfModel.updateRow(pfId, data)
        if pfId == 1:
            self.insRdTable.model().layoutChanged.emit()

    def onInstrumentDataMessage(self, jsonMsg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(jsonMsg, typ='series')
        insId = int(data['instrumentId'])
        rowNum = int(np.where(self.insRdModel._data == insId)[0][0])
        print insId
        print rowNum
        #if self.insParModel._data.loc[insId].enabled.checkState() == QtCore.Qt.Checked or self.insRdModel._data.loc[insId].activePlugin != self.insRdModel._data.loc[insId].activePlugin:
            #self.insRdModel.updateRow(insId, data)
        self.insRdModel.updateRow(rowNum, data)
        
    def StartAll(self):
    	print inspect.stack()[0][3], 'START'
        data = {}
        data['MsgType'] = 'UMSG'
        data["activePlugin"] = activePlugins[guiNo -1]
        data["value"] = '1'        
        data = {k: str(v) for k, v in data.items()}
        self.client.sendMessage(json.dumps(data).encode('utf8'))

        
    def StopAll(self):
    	print inspect.stack()[0][3], 'START'
        data = {}
        data['MsgType'] = 'UMSG'
        data["activePlugin"] = activePlugins[guiNo -1]
        data["value"] = '0'        
        data = {k: str(v) for k, v in data.items()}
        self.client.sendMessage(json.dumps(data).encode('utf8'))        

    def ClearAll(self):
    	print inspect.stack()[0][3], 'START'
        morphGUI.listWidget.clear() 
        
    def CheckAll(self):
    	print inspect.stack()[0][3], 'START'
        for i in range(0,self.insRdModel.rowCount()):
            if not self.insRdTable.isRowHidden(i):
                self.insParModel._data.iloc[i, 0].setChecked(True)
                dataToSend = {}
                dataToSend['MsgType'] = 'StateChange'
                dataToSend['portfolioId'] = str((self.insRdModel._data.iloc[i]).portfolioId)
                dataToSend['instrumentId'] = str((self.insRdModel._data.iloc[i]).instrumentId)
                dataToSend["activePlugin"] = str((self.insRdModel._data.iloc[i]).activePlugin)
                if self.insParModel._data.iloc[i, 0].checkState() == QtCore.Qt.Checked and self.insRdModel._data.iloc[i].activePlugin == self.insRdModel._data.iloc[i].activePlugin:
                    dataToSend['state'] = '4'#'Trading'
                    dataToSend = {k: str(v) for k, v in dataToSend.items()}
                    self.client.sendMessage(json.dumps(dataToSend).encode('utf8'))


    def UnhidePosn(self):
    	print inspect.stack()[0][3], 'START'
        for i in range(0,self.insRdModel.rowCount()):
            if (not self.insHdTable.isRowHidden(i)) and self.insRdModel._data.iloc[i].activePlugin == self.insRdModel._data.iloc[i].activePlugin:
                if self.insRdModel._data.iloc[i, 4] != 0 :
                    self.insHdTable.setRowHidden(i,True)
                    self.insRdTable.setRowHidden(i,False)
                    
        
    def onTradeDataMessage(self, jsonMsg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(jsonMsg, typ='series')
        tradeInfo = ["BUY","SELL"]
        inId = data['instrumentId']
        timeNs = data['tradeTime']
        timeNs = int(timeNs/1000000000)
        mi, sc = divmod(timeNs,60)
        hr, mi = divmod(mi,60)
        tContract = self.insRdModel._data.loc[inId]
        morphGUI.tradeList.insertItem(0, str(hr).zfill(2) +":"+ str(mi).zfill(2) +":"+ str(sc).zfill(2) +" ;  "+ tContract.cname +" ;  "+ str(tradeInfo[data['side']]) +" ;  "+ str(data['tradeQty']) +" @  "+ str(data['tradePrice']) +" ;  "+ str(data['refPrice']) )
        
    def onAlertMessage(self, jsonMsg):
    	print inspect.stack()[0][3], 'START'
        data = pd.read_json(jsonMsg, typ='series')
        morphGUI.listWidget.insertItem(0,data['alert'])

    def closeEvent(self, e):
    	print inspect.stack()[0][3], 'START'
        self.reactor.stop()




if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    try:
        import qt5reactor
    except ImportError:
        from twisted.internet import qt5reactor
    qt5reactor.install()

    from twisted.internet import reactor

    #login = Login()

    #if login.exec_() == QtGui.QDialog.Accepted:
        #morphGUI = MorphGUI(reactor)
        #morphGUI.show()
        #reactor.run()

    morphGUI = MorphGUI(reactor)
    morphGUI.show()
    reactor.run()



