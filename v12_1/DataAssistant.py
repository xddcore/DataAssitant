#coding:utf-8
import wx
import os
from PIL import Image
import configparser
import os,time,zipfile
import shutil
from threading import Thread  # 创建线程的模块
import cv2
import xml.dom.minidom as Dom
import glob

mode_status = 0#数据集预处理模式(默认0，0:目标分类 1:目标检测 2:目标检测(自动标注))
ch1_list0=['目标分类','目标检测','目标检测(自动标注)']
ch1_list1=['classification','Object Detection','Object Detection(auto label)']
cfgpath = "config.ini" ##配置文件
dataset_path =""#处理根目录
classes = [] #所有标签名
classes_path = [] #所有标签路径
output_path = './output/output/'#目标分类转换后图片的目录
Object_Detection_path = "./Object_Detection"#目标检测转换后图片的目录
image_weight = 0 #转换后的宽度
image_hight = 0 #转换后的高度
video_handel_flag = 0#视频文件处理标志
# 创建管理对象
conf = configparser.ConfigParser()
# 读ini文件
conf.read(cfgpath, encoding="utf-8")  # python3
#获取Section UI
UI = conf.items('UI')
language = UI[0][1]#获取语言
#获取Section Image
UI = conf.items('Image')
image_weight = int(UI[0][1])#获取语言
image_hight = int(UI[1][1])#获取语言
###############################################################################
def F9_down(event):#F9按下事件
    # 创建管理对象
    conf = configparser.ConfigParser()
    # 读ini文件
    conf.read(cfgpath, encoding="utf-8")  # python3
    #获取Section UI
    UI = conf.items('UI')
    language = UI[0][1]#获取语言
    key = event.GetKeyCode()
    if key == 348:#F9按下
        if(language == "english"):
            conf.set("UI", "language", "chinese")  # 写入中文
            conf.write(open(cfgpath, "r+", encoding="utf-8"))  # r+模式
            wx.MessageBox("软件重启后,语言将切换为中文", '信息', wx.OK | wx.ICON_INFORMATION)
            frame.Destroy()
        elif(language == "chinese"):
            conf.set("UI", "language", "english")  # 写入英文
            conf.write(open(cfgpath, "r+", encoding="utf-8"))  # r+模式
            wx.MessageBox("After the software restarts,the language will switch to English", 'Info', wx.OK | wx.ICON_INFORMATION)
            frame.Destroy()
###############################################################################
def is_Chinese(word):#标签文件夹中文检测
    for ch in word:
        if '\u4e00' <= ch <= '\u9fa5':
            return True
    return False
###############################################################################
def get_lable_number():#获取标签文件夹数目
    global dataset_path
    global language
    lable = 0
    for filename in os.listdir(dataset_path):
        if (os.path.isdir(dataset_path+filename+"/")):
            if(is_Chinese(filename)):
                if(language == "chinese"):
                    wx.MessageBox("/"+filename+'标签文件夹不能含有中文', '错误', wx.OK | wx.ICON_INFORMATION)
                    return 0
                elif(language == "english"):
                    wx.MessageBox("/"+filename+'||Label folder cannot contain Chinese', 'Error', wx.OK | wx.ICON_INFORMATION)
                    return 0
            else:
                classes.append(str(filename))
            lable = lable + 1
        else:
            if(language == "chinese"):
                wx.MessageBox("/"+filename+'不是一个文件夹', '错误', wx.OK | wx.ICON_INFORMATION)
                return 0
            elif(language == "english"):
                wx.MessageBox("/"+filename+'||Not a folder', 'Error', wx.OK | wx.ICON_INFORMATION)
                return 0
    #异常处理:标签文件夹小于2个
    if(mode_status == 0):#目标分类模式
        if(lable <2):
            if(language == "chinese"):
                wx.MessageBox('标签文件夹数量需要大于2个','错误', wx.OK | wx.ICON_INFORMATION)
                return 0 
            elif(language == "english"):
                wx.MessageBox('The number of label folders needs to be greater than 2','Error', wx.OK | wx.ICON_INFORMATION)
                return 0
    elif(mode_status == 1 or mode_status == 2 ):#目标检测模式
        if(lable <1):
            if(language == "chinese"):
                wx.MessageBox('标签文件夹数量需要大于/等于1个','错误', wx.OK | wx.ICON_INFORMATION)
                return 0 
            elif(language == "english"):
                wx.MessageBox('The number of label folders needs to be greater than 1','Error', wx.OK | wx.ICON_INFORMATION)
                return 0    
    return lable
