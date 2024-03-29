# -*- coding: utf-8 -*-
#..............................PyQt5 libraries.....................................#
from __future__ import print_function
import sys
import os
import cv2
import time
import MySQLdb
import jdatetime
import datetime
import pyqtgraph as pg
from PyQt5.uic import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.uic import loadUiType
from PyQt5.QtPrintSupport import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5 import QtWidgets, QtMultimedia, uic, QtCore, QtChart
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis

#...............................Libraries for algorithms....................................#
import torch
import numpy as np
import FCN_NetModel as FCN             # The net Class
import matplotlib.image as mpimg
import CategoryDictionary as CatDic
from keras.models import load_model
from tensorflow.keras import backend as K

sys.path.append("./Algorithms/level")


#.................................global variables......................................

default_input_dir="C:/Users/Win10/Desktop/BMN-main/FinalVersion/IMG/Inputs" # Folder of input images
default_output_dir="C:/Users/Win10/Desktop/BMN-main/FinalVersion/IMG/Outputs" # Folder of output
level_model_path = "C:/Users/Win10/Desktop/BMN-main/FinalVersion/Algorithms/level/logs/TrainedModelWeiht1m_steps_Semantic_TrainedWithLabPicsAndCOCO_AllSets.torch"
foreign_object_model_path = "C:/Users\Win10/Desktop/BMN-main/FinalVersion/Algorithms/foreign_object/sos/sos_model.h5"
current_product = "" # Product which is on product line
current_alg = ""
selected_model = "none"
totalPass = 0
totalFail = 0
low_weight = 15
over_weight = 0
foreign_object = 25
low_level = 5
row_num_g = 0
change = 1


#.................................Algorithms....................................................

