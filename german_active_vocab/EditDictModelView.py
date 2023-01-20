#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTreeView, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QRectF, QSize, QItemSelectionModel
from PyQt5.QtGui import QTextDocument, QAbstractTextDocumentLayout


class DictEditorWidget(QTreeView):
    def __init__(self, model, parent=None):
        """ Dict Editor Widget """
        super().__init__(parent=parent)
        
        self.setModel(model)
        # tree_view.setEditTriggers(QAbstractItemView.SelectedClicked)  # .setEditTriggers(QTreeView.NoEditTriggers)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.expandAll()
        self.resizeColumnToContents(0)

        self.clicked.connect(self.onTreeViewClicked)

        delegate = HTMLDelegate();
        self.setItemDelegate(delegate);

        # TODO (5) add x button beside every item
        # x_button = QPushButton('x', self)
        # x_button.resize(10, 10)  # QIcon, str, parent: QWidget = None
        # for i in range(self.model().rowCount()):
        #     idx = self.model().index(i, 2)
        #     self.setIndexWidget(idx, x_button)

    def onTreeViewClicked(self, index):
        nb_children = index.internalPointer().childCount()
        if nb_children == 0:
            return
        for r in range(nb_children):
            childIndex = self.model().index(r,0,index);
            self.selectionModel().select(childIndex, QItemSelectionModel.Select)
            self.onTreeViewClicked(childIndex)
            childIndex = self.model().index(r,1,index);
            self.selectionModel().select(childIndex, QItemSelectionModel.Select)
            self.onTreeViewClicked(childIndex)