###############################################################################
def get_image_number(classes):#获取每个标签下图片数目
    global dataset_path
    global classes_path
    global language
    global video_handel_flag
    global avi_path_list,mp4_path_list
    image_number = 0
    image_number_list = []
    avi_path_list = []
    mp4_path_list = []
    for class_name in classes:#所有标签目录遍历
        image_number = 0
        class_path = dataset_path + class_name + '/'
        classes_path.append(class_path+"/")
        if(len(glob.glob(class_path+'*.avi'))):#检查是否有视频文件
            avi_path_list.append(glob.glob(class_path+'*.avi')[0])#路径存放到list
        if(len(glob.glob(class_path+'*.mp4'))):#检查是否有视频文件
            mp4_path_list.append(glob.glob(class_path+'*.mp4')[0])#路径存放到list
        if(len(avi_path_list) or len(mp4_path_list) ):
            image_number = 100#直接越过图片数量检查
            video_handel_flag = 1
        for img_name in os.listdir(class_path): #一个标签目录下所有图片遍历#class_path
            image_number = image_number + 1
        if(mode_status == 0):#目标分类模式
            if(image_number <40):#此处考虑目标检测每类图片大于200张
                if(language == "chinese"):
                    wx.MessageBox("/"+class_name+'标签文件夹下图片数量应>=40张','错误', wx.OK | wx.ICON_INFORMATION)
                    return 0
                elif(language == "english"):
                    wx.MessageBox("/"+class_name+'||The number of pictures under the label folder should be> = 40','Error', wx.OK | wx.ICON_INFORMATION)
                    return 0
                image_number_list.append(image_number)
        elif(mode_status == 1 ):#目标检测模式
            if(image_number <100):#此处考虑目标检测每类图片大于100张
                if(language == "chinese"):
                    wx.MessageBox("/"+class_name+'标签文件夹下图片数量应>=100张','错误', wx.OK | wx.ICON_INFORMATION)
                    return 0
                elif(language == "english"):
                    wx.MessageBox("/"+class_name+'||The number of pictures under the label folder should be> = 100','Error', wx.OK | wx.ICON_INFORMATION)
                    return 0
                image_number_list.append(image_number)
        elif(mode_status == 2):#目标检测(自动标注)模式(图片/视频
            if(image_number <100):#此处考虑目标检测每类图片大于100张
                if(language == "chinese"):
                    wx.MessageBox("/"+class_name+'标签文件夹下图片数量应>=100张/视频文件应>0','错误', wx.OK | wx.ICON_INFORMATION)
                    return 0
                elif(language == "english"):
                    wx.MessageBox("/"+class_name+'||The number of pictures under the label folder should be> = 100/video file must more than 0.','Error', wx.OK | wx.ICON_INFORMATION)
                    return 0
                image_number_list.append(image_number)        
    return image_number_list
###############################################################################
def image_padding(image,image_weight,image_hight):#图片填充
    longer_side = max(image.size)
    horizontal_padding = (image_weight - image.size[0]) / 2
    vertical_padding = (image_hight - image.size[1]) / 2
    image = image.crop(
    (
        -horizontal_padding,
        -vertical_padding,
        image.size[0] + horizontal_padding,
        image.size[1] + vertical_padding
    )
                   )   
    return image
def process_image_classification(image,mwidth=image_weight, mheight=image_hight):#目标分类用
    w,h = image.size
    #print(w,h,mwidth,mheight)
    if w<=mwidth and h<=mheight:#小于处理尺寸
        #print(filename,'is OK.')
        if(w<h):#竖屏图片
            image = image.transpose(Image.ROTATE_90)   # 引用固定的常量值
            return image
        else :
            return image
    if (1.0*w/mwidth) > (1.0*h/mheight):#等比例缩放
        scale = 1.0*w/mwidth
        new_im = image.resize((int(w/scale), int(h/scale)), Image.ANTIALIAS)
        new_w,new_h = new_im.size
        if(new_w<new_h):#竖屏图片
            new_im = new_im.transpose(Image.ROTATE_90)   # 引用固定的常量值
        else :
            pass
    else:
        scale = 1.0*h/mheight
        new_im = image.resize((int(w/scale),int(h/scale)), Image.ANTIALIAS) 
        new_w,new_h = new_im.size
        if(new_w<new_h):#竖屏图片
            new_im = new_im.transpose(Image.ROTATE_90)   # 引用固定的常量值
        else :
            pass
    '''
    #自适应填充黑色目标检测要用
    longer_side = max(new_im.size)
    horizontal_padding = (image_weight - new_im.size[0]) / 2
    vertical_padding = (image_hight - new_im.size[1]) / 2
    new_im = new_im.crop(
        (
        -horizontal_padding,
        -vertical_padding,
        new_im.size[0] + horizontal_padding,
        new_im.size[1] + vertical_padding
        )
                   )    
    '''
    return new_im
