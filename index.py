# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
from PyQt5 import QtWidgets, QtMultimedia, uic, QtCore, QtChart
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.uic import *
import pyqtgraph as pg
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis
import MySQLdb
from PyQt5.uic import loadUiType
import jdatetime
import datetime
import cv2

# from icons import icons_rc

# ui,_ = loadUiType('mainwindow2.ui')
login, _ = loadUiType('login.ui')
first_name = bytes()
last_name = bytes()
class Login(QWidget, login):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.login_btn.clicked.connect(self.handle_login)

    def handle_login(self):
            global first_name
            global last_name
            username = self.username.text()
            password = self.password.text()
            self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
            self.cur = self.db.cursor()
            self.cur.execute('''SET character_set_results=utf8;''')
            self.cur.execute('''SET character_set_client=utf8;''')
            self.cur.execute('''SET character_set_connection=utf8;''')
            self.cur.execute('''SET character_set_database=utf8;''')
            self.cur.execute('''SET character_set_server=utf8;''')
            sql = ''' SELECT * FROM users '''
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for row in data:
                if username == row[1] and password == row[4]:
                    first_name = row[2]
                    last_name = row[3]
                    self.window2 = MainApp()
                    self.close()
                    self.window2.show()
            self.loginErrorLabel.setText("نام کاربری یا رمز عبور اشتباه است")
            

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
        # self.player = QtMultimedia.QMediaPlayer()

        self.tabWidget.setCurrentIndex(0)
        self.help_tabWidget.setCurrentIndex(0)

        # Conncect to Webcam
        self.available_cameras = QCameraInfo.availableCameras()
        if not self.available_cameras:
            pass #quit

        # Set the default camera.
        self.camera = QCamera(self.available_cameras[0])
        self.camera.setViewfinder(self.ui.widget)
        self.camera.setCaptureMode(QCamera.CaptureStillImage)
        self.camera.error.connect(lambda: self.alert(self.camera.errorString()))
        self.camera.start()

        
        self.getUser()
        ################################
        
        self.setLineGraph()
        self.createPieChart()

        self.handleUiChanges()
        self.handleButtons()

        self.show_users_table_data()
        self.show_products_table_data()
        ################################
    
    def select_camera(self, i):
        self.camera = QCamera(self.available_cameras[i])
        self.camera.setViewfinder(self.viewfinder)
        self.camera.setCaptureMode(QCamera.CaptureStillImage)
        self.camera.error.connect(lambda: self.alert(self.camera.errorString()))
        self.camera.start()

        # self.capture = QCameraImageCapture(self.camera)
        # self.capture.error.connect(lambda i, e, s: self.alert(s))
        # self.capture.imageCaptured.connect(lambda d, i: self.status.showMessage("Image %04d captured" % self.save_seq))

        self.current_camera_name = self.available_cameras[i].description()
        self.save_seq = 0

    def show_users_table_data(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM users '''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        self.users_details_table.setRowCount(0)
        for row_num, row_data in enumerate(data):
            self.users_details_table.insertRow(row_num)
            self.users_details_table.setItem(row_num, 0, QTableWidgetItem(str(row_data[2]) + " " +str(row_data[3])))
            self.users_details_table.setItem(row_num, 1, QTableWidgetItem(str(row_data[5])))
            self.users_details_table.setItem(row_num, 2, QTableWidgetItem(str(row_data[1])))
            self.users_details_table.setItem(row_num, 3, QTableWidgetItem(str(row_data[4])))

        self.db.close()

    def show_products_table_data(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM products '''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        self.products_details_table.setRowCount(0)
        for row_num, row_data in enumerate(data):
            self.products_details_table.insertRow(row_num)
            self.products_details_table.setItem(row_num, 0, QTableWidgetItem(str(row_data[0])))
            self.products_details_table.setItem(row_num, 1, QTableWidgetItem(str(row_data[1])))


        self.db.close()

    
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
        self.db_tabWidget.tabBar().setVisible(False)
        self.settings_tabWidget.tabBar().setVisible(False)
        # self.getUser()

        self.setPassedNumber()
        self.setFailedNumber()
        self.showProductComboBox()
        self.setStatus()

    def handleButtons(self):
        self.homeButton.clicked.connect(self.openHomeTab)
        self.staticsButton.clicked.connect(self.openStaticsTab)
        # Go to Database Page
        self.databaseButton.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_2.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_3.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_4.clicked.connect(self.openDataBaseTab)
        self.settingsButton.clicked.connect(self.openSettingsTab)
        self.helpButton.clicked.connect(self.openHelpTab)
        self.erProductReporrt.clicked.connect(self.openERProductReport)#
        self.erDateReport.clicked.connect(self.openERDateReport)#
        self.backToStatic_1.clicked.connect(self.backToStaticsTab)#
        self.backToStatic_2.clicked.connect(self.backToStaticsTab)#
        self.help_error_list.clicked.connect(self.open_helpTab_error_list)
        self.help_color_list.clicked.connect(self.open_helpTab_color_list)
        self.error_list_prev_page.clicked.connect(self.openHelpTab)
        self.error_list_next_page.clicked.connect(self.open_helpTab_color_list)
        self.color_list_prev_page.clicked.connect(self.open_helpTab_error_list)
        # open add user page
        self.add_user.clicked.connect(self.open_add_user_page)
        # add user 
        self.add_user_2.clicked.connect(self.add_new_user)
        # go to user edit page
        self.edit_user.clicked.connect(self.open_edit_user_page)
        self.remove_user.clicked.connect(self.open_edit_user_page)
        # go to product edit page
        self.edit_product.clicked.connect(self.open_edit_product_page)
        self.remover_product.clicked.connect(self.open_edit_product_page)
        # go to curr user edit page
        self.curr_user_edit_btn.clicked.connect(self.open_curr_edit_user_page)
        # edit current user data
        self.edit_user_btn_2.clicked.connect(self.edit_curr_user_data)
        # edit user data by username
        self.edit_user_btn.clicked.connect(self.edit_user_data)
        # login
        self.login_btn_2.clicked.connect(self.login)
        # search user
        self.search_btn.clicked.connect(self.search_user)
        # delete user
        self.delete_user_btn.clicked.connect(self.delete_user)
        # go to add product page
        self.add_product.clicked.connect(self.open_add_product_page)
        # add new product
        self.add_product_2.clicked.connect(self.add_product_func)
        # search product
        self.search_btn_2.clicked.connect(self.search_product)
        # delete product
        self.delete_product_btn_2.clicked.connect(self.delete_product)
        # edit product
        self.edit_product_btn.clicked.connect(self.edit_product_data)
        # Change product type from settings
        self.confirm_product_type_btn.clicked.connect(self.change_product_type)
        ######################################day Report
        self.searchERDate.clicked.connect(self.retERDate)
        self.searchERProduct.clicked.connect(self.retERProduct)
    #########################################

    def change_product_type(self):
        self.productType.setText(self.productComboBox_2.currentText())
        self.productType_2.setText(self.productComboBox_2.currentText())
        
    def add_product_func(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        product_name = self.product_name.text()
        product_code = self.product_code.text()
        if (product_name != '') or (product_code != ''):
            self.cur.execute('''
                INSERT INTO products(product_name, product_code)
                VALUES (%s, %s)
            ''', (product_name.encode('utf-8'), product_code.encode('utf-8')))
            self.db.commit()
            self.statusBar().showMessage('New Product Added')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')
        self.show_users_table_data()
        self.show_products_table_data()
        self.showProductComboBox()

    def search_product(self):
        product_code = self.lineEdit_3.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM products WHERE product_code=%s'''
        self.cur.execute(sql, [(product_code)])
        data = self.cur.fetchone()
        # print(data)
        self.lineEdit_14.setText(data[0])
        self.lineEdit_15.setText(data[1])

    def delete_product(self):
        product_code = self.lineEdit_3.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        if product_code != '':
            self.cur.execute('''
                DELETE FROM products WHERE product_code = %s
            ''', [product_code])
            self.db.commit()
            self.statusBar().showMessage('Product Deleted')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')

        self.show_users_table_data()
        self.show_products_table_data()
        self.showProductComboBox()

    def edit_product_data(self):
        original_product_code = self.lineEdit_3.text()
        product_name = self.lineEdit_14.text()
        product_code = self.lineEdit_15.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        if (product_name != '') or (product_code != ''):
            self.cur.execute('''
                UPDATE products SET product_name = %s, product_code = %s WHERE product_code = %s
            ''', (product_name.encode('utf-8'), product_code.encode('utf-8'), original_product_code))

            self.db.commit()
            self.statusBar().showMessage('Product Edited')
        else:
            print("Error! --> Fields are empty!")
        self.lineEdit_14.clear()
        self.lineEdit_15.clear()
        self.show_users_table_data()
        self.show_products_table_data()
        self.showProductComboBox()


    def add_new_user(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        username = self.new_user_name.text()
        password = self.new_user_password.text()
        fname = self.new_user_fname.text()
        lname = self.new_user_lname.text()
        post = self.new_user_post.currentText()
        if (username != '') or (password != '') or (fname != '') or (lname != ''):
            self.cur.execute('''
                INSERT INTO users(user_name, first_name, last_name, user_password, user_post)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username.encode('utf-8'), fname.encode('utf-8'), lname.encode('utf-8'), password.encode('utf-8'), post.encode('utf-8')))
            self.db.commit()
            self.statusBar().showMessage('New User Added')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first')
        self.show_users_table_data()
        self.show_products_table_data()
    
    def search_user(self):
        username = self.lineEdit_2.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM users WHERE user_name=%s'''
        self.cur.execute(sql, [(username)])
        data = self.cur.fetchone()
        # print(data)
        self.lineEdit_4.setText(data[1])
        self.lineEdit_5.setText(data[4])
        self.lineEdit_6.setText(data[2])
        self.lineEdit_7.setText(data[3])
        post = data[5]
        if post == 'مدیرخط':
            self.user_post.setCurrentIndex(1)
        elif post == 'کارگر':
            self.user_post.setCurrentIndex(0)
        elif post == 'مدیریت کارخانه':
            self.user_post.setCurrentIndex(2)
        self.db.close()

    def delete_user(self):
        original_user_name = self.lineEdit_2.text()
        username = self.lineEdit_4.text()
        password = self.lineEdit_5.text()
        fname = self.lineEdit_6.text()
        lname = self.lineEdit_7.text()
        post = self.user_post.currentText()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        if (username != '') or (password != '') or (fname != '') or (lname != ''):
            self.cur.execute('''
                DELETE FROM users WHERE user_name = %s
            ''', [original_user_name])
            self.db.commit()
            self.statusBar().showMessage('User Deleted')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')

        self.show_users_table_data()
        self.show_products_table_data()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.lineEdit_6.clear()
        self.lineEdit_7.clear()

    def edit_user_data(self):
        original_user_name = self.lineEdit_2.text()
        username = self.lineEdit_4.text()
        password = self.lineEdit_5.text()
        fname = self.lineEdit_6.text()
        lname = self.lineEdit_7.text()
        post = self.user_post.currentText()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        if (username != '') or (password != '') or (fname != '') or (lname != ''):
            self.cur.execute('''
                UPDATE users SET user_name = %s, first_name = %s, last_name = %s, user_password = %s, user_post = %s WHERE user_name = %s
            ''', (username.encode('utf-8'), fname.encode('utf-8'), lname.encode('utf-8'), password.encode('utf-8'),  post.encode('utf-8'), original_user_name))

            self.db.commit()
            self.statusBar().showMessage('User Edited')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')
        global first_name
        global last_name
        first_name = fname
        last_name = lname
        self.getUser()
        self.show_users_table_data()
        self.show_products_table_data()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.lineEdit_6.clear()
        self.lineEdit_7.clear()
    
    def login(self):
        username = self.lineEdit_9.text()
        password = self.lineEdit_8.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM users '''
        self.cur.execute(sql)
        data = self.cur.fetchall()
        for row in data:
            if username == row[1] and password == row[4]:
                self.groupBox_6.setEnabled(True)
                self.lineEdit_10.setText(row[1])
                self.lineEdit_11.setText(row[4])
                self.lineEdit_12.setText(row[2])
                self.lineEdit_13.setText(row[3])

    def edit_curr_user_data(self):
        original_user_name = self.lineEdit_9.text()
        username = self.lineEdit_10.text()
        password = self.lineEdit_11.text()
        fname = self.lineEdit_12.text()
        lname = self.lineEdit_13.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        self.cur.execute('''
            UPDATE users SET user_name = %s, first_name = %s, last_name = %s, user_password = %s WHERE user_name = %s
        ''', (username.encode('utf-8'), fname.encode('utf-8'), lname.encode('utf-8'), password.encode('utf-8'), original_user_name))

        self.db.commit()
        self.statusBar().showMessage('User Edited')

        self.show_users_table_data()
        self.show_products_table_data()
        global first_name
        global last_name
        first_name = fname
        last_name = lname
        self.getUser()

    def open_add_user_page(self):
         self.db_tabWidget.setCurrentIndex(1)
         self.new_user_fname.clear()
         self.new_user_lname.clear()
         self.new_user_name.clear()
         self.new_user_password.clear()

    def open_add_product_page(self):
         self.db_tabWidget.setCurrentIndex(3)
         self.product_name.clear()
         self.product_code.clear()

    def open_edit_user_page(self):
         self.db_tabWidget.setCurrentIndex(2)
         self.lineEdit_2.clear()
         self.lineEdit_4.clear()
         self.lineEdit_5.clear()
         self.lineEdit_6.clear()
         self.lineEdit_7.clear()

    def open_edit_product_page(self):
         self.db_tabWidget.setCurrentIndex(4)
         self.lineEdit_3.clear()
         self.lineEdit_14.clear()
         self.lineEdit_15.clear()

        
    def open_curr_edit_user_page(self):
         self.settings_tabWidget.setCurrentIndex(1)


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

    ########################################
    ##########################Getting User#############################
    def getUser(self):
        global first_name
        global last_name
        self.User.setText(first_name + " " +last_name)
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
        self.db_tabWidget.setCurrentIndex(0)

    def openSettingsTab(self):
        self.tabWidget.setCurrentIndex(3)
        self.settings_tabWidget.setCurrentIndex(0)

    def openHelpTab(self):
        self.tabWidget.setCurrentIndex(4)
        self.help_tabWidget.setCurrentIndex(0)

    def openERDateReport(self):
        self.staticsTabWidget.setCurrentIndex(1)
    
    def openERProductReport(self):
        self.staticsTabWidget.setCurrentIndex(2)

    def backToStaticsTab(self):
        self.staticsTabWidget.setCurrentIndex(0)

    # def openSettingsTab(self):
    #     self.staticsTabWidget.setCurrentIndex(3)

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
        errorType = 'low weight'
        status = 1
        if status:
            self.passFail.setText('Pass')
            self.passFail.setStyleSheet("background-color:rgb(85, 255, 127)")
        else:
            ##change if possible-> make function
            dateAndTime = datetime.datetime.now()
            date = jdatetime.date.today() 

            year = date.strftime('%Y')
            month = date.strftime('%m')
            day = date.strftime('%d')
            ttoday = day + "/" + month + "/" + year
            ttime = str(dateAndTime.hour) +":"+ str(dateAndTime.minute) +":"+ str(dateAndTime.second)
            self.saveErDb(ttoday, ttime, errorType)
            self.passFail.setText('Fail')
            self.failCode.setText(errorType)
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
        chart.setTitle("Pass/Fail Pie Chart")
        self.pieChart = QChartView(chart)
        self.pieChart.setRenderHint(QPainter.Antialiasing)
        self.pieChartLayout.addWidget(self.pieChart)
    ##########################################33
    ################Save Error to DataBase##########################

    def saveErDb(self, date, time, error):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        product_type = self.productType.text()
        sql = ''' SELECT product_code FROM products WHERE product_name=%s'''
        self.cur.execute(sql, [(product_type.encode(('utf-8')))])
        prod_code = self.cur.fetchone()[0]
        self.cur.execute('''
            INSERT INTO errors(product_type, prod_code, error, error_date, error_time)
            VALUES (%s, %s, %s, %s, %s)
        ''', (product_type.encode('utf-8'), prod_code, error.encode('utf-8'), date.encode('utf-8'), time.encode('utf-8')))
        self.db.commit()

    #########################################################retrive errors ################################

    def retERProduct(self):

        productType=self.productComboBox.currentText()

        #username = self.lineEdit_2.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM errors WHERE product_type=%s'''
        self.cur.execute(sql, [(productType.encode(('utf-8')))])
        data = self.cur.fetchall()
        if not(data) :
            self.errorMessage_2.setText("اطلاعاتی برای این محصول وجود ندارد")
        else:
            self.errorMessage_2.clear()
        self.productERTable.setRowCount(0)
        for row_num, row_data in enumerate(data):
            # print(row_num, "---", row_data)
            self.productERTable.insertRow(row_num)
            # for column_num, data in enumerate(row_data):
            #     print(column_num, "---", data)
            self.productERTable.setItem(row_num, 0, QTableWidgetItem(str(row_data[2])))
            self.productERTable.setItem(row_num, 1, QTableWidgetItem(str(row_data[3])))
            self.productERTable.setItem(row_num, 2, QTableWidgetItem(str(row_data[4])))
            self.productERTable.setItem(row_num, 3, QTableWidgetItem(str(row_data[5])))

        self.db.close()
    ######################## Return errors based on date #############
    def retERDate(self):
        day=self.dayComboBox.currentText()
        month=self.monthComboBox.currentText()
        year=self.yearComboBox.currentText()
        date=day + "/" + month + "/" + year

        try:
            self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
            self.cur = self.db.cursor()
            self.cur.execute('''SET character_set_results=utf8;''')
            self.cur.execute('''SET character_set_client=utf8;''')
            self.cur.execute('''SET character_set_connection=utf8;''')
            self.cur.execute('''SET character_set_database=utf8;''')
            self.cur.execute('''SET character_set_server=utf8;''')
            sql = ''' SELECT * FROM errors WHERE error_date=%s'''
            self.cur.execute(sql, [(date.encode(('utf-8')))])
            data = self.cur.fetchall()
            if not(data) :
                self.errorMessage.setText("اطلاعاتی برای این تاریخ وجود ندارد")
            else:
                self.errorMessage.clear()


            self.dateERTable.setRowCount(0)
            for row_num, row_data in enumerate(data):
                self.dateERTable.insertRow(row_num)
                self.dateERTable.setItem(row_num, 0, QTableWidgetItem(str(row_data[1])))
                self.dateERTable.setItem(row_num, 1, QTableWidgetItem(str(row_data[2])))
                self.dateERTable.setItem(row_num, 2, QTableWidgetItem(str(row_data[3])))
                self.dateERTable.setItem(row_num, 3, QTableWidgetItem(str(row_data[5])))

            self.db.close()
            self.barGraph(date, data)
            
                #self.errorMessage.setText("اطلاعاتی برای این تاریخ وجود ندارد")
        
        except: #change
            pass


           
    ############ Draw Error BarGraph for the date###########
    def barGraph(self, date, data):
        try:##chnage if possible-> make one function
            self.barGraphLayout.itemAt(0).widget().deleteLater()
            self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
            self.cur = self.db.cursor()
            self.cur.execute('''SET character_set_results=utf8;''')
            self.cur.execute('''SET character_set_client=utf8;''')
            self.cur.execute('''SET character_set_connection=utf8;''')
            self.cur.execute('''SET character_set_database=utf8;''')
            self.cur.execute('''SET character_set_server=utf8;''')
            ###get data
            error = "low weight"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            LW = self.cur.fetchone()[0]
            #print(LW)
            #
            error = "high weight"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            HW = self.cur.fetchone()[0]
            #print(HW)
            #
            error = "low level"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            LL = self.cur.fetchone()[0]
            #print(LL)
            #
            error = "high level"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            HL = self.cur.fetchone()[0]
            #print(HL)
            #
            error = "foreign object"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            FO = self.cur.fetchone()[0]
            #print(FO)
            ###draw the graph
            set0 = QBarSet("LW")
            set0 << LW
            set1 = QBarSet("HW")
            set1 << HW
            set2 = QBarSet("LL")
            set2 << LL
            set3 = QBarSet("HL")
            set3 << HL
            set4 = QBarSet("FO")
            set4 << FO

            series = QBarSeries()
            series.append(set0)
            series.append(set1)
            series.append(set2)
            series.append(set3)
            series.append(set4)
    
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("جمع انواع خطاها")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            axisX = QBarCategoryAxis();
            axisX.append("date");
            chart.addAxis(axisX, Qt.AlignBottom);
            series.attachAxis(axisX);

            axisY = QValueAxis();
            axisY.applyNiceNumbers()
            chart.addAxis(axisY,Qt.AlignLeft);
            series.attachAxis(axisY);

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            chartView = QChartView(chart)
            chartView.setRenderHint(QPainter.Antialiasing)
            self.barGraphLayout.addWidget(chartView)
        except:
            self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
            self.cur = self.db.cursor()
            self.cur.execute('''SET character_set_results=utf8;''')
            self.cur.execute('''SET character_set_client=utf8;''')
            self.cur.execute('''SET character_set_connection=utf8;''')
            self.cur.execute('''SET character_set_database=utf8;''')
            self.cur.execute('''SET character_set_server=utf8;''')
            ###get data
            error = "low weight"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            LW = self.cur.fetchone()[0]
            #print(LW)
            #
            error = "high weight"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            HW = self.cur.fetchone()[0]
            #print(HW)
            #
            error = "low level"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            LL = self.cur.fetchone()[0]
            #print(LL)
            #
            error = "high level"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            HL = self.cur.fetchone()[0]
            #print(HL)
            #
            error = "foreign object"
            self.cur.execute(''' SELECT COUNT(iderrors) FROM errors WHERE error_date=%s AND error=%s''', 
            (date.encode(('utf-8')), error.encode(('utf-8'))))
            FO = self.cur.fetchone()[0]
            #print(FO)
            ###draw the graph
            set0 = QBarSet("LW")
            set0 << LW
            set1 = QBarSet("HW")
            set1 << HW
            set2 = QBarSet("LL")
            set2 << LL
            set3 = QBarSet("HL")
            set3 << HL
            set4 = QBarSet("FO")
            set4 << FO

            series = QBarSeries()
            series.append(set0)
            series.append(set1)
            series.append(set2)
            series.append(set3)
            series.append(set4)
    
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("جمع انواع خطاها")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            axisX = QBarCategoryAxis();
            axisX.append("date");
            chart.addAxis(axisX, Qt.AlignBottom);
            series.attachAxis(axisX);

            axisY = QValueAxis();
            axisY.applyNiceNumbers()
            chart.addAxis(axisY,Qt.AlignLeft);
            series.attachAxis(axisY);

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            chartView = QChartView(chart)
            chartView.setRenderHint(QPainter.Antialiasing)
            self.barGraphLayout.addWidget(chartView)

    ####################################
    ######################Adjust ComboBoxes###################
    def showProductComboBox(self):
        self.productComboBox.clear()
        self.productComboBox_2.clear()
        
        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        self.cur.execute(''' SELECT product_name FROM products ''')
        data = self.cur.fetchall()

        for product in data:
            self.productComboBox.addItem(product[0])
            self.productComboBox_2.addItem(product[0])

def main():
    app = QApplication(sys.argv)
    window = Login()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()