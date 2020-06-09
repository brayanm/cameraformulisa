import sys, time, logging
from io import BytesIO
import PyIndi
import astropy.io.fits as pyfits
import cv2
from datetime import datetime
from threading import Thread
import time
import csv
import numpy as np
import os
from random import randint
import pygame
from picamera.array import PiRGBArray
from picamera import PiCamera
from fractions import Fraction
from numpy import copy
from pygame_vkeyboard import *


'''os.environ['SDL_FBDEV'] = "/dev/fb0"
os.environ['SDL_VIDEODRIVER'] = "fbcon"
os.environ['SDL_MOUSEDRV'] = "TSLIB"
os.environ['SDL_MOUSEDEV'] = "/dev/input/event0"'''

x = 0
y = 0

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)

path_fotos_ajustadas = '/media/usb/fotos_ajustadas'
path_fotos_originales = '/media/usb/fotos_originales'
path_fotos_ajustadas_pi = '/media/usb/fotos_ajustadas_pi'
path_fotos_originales_pi = '/media/usb/fotos_originales_pi'
path_fotos_secuencia = '/media/usb/secuencias_zwo'
#path_fotos_ajustadas = '/home/pi/Documents/capturas/ajustadas'
#path_fotos_originales = '/home/pi/Documents/capturas/originales'

if not os.path.exists(path_fotos_ajustadas):
    os.makedirs(path_fotos_ajustadas)
    
if not os.path.exists(path_fotos_ajustadas_pi):
    os.makedirs(path_fotos_ajustadas_pi)
    
if not os.path.exists(path_fotos_originales):
    os.makedirs(path_fotos_originales)
    
if not os.path.exists(path_fotos_originales_pi):
    os.makedirs(path_fotos_originales_pi)

if not os.path.exists(path_fotos_secuencia):
    os.makedirs(path_fotos_secuencia)

DEVICE_NAME = "ZWO CCD ASI290MM"
#DEVICE_NAME = 'CCD Simulator'
'''tabla_ajuste = '/media/usb/tabla_ajuste/tabla_ajuste.csv'
with open(tabla_ajuste, mode='r') as infile:
    reader = csv.reader(infile)
    dict_ajuste = {int(rows[0]):int(rows[1]) for rows in reader}'''
dict_ajuste = {}
for x in range(256):
    dict_ajuste[x] = 0
    
tabla_params = '/home/pi/Documents/params.csv'