def process_image_Object_Detection(image,mwidth=320, mheight=240):#目标检测用,yolov2下采样/32
    w,h = image.size
    #print(w,h,mwidth,mheight)
    if w<=mwidth and h<=mheight:#小于处理尺寸
        #print(filename,'is OK.')
        if(w<h):#竖屏转横屏
            image = image.transpose(Image.ROTATE_90)   # 引用固定的常量值
            image = image_padding(image,mwidth,mheight) #填充为416*416
            return image
        else :
            #填充为416*416
            image = image_padding(image,mwidth,mheight) #填充为416*416
            return image
    if (1.0*w/mwidth) > (1.0*h/mheight):#等比例缩放
        scale = 1.0*w/mwidth
        new_im = image.resize((int(w/scale), int(h/scale)), Image.ANTIALIAS)
        new_w,new_h = new_im.size
        if(new_w<new_h):#竖屏转横屏
            new_im = new_im.transpose(Image.ROTATE_90)   # 引用固定的常量值
            new_im = image_padding(new_im,mwidth,mheight) #填充为416*416
        else :
            new_im = image_padding(new_im,mwidth,mheight) #填充为416*416
    else:
        scale = 1.0*h/mheight
        new_im = image.resize((int(w/scale),int(h/scale)), Image.ANTIALIAS) 
        new_w,new_h = new_im.size
        if(new_w<new_h):#竖屏转横屏
            new_im = new_im.transpose(Image.ROTATE_90)   # 引用固定的常量值
            new_im = image_padding(new_im,mwidth,mheight) #填充为416*416
        else :
            new_im = image_padding(new_im,mwidth,mheight) #填充为416*416

    return new_im
###############################################################################
def gen_xml(file_path,xmin,ymin,xmax,ymax,label):#生成xml文件
    doc = Dom.Document()
    root_node = doc.createElement("bounding_box")
    doc.appendChild(root_node)

    # SERVICE_CODE

    service_node = doc.createElement("xmin")
    service_value = doc.createTextNode(str(xmin))
    service_node.appendChild(service_value)
    root_node.appendChild(service_node)
    
    service_node = doc.createElement("ymin")
    service_value = doc.createTextNode(str(ymin))
    service_node.appendChild(service_value)
    root_node.appendChild(service_node)
    
    service_node = doc.createElement("xmax")
    service_value = doc.createTextNode(str(xmax))
    service_node.appendChild(service_value)
    root_node.appendChild(service_node)
    
    service_node = doc.createElement("ymax")  
    service_value = doc.createTextNode(str(ymax))
    service_node.appendChild(service_value)
    root_node.appendChild(service_node)
    
    service_node = doc.createElement("label")  
    service_value = doc.createTextNode(str(label))
    service_node.appendChild(service_value)
    root_node.appendChild(service_node)

    #print (doc.toxml("utf-8"))
    f = open(file_path, "wb")
    f.write(doc.toprettyxml(indent="\t", newl="\n", encoding="utf-8"))
    f.close()
###############################################################################
def video_to_photo(video_path_list):#视频帧提取
    video_num = 0#视频数量
    for video_path in video_path_list:
        video_num = video_num + 1
        if(language == "chinese"):
            log_text.AppendText("\n开始处理第"+str(video_num)+"个视频文件")
        elif(language == "english"):
            log_text.AppendText("\nStart processing the "+str(video_num)+" video file") 
        vc = cv2.VideoCapture(video_path)  # 读入视频文件
        c=1
        img_num = 0
        if vc.isOpened():  # 判断是否正常打开
            rval, frame = vc.read()
        else:
            rval = False
        timeF = 5  # 视频帧计数间隔频率
        while rval:
            # 循环读取视频帧
            rval, frame = vc.read()
            if (c % timeF == 0):
                # 每隔timeF帧进行存储操作
                try:
                    cv2.imwrite(str(video_path.partition('\\')[0])+"/"+str(img_num) + '.jpg', frame)  # 存储为图像
                except:
                    if(language == "chinese"):
                        log_text.AppendText("\n无法提取"+str(img_num)+"帧")
                    elif(language == "english"):
                        log_text.AppendText("\nExtract failed "+str(img_num)+" frame") 
                    break
                img_num = img_num + 1
                if(language == "chinese"):
                    log_text.AppendText("\n成功提取"+str(img_num)+"帧")
                elif(language == "english"):
                    log_text.AppendText("\nExtract successfully "+str(img_num)+" frame") 
                #print("成功处理"+str(img_num)+"帧")
            c = c + 1
        vc.release()
        cv2.destroyAllWindows()
