from PyQt5 import QtCore, QtGui
import sys
import numpy as np
from PyQt5.QtGui import *   

import pdb
import inspect
class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, minData=None, maxData=None, parent=None):
        print inspect.stack()[0][3], 'START'
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = np.array(data.values)
        self._cols = data.columns
        self.r, self.c = np.shape(self._data)

    def rowCount(self, parent=None):
        return self.r

    def columnCount(self, parent=None):
        return self.c

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        column = index.column()
        #if (self._data.columns[column] == 'enabled'):
            #value = self._data.iloc[index.row() ,column]
        #else:
        value  = str(self._data[index.row(),index.column()])
        if role == QtCore.Qt.DisplayRole:
            return value
        elif role == QtCore.Qt.EditRole:
            return value
        
        ctrct = str(self._data[index.row(), 3])
        
        ##Coloring Rows, Bid-Ask

        return None

    def headerData(self, p_int, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._cols[p_int]
        return None


    def flags(self, index):
        flags = super(self.__class__,self).flags(index)
        flags |= QtCore.Qt.ItemIsSelectable
        flags |= QtCore.Qt.ItemIsEnabled
        return flags

    def updateRow(self, key, data, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False
        for col in data.keys(): #column names are in data.dtype.names
            self._data[key,col] = data[col]
        self._data[key,'net'] = data['bought'] - data['sold'] + self._data[key,'init']
        return True
