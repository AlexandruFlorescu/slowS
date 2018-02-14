from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import numpy as np
from PyQt5.QtGui import *   

import pdb

class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, minData=None, maxData=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self._min  = minData
        self._max  = maxData

    def rowCount(self, parent=None):
        return len(self._data.index)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        column = index.column()
        if (self._data.columns[column] == 'enabled'):
            value = self._data.iloc[index.row() ,column]
        else:
            value  = str(self._data.values[index.row()][column])
        if role == QtCore.Qt.DisplayRole:
            return value
        elif role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.CheckStateRole:
            if (self._data.columns[column] == 'enabled'):
                if self._data.iloc[index.row(), column].isChecked():
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

                        
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        row = index.row()
        if row < 0 or row >= len(self._data.values):
            return False
        column = index.column()
        if column < 0 or column >= self._data.columns.size:
            return False
        if (role == QtCore.Qt.CheckStateRole) and (self._data.columns[column] == 'enabled'):
            if value == QtCore.Qt.Checked:
                self._data.iloc[row, column].setChecked(True)
            else:
                self._data.iloc[row, column].setChecked(False)
        elif role == QtCore.Qt.EditRole:
            try:
                val = float(value)
            except ValueError:
                valErr = QtWidgets.QMessageBox()
                valErr.setText("Don't set non-numeric values dude!!")
                valErr.exec_()
                return False
            if (self._min is None) or (self._max is None):
                self._data.iloc[row ,column] = val
            else:
                minLimit = self._min.iloc[row, column]
                maxLimit = self._max.iloc[row, column]
                if (val < minLimit) or (val > maxLimit):
                    limitError = QtWidgets.QMessageBox()
                    limitError.setText("Limit Exceeded, Value Entered = %.1f, Minimum Limit = %.1f, Maximum Limit = %.1f" % (val, minLimit, maxLimit))
                    limitError.exec_()

                    return False
                else:
                    self._data.iloc[row ,column] = val

        else:
            return False

        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        flags = super(self.__class__,self).flags(index)
        column = index.column()
        if (self._data.columns[column] == 'enabled'):
            flags |= QtCore.Qt.ItemIsUserCheckable
            flags |= QtCore.Qt.ItemIsEnabled 
            flags |= QtCore.Qt.ItemIsSelectable
        else:
            flags |= QtCore.Qt.ItemIsEditable
            flags |= QtCore.Qt.ItemIsSelectable
            flags |= QtCore.Qt.ItemIsEnabled
            #flags |= QtCore.Qt.ItemIsDragEnabled
            #flags |= QtCore.Qt.ItemIsDropEnabled
        return flags

    def insertRow(self, row, index=QtCore.QModelIndex()):
        #print "Inserting at row: %s"%row
        self.beginInsertRows(QtCore.QModelIndex(), 0, 1)
        self._data = self._data.append(row, ignore_index=True)
        self.endInsertRows()
        return True

    def updateRow(self, key, data, role=QtCore.Qt.EditRole):
        if (not key in self._data.index):
            return False
        if role != QtCore.Qt.EditRole:
            return False
        for col in data.keys():
            self._data.loc[key,col] = data[col]
        return True