###############################################################################
def convert_24bit_320_240():#将每个图片位深度转换为24bit，分辨率转为QVGA320*240
    global dataset_path
    global classes
    global image_weight,image_hight
    global language
    global Object_Detection_path
    global video_handel_flag#1:处理视频模式 0：处理图片
    broken_flag = 0#文件破损
    i = 0
    class_number = 0
    box = []
    today = time.strftime('%Y%m%d')
    now = time.strftime('%H%M%S')
    Object_Detection_path = "./Object_Detection" + "-" + today + "-" + now + "/"
    Object_Detection_path_zip = "./Object_Detection" + "-" + today + "-" + now
    if(video_handel_flag == 0):#图片处理
        try :
            for class_name in classes:#class_name:文件夹标签名
                class_path = dataset_path + class_name + '/'
                print(class_path)
                for img_name in os.listdir(class_path): #图片实例名
                    img_path = class_path + img_name #每一个图片的地址 
                    print(img_path)
                    img = Image.open(img_path).convert('RGB')#转为24bit
                    if(mode_status == 0):#目标分类模式
                        img = process_image_classification(img)#目标分类图片处理
                        #img = img.resize((image_weight,image_hight))#转换image_weight*image_hight分辨率
                        file_name, file_extend = os.path.splitext(img_name)#获取文件名     
                        if os.path.exists(output_path + class_name + '/') is False:#不存在目录则创建
                            os.makedirs(output_path + class_name + '/')
                        new_image_path = os.path.join(os.path.abspath(output_path + class_name + '/'), file_name + '.jpg')
                        img.save(new_image_path)
                    elif(mode_status == 1):#目标检测模式
                        img = process_image_Object_Detection(img)#目标检测图片处理
                        #img = img.resize((image_weight,image_hight))#转换image_weight*image_hight分辨率
                        file_name, file_extend = os.path.splitext(img_name)#获取文件名     
                        if os.path.exists(Object_Detection_path + class_name + '/') is False:#不存在目录则创建
                            os.makedirs(Object_Detection_path + class_name + '/')
                        new_image_path = os.path.join(os.path.abspath(Object_Detection_path + class_name + '/'), file_name + '.jpg')
                        img.save(new_image_path)
                    elif(mode_status == 2):#目标检测(自动标注)模式
                        img = process_image_Object_Detection(img)#目标检测图片处理
                        #img = img.resize((image_weight,image_hight))#转换image_weight*image_hight分辨率
                        file_name, file_extend = os.path.splitext(img_name)#获取文件名 
                        if os.path.exists(Object_Detection_path + class_name + '/') is False:#不存在目录则创建
                            os.makedirs(Object_Detection_path + class_name + '/')
                        new_image_path = os.path.join(os.path.abspath(Object_Detection_path + class_name + '/'), file_name + '.jpg')
                        img.save(new_image_path)
                        if(file_name == "0"):#0.jpg   
                            image=cv2.imread(new_image_path)
                            roi = list(cv2.selectROI('Label',image, False, False))
                            box = roi
                            #print(roi)#xmin ymin w h
                            box[0] = roi[0]#xmin
                            box[1] = roi[1]#ymin
                            box[2] = roi[0] + roi[2]#xmax
                            box[3] = roi[1] + roi[3]#ymax
                            box.append(class_number)#label
                            #print(box)
                            gen_xml(Object_Detection_path + class_name + '/'+"0.xml",box[0],box[1],box[2],box[3],box[4])
                            cv2.destroyWindow('Label')
                    i = i + 1
                    if(language == "chinese"):
                        log_text.AppendText("\n已处理"+str(i)+"张图片...")
                    elif(language == "english"):
                        log_text.AppendText("\n"+str(i)+" pictures processed...")
                if((not len(glob.glob(class_path+'0.jpg'))) and (not len(glob.glob(class_path+'0.png')))):#检查是否有0.jpg/0.png文件
                    if(language == "chinese"):
                        wx.MessageBox('未在/'+class_name+'发现0.jpg/0.png文件。','错误', wx.OK | wx.ICON_INFORMATION)
                    elif(language == "english"):
                        wx.MessageBox('No 0.jpg/0.png file found in/'+class_name,'Error', wx.OK | wx.ICON_INFORMATION)
                    exit(0)
                class_number = class_number + 1
        except Exception as e :
            print(e)
            broken_flag = 1#文件破损
            if(language == "chinese"):
                log_text.AppendText("\n图片文件破损，软件无法处理，请手动删除破损图片文件")
            elif(language == "english"):
                log_text.AppendText("\nThe image file is damaged and the software cannot process it, please delete the damaged image file manually.")  
        if(broken_flag == 0):
            if(language == "chinese"):
                log_text.AppendText("\n\n\n处理成功！")
            elif(language == "english"):
                log_text.AppendText("\n\n\nFinish！")
            if(mode_status == 0):#目标分类模式
                #os.system("explorer.exe %s" % output_path.replace('/','\\'))#处理完成后打开目录
                os.system("explorer.exe %s" % "./".replace('/','\\'))#处理完成后打开目录
                createZip("./output/","./output")
                shutil.rmtree("./output/") # 能删除该文件夹和文件夹下所有文件
            if(mode_status == 1):#目标检测模式
                if(language == "chinese"):
                    wx.MessageBox('处理成功!请使用VoTT对处理后的图片进行手工标定。','信息', wx.OK | wx.ICON_INFORMATION)
                elif(language == "english"):
                    wx.MessageBox('Successful processing! Please use VoTT to manually calibrate the processed pictures.','Info', wx.OK | wx.ICON_INFORMATION)
            if(mode_status == 2):#目标检测(自动标注)模式
                if(language == "chinese"):
                    wx.MessageBox('处理成功!请上传对应压缩包至Maixhub进行训练。','信息', wx.OK | wx.ICON_INFORMATION)
                elif(language == "english"):
                    wx.MessageBox('Successful processing!Please upload the corresponding compressed package to Maixhub for training.','Info', wx.OK | wx.ICON_INFORMATION)
                print(Object_Detection_path_zip)
                createZip(Object_Detection_path,Object_Detection_path_zip)#打包zip有bug!!!
                shutil.rmtree(Object_Detection_path) # 能删除该文件夹和文件夹下所有文件
                os.system("explorer.exe %s" % "./".replace('/','\\'))#处理完成后打开目录
    elif(video_handel_flag == 1):#视频处理
        print("进入视频处理模式")
        print(avi_path_list,mp4_path_list)
        print(mp4_path_list[0].partition('\\'))
        #视频帧提取
        if(len(avi_path_list)):
            video_to_photo(avi_path_list)
        if(len(mp4_path_list)):
            video_to_photo(mp4_path_list)
        #删除视频文件
        for mp4_path in mp4_path_list:
            os.remove(mp4_path)
        for avi_path in avi_path_list:
            os.remove(avi_path)
        video_handel_flag = 0#进入图片处理模式
        if(language == "chinese"):
            log_text.AppendText("\n视频帧提取成功！请再次点击开始处理按钮")
        elif(language == "english"):
            log_text.AppendText("\nVideo frame extraction succeeded! Please click the start processing button again")        