class IndiClient(PyIndi.BaseClient):
    with open(tabla_params, mode='r') as infile:
        reader = csv.reader(infile)
        dict_params = {str(rows[0]):float(rows[1]) for rows in reader}    
    roi = None
    device = None
    run = True
    gain_stream = dict_params['gan_s']
    gain_photo = dict_params['gan_f']
    exposure_time_stream = dict_params['exp_s']
    exposure_time_photo = dict_params['exp_f']
    print('valor')
    print(dict_params['exp_f'])
    binning = 2
    width = 1600
    height = 960
    aplicar_ajuste = True
    stream_on = True
    change_to_photo = False
    first_exposure = False
    flag = False
    first_click = False
    connected = True
    sequence = False
    count_sequence = 0
    cant_f = 0
    counter_dir = 0
    notcontinue_seq = False

    def __init__(self):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger('PyQtIndi.IndiClient')
        self.logger.info('creating an instance of PyQtIndi.IndiClient')
    def newDevice(self, d):
        #self.logger.info("new device " + d.getDeviceName())
        if d.getDeviceName() == DEVICE_NAME:
            self.logger.info("Set new device %s!" % DEVICE_NAME)
            # save reference to the device in member variable
            self.device = d
    def newProperty(self, p):
        #self.logger.info("new property "+ p.getName() + " for device "+ p.getDeviceName())
        if self.device is not None and p.getName() == "CONNECTION" and p.getDeviceName() == self.device.getDeviceName():
            self.logger.info("Got property CONNECTION for %s!" % DEVICE_NAME)
            # connect to device
            self.connectDevice(self.device.getDeviceName())
            # set BLOB mode to BLOB_ALSO
            self.setBLOBMode(1, self.device.getDeviceName(), None)
        if p.getName() == "CCD_EXPOSURE":
            # take first exposure
            self.takeExposure(self.exposure_time_stream)
        if p.getName() == "CCD_CONTROLS":
            gain = self.device.getNumber("CCD_CONTROLS")
            gain[0].value = self.gain_stream
            self.sendNewNumber(gain)
        if p.getName() == "CCD_BINNING":
            binning = self.device.getNumber("CCD_BINNING")
            binning[0].value = self.binning
            binning[1].value = self.binning
            self.sendNewNumber(binning)
        if p.getName() == "CCD_FRAME":
            frame = self.device.getNumber("CCD_FRAME")
            print("width-height frame")
            print(frame[2].value)
            print(frame[3].value)
            frame[2].value = self.width
            frame[3].value = self.height
            print(frame[2].value)
            print(frame[3].value)
            self.sendNewNumber(frame)
    def removeProperty(self, p):
        #self.logger.info("remove property "+ p.getName() + " for device "+ p.getDeviceName())
        pass
    def newBLOB(self, bp):
        self.logger.info("new BLOB "+ bp.name)
        # get image data
        img = bp.getblobdata()

        if self.stream_on == True:
            blobfile=BytesIO(img)
            hdulist=pyfits.open(blobfile)
            scidata = hdulist[0].data
            print(scidata.shape)
            w = scidata.shape[0]
            h = scidata.shape[1]
            text1 = "Encuadre y Enfoque"
            text2 = "Presionar para capturar"

            img2 = cv2.merge((scidata,scidata,scidata))
            surf = pygame.surfarray.make_surface(img2)
            surf2 = pygame.transform.rotate(surf, 270)
            surf3 = pygame.transform.flip(surf2, True, False)
            pygame.draw.line(surf3,(255,0,0),(400,0),(400,230), 1)
            pygame.draw.line(surf3,(255,0,0),(400,250),(400,480), 1)
            pygame.draw.line(surf3,(255,0,0),(0,240),(390,240), 1)
            pygame.draw.line(surf3,(255,0,0),(410,240),(800,240), 1)
            display.blit(surf3, (0, 0))
            #surf_text1 = font.render(text1, True, (255,0,0))
            surf_text2 = font.render(text2, True, (255,0,0))
            #display.blit(surf_text1, (10, 30))
            display.blit(surf_text2, (5, 5))
            mouse = pygame.mouse.get_pos()
            print(mouse)
            #menu
            text_back = smallfont2.render('MENU' , True , color)
            if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70: 
                pygame.draw.rect(display,color_light,[700,400,100,70]) 
                  
            else: 
                pygame.draw.rect(display,color_dark,[700,400,100,70]) 
            # superimposing the text onto our button 
            display.blit(text_back , (700+1,400+15))

            #secuencia
            text_sec = smallfont3.render('Secuencia' , True , color)
            if 0 <= mouse[0] <= 0+100 and 400 <= mouse[1] <= 400+70: 
                pygame.draw.rect(display,color_light,[0,400,120,70]) 
                  
            else: 
                pygame.draw.rect(display,color_dark,[0,400,120,70]) 
            # superimposing the text onto our button 
            display.blit(text_sec , (0+1,400+15))     

            pygame.display.flip()
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    print("click")
                    if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70:
                        print("saliir")
                        self.connected = False
                        print(self.connected)
                        #self.disconnectServer()
                    elif 0 <= mouse[0] <= 0+100 and 400 <= mouse[1] <= 400+70: 
                        print('secuencia')
                        self.click_sequence()
                    elif self.first_click==False and (130 <= mouse[0] <= 130+540 and 190 <= mouse[1] <= 190+150):
                        self.first_click = True
                    elif self.first_click==True:
                        self.click_take_photo()
                if event.type == pygame.KEYDOWN:
                    pygame.quit()
                    pygame.display.quit()

            self.takeExposure(self.exposure_time_stream)
        elif self.sequence == True:
            self.notcontinue_seq = False
            blobfile=BytesIO(img)
            hdulist=pyfits.open(blobfile)
            scidata = hdulist[0].data
            print(scidata.shape)
            w = scidata.shape[0]
            h = scidata.shape[1]      
            with open(tabla_params, mode='r') as infile:
                reader = csv.reader(infile)
                dict_params = {str(rows[0]):float(rows[1]) for rows in reader} 
            self.exposure_time_photo = dict_params['exp_f'] 
            dir_seq = path_fotos_secuencia+"/"+str(int(self.counter_dir))  
            if int(self.count_sequence) <= int(self.cant_f):
                hdulist.writeto(dir_seq+"/%s.fit" % str(self.count_sequence))
                self.count_sequence = self.count_sequence + 1
                if self.count_sequence > int(self.cant_f):
                    self.notcontinue_seq = True
                while self.notcontinue_seq==True:
                    display.fill((0,0,0))
                    text1 = "Finalizado"
                    surf_text1 = font.render(text1, True, (255,0,0))
                    display.blit(surf_text1 , (5,5))     
                    pygame.display.update()
                    for event in pygame.event.get():
                        if event.type == pygame.MOUSEBUTTONUP:
                            print("click back stream")
                            self.click_back_stream()
                self.takeExposure(self.exposure_time_photo)
        elif self.stream_on == False and self.first_exposure==False:
            self.flag = False
            blobfile=BytesIO(img)
            hdulist=pyfits.open(blobfile)
            scidata = hdulist[0].data
            print(scidata.shape)
            w = scidata.shape[0]
            h = scidata.shape[1]
            with open(tabla_params, mode='r') as infile:
                reader = csv.reader(infile)
                dict_params = {str(rows[0]):float(rows[1]) for rows in reader}
            name_file = str(int(dict_params['counter_zwo']))
            hdulist.writeto(path_fotos_originales+"/%s.fit" % name_file)
            #calcular frecuencia
            uniqueValues, occurCount = np.unique(scidata, return_counts=True)
            #listOfUniqueValues = zip(uniqueValues, occurCount)
            listOfUniqueValues = sorted(zip(uniqueValues, occurCount), key=lambda x:-x[1])
            print(listOfUniqueValues[0][0])
            maxfreq = listOfUniqueValues[0][0]+int(dict_params['df'])
            print(listOfUniqueValues[0][0])
            print(maxfreq)
            for key in dict_ajuste:
                if key < maxfreq:
                    dict_ajuste[key] = 0
                else:
                    dict_ajuste[key] = int(5+np.log(((key-(maxfreq-1))/10)+0.9)*220)
                    if dict_ajuste[key]>255:
                        dict_ajuste[key] = 255
            #print(dict_ajuste)
            if self.aplicar_ajuste==True:
                for x in range(w):
                    for y in range(h):
                        scidata[x][y] = dict_ajuste[scidata[x][y]]

            hdulist.writeto(path_fotos_ajustadas+"/%s.fit" % name_file)
            cv2.imwrite(path_fotos_ajustadas+"/%s.jpg" % name_file, scidata)
            print("self flag")
            print(self.flag)
            img2 = cv2.merge((scidata,scidata,scidata))
            surf = pygame.surfarray.make_surface(img2)
            surf2 = pygame.transform.rotate(surf, 270)
            surf3 = pygame.transform.flip(surf2, True, False)
            display.blit(surf3, (0, 0))
            pygame.display.update()
            dict_params['counter_zwo'] = int(dict_params['counter_zwo']) + 1
            a_file = open(tabla_params, "w")
            writer = csv.writer(a_file)
            for key, value in dict_params.items():
                writer.writerow([key, value])
            a_file.close()  
            while(self.flag==False):
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONUP:
                        print("click")
                        self.click_back_stream()
                    if event.type == pygame.KEYDOWN:
                        pygame.quit()
                        pygame.display.quit()
        elif self.stream_on == False and self.first_exposure==True:
            print("entro elif")
            self.first_exposure=False
            self.takeExposure(self.exposure_time_photo)
    def newSwitch(self, svp):
        self.logger.info ("new Switch "+ svp.name + " for device "+ svp.device)
    def newNumber(self, nvp):
        self.logger.info("new Number "+ nvp.name + " for device "+ nvp.device)
        print(nvp[0].value)
        if self.stream_on==False and nvp.name=="CCD_EXPOSURE" and nvp[0].value!=0.0:
            text1 = "Tiempo restante: %.2f" % nvp[0].value
            text2 = "Por favor, Espere..."
            img = np.zeros((800,480,3),dtype='uint8')
            surf = pygame.surfarray.make_surface(img)
            display.blit(surf, (0, 0))
            surf_text1 = font.render(text1, True, (255,0,0))
            surf_text2 = font.render(text2, True, (255,0,0))
            display.blit(surf_text1, (10, 30))
            display.blit(surf_text2, (10, 60))
            if self.sequence==True:
                text_c_s = str(self.count_sequence)+" de "+str(int(self.cant_f))
                surf_textc = font.render(text_c_s, True, (255,0,0))
                display.blit(surf_textc, (10, 90))
            pygame.display.update()
    def newText(self, tvp):
        self.logger.info("new Text "+ tvp.name + " for device "+ tvp.device)
    def newLight(self, lvp):
        self.logger.info("new Light "+ lvp.name + " for device "+ lvp.device)
    def newMessage(self, d, m):
        #self.logger.info("new Message "+ d.messageQueue(m))
        pass
    def serverConnected(self):
        print("Server connected ("+self.getHost()+":"+str(self.getPort())+")")
        self.connected = True
    def serverDisconnected(self, code):
        self.logger.info("Server disconnected (exit code = "+str(code)+","+str(self.getHost())+":"+str(self.getPort())+")")
        # set connected to False
        self.connected = False
    def takeExposure(self, exposure_time):
        self.logger.info("<<<<<<<< Exposure >>>>>>>>>")
        #get current exposure time
        exp = self.device.getNumber("CCD_EXPOSURE")
        # set exposure time to 0.5 seconds
        exp[0].value = exposure_time
        # send new exposure time to server/device
        self.sendNewNumber(exp)
    def click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.stream_on==True:
            self.stream_on = False
            print("stream off")
            self.first_exposure = True
            #CCD_CONTROLS
            gain = self.device.getNumber("CCD_CONTROLS")
            gain[0].value = self.gain_photo
            self.sendNewNumber(gain)

            self.takeExposure(3)
        elif event == cv2.EVENT_LBUTTONDOWN and self.stream_on==False:
            self.flag = True
            print("click back stream on")
            self.stream_on = True
            #CCD_CONTROLS
            gain = self.device.getNumber("CCD_CONTROLS")
            gain[0].value = self.gain_stream
            self.sendNewNumber(gain)
            
            self.takeExposure(self.exposure_time_stream)
    def click_take_photo(self):
        self.stream_on = False
        print("stream off")
        self.first_exposure = True
        with open(tabla_params, mode='r') as infile:
            reader = csv.reader(infile)
            dict_params = {str(rows[0]):float(rows[1]) for rows in reader}
        self.exposure_time_photo = dict_params['exp_f']
        self.gain_photo = dict_params['gan_f']
        #CCD_CONTROLS
        #gain = self.device.getNumber("CCD_CONTROLS")
        gain = self.device.getNumber("CCD_CONTROLS")
        gain[0].value = self.gain_photo
        self.sendNewNumber(gain)
        self.takeExposure(3)
    
    def click_back_stream(self):
        self.notcontinue_seq
        self.flag = True
        self.sequence = False
        print("click back stream on")
        self.stream_on = True
        #CCD_CONTROLS
        #gain = self.device.getNumber("CCD_CONTROLS")
        gain = self.device.getNumber("CCD_CONTROLS")
        gain[0].value = self.gain_stream
        self.sendNewNumber(gain)
        
        self.takeExposure(self.exposure_time_stream)

    def click_sequence(self):
        self.stream_on = False
        self.sequence = True
        self.count_sequence = 1
        with open(tabla_params, mode='r') as infile:
            reader = csv.reader(infile)
            dict_params = {str(rows[0]):float(rows[1]) for rows in reader}
        self.exposure_time_photo = dict_params['exp_f']
        self.gain_photo = dict_params['gan_f']
        self.cant_f = dict_params['cant_f']
        self.counter_dir = dict_params['counter_dir']
        if not os.path.exists(path_fotos_secuencia+"/"+str(int(self.counter_dir))):
            os.makedirs(path_fotos_secuencia+"/"+str(int(self.counter_dir)))
        dict_params['counter_dir'] = int(dict_params['counter_dir']) + 1
        a_file = open(tabla_params, "w")
        writer = csv.writer(a_file)
        for key, value in dict_params.items():
            writer.writerow([key, value])
        a_file.close()
        gain = self.device.getNumber("CCD_CONTROLS")
        gain[0].value = self.gain_photo
        self.sendNewNumber(gain)
        self.takeExposure(self.exposure_time_photo)
        
    def disconnect_s(self):
        return self.connected
            
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


