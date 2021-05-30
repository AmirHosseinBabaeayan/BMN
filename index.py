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
import time

import matplotlib.image as mpimg
from tensorflow.keras import backend as K
from keras.models import load_model

sys.path.append("./Algorithms/level")
# import RunPredictionOnFolder
# ------------------------------------------------------------------------------New Chnages made by me! -----------------------------------------------
import torch
import numpy as np
import FCN_NetModel as FCN # The net Class
import CategoryDictionary as CatDic

#....................global variables....................

default_input_dir="C:/Users/Amirhossein/Desktop/BMN/BMN2/IMG/Inputs" # Folder of input images
default_output_dir="C:/Users/Amirhossein/Desktop/BMN/BMN2/IMG/Outputs" # Folder of output
level_model_path = "C:/Users/Amirhossein/Desktop/BMN/BMN2/Algorithms/level/logs/TrainedModelWeiht1m_steps_Semantic_TrainedWithLabPicsAndCOCO_AllSets.torch"
foreign_object_model_path = "C:/Users/Amirhossein/Desktop/BMN/BMN2/Algorithms/foreign_object/sos/sos_model.h5"
InputDir = ""
OutputDir = ""
current_product = "" # Product which is on product line
current_alg = ""

totalPass = 0
totalFail = 0
low_weight = 15
over_weight = 0
foreign_object = 25
low_level = 5

row_num_g = 0
change = 1
#import scipy.misc as misc
#from google.colab.patches import cv2_imshow

def saveErDb(date, time, img, level, error):
    global current_product
    db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
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