###############################################################################
def createZip(filePath,savePath,note = ''):
    '''
    将文件夹下的文件保存到zip文件中。
    :param filePath: 待备份文件
    :param savePath: 备份路径
    :param note: 备份文件说明
    :return:
    '''
    today = time.strftime('%Y%m%d')
    now = time.strftime('%H%M%S')
    fileList=[]
    if len(note) == 0:
        target = savePath + "-" + today + "-" + now + '.zip'
    else:
        target = savePath + "-" + today + "-" + now + "-" + note + '.zip'
    newZip = zipfile.ZipFile(target,'w')
    for dirpath,dirnames,filenames in os.walk(filePath):
        for filename in filenames:
            fileList.append(os.path.join(dirpath,filename))
    for tar in fileList:
        newZip.write(tar,tar[len(filePath):])#tar为写入的文件，tar[len(filePath)]为保存的文件名
    newZip.close()
    #print('backup to',target)

###############################################################################
#文件夹选择事件
def opendir(event):
    global panel #父类窗口
    global dataset_path
    global classes
    global language
    if(language == "chinese"):
        dlg = wx.DirDialog(panel,"选择文件夹",style=wx.DD_DEFAULT_STYLE)
    elif(language == "english"):
        dlg = wx.DirDialog(panel,"Select folder",style=wx.DD_DEFAULT_STYLE)
    if dlg.ShowModal() == wx.ID_OK:
        path_text.SetValue(dlg.GetPath())
        dataset_path = dlg.GetPath().replace('\\','/')+"/"
        classes.clear()#清空上一次的标签名
    dlg.Destroy()
###############################################################################
#开始处理事件
def data_handel(event):
    global panel #父类窗口
    global dataset_path
    global classes
    global language

    lable_number = 0
    image_number_list = []
    if(dataset_path.strip()==''):
        if(language == "chinese"):
            wx.MessageBox('请先选择文件夹!','错误', wx.OK | wx.ICON_INFORMATION)
        elif(language == "english"):
            wx.MessageBox('Please select a folder first!','Error', wx.OK | wx.ICON_INFORMATION)
    else:
        classes.clear()#清空上一次的标签名
        if(language == "chinese"):
            log_text.SetValue("开始处理...")
        elif(language == "english"):
            log_text.SetValue("Start processing ...")
        lable_number = get_lable_number()
        if(language == "chinese"):
            log_text.AppendText("\n已发现"+str(lable_number)+"个标签文件夹")
        elif(language == "english"):
            log_text.AppendText("\nFound "+str(lable_number)+" label folder")
        #异常处理:标签文件夹数量不足2个
        if (lable_number < 1):
            pass
        else:
            image_number_list = get_image_number(classes)
            #print(image_number_list)
            if(image_number_list):#是否有标签文件夹图片少于40个/100
                if(language == "chinese"):
                    log_text.AppendText("\n错误：标签文件夹下图片数量应>=40张")
                elif(language == "english"):
                    log_text.AppendText("\nError:The number of pictures under the label folder should be> = 40")
            elif(image_number_list != 0):
                image_handel = Thread(target=convert_24bit_320_240)
                image_handel.start()  # 只是给操作系统发送了一个就绪信号，并不是执行。操作系统接收信号后安排cpu运行
                #convert_24bit_320_240()#将每个图片位深度转换为24bit，转换image_weight*image_hight分辨率