class InputBox:

    def __init__(self, x, y, w, h, name, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.name = name

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print(self.text)
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(70, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, display):
        # Blit the text.
        display.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(display, self.color, self.rect, 2)
        
    def get_text(self):
        return self.text
    def set_text(self, text):
        self.txt_surface = FONT.render(text, True, self.color)

def streampicamera(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2):
    camera.color_effects = (128,128)
    print('exp')
    print(exp_s_2)

    camera.framerate = 1/exp_s_2
    camera.shutter_speed = int(exp_s_2*1000000)
    rawCapture = PiRGBArray(camera)
    camera.awb_gains = (int(gan_s_2),int(gan_s_2))
    camera.exposure_mode = 'off'
    time.sleep(1)
    continuepi = True
    first_click = False

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        # show the frame
        img_gray = np.sum(image, axis=2).round()
        img_gray[img_gray > 255] = 255
        #print(img_gray.shape)
        #print(image.shape)
        #img_gray = (img_gray * 255).round().astype(np.uint8)
        print(img_gray)
        #cv2.imshow("Frame", img_gray)
        #key = cv2.waitKey(1) & 0xFF
        # clear the stream in preparation for the next frame
        surf = pygame.surfarray.make_surface(img_gray)
        surf2 = pygame.transform.rotate(surf, 270)
        surf3 = pygame.transform.flip(surf2, True, False)
        #display.blit(surf3, (0, 0))
        text1 = "Encuadre y Enfoque"
        text2 = "Presionar para capturar"
        
        pygame.draw.line(surf3,(255,0,0),(400,0),(400,230), 1)
        pygame.draw.line(surf3,(255,0,0),(400,250),(400,480), 1)
        pygame.draw.line(surf3,(255,0,0),(0,240),(390,240), 1)
        pygame.draw.line(surf3,(255,0,0),(410,240),(800,240), 1)
        display.blit(surf3, (0, 0))
        #surf_text1 = font.render(text1, True, (255,0,0))
        surf_text2 = font.render(text2, True, (255,0,0))
        #display.blit(surf_text1, (10, 30))
        display.blit(surf_text2, (5, 5))
        mouse = pygame.mouse.get_pos()
        print(mouse)
        text_back = smallfont2.render('MENU' , True , color)
        if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70: 
            pygame.draw.rect(display,color_light,[700,400,100,70]) 
              
        else: 
            pygame.draw.rect(display,color_dark,[700,400,100,70]) 
        # superimposing the text onto our button 
        display.blit(text_back , (700+1,400+15))
        pygame.display.flip()
        pygame.display.update()
        rawCapture.truncate(0)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print("click")
                if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70:
                    print("saliir")
                    continuepi = False
                elif first_click==False and (130 <= mouse[0] <= 130+540 and 20 <= mouse[1] <= 20+150):
                    first_click = True
                elif first_click==True:
                    takephotopi(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2)
                    continuepi = False
        if continuepi == False:
            try:
                camera.close()
            except:
                print('except')
            break

def takephotopi(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2):
    camera.close()
    print('expf')
    print(exp_f_2)
    display.fill((0,0,0))
    text2 = "Capturando Imagen, Espere por favor..."
    surf_text2 = font.render(text2, True, (255,0,0))
    display.blit(surf_text2, (5, 5))
    pygame.display.update()
    camera = PiCamera()
    camera.resolution = (800, 480)
    camera.framerate = 1/exp_f_2
    camera.shutter_speed = int(exp_f_2*1000000)
    camera.awb_gains = (int(gan_f_2),int(gan_f_2))
    camera.sensor_mode = 4
    camera.exposure_mode = 'off'
    rawCapture = PiRGBArray(camera)
    # allow the camera to warmup
    time.sleep(1)
    # grab an image from the camera
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    # display the image on screen and wait for a keypress
    #cv2.imshow("Image", image)
    with open(tabla_params, mode='r') as infile:
        reader = csv.reader(infile)
        dict_params = {str(rows[0]):float(rows[1]) for rows in reader}

    w = image.shape[0]
    h = image.shape[1]
    print('image shape')
    print(image.shape)
    img_gray = np.sum(image, axis=2).round()
    img_gray[img_gray > 255] = 255
    print('image gray')
    print(img_gray.shape)
    
    img_gray = img_gray.astype(np.uint8)
    
    hdu = pyfits.PrimaryHDU(img_gray)
    name_file = str(int(dict_params['counter_pi']))
    hdu.writeto(path_fotos_originales_pi+"/%s.fit" % name_file)
    #calcular frecuencia
    uniqueValues, occurCount = np.unique(img_gray, return_counts=True)
    #listOfUniqueValues = zip(uniqueValues, occurCount)
    listOfUniqueValues = sorted(zip(uniqueValues, occurCount), key=lambda x:-x[1])
    print(listOfUniqueValues[0][0])
    maxfreq = listOfUniqueValues[0][0]+df_2
    #print(dict_ajuste)
    for key in dict_ajuste:
        if key < maxfreq:
            dict_ajuste[key] = 0
        else:
            dict_ajuste[key] = int(5+np.log(((key-(maxfreq-1))/10)+0.9)*220)
            if dict_ajuste[key]>255:
                dict_ajuste[key] = 255
    print(dict_ajuste)
    for x in range(w):
        for y in range(h):
            img_gray[x][y] = dict_ajuste[img_gray[x][y]]
    print('image gray')
    print(img_gray.shape)
    hdu2 = pyfits.PrimaryHDU(img_gray)
    hdu2.writeto(path_fotos_ajustadas_pi+"/%s.fit" % name_file)
    cv2.imwrite(path_fotos_ajustadas_pi+"/%s.jpg" % name_file, img_gray)
    
    dict_params['counter_pi'] = int(dict_params['counter_pi'])+1
    print(dict_params['counter_pi'])
    a_file = open(tabla_params, "w")
    writer = csv.writer(a_file)
    for key, value in dict_params.items():
        writer.writerow([key, value])
    a_file.close() 
    
    continueshowimg = True
    while continueshowimg:
        surf = pygame.surfarray.make_surface(img_gray)
        surf2 = pygame.transform.rotate(surf, 270)
        surf3 = pygame.transform.flip(surf2, True, False)
        display.blit(surf3, (0, 0))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print("click")
                continueshowimg = False
    camera.close()
    time.sleep(1)
    camera = PiCamera(sensor_mode=4, resolution = (800, 480))
    display.fill((0,0,0))
    text2 = "Espere por favor"
    surf_text2 = font.render(text2, True, (255,0,0))
    display.blit(surf_text2, (5, 5))
    pygame.display.update()
    streampicamera(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2)


def streamfutureo(gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2):
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    camera.set(cv2.CAP_PROP_EXPOSURE, exp_s_2)
    camera.set(cv2.CAP_PROP_GAIN, gan_s_2)
    continuecam = True
    first_click = False
    while continuecam:
        next, frame = camera.read()
        #print(frame.shape)
        w = frame.shape[0]
        h = frame.shape[1]
        img_gray = np.sum(frame, axis=2).round()
        img_gray[img_gray > 255] = 255
        img_gray = img_gray.astype(np.uint8)
        #image2 = cv2.merge((img_gray,img_gray,img_gray))
        uniqueValues, occurCount = np.unique(img_gray, return_counts=True)
        #listOfUniqueValues = zip(uniqueValues, occurCount)
        listOfUniqueValues = sorted(zip(uniqueValues, occurCount), key=lambda x:-x[1])
        print(listOfUniqueValues[0][0])
        maxfreq = listOfUniqueValues[0][0]+df_2
        #print(dict_ajuste)
        for key in dict_ajuste:
            if key < maxfreq:
                dict_ajuste[key] = 0
            else:
                dict_ajuste[key] = int(5+np.log(((key-(maxfreq-1))/10)+0.9)*220)
                if dict_ajuste[key]>255:
                    dict_ajuste[key] = 255
        #print(dict_ajuste)
        '''for x in range(w):
            for y in range(h):
                img_gray[x][y] = dict_ajuste[img_gray[x][y]]'''
        newArray = copy(img_gray)
        for k, v in dict_ajuste.items(): newArray[img_gray==k] = v
        print('image gray')
        print(newArray.shape)
        image3 = cv2.merge((newArray,newArray,newArray))
        surf = pygame.surfarray.make_surface(image3)
        surf2 = pygame.transform.rotate(surf, 270)
        surf3 = pygame.transform.flip(surf2, True, False)
        #display.blit(surf3, (0, 0))
        text1 = "Encuadre y Enfoque"
        text2 = "Presionar para capturar"
        
        pygame.draw.line(surf3,(255,0,0),(400,0),(400,230), 1)
        pygame.draw.line(surf3,(255,0,0),(400,250),(400,480), 1)
        pygame.draw.line(surf3,(255,0,0),(0,240),(390,240), 1)
        pygame.draw.line(surf3,(255,0,0),(410,240),(800,240), 1)
        display.blit(surf3, (0, 0))
        #surf_text1 = font.render(text1, True, (255,0,0))
        surf_text2 = font.render(text2, True, (255,0,0))
        #display.blit(surf_text1, (10, 30))
        display.blit(surf_text2, (5, 5))
        mouse = pygame.mouse.get_pos()
        print(mouse)
        text_back = smallfont2.render('MENU' , True , color)
        if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70: 
            pygame.draw.rect(display,color_light,[700,400,100,70]) 
              
        else: 
            pygame.draw.rect(display,color_dark,[700,400,100,70]) 
        # superimposing the text onto our button 
        display.blit(text_back , (700+1,400+15))
        pygame.display.flip()
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print("click")
                if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70:
                    print("saliir")
                    continuecam = False
                elif first_click==False and (130 <= mouse[0] <= 130+540 and 20 <= mouse[1] <= 20+150):
                    first_click = True
                elif first_click==True:
                    takephotofutureo(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2)
                    continuecam = False        
        if continuecam == False:
            try:
                camera.release()
            except:
                print('except')
            break        
        
def takephotofutureo(camera, gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2):
    camera.release()
    display.fill((0,0,0))
    text2 = "Capturando Imagen, Espere por favor..."
    surf_text2 = font.render(text2, True, (255,0,0))
    display.blit(surf_text2, (5, 5))
    pygame.display.update()

    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    camera.set(cv2.CAP_PROP_EXPOSURE, exp_f_2)
    camera.set(cv2.CAP_PROP_GAIN, gan_f_2)
    next, frame = camera.read()

    with open(tabla_params, mode='r') as infile:
        reader = csv.reader(infile)
        dict_params = {str(rows[0]):float(rows[1]) for rows in reader}

    w = frame.shape[0]
    h = frame.shape[1]

    img_gray = np.sum(frame, axis=2).round()
    img_gray[img_gray > 255] = 255
    img_gray = img_gray.astype(np.uint8)
    image2 = cv2.merge((img_gray,img_gray,img_gray))

    hdu = pyfits.PrimaryHDU(image2)
    name_file = str(int(dict_params['counter_pi']))
    hdu.writeto(path_fotos_originales_pi+"/%s.fit" % name_file)
    #calcular frecuencia
    uniqueValues, occurCount = np.unique(img_gray, return_counts=True)
    #listOfUniqueValues = zip(uniqueValues, occurCount)
    listOfUniqueValues = sorted(zip(uniqueValues, occurCount), key=lambda x:-x[1])
    print(listOfUniqueValues[0][0])
    maxfreq = listOfUniqueValues[0][0]+df_2
    #print(dict_ajuste)
    for key in dict_ajuste:
        if key < maxfreq:
            dict_ajuste[key] = 0
        else:
            dict_ajuste[key] = int(5+np.log(((key-(maxfreq-1))/10)+0.9)*220)
            if dict_ajuste[key]>255:
                dict_ajuste[key] = 255
    #print(dict_ajuste)
    '''for x in range(w):
        for y in range(h):
            img_gray[x][y] = dict_ajuste[img_gray[x][y]]'''
    newArray = copy(img_gray)
    for k, v in dict_ajuste.items(): newArray[img_gray==k] = v
    print('image gray')
    print(img_gray.shape)
    image3 = cv2.merge((newArray,newArray,newArray))
    hdu2 = pyfits.PrimaryHDU(image3)
    hdu2.writeto(path_fotos_ajustadas_pi+"/%s.fit" % name_file)
    cv2.imwrite(path_fotos_ajustadas_pi+"/%s.jpg" % name_file, img_gray)
    
    dict_params['counter_pi'] = int(dict_params['counter_pi'])+1
    print(dict_params['counter_pi'])
    a_file = open(tabla_params, "w")
    writer = csv.writer(a_file)
    for key, value in dict_params.items():
        writer.writerow([key, value])
    a_file.close() 
    
    continueshowimg = True
    while continueshowimg:
        surf = pygame.surfarray.make_surface(image3)
        surf2 = pygame.transform.rotate(surf, 270)
        surf3 = pygame.transform.flip(surf2, True, False)
        display.blit(surf3, (0, 0))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                print("click")
                continueshowimg = False
    camera.release()
    time.sleep(1)
    display.fill((0,0,0))
    text2 = "Espere por favor"
    surf_text2 = font.render(text2, True, (255,0,0))
    display.blit(surf_text2, (5, 5))
    pygame.display.update()
    streamfutureo(gan_s_2, exp_s_2, gan_f_2, exp_f_2, df_2)

def on_key_event(text):
    print('Current text : %s' % text)
        
if __name__ == '__main__':
    # instantiate the client
    #indiclient=IndiClient()
    # set indi server localhost and port 7624
    #indiclient.setServer("localhost",7624)
    pygame.init()
    display = pygame.display.set_mode((800, 480))
    font = pygame.font.SysFont('Arial', 15)
    #pygame.mouse.set_visible(0)
    color = (0,0,0) 
    color_light = (204,0,0) 
    color_dark = (255,0,0) 
    width = display.get_width() 
    height = display.get_height() 
    smallfont = pygame.font.SysFont('Corbel',60)
    smallfont2 = pygame.font.SysFont('Corbel',48)
    smallfont3 = pygame.font.SysFont('Corbel',30) 
    text1_p = smallfont.render('Cámara Secundaria' , True , color)
    text2_p = smallfont.render('Cámara Principal' , True , color)
    text3_p = smallfont.render('Configuración' , True , color)
    COLOR_INACTIVE = pygame.Color('red')
    COLOR_ACTIVE = (255,51,51)
    FONT = pygame.font.Font(None, 32)
    text = ""
    running = True
    model = ['123', '456', '789', '0']
    layout = VKeyboardLayout(model)
    keyboard = VKeyboard(display,
                                 on_key_event,
                                 layout,
                                 renderer=VKeyboardRenderer.DARK,
                                 show_text=True,
                                 joystick_navigation=False)
    box_active = False
    number_input = ''
    while running:
        display.fill((0,0,0))
        for ev in pygame.event.get(): 
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
            #checks if a mouse is clicked 
            if ev.type == pygame.MOUSEBUTTONDOWN: 
                if 130 <= mouse[0] <= 130+540 and 20 <= mouse[1] <= 20+150:  
                    print('camara secuandaria')
                    try:
                        with open(tabla_params, mode='r') as infile:
                            reader = csv.reader(infile)
                            dict_params = {str(rows[0]):float(rows[1]) for rows in reader}
                        display.fill((0,0,0))
                        text2 = "Espere por favor"
                        surf_text2 = font.render(text2, True, (255,0,0))
                        display.blit(surf_text2, (5, 5))
                        pygame.display.update()
                        #streampicamera(camera, dict_params['gan_s_2'], dict_params['exp_s_2'], dict_params['gan_f_2'], dict_params['exp_f_2'], dict_params['df_2'])
                        streamfutureo(dict_params['gan_s_2'], dict_params['exp_s_2'], dict_params['gan_f_2'], dict_params['exp_f_2'], dict_params['df_2'])
                    except SystemExit as e:
                        print(e)
                    else:
                        print("nada")
                    #camera.close()
                if 130 <= mouse[0] <= 130+540 and 190 <= mouse[1] <= 190+150:
                    print('camara principal')
                    display.fill((0,0,0))
                    try:
                        display.fill((0,0,0))
                        text2 = "Espere por favor"
                        surf_text2 = font.render(text2, True, (255,0,0))
                        display.blit(surf_text2, (5, 5))
                        pygame.display.update()
                        indiclient=IndiClient()
                        indiclient.setServer("localhost",7624)
                        if (not(indiclient.connectServer())):
                             print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
                             print("  indiserver indi_simulator_telescope indi_simulator_ccd")
                             #sys.exit(1)
                        time.sleep(1)
                        #while indiclient.connected:
                        while indiclient.disconnect_s():
                            print('en while')
                            print(indiclient.disconnect_s())
                            #if not(indiclient.connected):
                            #    connected = False
                            time.sleep(1)
                        indiclient.disconnectServer()
                        print('sale')
                    except SystemExit as e:
                        print(e)
                    else:
                        print("nada")
                if 130 <= mouse[0] <= 130+540 and 330 <= mouse[1] <= 330+150:
                    print('configuracion')
                    display.fill((0,0,0))

                    clock = pygame.time.Clock()
                    input_box_gan_s = InputBox(160, 60, 70, 32, 'gan_s')
                    input_box_exp_s = InputBox(380, 60, 70, 32, 'exp_s')
                    input_box_gan_f = InputBox(160, 120, 70, 32, 'gan_f')
                    input_box_exp_f = InputBox(380, 120, 70, 32, 'exp_f')
                    input_box_df = InputBox(570, 120, 70, 32, 'df')
                    input_box_cant_f = InputBox(570, 60, 70, 32, 'cant_f')
                    input_box_gan_s_2 = InputBox(160, 230, 70, 32, 'gan_s_2')
                    input_box_exp_s_2 = InputBox(380, 230, 70, 32, 'exp_s_2')
                    input_box_gan_f_2 = InputBox(160, 290, 70, 32, 'gan_f_2')
                    input_box_exp_f_2 = InputBox(380, 290, 70, 32, 'exp_f_2')
                    input_box_df_2 = InputBox(570, 290, 70, 32, 'df_2')
                    input_boxes = [input_box_gan_s, input_box_exp_s, input_box_gan_f, input_box_exp_f, input_box_df, input_box_gan_s_2, input_box_exp_s_2, input_box_gan_f_2, input_box_exp_f_2, input_box_df_2, input_box_cant_f]
                    done = False
                    
                    with open(tabla_params, mode='r') as infile:
                        reader = csv.reader(infile)
                        dict_params = {str(rows[0]):float(rows[1]) for rows in reader}
                    print(dict_params)
                    input_box_gan_s.set_text(str(dict_params['gan_s']))
                    input_box_exp_s.set_text(str(dict_params['exp_s']))
                    input_box_gan_f.set_text(str(dict_params['gan_f']))
                    input_box_exp_f.set_text(str(dict_params['exp_f']))
                    input_box_df.set_text(str(int(dict_params['df'])))
                    input_box_gan_s_2.set_text(str(dict_params['gan_s_2']))
                    input_box_exp_s_2.set_text(str(dict_params['exp_s_2']))
                    input_box_gan_f_2.set_text(str(dict_params['gan_f_2']))
                    input_box_exp_f_2.set_text(str(dict_params['exp_f_2']))
                    input_box_df_2.set_text(str(int(dict_params['df_2'])))
                    input_box_cant_f.set_text(str(int(dict_params['cant_f'])))
                    
                    
                    while not done:
                        mouse = pygame.mouse.get_pos() 
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                done = True
                                #dict_params['df'] if not input_box_df.get_text() else input_box_df.get_text()
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                if 700 <= mouse[0] <= 700+90 and 400 <= mouse[1] <= 400+40:
                                    dict_params['gan_s'] = dict_params['gan_s'] if not input_box_gan_s.get_text() else input_box_gan_s.get_text() 
                                    dict_params['exp_s'] = dict_params['exp_s'] if not input_box_exp_s.get_text() else input_box_exp_s.get_text()
                                    dict_params['gan_f'] = dict_params['gan_f'] if not input_box_gan_f.get_text() else input_box_gan_f.get_text()
                                    dict_params['exp_f'] = dict_params['exp_f'] if not input_box_exp_f.get_text() else input_box_exp_f.get_text()
                                    dict_params['df'] = dict_params['df'] if not input_box_df.get_text() else input_box_df.get_text()
                                    dict_params['gan_s_2'] = dict_params['gan_s_2'] if not input_box_gan_s_2.get_text() else input_box_gan_s_2.get_text()
                                    dict_params['exp_s_2'] = dict_params['exp_s_2'] if not input_box_exp_s_2.get_text() else input_box_exp_s_2.get_text()
                                    dict_params['gan_f_2'] = dict_params['gan_f_2'] if not input_box_gan_f_2.get_text() else input_box_gan_f_2.get_text()
                                    dict_params['exp_f_2'] = dict_params['exp_f_2'] if not input_box_exp_f_2.get_text() else input_box_exp_f_2.get_text()
                                    dict_params['df_2'] = dict_params['df_2'] if not input_box_df_2.get_text() else input_box_df_2.get_text()
                                    dict_params['cant_f'] = dict_params['cant_f'] if not input_box_cant_f.get_text() else input_box_cant_f.get_text()
                                    a_file = open(tabla_params, "w")
                                    writer = csv.writer(a_file)
                                    for key, value in dict_params.items():
                                        writer.writerow([key, value])
                                    a_file.close()
                                    done = True
                                if 30 <= mouse[0] <= 30+70 and 330 <= mouse[1] <= 330+70:
                                    print('1')
                                    number_input = number_input + '1'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 105 <= mouse[0] <= 105+70 and 330 <= mouse[1] <= 330+70:
                                    print('2')
                                    number_input = number_input + '2'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 180 <= mouse[0] <= 180+70 and 330 <= mouse[1] <= 330+70:
                                    print('3')
                                    number_input = number_input + '3'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 255 <= mouse[0] <= 255+70 and 330 <= mouse[1] <= 330+70:
                                    print('4')
                                    number_input = number_input + '4'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 330 <= mouse[0] <= 330+70 and 330 <= mouse[1] <= 330+70:
                                    print('5')
                                    number_input = number_input + '5'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 405 <= mouse[0] <= 405+70 and 330 <= mouse[1] <= 330+70:
                                    print('.')
                                    number_input = number_input + '.'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 30 <= mouse[0] <= 30+70 and 405 <= mouse[1] <= 405+70:
                                    print('6')
                                    number_input = number_input + '6'
                                    if box_active == True:
                                        inptbox.set_text(number_input)    
                                if 105 <= mouse[0] <= 105+70 and 405 <= mouse[1] <= 405+70:
                                    print('7')
                                    number_input = number_input + '7'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 180 <= mouse[0] <= 180+70 and 405 <= mouse[1] <= 405+70:
                                    print('8')
                                    number_input = number_input + '8'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 255 <= mouse[0] <= 255+70 and 405 <= mouse[1] <= 405+70:
                                    print('9')
                                    number_input = number_input + '9'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 330 <= mouse[0] <= 330+70 and 405 <= mouse[1] <= 405+70:
                                    print('0')
                                    number_input = number_input + '0'
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 405 <= mouse[0] <= 405+70 and 405 <= mouse[1] <= 405+70:
                                    print('borrar')
                                    number_input = number_input[:-1]
                                    if box_active == True:
                                        inptbox.set_text(number_input)
                                if 480 <= mouse[0] <= 480+70 and 405 <= mouse[1] <= 405+70:
                                    print('enter')
                                    dict_params[inptbox.name] = float(number_input)
                                    number_input = ''
                                    box_active = False
                                    
                            for box in input_boxes:
                                box.handle_event(event)

                        for box in input_boxes:
                            box.update()
                        display.fill((30, 30, 30))
                        for box in input_boxes:
                            box.draw(display)
                        

                        
                        #textos
                        surf_text_cam_p = FONT.render("Cámara Principal", True, (255,0,0))
                        surf_text_cam_sec = FONT.render("Cámara Secundaria", True, (255,0,0))
                        surf_text_gan_s = FONT.render("Gan Stream", True, (255,0,0))
                        surf_text_exp_s = FONT.render("Exp Stream", True, (255,0,0))
                        surf_text_gan_f = FONT.render("Gan Foto", True, (255,0,0))
                        surf_text_exp_f = FONT.render("Exp Foto", True, (255,0,0))
                        surf_text_df = FONT.render("DF Foto", True, (255,0,0))
                        display.blit(surf_text_cam_p, (300, 30))
                        display.blit(surf_text_gan_s, (30, 60))
                        display.blit(surf_text_exp_s, (250, 60))
                        display.blit(surf_text_gan_f, (30, 120))
                        display.blit(surf_text_exp_f, (250, 120))
                        display.blit(surf_text_df, (470, 120))
                        display.blit(surf_text_cam_sec, (300, 200))
                        display.blit(surf_text_gan_s, (30, 230))
                        display.blit(surf_text_exp_s, (250, 230))
                        display.blit(surf_text_gan_f, (30, 290))
                        display.blit(surf_text_exp_f, (250, 290))
                        display.blit(surf_text_df, (470, 290))
                        #back menu botton
                        text_back = smallfont2.render('MENU' , True , color)
                        if 700 <= mouse[0] <= 700+100 and 400 <= mouse[1] <= 400+70: 
                            pygame.draw.rect(display,color_light,[700,400,100,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[700,400,100,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_back , (700+1,400+15))
                        
                        #1 arriba
                        text_1 = smallfont2.render('1' , True , color)
                        if 30 <= mouse[0] <= 30+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[30,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[30,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_1 , (30+20,330+20))
                        #2 arriba
                        text_2 = smallfont2.render('2' , True , color)
                        if 105 <= mouse[0] <= 105+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[105,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[105,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_2 , (105+20,330+20))

                        #3 arriba
                        text_3 = smallfont2.render('3' , True , color)
                        if 180 <= mouse[0] <= 180+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[180,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[180,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_3 , (180+20,330+20))
                        
                        #4 arriba
                        text_4 = smallfont2.render('4' , True , color)
                        if 255 <= mouse[0] <= 255+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[255,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[255,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_4 , (255+20,330+20))

                        #5 arriba
                        text_5 = smallfont2.render('5' , True , color)
                        if 330 <= mouse[0] <= 330+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[330,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[330,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_5 , (330+20,330+20))

                        #. arriba
                        text_p = smallfont2.render('.' , True , color)
                        if 405 <= mouse[0] <= 405+70 and 330 <= mouse[1] <= 330+70: 
                            pygame.draw.rect(display,color_light,[405,330,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[405,330,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_p , (405+20,330+20))
                        
                        #6 abajo
                        text_6 = smallfont2.render('6' , True , color)
                        if 30 <= mouse[0] <= 30+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[30,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[30,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_6 , (30+20,405+20))
                        
                        #7 abajo
                        text_7 = smallfont2.render('7' , True , color)
                        if 105 <= mouse[0] <= 105+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[105,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[105,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_7 , (105+20,405+20))
                        
                        #8 abajo
                        text_8 = smallfont2.render('8' , True , color)
                        if 180 <= mouse[0] <= 180+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[180,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[180,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_8 , (180+20,405+20))

                        #9 abajo
                        text_9 = smallfont2.render('9' , True , color)
                        if 255 <= mouse[0] <= 255+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[255,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[255,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_9 , (255+20,405+20))
                        
                        #0 abajo
                        text_0 = smallfont2.render('0' , True , color)
                        if 330 <= mouse[0] <= 330+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[330,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[330,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_0 , (330+20,405+20))
                        
                        #borrar abajo
                        text_b = smallfont2.render('<' , True , color)
                        if 405 <= mouse[0] <= 405+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[405,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[405,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_b , (405+20,405+20))

                        #enter abajo
                        text_e = smallfont2.render('E' , True , color)
                        if 480 <= mouse[0] <= 480+70 and 405 <= mouse[1] <= 405+70: 
                            pygame.draw.rect(display,color_light,[480,405,70,70]) 
                              
                        else: 
                            pygame.draw.rect(display,color_dark,[480,405,70,70]) 
                        # superimposing the text onto our button 
                        display.blit(text_e , (480+20,405+20))
                        #events = pygame.event.get()
                        #keyboard.update(events)
                        #rects = keyboard.draw(display)

                        # Flip only the updated area
                        
                        
                        for box in input_boxes:
                            #print(box.active)
                            if box.active == True:
                                box_active = True
                                inptbox = box
                                
                        pygame.display.flip()
                        #pygame.display.update(rects)
                        #pygame.display.update()


                        '''while box_active == True:
                            print('si')
                            display.fill((0, 0, 0))
                            events = pygame.event.get()
                            keyboard.update(events)
                            rects = keyboard.draw(display)
                            #keyboard.draw(display) 
                            #pygame.display.flip()
                            tx = keyboard.get_text()
                            x = tx.split(" ")
                            if len(x) >= 2:
                                inptbox.active = False
                                box_active = False
                                inptbox.set_text(x[0])
                                keyboard.set_text('')
                            pygame.display.update(rects)
                            #pygame.display.update()
                            #pygame.display.flip()'''
                        clock.tick(30)
        mouse = pygame.mouse.get_pos() 
          
        # boton camara secuandara
        if 130 <= mouse[0] <= 130+540 and 20 <= mouse[1] <= 20+150: 
            pygame.draw.rect(display,color_light,[130,10,540,150]) 
              
        else: 
            pygame.draw.rect(display,color_dark,[130,10,540,150]) 
        # superimposing the text onto our button 
        display.blit(text1_p , (130+80,10+50))
        
          
        # boton camara principal
        if 130 <= mouse[0] <= 130+540 and 190 <= mouse[1] <= 190+150: 
            pygame.draw.rect(display,color_light,[130,170,540,150]) 
              
        else: 
            pygame.draw.rect(display,color_dark,[130,170,540,150]) 
        # superimposing the text onto our button 
        display.blit(text2_p , (130+100,170+50))
        
        # boton configuracion
        if 130 <= mouse[0] <= 130+540 and 330 <= mouse[1] <= 330+150: 
            pygame.draw.rect(display,color_light,[130,330,540,150]) 
              
        else: 
            pygame.draw.rect(display,color_dark,[130,330,540,150]) 
        display.blit(text3_p , (130+130,330+50)) 
        # superimposing the text onto our button 
        #events = pygame.event.get()
        #keyboard.update(events)
        #rects = keyboard.draw(display)

        # Flip only the updated area
        #pygame.display.update(rects)
        # updates the frames of the game 
        pygame.display.update()
    pygame.quit() 
    # connect to indi server
    '''print("Connecting and waiting 2secs")
    if (not(indiclient.connectServer())):
         print("No indiserver running on "+indiclient.getHost()+":"+str(indiclient.getPort())+" - Try to run")
         print("  indiserver indi_simulator_telescope indi_simulator_ccd")
         sys.exit(1)
    time.sleep(1)
     
    # start endless loop, client works asynchron in background, loop stops after disconnect
    while indiclient.connected:
        time.sleep(1)'''