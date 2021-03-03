from __future__ import print_function
import sys
import os
from PyQt5 import QtWidgets, QtMultimedia, uic, QtCore, QtChart
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
import pyqtgraph as pg
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice

from PyQt5.uic import loadUiType
import jdatetime
import datetime

from icons import icons_rc

import MySQLdb

#ui,_ = loadUiType('mainwindow2.ui')

class MainApp(QMainWindow,QtWidgets.QDialog):
    
    totalPass = 0
    totalFail = 0
    low_weight = 15
    over_weight = 0
    foreign_object = 25
    low_level = 5


    def __init__(self):
        QMainWindow.__init__(self, parent=None)
        # self.setupUi(self)

        #################################################
        QtWidgets.QDialog.__init__(self)
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "mainwindow2.ui"),self)
        self.player = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.tabWidget.setCurrentIndex(0)
        self.help_tabWidget.setCurrentIndex(0)
        file = os.path.join(os.path.dirname(__file__), "small.mp4")
        self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(file)))
        self.player.setVideoOutput(self.ui.widget)
        self.player.play()

        ################################
        
        self.setLineGraph()
        self.createPieChart()

        self.handleUiChanges()
        self.handleButtons()

        ################################
        


    def handleUiChanges(self):
        #creating a timer object 
        timer = QTimer(self) 
		# adding action to timer 
        timer.timeout.connect(self.dateTime) 
		# update the timer every second 
        timer.start(1000)

        self.tabWidget.tabBar().setVisible(False)
        self.staticsTabWidget.tabBar().setVisible(False)
        self.help_tabWidget.tabBar().setVisible(False)
        self.getUser()

        self.setPassedNumber()
        self.setFailedNumber()

        self.setStatus()

    def handleButtons(self):
        self.homeButton.clicked.connect(self.openHomeTab)
        self.staticsButton.clicked.connect(self.openStaticsTab)
        self.databaseButton.clicked.connect(self.openDataBaseTab)
        self.settingsButton.clicked.connect(self.openSettingsTab)
        self.helpButton.clicked.connect(self.openHelpTab)
        self.dayReport.clicked.connect(self.openDayReport)
        self.backToStatic.clicked.connect(self.backToStaticsTab)
        self.help_error_list.clicked.connect(self.open_helpTab_error_list)
        self.help_color_list.clicked.connect(self.open_helpTab_color_list)
        self.error_list_prev_page.clicked.connect(self.openHelpTab)
        self.error_list_next_page.clicked.connect(self.open_helpTab_color_list)
        self.color_list_prev_page.clicked.connect(self.open_helpTab_error_list)

        ## DB Buttons ##
        # P
        self.add_product.clicked.connect(self.Add_Product)
        self.remover_product.clicked.connect(self.Delete_Product)
        self.edit_product.clicked.connect(self.Edit_Porduct)
        
        # U
        self.add_user.clicked.connect(self.Add_Product)
        self.remove_user.clicked.connect(self.Delete_Product)
        self.edit_user.clicked.connect(self.Edit_Porduct)

        ######################################day Report
        self.searchDate.clicked.connect(self.readFromFile)
    #########################################
    ####################Setting Date and Time#########################
    def dateTime(self):

        dateAndTime = datetime.datetime.now()
        date = jdatetime.date.today() 

        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')

        #self.Date.setText('%s/%s/%s' % (dateAndTime.day , dateAndTime.month, dateAndTime.year))
        self.Date.setText('%s/%s/%s' % (year , month, day))
        self.Time.setText('%s:%s:%s' % (dateAndTime.hour , dateAndTime.minute, dateAndTime.second))

        if (dateAndTime.hour==8  and dateAndTime.minute==27 and dateAndTime.second==5): 
            self.saveToFile()

    ########################################
    ##########################Getting User#############################
    def getUser(self):
        # Until User database is ready-> Must change
        self.User.setText('علی علوی')
    #########################################
    ###################setting pass/fail totals########################
    def setPassedNumber(self):
        # Until Algo is ready-> Must change
        number =str(self.totalPass)
        self.passNumber.setText(number)

    def setFailedNumber(self):
        # Until Algo is ready-> Must change
        number =str(self.totalFail)
        self.failNumber.setText(number)
    ##########################################
    ######################### Opening Tabs ###########################
    def openHomeTab(self):
        self.tabWidget.setCurrentIndex(0)

    def openStaticsTab(self):
        self.tabWidget.setCurrentIndex(1)

    def openDataBaseTab(self):
        self.tabWidget.setCurrentIndex(2)

    def openSettingsTab(self):
        self.tabWidget.setCurrentIndex(3)

    def openHelpTab(self):
        self.tabWidget.setCurrentIndex(4)
        self.help_tabWidget.setCurrentIndex(0)

    def openDayReport(self):
        self.staticsTabWidget.setCurrentIndex(1)

    def backToStaticsTab(self):
        self.staticsTabWidget.setCurrentIndex(0)

    def openSettingsTab(self):
        self.staticsTabWidget.setCurrentIndex(3)

    def open_helpTab_error_list(self):
        self.help_tabWidget.setCurrentIndex(1)
        self.help_error_list_textBrowser.setText("لیست خطاها")

    def open_helpTab_color_list(self):
        self.help_tabWidget.setCurrentIndex(2)
        self.help_color_list_textBrowser.setText("توضیح انواع رنگ ها")

    ####################################
    ############################Setting Sensor Status#######################
    def setStatus(self):
        self.setTempStat()
        self.setHumidStat()
        self.setLightStat()
        self.setPassFailStat()
    
    def setTempStat(self):
        # To be fixed
        status = 1
        if status:
            self.tempStat.setStyleSheet("background-color:rgb(85, 255, 127)")
        else:
            self.tempStat.setStyleSheet("background-color:rgb(255,37,95)")

    def setHumidStat(self):
        # To be fixed
        status = 0
        if status:
            self.humidStat.setStyleSheet("background-color:rgb(85, 255, 127)")
        else:
            self.humidStat.setStyleSheet("background-color:rgb(255,37,95)")

    def setLightStat(self):
        # To be fixed
        status = 1
        if status:
            self.lightStat.setStyleSheet("background-color:rgb(85, 255, 127)")
        else:
            self.lightStat.setStyleSheet("background-color:rgb(255,37,95)")

    def setPassFailStat(self):
        # To be fixed
        errorCode = 'Low weight'
        status = 0
        if status:
            self.passFail.setText('Pass')
            self.passFail.setStyleSheet("background-color:rgb(85, 255, 127)")
        else:
            self.passFail.setText('Fail')
            self.failCode.setText(errorCode)
            self.passFail.setStyleSheet("background-color:rgb(255,37,95)")

    ######################################
    ######################Creating Linear Graphs#####################
    def setLineGraph(self):
        
        hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]

        self.lineGraph(hour, temperature)



    def lineGraph(self, hour, temperature):
        # pass
        #self.graphWidget.setBackground('w') we prefer dark
        self.graphWidget.plot(hour, temperature, pen= pg.mkPen('w', width=3))


    ########################################
    #########################Creating pieChart#######################
    def createPieChart(self):
        series = QPieSeries()
        series.append("Passed", 80)
        series.append("Failed", 10)
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Pie Chart Example")
        self.pieChart = QChartView(chart)
        self.pieChart.setRenderHint(QPainter.Antialiasing)
        self.pieChartLayout.addWidget(self.pieChart)
    #####################################

    def saveToFile(self):
        
        error = {}
        date = {}

        today = jdatetime.date.today()
        year = today.strftime('%Y')
        month = today.strftime('%m')
        day = today.strftime('%d')

        ttoday = "Date "+year + "-" + month + "-" + day
        error = {'totalPass':self.totalPass,'totalFail':self.totalFail,'low weight':self.low_weight, 'over weight':self.over_weight, 'foreign object':self.foreign_object, 'low level':self.low_level}
        date[ttoday] = error


        with open("test2.txt", "a") as f:
            for key, nested in date.items():
                print(key, file=f)
                for subkey, value in nested.items():
                    print('{}: {}'.format(subkey, value), file=f)
                print(file=f)


    ###############Read from file
    def readFromFile(self):
        d = {}
        k = ''
        for line in open('test2.txt'):
            if ':' in line:
                key, value = line.split(':', 1)
                d[k][key] = value.strip()
            else:
                k = line.strip()
                d[k] = {}

        day=self.dayComboBox.currentText()
        month=self.monthComboBox.currentText()
        year=self.yearComboBox.currentText()
        date="Date "+year+"-"+month+"-"+day
        
        k1 = date

        try:
            self.errorMessage.clear()
            #for total pass
            k2 = 'totalPass'
            TP = d[k1][k2]
            self.Pass.setText(TP)

            #for total fail
            k2 = 'totalFail'
            TF = d[k1][k2]
            self.Fail.setText(TF)

            #for low weight
            k2 = 'low weight'
            LW = d[k1][k2]
            self.lowWeight.setText(LW)

            #for over weight
            k2 = 'over weight'
            OV = d[k1][k2]
            self.overWeight.setText(OV)

            #for foreign object
            k2 = 'foreign object'
            FO = d[k1][k2]
            self.foreignObject.setText(FO)

            #for low level
            k2 = 'low level'
            LL = d[k1][k2]
            self.lowLevel.setText(LL)

        except:
            self.errorMessage.setText("اطلاعاتی برای این تاریخ وجود ندارد")
            self.Pass.clear()
            self.Fail.clear()
            self.lowWeight.clear()
            self.overWeight.clear()
            self.foreignObject.clear()
            self.lowLevel.clear()

    #########################################################

    #####################
    ## DB - Connection ##
    #####################

    #product
    def Add_Product(self):
        self.db = MySQLdb.connect(host='localhost', user='ahb', password='4', db='bmn')
        self.cur = self.db.cursor()

        code = self.lineEdit_2.text()
        name = self.lineEdit.text()

        self.cur.execute('''
            INSERT INTO products (product_name, product_code) VALUES (%s,%s);
        ''', (name, code,))
        self.db.commit()
        self.statusBar().showMessage('محصول جدید اضافه شد.')


    def Edit_Porduct(self):
        pass


    def Delete_Product(self):
        pass


    #user
    def Add_User(self):
        self.db = MySQLdb.connect(host='localhost', user='ahb', password='4', db='bmn')
        self.cur = self.db.cursor()
        
        fullname = self.lineEdit_3.text()
        fname = fullname.split(' ')[0];
        lname = fullname.split(' ')[1:].join(' ')
        user_name = self.lineEdit_4.text()
        user_password = self.lineEdit_5.text()

        self.cur.execute('''
            INSERT INTO users (user_name, first_name, last_name, user_password) VALUES (%s,%s,%s,%s);
        ''', (user_name, fname, lname, user_password,))
        self.db.commit()
        self.statusBar().showMessage('کاربر جدید اضافه شد.')


    def Edit_User(self):
        pass


    def Delete_User(self):
        pass       


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()