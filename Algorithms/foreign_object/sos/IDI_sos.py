import cv2
import os
import numpy as np
import matplotlib.image as mpimg
from tensorflow.keras import backend as K
from keras.models import load_model

def IOU_calc(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)

    return 2*(intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def IOU_calc_loss(y_true, y_pred):
    return -IOU_calc(y_true, y_pred)

model = load_model('sos_model.h5', custom_objects={'IOU_calc_loss': IOU_calc_loss, 'IOU_calc': IOU_calc})


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
    

X = load_images('./test_img/', img_format='gray', resize=(512, 512))
# X.shape

pred = model.predict(X)

## Pass/Fail output
test_num = 0
im_pred = np.array(255*pred[test_num,:,:,0], dtype=np.uint8)
PF_threshold = 100000 # Fail~1000000  Pass~1000 ==> Pass < PF_threshold < Fail
if np.sum(im_pred) < 100000:
  print('Pass :D')
else:
  print('Fail D:')


## Fail pattern illustration
img = np.array(X[test_num,:,:,0], np.uint8)
rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
rgb_pred = cv2.cvtColor(im_pred, cv2.COLOR_GRAY2RGB)
rgb_pred[:, :, 0] = 0*rgb_pred[:, :, 0]
rgb_pred[:, :, 2] = 0*rgb_pred[:, :, 2]
rgb_pred = cv2.addWeighted(rgb_img, 1, rgb_pred, 0.3, 0)

## write result to file
out_path = 'result/'
cv2.imwrite(out_path + 'out.jpg',cv2.resize(rgb_pred, (400, 400)))