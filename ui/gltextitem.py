import pyqtgraph.opengl as gl
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from pyqtgraph.Qt import QtCore, QtGui

class GLTextItem(GLGraphicsItem):
    def __init__(self, X=None, Y=None, Z=None, text=None):
        super().__init__()
        self.text = text
        self.X = X
        self.Y = Y
        self.Z = Z
        #self.GLViewWidget = parent

    def setGLViewWidget(self, GLViewWidget):
        self.GLViewWidget = GLViewWidget

    def setText(self, text):
        self.text = text
        self.update()

    def setX(self, X):
        self.X = X
        self.update()

    def setY(self, Y):
        self.Y = Y
        self.update()

    def setZ(self, Z):
        self.Z = Z
        self.update()

    def paint(self):
        self.GLViewWidget.qglColor(QtCore.Qt.white)
        self.GLViewWidget.renderText(self.X, self.Y, self.Z, self.text)

if __name__ == '__main__':
    import numpy as np
    # demo
    app = QtGui.QApplication([])
    w = gl.GLViewWidget()
    w.opts['distance'] = 40
    w.show()

    poly = np.array(
        [[0.0, 0.0, 1.0],
        [0.0, 3.0, 1.0],
        [3.0, 3.0, 1.0],
        [0.0, 0.0, 1.0]])
    line = gl.GLLinePlotItem(pos=poly,
        color=(0.0, 1.0, 0.0, 1.0), width=2)
    w.addItem(line)

    t1 = GLTextItem(X=0.0, Y=0.0, Z=1.0, text="p1")
    t2 = GLTextItem(X=0.0, Y=3.0, Z=1.0, text="p2")
    t3 = GLTextItem(X=3.0, Y=3.0, Z=1.0, text="p3")
    t1.setGLViewWidget(w)
    t2.setGLViewWidget(w)
    t3.setGLViewWidget(w)
    w.addItem(t1)
    w.addItem(t2)
    w.addItem(t3)

    g = gl.GLGridItem()
    w.addItem(g)

    app.exec_()