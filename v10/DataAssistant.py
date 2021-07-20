#coding:utf-8
import wx
import os
from PIL import Image
import configparser
import os,time,zipfile
import shutil
cfgpath = "config.ini" ##配置文件
dataset_path =""#处理根目录
classes = [] #所有标签名
classes_path = [] #所有标签路径
output_path = './output/output/'#转换后图片的目录

image_weight = 0 #转换后的宽度
image_hight = 0 #转换后的高度
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
                elif(language == "english"):
                    wx.MessageBox("/"+filename+'||Label folder cannot contain Chinese', 'Error', wx.OK | wx.ICON_INFORMATION)
            else:
                classes.append(str(filename))
            lable = lable + 1
        else:
            if(language == "chinese"):
                wx.MessageBox("/"+filename+'不是一个文件夹', '错误', wx.OK | wx.ICON_INFORMATION)
            elif(language == "english"):
                wx.MessageBox("/"+filename+'||Not a folder', 'Error', wx.OK | wx.ICON_INFORMATION)            
    #异常处理:标签文件夹小于2个
    if(lable <2):
        if(language == "chinese"):
            wx.MessageBox('标签文件夹数量需要大于2个','错误', wx.OK | wx.ICON_INFORMATION)
        elif(language == "english"):
            wx.MessageBox('The number of label folders needs to be greater than 2','Error', wx.OK | wx.ICON_INFORMATION)
    return lable
###############################################################################
def get_image_number(classes):#获取每个标签下图片数目
    global dataset_path
    global classes_path
    global language

    image_number = 0
    image_number_list = []
    for class_name in classes:#所有标签目录遍历
        image_number = 0
        class_path = dataset_path + class_name + '/'
        classes_path.append(class_path+"/")
        for img_name in os.listdir(class_path): #一个标签目录下所有图片遍历#class_path
            image_number = image_number + 1
        if(image_number <40):
            if(language == "chinese"):
                wx.MessageBox("/"+class_name+'标签文件夹下图片数量应>=40张','错误', wx.OK | wx.ICON_INFORMATION)
            elif(language == "english"):
                wx.MessageBox("/"+class_name+'||The number of pictures under the label folder should be> = 40','Error', wx.OK | wx.ICON_INFORMATION)
            image_number_list.append(image_number)
    return image_number_list
###############################################################################
def process_image(image,mwidth=image_weight, mheight=image_hight):#等比例处理图片，长宽比4:3
    w,h = image.size
    #print(w,h,mwidth,mheight)
    if w<=mwidth and h<=mheight:
        #print(filename,'is OK.')
        if(w<h):#竖屏图片
            image = image.transpose(Image.ROTATE_90)   # 引用固定的常量值
            return image
        else :
            return image
    if (1.0*w/mwidth) > (1.0*h/mheight):
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
    #自适应填充黑色
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
###############################################################################
def convert_24bit_320_240():#将每个图片位深度转换为24bit，分辨率转为QVGA320*240
    global dataset_path
    global classes
    global image_weight,image_hight
    global language
    broken_flag = 0#文件破损
    i = 0
    try :
        for class_name in classes:#class_name:文件夹标签名
            class_path = dataset_path + class_name + '/'
            print(class_path)
            for img_name in os.listdir(class_path): #图片实例名
                img_path = class_path + img_name #每一个图片的地址 
                print(img_path)
                img = Image.open(img_path).convert('RGB')#转为24bit
                img = process_image(img)#等比例转换为
                #img = img.resize((image_weight,image_hight))#转换image_weight*image_hight分辨率
                file_name, file_extend = os.path.splitext(img_name)#获取文件名     
                if os.path.exists(output_path + class_name + '/') is False:#不存在目录则创建
                    os.makedirs(output_path + class_name + '/')
                new_image_path = os.path.join(os.path.abspath(output_path + class_name + '/'), file_name + '.jpg')
                img.save(new_image_path)
                i = i + 1
                if(language == "chinese"):
                    log_text.AppendText("\n已处理"+str(i)+"张图片...")
                elif(language == "english"):
                    log_text.AppendText("\n"+str(i)+"pictures processed...")
    except :
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
        #os.system("explorer.exe %s" % output_path.replace('/','\\'))#处理完成后打开目录
        os.system("explorer.exe %s" % "./".replace('/','\\'))#处理完成后打开目录
        createZip("./output/","./output")
        shutil.rmtree("./output/") # 能删除该文件夹和文件夹下所有文件
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
            log_text.AppendText("\nFound"+str(lable_number)+"label folder")
        #异常处理:标签文件夹数量不足2个
        if (lable_number < 2):
            pass
        else:
            image_number_list = get_image_number(classes)
            if(image_number_list):#是否有标签文件夹图片少于40个
                if(language == "chinese"):
                    log_text.AppendText("\n错误：标签文件夹下图片数量应>=40张")
                elif(language == "english"):
                    log_text.AppendText("\nError:The number of pictures under the label folder should be> = 40")
            else:
                convert_24bit_320_240()#将每个图片位深度转换为24bit，转换image_weight*image_hight分辨率