def foreign_object_detection_alg(input_dir, output_dir, model_path):

    def IOU_calc(y_true, y_pred):
        y_true_f = K.flatten(y_true)
        y_pred_f = K.flatten(y_pred)
        intersection = K.sum(y_true_f * y_pred_f)
        return 2*(intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

    def IOU_calc_loss(y_true, y_pred):
        return -IOU_calc(y_true, y_pred)

    model = load_model(model_path, custom_objects={'IOU_calc_loss': IOU_calc_loss, 'IOU_calc': IOU_calc})

    IMAGE_HEIGHT = 512
    IMAGE_WIDTH = 512
    IMAGE_CHANNELS = 1

    def load_images(path_to_images, img_format, resize):
        image_names = [x for x in os.listdir(path_to_images)]
        image_num = len(image_names)
        images_all = np.empty([image_num, resize[0], resize[1], IMAGE_CHANNELS])


        for image_index in range(image_num):
            image_filename = image_names[image_index]

            # print(image_filename)
            image = mpimg.imread(os.path.join(path_to_images, image_filename), format=img_format)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            if resize:
                image = cv2.resize(image, (resize[0], resize[1]))


            images_all[image_index] = np.reshape(image, (resize[0], resize[1], IMAGE_CHANNELS))

        return images_all
    
    imgs_names = [name for name in os.listdir(input_dir)]
    X = load_images(input_dir, img_format='gray', resize=(512, 512))
    pred = model.predict(X)
    
    ## Pass/Fail output
    for i, name in enumerate(imgs_names):
        # test_num = 0
        dateAndTime = datetime.datetime.now()
        date = jdatetime.date.today() 
        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')
        ttoday = day + "/" + month + "/" + year
        ttime = str(dateAndTime.hour) +":"+ str(dateAndTime.minute) +":"+ str(dateAndTime.second)

        im_pred = np.array(255*pred[i,:,:,0], dtype=np.uint8)
        PF_threshold = 100000 # Fail~1000000  Pass~1000 ==> Pass < PF_threshold < Fail
        if np.sum(im_pred) < PF_threshold:
            print('Pass :D')
        else:
            print('Fail D:')
            saveErDb(ttoday, ttime, name, 0.0, "Foreign Object")



        ## Fail pattern illustration
        img = np.array(X[i,:,:,0], np.uint8)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        rgb_pred = cv2.cvtColor(im_pred, cv2.COLOR_GRAY2RGB)
        rgb_pred[:, :, 0] = 0*rgb_pred[:, :, 0]
        rgb_pred[:, :, 2] = 0*rgb_pred[:, :, 2]
        rgb_pred = cv2.addWeighted(rgb_img, 1, rgb_pred, 0.3, 0)

        ## write result to file
        # out_path = 'result/'
        t = cv2.imread(os.path.join(input_dir, name), cv2.IMREAD_COLOR)
        cv2.imwrite(output_dir + '/' + name[:-4] + '_original.jpg', cv2.resize(t, (400, 400)))
        cv2.imwrite(output_dir + '/' + name, cv2.resize(rgb_pred, (400, 400)))

    
def level_detection_alg(input_dir, output_dir, model_path, use_gpu=False):
#-------------------------------------Input parameters-----------------------------------------------------------------------
    InputDir = input_dir # Folder of input images
    OutDir = output_dir # Folder of output
   
    OutName = ""
    UseGPU=use_gpu # Use GPU or CPU  for prediction (GPU faster but demend nvidia GPU and CUDA installed else set UseGPU to False)
    FreezeBatchNormStatistics=False # wether to freeze the batch statics on prediction  setting this true or false might change the prediction mostly False work better
    OutEnding="" # Add This to file name
    if not os.path.exists(OutDir): os.makedirs(OutDir) # Create folder for trained weight

    #-----------------------------------------Location of the pretrain model-----------------------------------------------------------------------------------
    Trained_model_path = model_path
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
    # Net.half()
    #file1 = open(OutDir+"/Level Percentages.txt","w")

    for name in os.listdir(InputDir): # Main read and predict results for all files
    #..................Read and resize image...............................................................................
        print(name)
        InPath=InputDir+"/"+name
        Im=cv2.imread(InPath)
        h,w,d=Im.shape
        r=np.max([h,w])
        if r>840: # Image larger then 840X840 are shrinked (this is not essential, but the net results might degrade when using to large images
            fr=840/r
            Im=cv2.resize(Im,(int(w*fr),int(h*fr)))
        Imgs=np.expand_dims(Im,axis=0)
        if not (type(Im) is np.ndarray): continue
    #................................Make Prediction.............................................................................................................
        with torch.autograd.no_grad():
              OutProbDict,OutLbDict=Net.forward(Images=Imgs,TrainMode=False,UseGPU=UseGPU, FreezeBatchNormStatistics=FreezeBatchNormStatistics) # Run net inference and get prediction
    #...............................Save prediction on fil
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
           
            OutName=OutPath+name[:-4]+OutEnding+".jpg"
            OutName2=OutPath+name[:-4]+OutEnding+"_original.jpg"
            OutName3=name+OutEnding #for DB
            
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
        ########
        dateAndTime = datetime.datetime.now()
        date = jdatetime.date.today() 
        year = date.strftime('%Y')
        month = date.strftime('%m')
        day = date.strftime('%d')
        ttoday = day + "/" + month + "/" + year
        ttime = str(dateAndTime.hour) +":"+ str(dateAndTime.minute) +":"+ str(dateAndTime.second)
        ########

        if(level)>85:
            passed=True
            # file1.writelines(name+': '+str(level)+'%-Pass\n')
            #saveErDb(name, "Pass")
        else:
            passed=False
            #file1.writelines(name+': '+str(level)+'%-Fail\n')
            saveErDb(ttoday, ttime, OutName3, level, "Low Level")

#.......................................................
# level_detection_alg(input_dir=InputDir, output_dir=OutputDir, model_path=model_path, use_gpu=True)
#......................................................
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
            

class MainApp(QMainWindow,QtWidgets.QDialog):
    
    


    def __init__(self):
        QMainWindow.__init__(self, parent=None)

        #################################################
        QtWidgets.QDialog.__init__(self)
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "mainwindow.ui"),self)
        self.player = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)

        self.tabWidget.setCurrentIndex(0)
        self.help_tabWidget.setCurrentIndex(0)
        #self.initUI()
        self.getUser()
        ################################
        
        self.setLineGraph()
        self.createPieChart()

        self.handleUiChanges()
        self.handleButtons()

        self.show_users_table_data()
        self.show_products_table_data()

        ##################################