class TreeModel(QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)
        """ subclassing the standard interface item models must use and 
                implementing index(), parent(), rowCount(), columnCount(), and data()."""

        rootData = [header for header in headers]
        self.rootItem = TreeNode(rootData)
        indent = -1
        self.parents = [self.rootItem]
        self.indentations = [0]
        self.createData(data, indent)

    def createData(self, data, indent=-1):
        if type(data) == dict:
            indent += 1
            position = 4 * indent
            for dict_keys, dict_values in data.items():
                if position > self.indentations[-1]:
                    if self.parents[-1].childCount() > 0:
                        self.parents.append(self.parents[-1].child(self.parents[-1].childCount() - 1))
                        self.indentations.append(position)
                else:
                    while position < self.indentations[-1] and len(self.parents) > 0:
                        self.parents.pop()
                        self.indentations.pop()
                parent = self.parents[-1]
                parent.insertChildren(parent.childCount(), 1, parent.columnCount())
                parent.child(parent.childCount() - 1).setData(0, dict_keys)
                if not isinstance(dict_values ,(dict,list)):
                    parent.child(parent.childCount() - 1).setData(1, str(dict_values))
                elif isinstance(dict_values, dict):
                    # TODO (2) STRUCT (systematicly?) mirror changes in get obj path structure
                    if 'header_num' in dict_values:
                        parent.child(parent.childCount() - 1).setData(0, dict_values['header_num'])
                self.createData(dict_values, indent)
        elif type(data) == list:
            indent += 1
            position = 4 * indent
            for values in data:
                if position > self.indentations[-1]:
                    if self.parents[-1].childCount() > 0:
                        self.parents.append(self.parents[-1].child(self.parents[-1].childCount() - 1))
                        self.indentations.append(position)
                else:
                    while position < self.indentations[-1] and len(self.parents) > 0:
                        self.parents.pop()
                        self.indentations.pop()
                parent = self.parents[-1]
                parent.insertChildren(parent.childCount(), 1, parent.columnCount())
                # parent.child(parent.childCount() - 1).setData(0, dict_keys)
                if not isinstance(values ,(dict,list)):
                    parent.child(parent.childCount() - 1).setData(1, str(values))
                elif isinstance(values, dict):
                    if 'header_num' in values:
                        parent.child(parent.childCount() - 1).setData(0, values['header_num'])
                self.createData(values, indent)

    def index(self, row, column, index=QModelIndex()):
        """ Returns the index of the item in the model specified by the given row, column and parent index """

        if not self.hasIndex(row, column, index):
            return QModelIndex()
        if not index.isValid():
            item = self.rootItem
        else:
            item = index.internalPointer()

        child = item.child(row)
        if child:
            # print(f'Row: {row}, Column: {column}')
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index):
        """ Returns the parent of the model item with the given index
                If the item has no parent, an invalid QModelIndex is returned """

        if not index.isValid():
            return QModelIndex()
        item = index.internalPointer()
        if not item:
            return QModelIndex()

        parent = item.parent_item
        if parent == self.rootItem:
            return QModelIndex()
        else:
            return self.createIndex(parent.childNumber(), 0, parent)

    def rowCount(self, index=QModelIndex()):
        """ Returns the number of rows under the given parent
                When the parent is valid it means that rowCount is returning the number of children of parent """

        if index.isValid():
            parent = index.internalPointer()
        else:
            parent = self.rootItem
        return parent.childCount()

    def columnCount(self, index=QModelIndex()):
        """ Returns the number of columns for the children of the given parent """

        return self.rootItem.columnCount()

    def data(self, index, role=Qt.DisplayRole):
        """ Returns the data stored under the given role for the item referred to by the index """

        if index.isValid() and (role == Qt.DisplayRole or role == Qt.EditRole):
            return index.internalPointer().data(index.column())
        elif not index.isValid():
            return self.rootItem.data(index.column())

        

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Returns the data for the given role and section in the header with the specified orientation """

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

    def removeRows(self, position: int, rows: int,
                   parent: QModelIndex = QModelIndex()) -> bool:
        parent_item: TreeNode = self.get_item(parent)
        if not parent_item:
            return False

        self.beginRemoveRows(parent, position, position + rows - 1)
        success: bool = parent_item.remove_children(position, rows)
        self.endRemoveRows()

        return success

    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEditable | super(TreeModel, self).flags(index)

    # def flags(self, index):
    #     return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.rootItem

    def get_dict_address(self, index):
        text = self.data(index)
        last_index = index
        address = []
        while last_index.isValid():
            column = last_index.column()
            assert column<2, "Index path is not valid."
            row = last_index.row()
            if column == 0:
                last_index_content = last_index.data()
                if last_index_content:
                    if (last_index_content[0].isdigit()
                        or last_index_content=='Phrases:'):
                        #special case for header_num
                        address.append(row)
                    else:
                        address.append(last_index_content)
                else:
                    address.append(row)
            elif column == 1:
                # element is value in dict
                # DONE (0) test with multiple examples
                key = last_index.siblingAtColumn(0).data()
                if key:
                    address.append(key)
                else:
                    address.append(row)
            last_index = last_index.parent()
        
        address.reverse()
        return text, address

    # def updateActions(self):
    #     hasSelection = not self.view.selectionModel().selection().isEmpty()
    #     self.removeRowAction.setEnabled(hasSelection)
    #     self.removeColumnAction.setEnabled(hasSelection)

    #     hasCurrent = self.view.selectionModel().currentIndex().isValid()
    #     self.insertRowAction.setEnabled(hasCurrent)
    #     self.insertColumnAction.setEnabled(hasCurrent)

    #     if hasCurrent:
    #         self.view.closePersistentEditor(self.view.selectionModel().currentIndex())

    #         row = self.view.selectionModel().currentIndex().row()
    #         column = self.view.selectionModel().currentIndex().column()
    #         if self.view.selectionModel().currentIndex().parent().isValid():
    #             self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
    #         else:
    #             self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))    


class TreeNode(object):
    def __init__(self, data, parent=None):
        self.parent_item = parent
        self.item_data = data
        self.children = []

    def child(self, row):
        return self.children[row]

    def childCount(self):
        return len(self.children)

    def childNumber(self):
        if self.parent_item is not None:
            return self.parent_item.children.index(self)

    def columnCount(self):
        return len(self.item_data)

    def data(self, column):
        return self.item_data[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.children):
            return False
        for row in range(count):
            data = [None] * columns
            item = TreeNode(data, self)
            self.children.insert(position, item)
        
        return True

    def remove_children(self, position: int, count: int) -> bool:
        if position < 0 or position + count > len(self.children):
            return False

        for row in range(count):
            self.children.pop(position)

        return True

    def remove_columns(self, position: int, columns: int) -> bool:
        if position < 0 or position + columns > len(self.item_data):
            return False

        for column in range(columns):
            self.item_data.pop(position)

        for child in self.child_items:
            child.remove_columns(position, columns)

        return True

    def parent(self):
        return self.parent_item

    def setData(self, column, value):
        if column < 0 or column >= len(self.item_data):
            return False
        self.item_data[column] = value
        return True

class HTMLDelegate( QStyledItemDelegate ):
    def __init__( self ):
        super().__init__()
        # probably better not to create new QTextDocuments every ms
        self.doc = QTextDocument()
        self.doc.setDefaultStyleSheet("background: rgba(0,0,0,0)")

    def paint(self, painter, option, index):
        if index.column() == 1:
            options = QStyleOptionViewItem(option)
            self.initStyleOption(options, index)
            painter.save()
            self.doc.setTextWidth(options.rect.width())                
            self.doc.setHtml(options.text)
            self.doc.setDefaultFont(options.font)
            options.text = ''
            options.widget.style().drawControl(QStyle.CE_ItemViewItem, options, painter)
            painter.translate(options.rect.left(), options.rect.top())
            clip = QRectF(0, 0, options.rect.width(), options.rect.height())
            painter.setClipRect(clip)
            ctx = QAbstractTextDocumentLayout.PaintContext()
            ctx.clip = clip
            self.doc.documentLayout().draw(painter, ctx)
            painter.restore()
        else:
            QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint( self, option, index ):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        self.doc.setHtml(option.text)
        self.doc.setTextWidth(option.rect.width())
        return QSize(int(self.doc.idealWidth()), int(self.doc.size().height()))