###############################################################################
#语言切换事件

############################################################################### 
#窗体实例化
app = wx.App()
frame = wx.Frame(None,title = "DataAssistantV1.0-Press F9 to switch languages",pos = (1000,200),size = (500,400))
panel = wx.Panel(frame)
#Sipeed图标
frame.icon1=wx.Icon(name="sipeed.ico",type=wx.BITMAP_TYPE_ICO)
frame.SetIcon(frame.icon1)
#组件实例化
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
frame.SetFocus()#获得焦点，否则语言切换按钮无效
#显示软件教程
if(language == "chinese"):
    log_text.SetValue("欢迎使用DataAssistantV1.0\n"
                          +"本软件用于进行神经网络模型训练前的数据集预处理.\n"
                          +"使用指南:\n"
                          +"第一步:点击“选择文件夹”按钮,选择需要进行数据集预处理的文件夹.(请注意，被选取的文件夹中应直接含有所有标签文件夹).\n"
                          +"第二步:点击“开始处理”按钮，软件将会开始自动处理数据集,请等待下方文本显示“处理成功！”字样.\n"
                          +"第三步:处理成功后,会在与软件根目录下生成以output+日期为前缀.ZIP压缩包,找到对应时间生成的压缩包，将此压缩包上传MaixHub即可开始训练.\n"
                          +"MaixHub地址:www.maixhub.com  QQ交流群:878189804\n"
                          +"\nPS:\n1.由于数据预处理占用CPU资源较高，软件运行过程中可能出现|未响应|，此现象为正常现象，请等待一段时间,方可完成处理.\n"
                          +"2.如果某些杀毒软件将本软件检测为病毒软件，请忽略此警告，并将本软件加入至杀毒软件白名单中.")
elif(language == "english"):
   log_text.SetValue("Welcome to DataAssistantV1.0\n"
                          +"This software is used to preprocess the data set before the neural network model training.\n"
                          +"User's guidance:\n"
                          +"Step 1: Click the 'Select Folder' button and select the folder that needs to be preprocessed for the data set. (Please note that the selected folder should contain all tag folders directly).\n"
                          +"Step 2: Click the 'Start Processing' button, the software will automatically process the data set, please wait for the text below to display 'Finish!'.\n"
                          +"Step 3: After processing is successful, a ZIP archive with output + date as the prefix will be generated in the root directory of the software. Find the archive generated at the corresponding time. Upload this archive to MaixHub to start training.\n"
                          +"MaixHub:www.maixhub.com\n"
                          +"\nPS:\n1.Because the data preprocessing consumes high CPU resources, it may appear during the software operation | Not responding | This phenomenon is normal, please wait for a period of time to complete the processing\n"
                          +"2.If some anti-virus software detects this software as virus software, please ignore this warning and add this software to the white list of anti-virus software.")
 
box = wx.BoxSizer() # 不带参数表示默认实例化一个水平尺寸器
box.Add(path_text,proportion = 5,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
    #proportion：相对比例
    #flag：填充的样式和方向,wx.EXPAND为完整填充，wx.ALL为填充的方向
    #border：边框
box.Add(open_dir_button,proportion = 2,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
box.Add(handel_button,proportion = 2,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
v_box = wx.BoxSizer(wx.VERTICAL) # wx.VERTICAL参数表示实例化一个垂直尺寸器
v_box.Add(box,proportion = 1,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
v_box.Add(log_text,proportion = 5,flag = wx.EXPAND|wx.ALL,border = 3) # 添加组件
panel.SetSizer(v_box) # 设置主尺寸器
frame.Show()
app.MainLoop()