###############################################################################
#数据集预处理模式选择事件汇总
def mode_button_event(event):#模式确定按钮
    if(language == "chinese"):
        wx.MessageBox("已成功切换为"+ch1_list0[mode_status]+"模式.",'信息', wx.OK | wx.ICON_INFORMATION)
    elif(language == "english"):
        wx.MessageBox("Has successfully switched to "+ch1_list1[mode_status]+" mode.",'信息', wx.OK | wx.ICON_INFORMATION)
    log_text.Clear()#清空log文件夹
    if(mode_status == 0):
        if(language == "chinese"):
            log_text.SetValue("目标分类模式使用指南:\n"
                              +"第一步:点击“选择文件夹”按钮,选择需要进行数据集预处理的文件夹.(请注意，被选取的文件夹中应直接含有所有标签文件夹).\n"
                              +"第二步:点击“开始处理”按钮，软件将会开始自动处理数据集,请等待下方文本显示“处理成功！”字样.\n"
                              +"第三步:处理成功后,会在与软件根目录下生成以output+日期为前缀.ZIP压缩包,找到对应时间生成的压缩包，在maixhub选择|目标分类|训练类型，并将.zip压缩包上传进行训练.\n"
                              +"MaixHub地址:www.maixhub.com  QQ交流群:878189804\n"
                              +"\nPS:\n1.由于数据预处理占用CPU资源较高，软件运行过程中可能出现|未响应|，此现象为正常现象，请等待一段时间,方可完成处理.\n"
                              +"2.如果某些杀毒软件将本软件检测为病毒软件，请忽略此警告，并将本软件加入至杀毒软件白名单中.")
        elif(language == "english"):
            log_text.SetValue("Guidelines for using the target classification mode:\n"
                              +"Step 1: Click the 'Select Folder' button and select the folder that needs to be preprocessed for the data set. (Please note that the selected folder should contain all tag folders directly).\n"
                              +"Step 2: Click the 'Start Processing' button, the software will automatically process the data set, please wait for the text below to display 'Finish!'.\n"
                              +"Step 3: After the processing is successful, a .ZIP compressed package with the output + date as the prefix will be generated in the root directory of the software, find the compressed package generated at the corresponding time, select | Classification | training type in maixhub, and upload the .zip compressed package for training.\n"
                              +"MaixHub:www.maixhub.com\n"
                              +"\nPS:\n1.Because the data preprocessing consumes high CPU resources, it may appear during the software operation | Not responding | This phenomenon is normal, please wait for a period of time to complete the processing.\n"
                              +"2.If some anti-virus software detects this software as virus software, please ignore this warning and add this software to the white list of anti-virus software.")
    elif(mode_status == 1):
        if(language == "chinese"):
            log_text.SetValue("目标检测模式使用指南:\n"
                              +"第一步:点击“选择文件夹”按钮,选择需要进行数据集预处理的文件夹.(请注意，被选取的文件夹中应直接含有所有标签文件夹).\n"
                              +"第二步:点击“开始处理”按钮，软件将会开始自动处理数据集,请等待下方文本显示“处理成功！”字样.\n"
                              +"第三步:处理成功后,会在与软件根目录下生成名为[Object_Detection+日期]的文件夹,用VoTT软件处理此文件夹.\n"
                              +"第四步:用VoTT标定完所有数据集后，在VoTT中导出TFRecord文件.\n"
                              +"第五步:创建一个非中文命名的文件夹，并将所有TFRecord文件放在其中.(应包含tf_label_map.pbtxt文件)\n"
                              +"第六步:将刚刚的文件夹压缩成.zip格式，在maixhub选择|目标检测|训练类型,并将.zip压缩包上传进行训练.\n"
                              +"MaixHub地址:www.maixhub.com  QQ交流群:878189804\n"
                              +"\nPS:\n1.由于数据预处理占用CPU资源较高，软件运行过程中可能出现|未响应|，此现象为正常现象，请等待一段时间,方可完成处理.\n"
                              +"2.如果某些杀毒软件将本软件检测为病毒软件，请忽略此警告，并将本软件加入至杀毒软件白名单中.")
        elif(language == "english"):
            log_text.SetValue("Guidelines for using the target Object Detection mode:\n"
                              +"Step 1: Click the 'Select Folder' button and select the folder that needs to be preprocessed for the data set. (Please note that the selected folder should contain all tag folders directly).\n"
                              +"Step 2: Click the 'Start Processing' button, the software will automatically process the data set, please wait for the text below to display 'Finish!'.\n"
                              +"Step 3: After the processing is successful, a folder named [Object_Detection+date] will be generated in the root directory of the software and processed with VoTT software.\n"
                              +"Step 4: After calibrating all data sets with VoTT, export the TFRecord file in VoTT."
                              +"Step 5: Create a non-Chinese named folder and place all TFRecord files in it.(Include tf_label_map.pbtxt file)"
                              +"Step 6: Compress the folder just now into .zip format, select | Object Detection | training type in maixhub, and upload the .zip compressed package for training."
                              +"MaixHub:www.maixhub.com\n"
                              +"\nPS:\n1.Because the data preprocessing consumes high CPU resources, it may appear during the software operation | Not responding | This phenomenon is normal, please wait for a period of time to complete the processing.\n"
                              +"2.If some anti-virus software detects this software as virus software, please ignore this warning and add this software to the white list of anti-virus software.")
    
    elif(mode_status == 2):
        if(language == "chinese"):
            log_text.SetValue("目标检测(自动标注)模式使用指南:\n"
                              +"第一步:点击“选择文件夹”按钮,选择需要进行数据集预处理的文件夹.(请注意，被选取的文件夹中应直接含有所有标签文件夹，标签文件夹中的文件可以为图片,可以为视频).\n"
                              +"第二步:点击“开始处理”按钮，软件将会开始自动处理数据集,请等待下方文本显示“处理成功！”字样.\n"
                              +"第三步:在处理过程中，软件会弹出窗口，请在弹出窗口中，长按鼠标左键将目标框出，并按回车键.\n"
                              +"第四步:处理成功后,会在与软件根目录下生成以[Object_Detection+日期]为前缀.ZIP压缩包,找到对应时间生成的压缩包，在maixhub选择|目标检测|训练类型，并将.zip压缩包上传进行训练.\n"
                              +"MaixHub地址:www.maixhub.com  QQ交流群:878189804\n"
                              +"\nPS:\n1.由于数据预处理占用CPU资源较高，软件运行过程中可能出现|未响应|，此现象为正常现象，请等待一段时间,方可完成处理.\n"
                              +"2.如果某些杀毒软件将本软件检测为病毒软件，请忽略此警告，并将本软件加入至杀毒软件白名单中.\n"
                              +"3.标签文件夹中的文件，若为图片，推荐使用基于maixpy的k210目标检测数据集收集脚本进行收集，以保证自动标注的准确性.若为视频，建议使用.mp4格式.\n"
                              +"4.手机录制时，建议设置为mp4/avi(1080P|30FPS),每类目标录制20秒左右\n"
                              +"5.软件会自动删除数据集中的视频文件，请做好备份")
        elif(language == "english"):
            log_text.SetValue("Guidelines for using the target Object Detection(auto label) mode:\n"
                              +"Step 1: Click the 'Select Folder' button to select the folder that requires data set preprocessing. (Please note that the selected folder should directly contain all label folders, and the files in the label folder can be pictures , Can be a video).\n"
                              +"Step 2: Click the 'Start Processing' button, the software will automatically process the data set, please wait for the text below to display 'Finish!'.\n"
                              +"Step 3: During the processing, the software will pop up a window. In the pop-up window, long-press the left mouse button to frame the target and press the Enter key.\n"
                              +"Step 4: After the processing is successful, a .ZIP compressed package with the [Object_Detection+date] as the prefix will be generated in the root directory of the software, find the compressed package generated at the corresponding time, select |Object Detection| training type in maixhub, and the .zip compressed package Upload for training."
                              +"MaixHub:www.maixhub.com\n"
                              +"\nPS:\n1.Because the data preprocessing consumes high CPU resources, it may appear during the software operation | Not responding | This phenomenon is normal, please wait for a period of time to complete the processing.\n"
                              +"2.If some anti-virus software detects this software as virus software, please ignore this warning and add this software to the white list of anti-virus software.\n"
                              +"3.If the files in the tag folder are pictures, it is recommended to use the maixpy-based k210 target detection data set collection script to collect to ensure the accuracy of automatic annotation. If it is a video, it is recommended to use the .mp4 format.\n"
                              +"4.When recording on a mobile phone, it is recommended to set to mp4 / avi (1080P | 30FPS), and each type of target is recorded for about 20 seconds.\n"
                              +"5.The software will automatically delete the video files in the data set, please make a backup")