#......................Foreign Object Detection.......................................
def foreign_object_detection_alg(self, img_name):

    state = ""

    def IOU_calc(y_true, y_pred):
        y_true_f = K.flatten(y_true)
        y_pred_f = K.flatten(y_pred)
        intersection = K.sum(y_true_f * y_pred_f)
        return 2*(intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

    def IOU_calc_loss(y_true, y_pred):
        return -IOU_calc(y_true, y_pred)


    model = load_model(foreign_object_model_path, custom_objects={'IOU_calc_loss': IOU_calc_loss, 'IOU_calc': IOU_calc})

    IMAGE_HEIGHT = 512
    IMAGE_WIDTH = 512
    IMAGE_CHANNELS = 1

    path_to_images = default_input_dir + '/foreign_object/sos'
    image_filename = img_name


    ## reading input file
    image = mpimg.imread(os.path.join(path_to_images, image_filename), format='gray')
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    resize=(512, 512)
    if resize:
        image = cv2.resize(image, (resize[0], resize[1]))
    image = np.reshape(image, (1, resize[0], resize[1], IMAGE_CHANNELS))
    #print(image.shape)
    pred = model.predict(image)

    ## Pass/Fail output
    im_pred = np.array(255*pred[0,:,:,0], dtype=np.uint8)
    PF_threshold = 100000 # Fail~1000000  Pass~1000 ==> Pass < PF_threshold < Fail
    if np.sum(im_pred) < 100000:
      #print('Pass :D')
      state = "Pass"
    else:
      #print('Fail D:')
      state = "Fail"



    ## Fail pattern illustration
    img = np.array(image[0,:,:,0], np.uint8)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    rgb_pred = cv2.cvtColor(im_pred, cv2.COLOR_GRAY2RGB)
    rgb_pred[:, :, 0] = 0*rgb_pred[:, :, 0]
    rgb_pred[:, :, 2] = 0*rgb_pred[:, :, 2]
    rgb_pred = cv2.addWeighted(rgb_img, 1, rgb_pred, 0.3, 0)

    ## write result to file
    out_path = default_output_dir + '/foreign_object/sos'
    #cv2.imwrite(out_path + 'out.jpg',cv2.resize(rgb_pred, (400, 400)))
    t = cv2.imread(os.path.join(path_to_images, img_name), cv2.IMREAD_COLOR)
    cv2.imwrite(out_path + '/' + img_name[:-4] + '_original.jpg', cv2.resize(t, (400, 400)))
    cv2.imwrite(out_path + '/' + img_name, cv2.resize(rgb_pred, (400, 400)))
    Img_name2 = img_name

    if state == "Pass":
        #print("ghorbami: ", Img_name2)
        self.level_percentage.setText("")
        self.passFail.setText('Pass')
        self.passFail.setStyleSheet("background-color:rgb(107, 255, 117)")
        self.level_percentage.setStyleSheet("background-color:rgb(107, 255, 117)")

        
        input_IMG_path = out_path + '/' + Img_name2
        output_IMG_path = out_path + '/'  + Img_name2[:-4] + "_original.jpg"

        input_IMG = QPixmap(input_IMG_path)
        output_IMG = QPixmap(output_IMG_path)
        
        self.video_stream1.setPixmap(input_IMG)
        self.video_stream2.setPixmap(output_IMG)

        #........ not apply yet ........
        #totalPass += 1
        #self.setFailedNumber()
    
    else:
        error_percentage = "Foreign Object"
        self.level_percentage.setText("")
        self.passFail.setText('Fail')
        self.passFail.setStyleSheet("background-color:rgb(255,37,95)")
        self.level_percentage.setStyleSheet("background-color:rgb(255,37,95)")
        
        input_IMG_path = out_path + '/' + Img_name2
        output_IMG_path = out_path + '/'  + Img_name2[:-4] + "_original.jpg"
        
        
        input_IMG = QPixmap(input_IMG_path)
        output_IMG = QPixmap(output_IMG_path)
        
        self.video_stream1.setPixmap(input_IMG)
        self.video_stream2.setPixmap(output_IMG)

        #........ not apply yet ........
        #totalFail += 1
        #self.setFailedNumber()
    
#......................Foreign Object Detection.......................................
def level_detection_alg(self,img_name, use_gpu=False):

#--------------------Input parameters-----
    OutName = ""
    OutDir = default_output_dir + "/level/morabba_albalu/"
    UseGPU=use_gpu # Use GPU or CPU  for prediction (GPU faster but demend nvidia GPU and CUDA installed else set UseGPU to False)
    FreezeBatchNormStatistics=False # wether to freeze the batch statics on prediction  setting this true or false might change the prediction mostly False work better
    OutEnding="" # Add This to file name
    if not os.path.exists(OutDir): os.makedirs(OutDir) # Create folder for trained weight

    #-----------------------------------------Location of the pretrain model-----------------------------------------------------------------------------------
    Trained_model_path = level_model_path
    ##################################Load net###########################################################################################
    #---------------------Create and Initiate net and create optimizer------------------------------------------------------------------------------------
    Net=FCN.Net(CatDic.CatNum) # Create net and load pretrained encoder path
    if UseGPU==True:
        print("USING GPU")
        Net.load_state_dict(torch.load(Trained_model_path))
    else:
        print("USING CPU")
        Net.load_state_dict(torch.load(Trained_model_path, map_location=torch.device('cpu')))
    #--------------------------------------------------------------------------------------------------------------------------
    #..................Read and resize image..............................................................................
    InPath=default_input_dir + "/level/morabba_albalu" +"/"+img_name
    Im=cv2.imread(InPath)
    #print("Im: ",Im)
    h,w,d=Im.shape
    r=np.max([h,w])
    if r>840: # Image larger then 840X840 are shrinked (this is not essential, but the net results might degrade when using to large images
        fr=840/r
        Im=cv2.resize(Im,(int(w*fr),int(h*fr)))
    Imgs=np.expand_dims(Im,axis=0)
    #...............................Make Prediction.............................................................................................................
    with torch.autograd.no_grad():
      OutProbDict,OutLbDict=Net.forward(Images=Imgs,TrainMode=False,UseGPU=UseGPU, FreezeBatchNormStatistics=FreezeBatchNormStatistics) # Run net inference and get prediction
    #..............................Save prediction on fil
    print("Saving output to: " + OutDir)
    for nm in OutLbDict:
        
        if(nm!='Filled' and nm!='Vessel'):
            continue
    
        Lb=OutLbDict[nm].data.cpu().numpy()[0].astype(np.uint8)
        if Lb.mean()<0.001: continue
        if nm=='Ignore': continue
        ImOverlay1 = Im.copy()
        ImOverlay1[:, :, 0][Lb==1] = 255
        ImOverlay1[:, :, 1][Lb==1] = 0
        ImOverlay1[:, :, 2][Lb==1] = 255
        FinIm=np.concatenate([Im,ImOverlay1],axis=1)
        OutPath = OutDir + "//" + nm+"/"
        #My Code to Detect the Level Percentage:    
        # vessel_level=0
        # filled_level=0
        if(nm=='Vessel'):
            mask=np.zeros([ImOverlay1.shape[0],ImOverlay1.shape[1]])
            for i in range(ImOverlay1.shape[0]):
              for j in range(ImOverlay1.shape[1]):
                if(ImOverlay1[i,j,0]==255 and ImOverlay1[i,j,1]==0 and ImOverlay1[i,j,2]==255):
                  mask[i,j]=1
            sums=np.sum(mask,axis=0)
            vessel_level=np.mean(sums)
        if(nm=='Filled'):
            mask=np.zeros([ImOverlay1.shape[0],ImOverlay1.shape[1]])
            for i in range(ImOverlay1.shape[0]):
              for j in range(ImOverlay1.shape[1]):
                if(ImOverlay1[i,j,0]==255 and ImOverlay1[i,j,1]==0 and ImOverlay1[i,j,2]==255):
                  mask[i,j]=1
            sums=np.sum(mask,axis=0)
            filled_level=np.mean(sums)
        if not os.path.exists(OutPath): os.makedirs(OutPath)
       
        OutName=OutPath+img_name[:-4]+OutEnding+".jpg"
        OutName2=OutPath+img_name[:-4]+OutEnding+"_original.jpg"
        OutName3=img_name+OutEnding #for DB
        
        # cv2.imwrite(OutName,FinIm)
        new_image = cv2.resize(ImOverlay1, (400, 400))
        new_image2 = cv2.resize(Im, (400, 400))
    
        cv2.imwrite(OutName,new_image)
        cv2.imwrite(OutName2,new_image2)
        
    # cv2.imwrite(OutName,ImOverlay1)
    new_image = cv2.resize(ImOverlay1, (400, 400))
    cv2.imwrite(OutName,new_image)
    
    level=filled_level/vessel_level*100   
    level=round(level,1)

    #.................... before browser for savin in DB.....................
    dateAndTime = datetime.datetime.now()
    date = jdatetime.date.today() 
    year = date.strftime('%Y')
    month = date.strftime('%m')
    day = date.strftime('%d')
    ttoday = day + "/" + month + "/" + year
    ttime = str(dateAndTime.hour) +":"+ str(dateAndTime.minute) +":"+ str(dateAndTime.second)
    #.............................................................................

    if(level)>85: 
        #....before browser.....
        #passed=True
        # file1.writelines(name+': '+str(level)+'%-Pass\n')
        #saveErDb(name, "Pass")
        #....after browser.....
        Img_name2 = OutName3

        self.level_percentage.setText(error_percentage)
        self.level_percentage.setText("100")
        self.passFail.setText('Pass')
        self.passFail.setStyleSheet("background-color:rgb(107, 255, 117)")
        self.level_percentage.setStyleSheet("background-color:rgb(107, 255, 117)")

        
        input_IMG_path = default_output_dir + "/level/morabba_albalu/Filled/" + Img_name2
        output_IMG_path = default_output_dir + "/level/morabba_albalu/Filled/"  + Img_name2[:-4] + "_original.jpg"
        
        input_IMG = QPixmap(input_IMG_path)
        output_IMG = QPixmap(output_IMG_path)
       
        self.video_stream1.setPixmap(input_IMG)
        self.video_stream2.setPixmap(output_IMG)

        #........ not apply yet ........
        #totalPass += 1
        #self.setFailedNumber()
    else:
        #....before browser.....
        #passed=False
        #file1.writelines(name+': '+str(level)+'%-Fail\n')
        #saveErDb(ttoday, ttime, OutName3, level, "Low Level")
        #....after browser.....
        Img_name2 = OutName3

        self.level_percentage.setText(str(level))
        self.passFail.setText('Fail')
        self.passFail.setStyleSheet("background-color:rgb(255,37,95)")
        self.level_percentage.setStyleSheet("background-color:rgb(255,37,95)")
        
        input_IMG_path = default_output_dir + "/level/morabba_albalu/Filled/" + Img_name2
        output_IMG_path = default_output_dir + "/level/morabba_albalu/Filled/"  + Img_name2[:-4] + "_original.jpg"
       
        input_IMG = QPixmap(input_IMG_path)
        output_IMG = QPixmap(output_IMG_path)
        
        self.video_stream1.setPixmap(input_IMG)
        self.video_stream2.setPixmap(output_IMG)

        #........ not apply yet ........
        #totalFail += 1
        #self.setFailedNumber()

#.........................................................................................................

#............................................Login class...................................................

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
            self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

#............................................................................................................


##########################################################################################################
# For the camera feed
# class Thread(QThread):
#     changePixmap = pyqtSignal(QImage)
#     def run(self):
#         cap = cv2.VideoCapture(0)
#         while True:
#             ret, frame = cap.read()
#             if ret:
#                 rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 convertToQtFormat = QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0], QImage.Format_RGB888)
#                 p = convertToQtFormat.scaled(410, 460)
#                 self.changePixmap.emit(p)


# class Thread1(QThread):
#     changePixmap1 = pyqtSignal(QImage)

#     def run(self):
#         cap = cv2.VideoCapture('http://192.168.137.201:8080/video')
#         while True:
#             ret, frame = cap.read()
#             if ret:
#                 rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 convertToQtFormat = QImage(
#                     rgbImage.data, rgbImage.shape[1], rgbImage.shape[0], QImage.Format_RGB888)
#                 p1 = convertToQtFormat.scaled(410, 460)
#                 self.changePixmap1.emit(p1)

###########################################################################################################################
            
#............................................MainApp class...................................................
class MainApp(QMainWindow,QtWidgets.QDialog):

    def __init__(self):

        QMainWindow.__init__(self, parent=None)
        QtWidgets.QDialog.__init__(self)

        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "mainwindow.ui"),self)
        self.player = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        
        self.tabWidget.setCurrentIndex(0)
        self.help_tabWidget.setCurrentIndex(0)
       
        self.handleUiChanges()
        self.handleButtons()
        self.getUser()
        self.setLineGraph()
        self.createPieChart()
        self.show_users_table_data()
        self.show_products_table_data()


    def handleUiChanges(self):
        #creating a timer object 
        timer = QTimer(self) 
		# adding action to timer 
        timer.timeout.connect(self.dateTime) 
		# update the timer every second 
        timer.start(1000)

        #......we don not use statics fail pass for now.....
        #timer2 = QTimer(self) 
		# adding action to timer 
        #timer2.timeout.connect(self.setPassFailStatV2) #row_num_g,totalFail
        #timer2.timeout.connect(self.createPieChart)
		# update the timer every second 
        #timer2.start(5000) 
        #...............................................

        self.tabWidget.tabBar().setVisible(False)
        self.staticsTabWidget.tabBar().setVisible(False)
        self.help_tabWidget.tabBar().setVisible(False)
        self.db_tabWidget.tabBar().setVisible(False)
        self.settings_tabWidget.tabBar().setVisible(False)
        self.setPassedNumber()
        self.showProductComboBox()
        self.setStatus()
        #self.setPassFailStatV2(row_num_g,totalFail)

    def handleButtons(self):
        self.homeButton.clicked.connect(self.openHomeTab)
        self.staticsButton.clicked.connect(self.openStaticsTab)
        # login
        self.login_btn_2.clicked.connect(self.login)
        # Go to Database Page
        self.databaseButton.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_2.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_3.clicked.connect(self.openDataBaseTab)
        self.prev_page_btn_4.clicked.connect(self.openDataBaseTab)
        self.settingsButton.clicked.connect(self.openSettingsTab)
        self.prev_page_btn_5.clicked.connect(self.openSettingsTab)
        self.helpButton.clicked.connect(self.openHelpTab)
        self.erProductReporrt.clicked.connect(self.openERProductReport)
        self.erDateReport.clicked.connect(self.openERDateReport)
        self.backToStatic_1.clicked.connect(self.backToStaticsTab)
        self.backToStatic_2.clicked.connect(self.backToStaticsTab)
        self.help_error_list.clicked.connect(self.open_helpTab_error_list)
        self.help_color_list.clicked.connect(self.open_helpTab_color_list)
        self.error_list_prev_page.clicked.connect(self.openHelpTab)
        self.error_list_next_page.clicked.connect(self.open_helpTab_color_list)
        self.color_list_prev_page.clicked.connect(self.open_helpTab_error_list)
        # open add user page
        self.add_user.clicked.connect(self.open_add_user_page)
        # go to user edit page
        self.edit_user.clicked.connect(self.open_edit_user_page)
        self.remove_user.clicked.connect(self.open_edit_user_page)
        # go to product edit page
        self.edit_product.clicked.connect(self.open_edit_product_page)
        self.remover_product.clicked.connect(self.open_edit_product_page)
        # go to curr user edit page
        self.curr_user_edit_btn.clicked.connect(self.open_curr_edit_user_page)
        # go to add product page
        self.add_product.clicked.connect(self.open_add_product_page)
        # add user 
        self.add_user_2.clicked.connect(self.add_new_user)
        # edit current user data
        self.edit_user_btn_2.clicked.connect(self.edit_curr_user_data)
        # edit user data by username
        self.edit_user_btn.clicked.connect(self.edit_user_data)
        # search user
        self.search_btn.clicked.connect(self.search_user)
        # delete user
        self.delete_user_btn.clicked.connect(self.delete_user)
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
        #ay Report
        self.searchERDate.clicked.connect(self.retERDate)
        self.searchERProduct.clicked.connect(self.retERProduct)
        #browswr
        self.browseButton.clicked.connect(self.OpenFolder)
        #close the app
        self.pushButton_5.clicked.connect(self.close_app)


    ################################ For the camera feed

    # @pyqtSlot(QImage)
    # def setImage(self, image):
    #     self.video_stream1.setPixmap(QPixmap.fromImage(image))

    # @pyqtSlot(QImage)
    # def setImage1(self, image):
    #     self.video_stream2.setPixmap(QPixmap.fromImage(image))

    # def initUI(self):
    #     th = Thread(self)
    #     th1 = Thread1(self)
    #     th1.changePixmap1.connect(self.setImage1)
    #     th.changePixmap.connect(self.setImage)
    #     th.start()
    #     th1.start()


 #######################################

    #..............................Getting User....................
    def getUser(self):
        global first_name
        global last_name
        self.User.setText(first_name + " " +last_name)


    #..........................Creating Linear Graph.................
    def setLineGraph(self):
        
        hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]

        self.lineGraph(hour, temperature)

    def lineGraph(self, hour, temperature):
        # pass
        #self.graphWidget.setBackground('w') we prefer dark
        self.graphWidget.plot(hour, temperature, pen= pg.mkPen('w', width=3))



    #...................................Creating pieChart..........................
    def createPieChart(self):

        global totalPass
        global totalFail
        #print(totalPass)
        #print(totalFail)
        series = QPieSeries()
        series.append("Passed", 80)
        series.append("Failed", 20)
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Pass/Fail Pie Chart")
        self.pieChart = QChartView(chart)
        self.pieChart.setRenderHint(QPainter.Antialiasing)
        self.pieChartLayout.addWidget(self.pieChart)

    def barGraph(self, date, data):
        try:##chnage if possible-> make one function
            self.barGraphLayout.itemAt(0).widget().deleteLater()
            self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

            axisX = QBarCategoryAxis()
            axisX.append("date")
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)

            axisY = QValueAxis()
            axisY.applyNiceNumbers()
            chart.addAxis(axisY,Qt.AlignLeft)
            series.attachAxis(axisY)

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            chartView = QChartView(chart)
            chartView.setRenderHint(QPainter.Antialiasing)
            self.barGraphLayout.addWidget(chartView)
        except:
            self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

            axisX = QBarCategoryAxis()
            axisX.append("date")
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)

            axisY = QValueAxis()
            axisY.applyNiceNumbers()
            chart.addAxis(axisY,Qt.AlignLeft)
            series.attachAxis(axisY)

            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)

            chartView = QChartView(chart)
            chartView.setRenderHint(QPainter.Antialiasing)
            self.barGraphLayout.addWidget(chartView)
    

    #...................................Show Users Table Data..........................
    def show_users_table_data(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

    #...................................Show Products Table Data..........................
    def show_products_table_data(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

  
    #..................................Setting Date and Time............................
    def dateTime(self):

        dateAndTime = datetime.datetime.now()
        date = jdatetime.date.today() 

        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')

        #self.Date.setText('%s/%s/%s' % (dateAndTime.day , dateAndTime.month, dateAndTime.year))
        self.Date.setText('%s/%s/%s' % (year , month, day))
        self.Time.setText('%s:%s:%s' % (dateAndTime.hour , dateAndTime.minute, dateAndTime.second))
    

    #..................................Setting pass/fail totals...........................
    def setPassedNumber(self):
        # Until Algo is ready-> Must change
        number =str(totalPass)
        self.passNumber.setText(number)

    def setFailedNumber(self):
        # Until Algo is ready-> Must change
        number =str(totalFail)
        self.failNumber.setText(number)

    
    #..................................Adjust ComboBoxes................................
    def showProductComboBox(self):
        self.productComboBox.clear()
        self.productComboBox_2.clear()
        
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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


    #.................................Setting Sensor Status..............................
    def setStatus(self):
        self.setTempStat()
        self.setHumidStat()
        self.setLightStat()
        #self.setPassFailStat()
        #self.setPassFailStatV2()

    def setPassFailStatV2(self):#,row_num_g,totalFail
        global OutputDir
        global row_num_g
        global totalFail
        global current_product
        global current_alg

        productType = current_product

        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM errors WHERE product_type=%s'''
        #sql2 = ''' SELECT MAX(iderrors) FROM errors WHERE product_type=%s'''
        self.cur.execute(sql, [(productType.encode(('utf-8')))])
        data = self.cur.fetchall()
        #self.cur.execute(sql2, [(productType.encode(('utf-8')))])
        #max_id = self.cur.fetchone()
        
        #for row_num, row_data in enumerate(data):

            #totalFail += 1 #it should be change for all
        # print(len(data))
        # print(row_num_g)
        if row_num_g < len(data) :
            row_data=data[row_num_g]
            row_num_g += 1
            error_percentage = str(row_data[6])
            Img_name = str(row_data[7])
            #print("\nrow_num."+error_percentage)
            self.level_percentage.setText(error_percentage)
            self.passFail.setText('Fail')
            self.passFail.setStyleSheet("background-color:rgb(255,37,95)")
            self.level_percentage.setStyleSheet("background-color:rgb(255,37,95)")
            if current_alg == "تشخیص سطح": 
                input_IMG_path = OutputDir + "/Filled/" + Img_name
                output_IMG_path = OutputDir + "/Filled/" + Img_name[:-4] + "_original.jpg"
            else:
                input_IMG_path = OutputDir + "/" + Img_name
                output_IMG_path = OutputDir + "/" + Img_name[:-4] + "_original.jpg"
            ##############################
            input_IMG = QPixmap(input_IMG_path)
            output_IMG = QPixmap(output_IMG_path)
            
            self.video_stream1.setPixmap(input_IMG)
            self.video_stream2.setPixmap(output_IMG)

            totalFail += 1
            self.setFailedNumber()

        else :
            row_num_g = 0 
            print("All images have been shown")
    
        #time.sleep(3)
            

        self.db.close()

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

    #we are not using this for now !!!!!!!!!!!!! ==> go to V2
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
    #.................................Login..............................
    def login(self):
        username = self.lineEdit_9.text()
        password = self.lineEdit_8.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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

    
        self.db.commit()
        self.statusBar().showMessage('User Edited')

        self.show_users_table_data()
        self.show_products_table_data()
        global first_name
        global last_name
        first_name = fname
        last_name = lname
        self.getUser()
    #................................. Opening Tabs ...........................................
    def openHomeTab(self):
        self.tabWidget.setCurrentIndex(0)

    def openStaticsTab(self):
        self.tabWidget.setCurrentIndex(1)
        self.staticsTabWidget.setCurrentIndex(0)

    def openDataBaseTab(self):
        self.tabWidget.setCurrentIndex(2)
        self.db_tabWidget.setCurrentIndex(0)

    def openSettingsTab(self):
        self.errorMessage_3.clear()
        self.errorMessage_4.clear()
        self.errorMessage_5.clear()
        self.tabWidget.setCurrentIndex(3)
        self.settings_tabWidget.setCurrentIndex(0)

    def openHelpTab(self):
        self.tabWidget.setCurrentIndex(4)
        self.help_tabWidget.setCurrentIndex(0)

    def openERDateReport(self):

        #clear table before show 
        self.dateERTable.setRowCount(0)

        #clear graph before show 
        for i in reversed(range(self.barGraphLayout.count())): 
            self.barGraphLayout.itemAt(i).widget().setParent(None)

        self.staticsTabWidget.setCurrentIndex(1)
    
    def openERProductReport(self):
        
        #clear table before show 
        self.productERTable.setRowCount(0)

        self.staticsTabWidget.setCurrentIndex(2)

    def backToStaticsTab(self):
        self.staticsTabWidget.setCurrentIndex(0)

    def open_helpTab_error_list(self):
        self.help_tabWidget.setCurrentIndex(1)
        self.help_error_list_textBrowser.setText("لیست خطاها")

    def open_helpTab_color_list(self):
        self.help_tabWidget.setCurrentIndex(2)
        self.help_color_list_textBrowser.setText("توضیح انواع رنگ ها")


    def open_add_user_page(self):
         self.db_tabWidget.setCurrentIndex(1)
         self.new_user_fname.clear()
         self.new_user_lname.clear()
         self.new_user_name.clear()
         self.new_user_password.clear()
         self.errorMessage_9.clear()

    def open_add_product_page(self):
         self.db_tabWidget.setCurrentIndex(3)
         self.product_name.clear()
         self.product_code.clear()
         self.errorMessage_6.clear()

    def open_edit_user_page(self):
         self.db_tabWidget.setCurrentIndex(2)
         self.lineEdit_2.clear()
         self.lineEdit_4.clear()
         self.lineEdit_5.clear()
         self.lineEdit_6.clear()
         self.lineEdit_7.clear()
         self.errorMessage_8.clear()
         self.errorMessage_10.clear()

    def open_edit_product_page(self):
         self.db_tabWidget.setCurrentIndex(4)
         self.lineEdit_3.clear()
         self.lineEdit_14.clear()
         self.lineEdit_15.clear()
         self.errorMessage_7.clear()
         self.errorMessage_12.clear()

        
    def open_curr_edit_user_page(self):
         self.settings_tabWidget.setCurrentIndex(1)

    #..........................................................................................

    #.....................................User.......................................
    def add_new_user(self):
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('New User Added')
            self.errorMessage_9.setText('کاربر جدید با موفقیت اضافه شد')
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first')
        self.show_users_table_data()
        self.show_products_table_data()

    def edit_curr_user_data(self):
        original_user_name = self.lineEdit_9.text()
        username = self.lineEdit_10.text()
        password = self.lineEdit_11.text()
        fname = self.lineEdit_12.text()
        lname = self.lineEdit_13.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        self.cur.execute('''
            UPDATE users SET user_name = %s, first_name = %s, last_name = %s, user_password = %s WHERE user_name = %s
        ''', (username.encode('utf-8'), fname.encode('utf-8'), lname.encode('utf-8'), password.encode('utf-8'), original_user_name))

    def edit_user_data(self):
        original_user_name = self.lineEdit_2.text()
        username = self.lineEdit_4.text()
        password = self.lineEdit_5.text()
        fname = self.lineEdit_6.text()
        lname = self.lineEdit_7.text()
        post = self.user_post.currentText()
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('User Edited')
            self.errorMessage_8.setText("کاربر منتخب با موفقیت ویرایش شد")
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

    def search_user(self):
        username = self.lineEdit_2.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM users WHERE user_name=%s'''
        self.cur.execute(sql, [(username)])
        data = self.cur.fetchone()
        data2= str(data)
        
        if data2 == "None":
            #print("\n\n***********\n\n")
            self.errorMessage_10.setText("کاربر مورد نظر یافت نشد")
            
        else:
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
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('User Deleted')
            self.errorMessage_8.setText("کاربر منتخب حذف شد")
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')

        self.show_users_table_data()
        self.show_products_table_data()
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.lineEdit_6.clear()
        self.lineEdit_7.clear()

    #.......................................................................................

    #.....................................Product.......................................
    def add_product_func(self):

        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('New Product Added')
            self.errorMessage_6.setText("محصول جدید با موفقیت اضافه شد")
            self.db.close()
        else:
            print('ERROR. --> Fill out the form first!')
        self.show_users_table_data()
        self.show_products_table_data()
        self.showProductComboBox()

    def search_product(self):
        product_code = self.lineEdit_3.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
        self.cur = self.db.cursor()
        self.cur.execute('''SET character_set_results=utf8;''')
        self.cur.execute('''SET character_set_client=utf8;''')
        self.cur.execute('''SET character_set_connection=utf8;''')
        self.cur.execute('''SET character_set_database=utf8;''')
        self.cur.execute('''SET character_set_server=utf8;''')
        sql = ''' SELECT * FROM products WHERE product_code=%s'''
        self.cur.execute(sql, [(product_code)])
        data = self.cur.fetchone()
        data2 = str(data)
        
        if data2 == "None":
            #print("\n\n***********\n\n")
            self.errorMessage_12.setText("محصول مورد نظر یافت نشد")
        else:
            self.lineEdit_14.setText(str(data[0]))
            self.lineEdit_15.setText(str(data[1]))

    def delete_product(self):
        product_code = self.lineEdit_3.text()
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('Product Deleted')
            self.errorMessage_7.setText("محصول منتخب حذف شد")
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
        self.db = MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            #self.statusBar().showMessage('Product Edited')
            self.errorMessage_7.setText("محصول منتخب با موفقیت ویرایش شد")
        else:
            print("Error! --> Fields are empty!")
        self.lineEdit_14.clear()
        self.lineEdit_15.clear()
        self.show_users_table_data()
        self.show_products_table_data()
        self.showProductComboBox()

    def change_product_type(self):

        self.errorMessage_3.clear()
        self.errorMessage_4.clear()
        self.errorMessage_5.clear()

        self.errorMessage_3.setText("محصول و الگوریتم مورد نظر انتخاب شد")
        global level_model_path
        global foreign_object_model_path
        global current_product
        global current_alg
        global selected_model
        current_product = self.productComboBox_2.currentText()
        current_alg = self.algorithmComboBox.currentText()
        self.productType.setText(current_product)
        self.productType_2.setText(current_product)
        #print('Product : ' + current_product)
        #print('Algorithm : ' + current_alg)
        
        if current_product == "مربا آلبالو":
            if current_alg == "تشخیص سطح":
                product = 'morabba_albalu'
                alg = 'level'
            else:
                self.errorMessage_5.setText("برای محصول منتخب فقط تشخیص سطح ممکن است")
                self.errorMessage_3.clear()

        elif current_product == "سس مایونز":
            if current_alg == "تشخیص جسم خارجی":
                product = 'sos'
                alg = 'foreign_object'
            else:
                self.errorMessage_5.setText("برای محصول منتخب فقط تشخیص جسم خارجی ممکن است")
                self.errorMessage_3.clear()
        else:
            self.errorMessage_4.setText("اطلاعات محصول مورد نظر در پایگاه داده ثبت نشده است. لطفا محصول دیگری را انتخاب کنید")
            self.errorMessage_3.clear()
                
        
        

        #............changed because of browser......................
        #if alg == "level":
            #print('Running Level Detection Algorithm: ...')
            #level_detection_alg(input_dir=InputDir, output_dir=OutputDir, model_path=level_model_path)
        #elif alg == "foreign_object":
            #print('Running Foreign Object Detection Algorithm: ... ')
            #foreign_object_detection_alg(input_dir=InputDir, output_dir=OutputDir, model_path=foreign_object_model_path)
        #.....................................................................
        if alg == "level":
            #print('Running Level Detection Algorithm: ...')
            selected_model = "level"
        elif alg == "foreign_object":
            #print('Running Foreign Object Detection Algorithm: ... ')
            selected_model = "foreign_object"

    #.......................................................................................

    #................................. Return errors based on date ........................
    def retERDate(self):
        fail_num = 0
        #pass_num = 0
        day=self.dayComboBox.currentText()
        month=self.monthComboBox.currentText()
        year=self.yearComboBox.currentText()
        date=day + "/" + month + "/" + year

        try:
            self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
                fail_num += 1
                self.dateERTable.insertRow(row_num)
                self.dateERTable.setItem(row_num, 0, QTableWidgetItem(str(row_data[1])))
                self.dateERTable.setItem(row_num, 1, QTableWidgetItem(str(row_data[2])))
                self.dateERTable.setItem(row_num, 2, QTableWidgetItem(str(row_data[3])))
                self.dateERTable.setItem(row_num, 3, QTableWidgetItem(str(row_data[5])))
                self.dateERTable.setItem(row_num, 4, QTableWidgetItem(str(row_data[6])))

            self.db.close()
            self.barGraph(date, data)

            self.Fail.setText(str(fail_num))
            
                #self.errorMessage.setText("اطلاعاتی برای این تاریخ وجود ندارد")
        
        except: #change
            pass

    #.................................Retrive errors ...................................
    def retERProduct(self):

        productType=self.productComboBox.currentText()

        #username = self.lineEdit_2.text()
        self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
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
            self.productERTable.setItem(row_num, 4, QTableWidgetItem(str(row_data[6])))

        self.db.close()
    

    #....................................browser.......................................
    def OpenFolder(self):

        if selected_model == "none":
            self.browserError.setText("ERROR")
        elif selected_model == "level":
            self.browserError.clear()
            file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', r"C:\\Users\\Win10\\Desktop\\BMN-main\\FinalVersion\\IMG\\Inputs\\level\\morabba_albalu\\", "Image files (*.jpg *.jpeg *.gif)")
            name = os.path.split(file_name)
            #print("name:",name[1])
            level_detection_alg(self,img_name=name[1])
        elif selected_model == "foreign_object":
            self.browserError.clear()
            file_name, _ = QFileDialog.getOpenFileName(self, 'Open Image File', r"C:\\Users\\Win10\\Desktop\\BMN-main\\FinalVersion\\IMG\\Inputs\\foreign_object\\sos", "Image files (*.jpg *.jpeg *.gif)")
            name = os.path.split(file_name)
            #print("name:",name[1])
            foreign_object_detection_alg(self,img_name=name[1])
    
    #..................................Wo Do Not Use for Now ..............................
    #.........................................Save Error to DataBas....................................
    # def saveErDb(self, date, time, error):
    #     self.db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
    #     self.cur = self.db.cursor()
    #     self.cur.execute('''SET character_set_results=utf8;''')
    #     self.cur.execute('''SET character_set_client=utf8;''')
    #     self.cur.execute('''SET character_set_connection=utf8;''')
    #     self.cur.execute('''SET character_set_database=utf8;''')
    #     self.cur.execute('''SET character_set_server=utf8;''')
    #     product_type = self.productType.text()
    #     sql = ''' SELECT product_code FROM products WHERE product_name=%s'''
    #     self.cur.execute(sql, [(product_type.encode(('utf-8')))])
    #     prod_code = self.cur.fetchone()[0]
    #     self.cur.execute('''
    #         INSERT INTO errors(product_type, prod_code, error, error_date, error_time)
    #         VALUES (%s, %s, %s, %s, %s)
    #     ''', (product_type.encode('utf-8'), prod_code, error.encode('utf-8'), date.encode('utf-8'), time.encode('utf-8')))
    #     self.db.commit()

    
    #.............................browserError..............................................
    def saveErDb(date, time, img, level, error):
        global current_product
        db =  MySQLdb.connect(host='localhost', user='root', password='mobina5158778489', db='bonyad')
        cur = db.cursor()
        cur.execute('''SET character_set_results=utf8;''')
        cur.execute('''SET character_set_client=utf8;''')
        cur.execute('''SET character_set_connection=utf8;''')
        cur.execute('''SET character_set_database=utf8;''')
        cur.execute('''SET character_set_server=utf8;''')
        #product_type = self.productType.text()
        product_type = current_product
        sql = ''' SELECT product_code FROM products WHERE product_name=%s'''
        cur.execute(sql, [(product_type.encode(('utf-8')))])
        prod_code = cur.fetchone()[0]
        cur.execute('''
            INSERT INTO errors(product_type, prod_code, error, error_date, error_time, error_percentage, error_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (product_type.encode('utf-8'), prod_code, error.encode('utf-8'), date.encode('utf-8'), time.encode('utf-8'), level, img.encode('utf-8')))
        db.commit() 

    #.......................... Close Application..........................
    def close_app(self):
        quit()


def main():
    app = QApplication(sys.argv)
    window = Login()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()