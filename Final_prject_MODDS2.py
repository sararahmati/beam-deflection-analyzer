from sympy.physics.continuum_mechanics.beam import Beam
from sympy import symbols
from PyQt5 import QtGui
from PyQt5.QtWidgets import QLineEdit,QApplication,QLabel,QMainWindow,QPushButton,QVBoxLayout,QWidget,QHBoxLayout,QGroupBox,QRadioButton
from PyQt5.QtGui import QIcon, QFont,QImage, QPalette, QBrush
from PyQt5.QtCore import QSize
import sys

# Inputs are stored in

listofinputs=[]
units=[]

## convert units

def convert_len(val, unit_in, unit_out):
    SI = { 'mm':0.001, 'm':1.0, 'ft':0.3048,'in':0.0254}
    return round(val*SI[unit_in]/SI[unit_out],4)

def convert_force(val, unit_in, unit_out):
    force = {'N':1.0,'KN':1000.0,'lb':4.448,'kip':4448.2216}
    return round(val*force[unit_in]/force[unit_out],4)

def convert_moment(val, unitf_in, unitf_out,unitl_in, unitl_out):
    force = {'N':1.0,'KN':1000.0,'lb':4.448,'kip':4448.2216}
    SI = {'mm': 0.001, 'm': 1.0, 'ft': 0.3048, 'in': 0.0254}
    return round((val * force[unitf_in] / force[unitf_out])*(SI[unitl_in]/SI[unitl_out]),4)

def convert_dist(val, unitf_in, unitf_out,unitl_in, unitl_out):
    force = {'N':1.0,'KN':1000.0,'lb':4.448,'kip':4448.2216}
    SI = {'mm': 0.001, 'm': 1.0, 'ft': 0.3048, 'in': 0.0254}
    return round((val * force[unitf_in] / force[unitf_out])/(SI[unitl_in]/SI[unitl_out]),4)

def convert_I(val, unit_in, unit_out):
    SI = { 'mm':0.001, 'm':1.0, 'ft':0.3048,'in':0.0254}
    return round(val*SI[unit_in]**4/SI[unit_out]**4,4)

## Calculate moment of inertia

def MomentOfInertia(bf1,tf1,d,tw,bf2,tf2):
    sigmaa = bf1 * tf1 + d * tw + tf2 * bf2
    ybar = (tf1 / 2 * bf1 * tf1 + (d / 2 + tf1) * d * tw + (d + tf1 + tf2 / 2) * tf2 * bf2) / sigmaa
    ix = 1 / 12 * bf1 * tf1 ** 3 + (ybar - tf1 / 2) ** 2 * (bf1 * tf1) + 1 / 12 * d ** 3 * tw + (
                ybar - (d / 2 + tf1)) ** 2 * d * tw + 1 / 12 * bf2 * tf2 ** 3 + bf2 * tf2 * (
                     ybar - (d + tf1 + tf2 / 2)) ** 2
    return ix

## working with PYQT5

class Main_Window(QWidget):
    def __init__(self):
       QWidget.__init__(self)
       self.setGeometry(100,100,400,400)
       button = QPushButton('Continue')
       oImage = QImage("beam.jpg")
       sImage = oImage.scaled(QSize(400,400))                   # resize Image to widgets size
       palette = QPalette()
       palette.setBrush(QPalette.Window, QBrush(sImage))
       self.setPalette(palette)

       self.label = QLabel('welcome to the beam solver application ', self)
       self.label.setGeometry(90,20,300,50)
       self.label = QLabel('To continue please follow the steps',
                           self)
       self.label.setGeometry(90, 50, 300, 50)
       self.setWindowTitle('Title')