def ch1_event(event):#模式选择框
    global mode_status
    print("选择{0}".format(event.GetString()))
    if(language == "chinese"):
        if(event.GetString() == ch1_list0[0]):
            mode_status = 0
        elif(event.GetString() == ch1_list0[1]):
            mode_status = 1
        elif(event.GetString() == ch1_list0[2]):
            mode_status = 2
    elif(language == "english"):
        if(event.GetString() == ch1_list1[0]):
            mode_status = 0
        elif(event.GetString() == ch1_list1[1]):
            mode_status = 1
        elif(event.GetString() == ch1_list1[2]):
            mode_status = 2
############################################################################### 
#窗体实例化
app = wx.App()
#不同语言 窗体大小不同
if(language == "chinese"):
    frame = wx.Frame(None,title = "DataAssistantV1.2-Press F9 to switch languages",pos = (1000,200),size = (500,400))
elif(language == "english"):
    frame = wx.Frame(None,title = "DataAssistantV1.2-Press F9 to switch languages",pos = (1000,200),size = (600,400))
panel = wx.Panel(frame)
#Sipeed图标
frame.icon1=wx.Icon(name="sipeed.ico",type=wx.BITMAP_TYPE_ICO)
frame.SetIcon(frame.icon1)
#组件实例化
#创建静态文本
if(language == "chinese"):
    statictext=wx.StaticText(panel,label='请选择数据集预处理模式：')
    ch1=wx.ComboBox(panel,-1,value='目标分类',choices=ch1_list0,style=wx.CB_SORT|wx.TE_READONLY)
    mode_button = wx.Button(panel,label = "确定")
    mode_button.Bind(wx.EVT_BUTTON,mode_button_event)# 绑定打开文件事件到open_dir按钮上
    ch1.Bind(wx.EVT_COMBOBOX,ch1_event)