#        RunPredictionOnFolder.func1()


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
    
    # def select_camera(self, i):
    #     self.camera = QCamera(self.available_cameras[i])
    #     self.camera.setViewfinder(self.viewfinder)
    #     self.camera.setCaptureMode(QCamera.CaptureStillImage)
    #     self.camera.error.connect(lambda: self.alert(self.camera.errorString()))
    #     self.camera.start()

    #     # self.capture = QCameraImageCapture(self.camera)
    #     # self.capture.error.connect(lambda i, e, s: self.alert(s))
    #     # self.capture.imageCaptured.connect(lambda d, i: self.status.showMessage("Image %04d captured" % self.save_seq))

    #     self.current_camera_name = self.available_cameras[i].description()
    #     self.save_seq = 0

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

        timer2 = QTimer(self) 
		# adding action to timer 
        timer2.timeout.connect(self.setPassFailStatV2) #row_num_g,totalFail
        #timer2.timeout.connect(self.createPieChart)
		# update the timer every second 
        timer2.start(5000) #

        self.tabWidget.tabBar().setVisible(False)
        self.staticsTabWidget.tabBar().setVisible(False)
        self.help_tabWidget.tabBar().setVisible(False)
        self.db_tabWidget.tabBar().setVisible(False)
        self.settings_tabWidget.tabBar().setVisible(False)
        # self.getUser()

        self.setPassedNumber()
        #self.setFailedNumber()
        self.showProductComboBox()
        self.setStatus()

        ########################
        #self.setPassFailStatV2(row_num_g,totalFail)

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
        #close the app
        self.pushButton_5.clicked.connect(self.close_app)
        ######################################day Report
        self.searchERDate.clicked.connect(self.retERDate)
        self.searchERProduct.clicked.connect(self.retERProduct)
    #########################################

    def change_product_type(self):
        global InputDir
        global OutputDir
        global level_model_path
        global foreign_object_model_path
        global current_product
        global current_alg
        current_product = self.productComboBox_2.currentText()
        current_alg = self.algorithmComboBox.currentText()
        self.productType.setText(current_product)
        self.productType_2.setText(current_product)
        print('Product : ' + current_product)
        print('Algorithm : ' + current_alg)
        if current_alg == "تشخیص سطح":
            alg = 'level'
        elif current_alg == "تشخیص جسم خارجی":
            alg = 'foreign_object'

        if current_product == "مربا آلبالو":
            product = 'morabba_albalu'
        elif current_product == "ذرت":
            product = 'zorat'
        elif current_product == "زیتون":
            product = 'zeytun'
        elif current_product == "سس":
            product = 'sos'

        InputDir = default_input_dir + "/" + alg + "/" + product
        OutputDir = default_output_dir + "/" + alg + "/" + product

        if alg == "level":
            print('Running Level Detection Algorithm: ...')
            level_detection_alg(input_dir=InputDir, output_dir=OutputDir, model_path=level_model_path, use_gpu=True)
        elif alg == "foreign_object":
            print('Running Foreign Object Detection Algorithm: ... ')
            foreign_object_detection_alg(input_dir=InputDir, output_dir=OutputDir, model_path=foreign_object_model_path)

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
        number =str(totalPass)
        self.passNumber.setText(number)

    def setFailedNumber(self):
        # Until Algo is ready-> Must change
        number =str(totalFail)
        self.failNumber.setText(number)
    ##########################################
    ######################### Opening Tabs ###########################
    def openHomeTab(self):
        self.tabWidget.setCurrentIndex(0)

    def openStaticsTab(self):
        self.tabWidget.setCurrentIndex(1)
        self.staticsTabWidget.setCurrentIndex(0)

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
        #self.setPassFailStat()
        #self.setPassFailStatV2()
    
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

    
    def setPassFailStatV2(self):#,row_num_g,totalFail
        global OutputDir
        global row_num_g
        global totalFail
        global current_product
        global current_alg

        productType = current_product

        self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
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
            print("\nrow_num."+error_percentage)
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
            print("path:",input_IMG_path)
            print("path:",output_IMG_path)
            self.video_stream1.setPixmap(input_IMG)
            self.video_stream2.setPixmap(output_IMG)

            totalFail += 1
            self.setFailedNumber()

        else :
            row_num_g = 0 
            print("All images have been shown")
    
        #time.sleep(3)
            

        self.db.close()


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

        global totalPass
        global totalFail
        print(totalPass)
        print(totalFail)
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
    ##########################################33
    ################Save Error to DataBase##########################

    # def saveErDb(self, date, time, error):
    #     self.db =  MySQLdb.connect(host='localhost', user='root', password='*#@mir#*1261', db='bonyad')
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
            self.productERTable.setItem(row_num, 4, QTableWidgetItem(str(row_data[6])))

        self.db.close()
    ######################## Return errors based on date #############
    def retERDate(self):
        fail_num = 0
        #pass_num = 0
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


    def close_app(self):
        quit()


def main():
    app = QApplication(sys.argv)
    window = Login()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()