class AnotherWindow1(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        label = QLabel('please enter the length of the beam:')
        button = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        button.clicked.connect(self.button_clicked)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Add beam')

##connecting buttons to function to make them productive

    def button_clicked(self):
        print("Length:" +self.textbox.text())
        l=convert_len(float(self.textbox.text()),units[0],units[1])
        listofinputs.append(l)
        self.hide()

class AnotherWindow2(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        label = QLabel('please enter the number of supports:')
        button = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        button.clicked.connect(self.button_clicked2)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('number of supports')

    def button_clicked2(self):
        listofinputs.append(int(self.textbox.text()))             ## add input to the list
        self.hide()
        print("Number of supports:"+self.textbox.text())

class AnotherWindow6(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        label = QLabel('please enter the number of Point Loads:')
        button = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        button.clicked.connect(self.button_clicked2)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('number of point loads')

    def button_clicked2(self):
        listofinputs.append("pointload")
        listofinputs.append(int(self.textbox.text()))      ## add input to the list
        print("Number of point lpads:"+ self.textbox.text())
        self.hide()

class AnotherWindow8(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        label = QLabel('please enter the number of Distributed Loads:')
        button = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        button.clicked.connect(self.button_clicked2)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('number of distributed loads')

    def button_clicked2(self):
        listofinputs.append("distload")
        listofinputs.append(int(self.textbox.text()))
        self.hide()
        print("Number of distributed loads:"+ self.textbox.text())

class AnotherWindow10(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        label = QLabel('please enter the number of Moments:')
        button = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        button.clicked.connect(self.button_clicked2)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('number of Moments')

    def button_clicked2(self):
        listofinputs.append("moment")
        listofinputs.append(int(self.textbox.text()))
        self.hide()
        print("Number of moments:"+self.textbox.text())

class AnotherWindow3(QWidget):
    def __init__(self):
        super().__init__()

        #winow requirement
        self.setGeometry(200,200, 400,300)
        #our method call
        self.create_radiobutton()
        #we need to create vertical layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.groupbox)
        #this is our label
        self.label = QLabel("")
        self.label.setFont(QFont("Sanserif", 14))
        #add your widgets in the vbox layout
        vbox.addWidget(self.label)
        #set your main window layout
        self.setLayout(vbox)
        but = QPushButton('Undo', self)
        but.clicked.connect(self.undo)
        but.resize(130, 20)
        but.move(160, 150)

    def create_radiobutton(self):

        #this is our groupbox
        self.groupbox = QGroupBox("choose the support types ")
        self.groupbox.setFont(QFont("Sanserif", 15))


        #this is hbox layout
        hbox = QHBoxLayout()

        #these are the radiobuttons
        self.rad1 = QRadioButton("pin")
        self.rad1.setChecked(True)
        self.rad1.setIcon(QIcon('pin.png'))
        self.rad1.setIconSize(QSize(40,40))
        self.rad1.setFont(QFont("Sanserif", 14))
        self.rad1.toggled.connect(self.on_selected)
        hbox.addWidget(self.rad1)

        self.rad2 = QRadioButton("fixed")
        self.rad2.setIcon(QIcon('fixed.jpg'))
        self.rad2.setIconSize(QSize(40, 40))
        self.rad2.setFont(QFont("Sanserif", 14))
        self.rad2.toggled.connect(self.on_selected)
        hbox.addWidget(self.rad2)

        self.rad3 = QRadioButton("roller")
        self.rad3.setIcon(QIcon('roller.png'))
        self.rad3.setIconSize(QSize(40, 40))
        self.rad3.setFont(QFont("Sanserif", 14))
        self.rad3.toggled.connect(self.on_selected)
        hbox.addWidget(self.rad3)
        self.groupbox.setLayout(hbox)

    #method or slot for the toggled signal

    def on_selected(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            self.label.setText("the support type : " + radio_button.text())
            s=str(radio_button.text())
            listofinputs.append(s)

    ##undo button function

    def undo(self):
        print(listofinputs[-1] +" has been removed")
        listofinputs.pop(-1)     ## remove the last element of the list

class AnotherWindow4(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()
    def initUI(self):

        label = QLabel('please enter the place of the supports:')
        button1 = QPushButton('OK')
        self.textbox = QLineEdit()
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.textbox)
        hbox.addWidget(button1)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)
        self.label = QLabel("")
        self.label.setFont(QFont("Sanserif", 14))
        #add your widgets in the vbox layout
        vbox.addWidget(self.label)
        button1.clicked.connect(self.button1_clicked)
        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Add supports')
        self.label.setText("please enter each support location in the input order ")

    def button1_clicked(self):
        l=convert_len(float(self.textbox.text()),units[0],units[1])             ## usage of convert functions
        listofinputs.append(l)
        print("place:"+self.textbox.text())

class AnotherWindow5(QWidget):
    def __init__(self):
        super().__init__()

        #winow requirement
        self.setGeometry(200,200, 400,300)
        #our method call
        self.create_radiobutton()
        #we need to create vertical layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.groupbox1)
        vbox.addWidget(self.groupbox2)
        vbox.addWidget(self.groupbox3)
        vbox.addWidget(self.groupbox4)
        #this is our label
        self.label = QLabel("")
        self.label.setFont(QFont("Sanserif", 14))
        #add your widgets in the vbox layout
        vbox.addWidget(self.label)
        #set your main window layout
        self.setLayout(vbox)
        but = QPushButton('Undo', self)
        but.clicked.connect(self.undo)
        but.resize(130, 20)
        but.move(200, 320)

    def create_radiobutton(self):

        #this is our groupbox
        self.groupbox1 = QGroupBox("choose your input unit for lenght")
        self.groupbox1.setFont(QFont("Sanserif", 15))

        #this is hbox layout
        hbox1 = QHBoxLayout()

        #these are the radiobuttons
        self.rad1 = QRadioButton("m")
        self.rad1.setChecked(True)
        self.rad1.setFont(QFont("Sanserif", 14))
        self.rad1.toggled.connect(self.on_selected)
        hbox1.addWidget(self.rad1)

        self.rad2 = QRadioButton("ft")
        self.rad2.setFont(QFont("Sanserif", 14))
        self.rad2.toggled.connect(self.on_selected)
        hbox1.addWidget(self.rad2)

        self.rad3 = QRadioButton("in")
        self.rad3.setFont(QFont("Sanserif", 14))
        self.rad3.toggled.connect(self.on_selected)
        hbox1.addWidget(self.rad3)
        self.groupbox1.setLayout(hbox1)

        self.rad4 = QRadioButton("mm")
        self.rad4.setFont(QFont("Sanserif", 14))
        self.rad4.toggled.connect(self.on_selected)
        hbox1.addWidget(self.rad4)
        self.groupbox1.setLayout(hbox1)

        self.groupbox2 = QGroupBox("choose your output unit for lenght")
        self.groupbox2.setFont(QFont("Sanserif", 15))
        hbox2 = QHBoxLayout()
        self.rad21 = QRadioButton("m")
        self.rad21.setChecked(True)
        self.rad21.setFont(QFont("Sanserif", 14))
        self.rad21.toggled.connect(self.on_selected)
        hbox2.addWidget(self.rad21)

        self.rad22 = QRadioButton("ft")
        self.rad22.setFont(QFont("Sanserif", 14))
        self.rad22.toggled.connect(self.on_selected)
        hbox2.addWidget(self.rad22)

        self.rad23 = QRadioButton("in")
        self.rad23.setFont(QFont("Sanserif", 14))
        self.rad23.toggled.connect(self.on_selected)
        hbox2.addWidget(self.rad23)
        self.groupbox2.setLayout(hbox2)

        self.rad24 = QRadioButton("mm")
        self.rad24.setFont(QFont("Sanserif", 14))
        self.rad24.toggled.connect(self.on_selected)
        hbox2.addWidget(self.rad24)
        self.groupbox2.setLayout(hbox2)

        self.groupbox3 = QGroupBox("choose your input unit for Force")
        self.groupbox3.setFont(QFont("Sanserif", 15))
        hbox3 = QHBoxLayout()
        self.rad31 = QRadioButton("N")
        self.rad31.setChecked(True)
        self.rad31.setFont(QFont("Sanserif", 14))
        self.rad31.toggled.connect(self.on_selected)
        hbox3.addWidget(self.rad31)

        self.rad32 = QRadioButton("KN")
        self.rad32.setFont(QFont("Sanserif", 14))
        self.rad32.toggled.connect(self.on_selected)
        hbox3.addWidget(self.rad32)

        self.rad33 = QRadioButton("lb")
        self.rad33.setFont(QFont("Sanserif", 14))
        self.rad33.toggled.connect(self.on_selected)
        hbox3.addWidget(self.rad33)
        self.groupbox3.setLayout(hbox3)

        self.rad34 = QRadioButton("kip")
        self.rad34.setFont(QFont("Sanserif", 14))
        self.rad34.toggled.connect(self.on_selected)
        hbox3.addWidget(self.rad34)
        self.groupbox3.setLayout(hbox3)

        self.groupbox4 = QGroupBox("choose your output unit for Force")
        self.groupbox4.setFont(QFont("Sanserif", 15))
        hbox4 = QHBoxLayout()
        self.rad41 = QRadioButton("N")
        self.rad41.setChecked(True)
        self.rad41.setFont(QFont("Sanserif", 14))
        self.rad41.toggled.connect(self.on_selected)
        hbox4.addWidget(self.rad41)

        self.rad42 = QRadioButton("KN")
        self.rad42.setFont(QFont("Sanserif", 14))
        self.rad42.toggled.connect(self.on_selected)
        hbox4.addWidget(self.rad42)

        self.rad43 = QRadioButton("lb")
        self.rad43.setFont(QFont("Sanserif", 14))
        self.rad43.toggled.connect(self.on_selected)
        hbox4.addWidget(self.rad43)
        self.groupbox4.setLayout(hbox4)

        self.rad44 = QRadioButton("kip")
        self.rad44.setFont(QFont("Sanserif", 14))
        self.rad44.toggled.connect(self.on_selected)
        hbox4.addWidget(self.rad44)
        self.groupbox4.setLayout(hbox4)

    #method or slot for the toggled signal
    def on_selected(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            self.label.setText("chosen Unit: " + radio_button.text())
            s=str(radio_button.text())
            units.append(s)
            print(s)

    def undo(self):
        print(units[-1] +" has been removed")
        units.pop(-1)

class AnotherWindow7(QWidget):
    def __init__(self):
        super().__init__()
        self.my_buttons()
        self.setMinimumSize(QSize(500, 500))
        self.setWindowTitle("Point Load")

        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Position:')
        self.line = QLineEdit(self)

        self.line.move(160, 125)
        self.line.resize(130, 20)
        self.nameLabel.move(80, 120)

        pybutton = QPushButton('OK', self)
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(130, 20)
        pybutton.move(160, 150)

        self.nameLabel2 = QLabel(self)
        self.nameLabel2.setText('Magnitude:')
        self.line2 = QLineEdit(self)

        self.line2.move(160, 175)
        self.line2.resize(130, 20)
        self.nameLabel2.move(80, 170)

        pybutton2 = QPushButton('OK', self)
        pybutton2.clicked.connect(self.clickMethod2)
        pybutton2.resize(130, 20)
        pybutton2.move(160, 200)

    def clickMethod(self):
        print('pos: ' + self.line.text())
        l=convert_len(float(self.line.text()),units[0],units[1])
        listofinputs.append(l)

    def clickMethod2(self):
        print('Mag: ' + self.line2.text())
        l=convert_force(float(self.line2.text()),units[2],units[3])
        listofinputs.append(l)

    def my_buttons(self):
        btn1 = QPushButton(self)
        btn1.setGeometry(160, 60, 60, 60)
        btn1.setIcon(QIcon("up.jpg"))
        btn1.setIconSize(QSize(60, 60))
        btn1.clicked.connect(self.button_clicked1)

        btn2 = QPushButton(self)
        btn2.setGeometry(290, 60, 60, 60)
        btn2.setIcon(QIcon("down.jpg"))
        btn2.setIconSize(QSize(60, 60))
        btn2.clicked.connect(self.button_clicked2)

    def button_clicked1(self):
        print("pressed")
        listofinputs.append("+")

    def button_clicked2(self):
        print("pressed")
        listofinputs.append("-")

class AnotherWindow11(QWidget):
    def __init__(self):
        super().__init__()
        self.my_buttons()
        self.setMinimumSize(QSize(500, 500))
        self.setWindowTitle("Moment")

        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Position:')
        self.line = QLineEdit(self)

        self.line.move(160, 125)
        self.line.resize(130, 20)
        self.nameLabel.move(80, 125)

        pybutton = QPushButton('OK', self)
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(130,20)
        pybutton.move(160, 150)

        self.nameLabel3 = QLabel(self)
        self.nameLabel3.setText(' Magnitude:')
        self.line3 = QLineEdit(self)

        self.line3.move(160, 175)
        self.line3.resize(130, 20)
        self.nameLabel3.move(80, 175)

        pybutton3 = QPushButton('OK', self)
        pybutton3.clicked.connect(self.clickMethod3)
        pybutton3.resize(130,20)
        pybutton3.move(160, 200)

    def clickMethod(self):
        l=convert_len(float(self.line.text()),units[0],units[1])
        listofinputs.append(l)
        print('Pos: ' + self.line.text())

    def clickMethod3(self):
        l=convert_force(float(self.line3.text()), units[2], units[3])
        listofinputs.append(l)
        print('Mag: ' + self.line3.text())

    def my_buttons(self):
        btn1 = QPushButton(self)
        btn1.setGeometry(160, 60, 60, 60)
        btn1.setIcon(QIcon("counterclock.jpg"))
        btn1.setIconSize(QSize(60, 60))
        btn1.clicked.connect(self.button_clicked1)

        btn2 = QPushButton(self)
        btn2.setGeometry(290, 60, 60, 60)
        btn2.setIcon(QIcon("clock.jpg"))
        btn2.setIconSize(QSize(60, 60))
        btn2.clicked.connect(self.button_clicked2)

    def button_clicked1(self):
        print("pressed")
        listofinputs.append("ccw")

    def button_clicked2(self):
        print("pressed")
        listofinputs.append("cw")

class AnotherWindow12(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(590, 602))
        self.setWindowTitle("Section properties")
        self.namelabel1 = QLabel(self)
        self.namelabel1.setText("TFw")
        self.line = QLineEdit(self)
        self.line.move(202, 250)
        self.line.resize( 151, 31)
        self.namelabel1.move(140, 260)
        pybutton1 = QPushButton('OK', self)
        pybutton1.clicked.connect(self.clickMethod)
        pybutton1.resize(93, 28)
        pybutton1.move(360, 250)

        self.namelabel2 = QLabel(self)
        self.namelabel2.setText("TFt")
        self.line2 = QLineEdit(self)
        self.line2.move(202, 290)
        self.line2.resize( 151, 31)
        self.namelabel2.move(140, 300)
        pybutton2 = QPushButton('OK', self)
        pybutton2.clicked.connect(self.clickMethod2)
        pybutton2.resize(93, 28)
        pybutton2.move(360, 290)
        self.namelabel3 = QLabel(self)

        self.namelabel3.setText("BFw")
        self.line3 = QLineEdit(self)
        self.line3.move(202, 330)
        self.line3.resize(151, 31)
        self.namelabel3.move(140, 340)
        pybutton3 = QPushButton('OK', self)
        pybutton3.clicked.connect(self.clickMethod3)
        pybutton3.resize(93, 28)
        pybutton3.move(360, 330)

        self.namelabel4 = QLabel(self)
        self.namelabel4.setText("BFt")
        self.line4 = QLineEdit(self)
        self.line4.move(202, 370)
        self.line4.resize(151, 31)
        self.namelabel4.move(140, 380)
        pybutton4 = QPushButton('OK', self)
        pybutton4.clicked.connect(self.clickMethod4)
        pybutton4.resize(93, 28)
        pybutton4.move(360, 370)

        self.namelabel5 = QLabel(self)
        self.namelabel5.setText("Wh")
        self.line5 = QLineEdit(self)
        self.line5.move(202, 410)
        self.line5.resize(151, 31)
        self.namelabel5.move(140, 420)
        pybutton5 = QPushButton('OK', self)
        pybutton5.clicked.connect(self.clickMethod5)
        pybutton5.resize(93, 28)
        pybutton5.move(360, 410)

        self.namelabel6 = QLabel(self)
        self.namelabel6.setText("Wt")
        self.line6 = QLineEdit(self)
        self.line6.move(202, 450)
        self.line6.resize(151, 31)
        self.namelabel6.move(140, 460)
        pybutton6 = QPushButton('OK', self)
        pybutton6.clicked.connect(self.clickMethod6)
        pybutton6.resize(93, 28)
        pybutton6.move(360, 450)

        self.namelabel7 = QLabel(self)
        self.namelabel7.setText("")
        self.namelabel7.setPixmap(QtGui.QPixmap("IBeam.png"))
        self.namelabel7.move(210, 30)

        self.namelabel8 = QLabel(self)
        self.namelabel8.setText("Modulus of Elasticity (GPa)")
        self.line8 = QLineEdit(self)
        self.line8.move(202, 490)
        self.line8.resize(151, 31)
        self.namelabel8.move(40 ,500)
        pybutton8 = QPushButton('OK', self)
        pybutton8.clicked.connect(self.clickMethod8)
        pybutton8.resize(93, 28)
        pybutton8.move(360, 490)

    ##convert section geometry to output unit
    def clickMethod(self):
        tfw=convert_len(float(self.line.text()),units[0],units[1])
        print(f"TFw={self.line.text()}")
        listofinputs.append("I")
        listofinputs.append(tfw)

    def clickMethod2(self):
        tft=convert_len(float(self.line2.text()),units[0],units[1])
        print(f"TFt={self.line2.text()}")
        listofinputs.append(tft)

    def clickMethod3(self):
        bfw=convert_len(float(self.line3.text()),units[0],units[1])
        print(f"BFw={self.line3.text()}")
        listofinputs.append(bfw)

    def clickMethod4(self):
        bft=convert_len(float(self.line4.text()),units[0],units[1])
        print(f"BFt={self.line4.text()}")
        listofinputs.append(bft)

    def clickMethod5(self):
        wh=convert_len(float(self.line5.text()),units[0],units[1])
        print(f"Wh={self.line5.text()}")
        listofinputs.append(wh)

    def clickMethod6(self):
        wt=convert_len(float(self.line6.text()),units[0],units[1])
        print(f"Wt={self.line6.text()}")
        listofinputs.append(wt)

    def clickMethod8(self):
        E=float(self.line8.text())
        print(f"E={self.line8.text()}")
        listofinputs.append("E")
        listofinputs.append(E)

class AnotherWindow9(QWidget):
    def __init__(self):
        super().__init__()
        self.my_buttons()
        self.setMinimumSize(QSize(500, 500))
        self.setWindowTitle("Distributed Load")

        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Start Position:')
        self.line = QLineEdit(self)

        self.line.move(160, 125)
        self.line.resize(130, 20)
        self.nameLabel.move(80, 120)

        pybutton = QPushButton('OK', self)
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(130,20)
        pybutton.move(160, 150)


        self.nameLabel2 = QLabel(self)
        self.nameLabel2.setText('End Position:')
        self.line2 = QLineEdit(self)

        self.line2.move(160, 175)
        self.line2.resize(130, 20)
        self.nameLabel2.move(80, 170)

        pybutton2 = QPushButton('OK', self)
        pybutton2.clicked.connect(self.clickMethod2)
        pybutton2.resize(130,20)
        pybutton2.move(160, 200)


        self.nameLabel3 = QLabel(self)
        self.nameLabel3.setText('Start Magnitude:')
        self.line3 = QLineEdit(self)

        self.line3.move(160, 225)
        self.line3.resize(130, 20)
        self.nameLabel3.move(80, 220)

        pybutton3 = QPushButton('OK', self)
        pybutton3.clicked.connect(self.clickMethod3)
        pybutton3.resize(130,20)
        pybutton3.move(160, 250)


        self.nameLabel4 = QLabel(self)
        self.nameLabel4.setText('End Magnitude:')
        self.line4 = QLineEdit(self)

        self.line4.move(160, 275)
        self.line4.resize(130, 20)
        self.nameLabel4.move(80, 270)

        pybutton4 = QPushButton('OK', self)
        pybutton4.clicked.connect(self.clickMethod4)
        pybutton4.resize(130,20)
        pybutton4.move(160, 300)

    def clickMethod(self):
        l=convert_len(float(self.line.text()),units[0],units[1])
        listofinputs.append(l)
        print('start pos: ' + self.line.text())

    def clickMethod2(self):
        l = convert_len(float(self.line2.text()), units[0], units[1])
        listofinputs.append(l)
        print('End pos: ' + self.line2.text())

    def clickMethod3(self):
        l = convert_force(float(self.line3.text()), units[2], units[3])
        listofinputs.append(l)
        print('Start Mag: ' + self.line3.text())

    def clickMethod4(self):
        l = convert_force(float(self.line4.text()), units[2], units[3])
        listofinputs.append(l)
        print('End Mag: ' + self.line4.text())

    def my_buttons(self):
        btn1 = QPushButton(self)
        btn1.setGeometry(160, 60, 60, 60)
        btn1.setIcon(QIcon("up.jpg"))
        btn1.setIconSize(QSize(60, 60))
        btn1.clicked.connect(self.button_clicked1)

        btn2 = QPushButton(self)
        btn2.setGeometry(290, 60, 60, 60)
        btn2.setIcon(QIcon("down.jpg"))
        btn2.setIconSize(QSize(60, 60))
        btn2.clicked.connect(self.button_clicked2)

    def button_clicked1(self):
        listofinputs.append("+")
        print("pressed")

    def button_clicked2(self):
        listofinputs.append("-")
        print("pressed")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Window = Main_Window()
        self.Window1 = AnotherWindow1()
        self.Window2 = AnotherWindow2()
        self.Window3 = AnotherWindow3()
        self.Window4 = AnotherWindow4()
        self.Window5 = AnotherWindow5()
        self.Window6 = AnotherWindow6()
        self.Window7 = AnotherWindow7()
        self.Window8 = AnotherWindow8()
        self.Window9 = AnotherWindow9()
        self.Window10 = AnotherWindow10()
        self.Window11 = AnotherWindow11()
        self.Window12 = AnotherWindow12()
        l = QVBoxLayout()
        button = QPushButton("Title")
        button.clicked.connect(self.toggle_Window)
        l.addWidget(button)

        button1 = QPushButton("Choose your preferred units")
        button1.clicked.connect(self.toggle_Window5)
        l.addWidget(button1)

        button2 = QPushButton("Add Beam")
        button2.clicked.connect(self.toggle_Window1)
        l.addWidget(button2)

        button3 = QPushButton("Enter the number of supports")
        button3.clicked.connect(self.toggle_Window2)
        l.addWidget(button3)

        button4 = QPushButton("Choose the support types")
        button4.clicked.connect(self.toggle_Window3)
        l.addWidget(button4)

        button5 = QPushButton("Place of supports")
        button5.clicked.connect(self.toggle_Window4)
        l.addWidget(button5)

        button6 = QPushButton("Number of Point Loads")
        button6.clicked.connect(self.toggle_Window6)
        l.addWidget(button6)

        button7 = QPushButton("Add Point Load")
        button7.clicked.connect(self.toggle_Window7)
        l.addWidget(button7)

        button8 = QPushButton("Number of Distributed Loads")
        button8.clicked.connect(self.toggle_Window8)
        l.addWidget(button8)


        button9 = QPushButton("Add Distributed Load")
        button9.clicked.connect(self.toggle_Window9)
        l.addWidget(button9)

        button10 = QPushButton("Number of Moments")
        button10.clicked.connect(self.toggle_Window10)
        l.addWidget(button10)

        button11 = QPushButton("Add Moment")
        button11.clicked.connect(self.toggle_Window11)
        l.addWidget(button11)

        button12 = QPushButton("Section Properties")
        button12.clicked.connect(self.toggle_Window12)
        l.addWidget(button12)

        w = QWidget()
        w.setLayout(l)
        self.setCentralWidget(w)

    def toggle_Window(self, checked):
        if self.Window.isVisible():
            self.Window.hide()

        else:
            self.Window.show()
    def toggle_Window1(self, checked):
        if self.Window1.isVisible():
            self.Window1.hide()

        else:
            self.Window1.show()

    def toggle_Window2(self, checked):
        if self.Window2.isVisible():
            self.Window2.hide()

        else:
            self.Window2.show()

    def toggle_Window3(self, checked):
        if self.Window3.isVisible():
            self.Window3.hide()

        else:
            self.Window3.show()
    def toggle_Window4(self, checked):
        if self.Window4.isVisible():
            self.Window4.hide()

        else:
            self.Window4.show()

    def toggle_Window5(self, checked):
        if self.Window5.isVisible():
            self.Window5.hide()

        else:
            self.Window5.show()

    def toggle_Window6(self, checked):
        if self.Window6.isVisible():
            self.Window6.hide()

        else:
            self.Window6.show()

    def toggle_Window7(self, checked):
        if self.Window7.isVisible():
            self.Window7.hide()

        else:
            self.Window7.show()
    def toggle_Window8(self, checked):
        if self.Window8.isVisible():
            self.Window8.hide()

        else:
            self.Window8.show()

    def toggle_Window9(self, checked):
        if self.Window9.isVisible():
            self.Window9.hide()

        else:
            self.Window9.show()

    def toggle_Window10(self, checked):
        if self.Window10.isVisible():
            self.Window10.hide()

        else:
            self.Window10.show()

    def toggle_Window11(self, checked):
        if self.Window11.isVisible():
            self.Window11.hide()

        else:
            self.Window11.show()

    def toggle_Window12(self, checked):
        if self.Window12.isVisible():
            self.Window12.hide()

        else:
            self.Window12.show()

app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec()

print(listofinputs)
length=listofinputs[0]

## Reaction forces or moment (unknown)
R1, R2 = symbols('R1, R2')
for _ in listofinputs:
    if _=="I":
        m = listofinputs.index("I")
        I=MomentOfInertia(listofinputs[m+3],listofinputs[m+4],listofinputs[m+5],listofinputs[m+6],listofinputs[m+1],listofinputs[m+2])
    if _=="E":
        m=listofinputs.index("E")
        E=listofinputs[m+1]
## elastic modals and second moment are not needed
## b for drawing the beam
b = Beam(length, E*10**9, I)

## diagram for bmd and sfd plots
diagram = Beam(length, E*10**9, I)
diagram2 = Beam(length, E*10**9, I)
## make inputs productive
for _ in listofinputs:
    if _=="pointload":
        ## find the point load string in list
        p = listofinputs.index("pointload")
        if listofinputs[p + 2] == "+":
            b.apply_load(-listofinputs[p + 4], listofinputs[p + 3], -1)
            diagram.apply_load(-listofinputs[p + 4], listofinputs[p + 3], -1)
            diagram2.apply_load(listofinputs[p + 4], listofinputs[p + 3], -1)
        elif listofinputs[p + 2] == "-":
            b.apply_load(+listofinputs[p + 4], listofinputs[p + 3], -1)
            diagram.apply_load(+listofinputs[p + 4], listofinputs[p + 3], -1)
            diagram2.apply_load(-listofinputs[p + 4], listofinputs[p + 3], -1)
        if listofinputs[p + 1] == 2:
            if listofinputs[p + 5] == "+":
                b.apply_load(-listofinputs[p + 7], listofinputs[p + 6], -1)
                diagram.apply_load(-listofinputs[p + 7], listofinputs[p + 6], -1)
                diagram2.apply_load(+listofinputs[p + 7], listofinputs[p + 6], -1)
            if listofinputs[p + 5] == "-":
                b.apply_load(listofinputs[p + 7], listofinputs[p + 6], -1)
                diagram.apply_load(-listofinputs[p + 7], listofinputs[p + 6], -1)
                diagram2.apply_load(-listofinputs[p + 7], listofinputs[p + 6], -1)
    if _=="distload":
        ## find the distributed load string in list
        d=listofinputs.index("distload")
        if listofinputs[d + 2] == "+":
            if listofinputs[d+5]==listofinputs[d+6]:
                b.apply_load(-listofinputs[d+5],listofinputs[d+3],0,listofinputs[d+4])
                diagram.apply_load(-listofinputs[d + 5], listofinputs[d + 3], 0, listofinputs[d + 4])
                diagram2.apply_load(listofinputs[d + 5], listofinputs[d + 3], 0, listofinputs[d + 4])
            else:
                if listofinputs[d+5]==0:
                    b.apply_load(-listofinputs[d+6],listofinputs[d+3],1,listofinputs[d+4])
                    diagram.apply_load(-listofinputs[d + 6], listofinputs[d + 3], 1, listofinputs[d + 4])
                    diagram2.apply_load(listofinputs[d + 6], listofinputs[d + 3], 1, listofinputs[d + 4])
                if listofinputs[d+6]==0:
                    b.apply_load(-listofinputs[d + 5], listofinputs[d + 4], 1, listofinputs[d + 3])
                    diagram.apply_load(listofinputs[d + 5], listofinputs[d + 4], 1, listofinputs[d + 3])
        if listofinputs[d+2]=="-":
            if listofinputs[d+5]==listofinputs[d+6]:
                b.apply_load(listofinputs[d+5],listofinputs[d+3],0,listofinputs[d+4])
                diagram.apply_load(listofinputs[d + 5], listofinputs[d + 3], 0, listofinputs[d + 4])
                diagram2.apply_load(-listofinputs[d + 5], listofinputs[d + 3], 0, listofinputs[d + 4])
            else:
                if listofinputs[d+5]==0:
                    b.apply_load(listofinputs[d+6],listofinputs[d+3],1,listofinputs[d+4])
                    diagram.apply_load(listofinputs[d + 6], listofinputs[d + 3], 1, listofinputs[d + 4])
                    diagram2.apply_load(-listofinputs[d + 6], listofinputs[d + 3], 1, listofinputs[d + 4])
                if listofinputs[d+6]==0:
                    b.apply_load(listofinputs[d + 5], listofinputs[d + 4], 1, listofinputs[d + 3])
                    diagram.apply_load(listofinputs[d + 5], listofinputs[d + 4], 1, listofinputs[d + 3])
                    diagram2.apply_load(-listofinputs[d + 5], listofinputs[d + 4], 1, listofinputs[d + 3])
        if listofinputs[d+1]==2:
            if listofinputs[d + 7] == "+":
                if listofinputs[d+10]==listofinputs[d+11]:
                    b.apply_load(-listofinputs[d+10],listofinputs[d+8],0,listofinputs[d+9])
                    diagram.apply_load(-listofinputs[d + 10], listofinputs[d + 8], 0, listofinputs[d + 9])
                    diagram2.apply_load(listofinputs[d + 10], listofinputs[d + 8], 0, listofinputs[d + 9])

                else:
                    if listofinputs[d+10]==0:
                        b.apply_load(-listofinputs[d+11],listofinputs[d+10],1,listofinputs[d+9])
                        diagram.apply_load(-listofinputs[d + 11], listofinputs[d + 10], 1, listofinputs[d + 9])
                        diagram2.apply_load(listofinputs[d + 11], listofinputs[d + 10], 1, listofinputs[d + 9])
                    if listofinputs[d+11]==0:
                        b.apply_load(-listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])
                        diagram.apply_load(-listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])
                        diagram2.apply_load(listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])
            if listofinputs[d+7]=="-":
                if listofinputs[d+10]==listofinputs[d+11]:
                    b.apply_load(listofinputs[d+10],listofinputs[d+8],0,listofinputs[d+9])
                    diagram.apply_load(listofinputs[d + 10], listofinputs[d + 8], 0, listofinputs[d + 9])
                    diagram2.apply_load(listofinputs[d + 10], listofinputs[d + 8], 0, listofinputs[d + 9])
                else:
                    if listofinputs[d+10]==0:
                        b.apply_load(listofinputs[d+11],listofinputs[d+8],1,listofinputs[d+9])
                        diagram.apply_load(listofinputs[d + 11], listofinputs[d + 8], 1, listofinputs[d + 9])
                        diagram2.apply_load(listofinputs[d + 11], listofinputs[d + 8], 1, listofinputs[d + 9])
                    if listofinputs[d+11]==0:
                        b.apply_load(listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])
                        diagram.apply_load(listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])
                        diagram2.apply_load(listofinputs[d + 10], listofinputs[d + 9], 1, listofinputs[d + 8])

    if _=="moment":
        ## find the moment string in list
        m=listofinputs.index("moment")
        ## - sign for clockwise and + for counter clockwise moment
        if listofinputs[m + 2] == "ccw":
            b.apply_load(listofinputs[m + 4], listofinputs[m + 3], -2)
            diagram.apply_load(listofinputs[m + 4], listofinputs[m + 3], -2)
            diagram2.apply_load(-listofinputs[m + 4], listofinputs[m + 3], -2)
        if listofinputs[m + 2] == "cw":
            b.apply_load(-listofinputs[m + 4], listofinputs[m + 3], -2)
            diagram.apply_load(-listofinputs[m + 4], listofinputs[m + 3], -2)
            diagram2.apply_load(listofinputs[m + 4], listofinputs[m + 3], -2)
        if listofinputs[m + 1] == 2:
            if listofinputs[m + 5] == "ccw":
                b.apply_load(listofinputs[m + 7], listofinputs[m + 6], -2)
                diagram.apply_load(listofinputs[m + 7], listofinputs[m + 6], -2)
                diagram2.apply_load(-listofinputs[m + 7], listofinputs[m + 6], -2)
            if listofinputs[m + 5] == "cw":
                b.apply_load(-listofinputs[m + 7], listofinputs[m + 6], -2)
                diagram.apply_load(-listofinputs[m + 7], listofinputs[m + 6], -2)
                diagram2.apply_load(listofinputs[m + 7], listofinputs[m + 6], -2)

## if 2 supports are added to the beam
if listofinputs[1] == 2:
    sup_1 = listofinputs[2]
    sup_1_place = listofinputs[4]
    sup_2 = listofinputs[3]
    sup_2_place = listofinputs[5]
    b.apply_support(sup_1_place, sup_1)
    b.apply_support(sup_2_place, sup_2)
    b.apply_load(R1, sup_1_place, -1)
    b.apply_load(R2, sup_2_place, -1)
    diagram.apply_load(R1, sup_1_place, -1)
    diagram.apply_load(R2, sup_2_place, -1)
    diagram2.apply_load(R1, sup_1_place, -1)
    diagram2.apply_load(R2, sup_2_place, -1)
    diagram2.bc_deflection=[(sup_1_place,0),(sup_2_place,0)]


## if 1 support is added to the beam
if listofinputs[1]==1:
    sup_1 = listofinputs[2]
    sup_1_place=listofinputs[3]
    b.apply_support(sup_1_place,sup_1)
    b.apply_load(R1,sup_1_place,-2)
    b.apply_load(R2, sup_1_place, -1)
    diagram.apply_load(R1,sup_1_place,-2)
    diagram.apply_load(R2, sup_1_place, -1)
    diagram2.apply_load(R1,sup_1_place,-2)
    diagram2.apply_load(R2, sup_1_place, -1)
    diagram2.bc_deflection=[(sup_1_place,0)]
    diagram2.bc_slope=[(sup_1_place,0)]

#Plot
p=b.draw()
p.show()
diagram.solve_for_reaction_loads(R1, R2)
diagram2.solve_for_reaction_loads(R1, R2)
diagram.plot_bending_moment()
diagram.plot_shear_force()
print(f"\nDeflection formula: {diagram2.deflection()}")
diagram2.plot_deflection()
print(f"Slope formula: {diagram2.slope()}")
diagram2.plot_slope()

#Taking input from the user and calculating deflection and slope at specified point

def SingularityFunction(x, a, n):
    if x < a:
        return 0
    else:
        return (x - a) ** n

x=float(input(f"Please input x in {units[1]}: "))
f = lambda x: eval(str(diagram2.deflection()))
g = lambda x: eval(str(diagram2.slope()))
print(f"Deflection @x={x}{units[1]}:{f(x)}")
print(f"Slope @x={x}{units[1]}:{g(x)}")