elif(language == "english"):
    statictext=wx.StaticText(panel,label='Please select the data set preprocessing mode:')
    ch1=wx.ComboBox(panel,-1,value='classification',choices=ch1_list1,style=wx.CB_SORT|wx.TE_READONLY)
    mode_button = wx.Button(panel,label = "OK")
    mode_button.Bind(wx.EVT_BUTTON,mode_button_event)# 绑定打开文件事件到open_dir按钮上
    ch1.Bind(wx.EVT_COMBOBOX,ch1_event)

path_text = wx.TextCtrl(panel,style = wx.TE_READONLY)
log_text = wx.TextCtrl(panel,style = wx.TE_MULTILINE|wx.TE_READONLY)
if(language == "chinese"):
    open_dir_button = wx.Button(panel,label = "选择文件夹")
elif(language == "english"):
    open_dir_button = wx.Button(panel,label = "Select folder")
open_dir_button.Bind(wx.EVT_BUTTON,opendir)# 绑定打开文件事件到open_dir按钮上
if(language == "chinese"):
    handel_button = wx.Button(panel,label = "开始处理")
elif(language == "english"):
    handel_button = wx.Button(panel,label = "Start processing")
handel_button.Bind(wx.EVT_BUTTON,data_handel)# 绑定打开文件事件到open_dir按钮上
#键盘事件绑定在所有控件上
frame.Bind(wx.EVT_KEY_DOWN,F9_down)#窗体
panel.Bind(wx.EVT_KEY_DOWN,F9_down)#窗体
path_text.Bind(wx.EVT_KEY_DOWN,F9_down)
log_text.Bind(wx.EVT_KEY_DOWN,F9_down)
open_dir_button.Bind(wx.EVT_KEY_DOWN,F9_down)
handel_button.Bind(wx.EVT_KEY_DOWN,F9_down)
statictext.Bind(wx.EVT_KEY_DOWN,F9_down)
ch1.Bind(wx.EVT_KEY_DOWN,F9_down)
mode_button.Bind(wx.EVT_KEY_DOWN,F9_down)
frame.SetFocus()#获得焦点，否则语言切换按钮无效
#显示软件教程
if(language == "chinese"):
    log_text.SetValue("欢迎使用DataAssistantV1.2\n"
                          +"本软件用于进行神经网络模型训练前的数据集预处理.\n"
                          +"使用指南:\n"
                          +"第一步:选择选择数据集预处理模式，并按下确定按钮.\n"
                          +"第二步:软件将会根据不同的数据集预处理模式，给出相应的使用指南.\n"
                          +"MaixHub地址:www.maixhub.com  QQ交流群:878189804\n"
                          +"\nPS:\n1.由于数据预处理占用CPU资源较高，软件运行过程中可能出现|未响应|，此现象为正常现象，请等待一段时间,方可完成处理.\n"
                          +"2.如果某些杀毒软件将本软件检测为病毒软件，请忽略此警告，并将本软件加入至杀毒软件白名单中.")
elif(language == "english"):
   log_text.SetValue("Welcome to DataAssistantV1.1\n"
                          +"This software is used to preprocess the data set before the neural network model training.\n"
                          +"User's guidance:\n"
                          +"Step 1:Select the data set pre-processing mode and press the OK button.\n"
                          +"Step 2: The software will give corresponding usage guidelines according to different data set preprocessing modes.\n"
                          +"MaixHub:www.maixhub.com\n"
                          +"\nPS:\n1.Because the data preprocessing consumes high CPU resources, it may appear during the software operation | Not responding | This phenomenon is normal, please wait for a period of time to complete the processing.\n"
                          +"2.If some anti-virus software detects this software as virus software, please ignore this warning and add this software to the white list of anti-virus software.")


box1 = wx.BoxSizer() # 不带参数表示默认实例化一个水平尺寸器
box1.Add(statictext,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 5) # 添加组件
box1.Add(ch1,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 5) # 添加组件
box1.Add(mode_button,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 5) # 添加组件

box = wx.BoxSizer() # 不带参数表示默认实例化一个水平尺寸器
box.Add(path_text,proportion = 5,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
    #proportion：相对比例
    #flag：填充的样式和方向,wx.EXPAND为完整填充，wx.ALL为填充的方向
    #border：边框
box.Add(open_dir_button,proportion = 2,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
box.Add(handel_button,proportion = 2,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
v_box = wx.BoxSizer(wx.VERTICAL) # wx.VERTICAL参数表示实例化一个垂直尺寸器
v_box.Add(box1,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
v_box.Add(box,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
v_box.Add(log_text,proportion = 5,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
panel.SetSizer(v_box) # 设置主尺寸器
frame.Show()
app.MainLoop()
