#本程序用于使用Maixpy系列开发板进行图像数据收集
#使用方法:
#0.为Maixpy系列开发板插入一张TF卡
#1.将本程序烧入Maixpy系列开发板中，上电运行
#2.阅读用户说明后，按下BOOT按钮进行拍照，LCD屏左下角会显示当前存储目录
#3.拍照后的图片默认存储在TF卡目录./0/下面，拍摄成功后，会在LCD屏正下方显示"OK！"字样
#长按BOOT按钮可切换拍照后图片的默认存储路径(默认支持./1/~./10/，也就是十分类，如有其他需求，请修改Classes_num变量)
#4.完成所有分类的图像采集后，将TF卡中的数据移动到电脑上，并自行按需修改存储图片的文件夹名称(标签名），
#并删除没有用到的标签文件夹
#5.用DataAssitant数据集与处理软件进行处理。
#6.将得到的.zip压缩文件上传MaixHub进行训练。
#PS:
#DataAssitant数据集与处理软件下载地址:
#https://cdn.sipeed.com/donwload/12kj346465hjkv68g7c/DataAssitantV1.0.zip
#数据集收集教程:https://www.maixhub.com/index.php/index/mtrain/help.html
##################################################################################
#This program is used for image data collection using Maixpy ​​series development boards#Instructions:
# 0. Insert a TF card for Maixpy ​​series development board
# 1. Burn the program into the Maixpy ​​series development board and power on
# 2. After reading the user's instructions, press the BOOT button to take a picture,
#    the current storage directory will be displayed in the lower left corner of the LCD screen
# 3. The picture after taking the picture is stored in the TF card directory by default.
#    Long press the BOOT button to switch the default storage path of pictures after taking pictures
#    (default supports ./1/~./10/, which is very class, if you have other needs, please modify the Classes_num variable)
# 4. After completing the collection of all the classified images, move the data in the TF card to the computer,
#    and modify the folder name (tag name) where the pictures are stored as needed,
#    And delete unused tag folders# 5. Use DataAssitant dataset and processing software for processing.
# 6. Upload the obtained .zip compressed file to MaixHub for training.
#PS:
#DataAssitantDataset and processing software download address:
#https: //cdn.sipeed.com/donwload/12kj346465hjkv68g7c/DataAssitantV1.0.zip
#Dataset Collection Tutorial: https://www.maixhub.com/index.php/index/mtrain/help.html
##################################################################################
import sensor, image, time, lcd
import utime
import uos
import sys
from Maix import GPIO
from board import board_info
from fpioa_manager import fm
##################################################################################
Classes_num = 10 #十分类(10个标签文件夹)|Tier 10 (10 tag folders)
##################################################################################
bg = lcd.RED
text = lcd.WHITE
boot_press_flag = 1
start = time.ticks_ms()
end = time.ticks_ms()
ui_num = 0
image_save_path = "/sd/image/"#图片保存目录头
claass = 0#文件夹名
image_num = 0#图像文件保存名
#完整图片保存路径image_save_path+claass+"/"
image_data = image.Image()#图像
shoot_flag = 0
##################################################################################
def boot_key_irq(pin_num):#
    global ui_num
    global boot_press_flag,start,end
    global claass
    global image_num
    global shoot_flag
    #utime.sleep_ms(100)
    if(boot_press_flag == 1):
        start = time.ticks_ms()
        boot_press_flag = 0
    elif(boot_press_flag == 0):
        end = time.ticks_ms()
        boot_press_flag = 1
        time_diff = time.ticks_diff(end, start)
        if(time_diff >120 and time_diff <500):
            print("短按拍摄",time_diff)
            ui_num = 1
            if(ui_num == 1):#已进入拍摄
                image_num = image_num + 1
                #shoot_flag = 1
                image_data.save("/sd/image/"+str(claass)+"/"+str(utime.ticks_us())+str(image_num)+".jpg")
                lcd.draw_string(160, 224,"ok!"+str(image_num))
                utime.sleep_ms(500)
                #print(str(utime.ticks_us()))
        elif(time_diff >=500 and time_diff <=2000):
            print("长按切换文件夹",time_diff)
            if(ui_num == 1):#已进入拍摄
                claass = claass + 1
                if(claass >Classes_num-1):#让保存路径始终有效
                    claass = 0
        elif():
            boot_press_flag = 1
            start = 0
            end = 0
    #print("key", pin_num)

fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)
boot_key=GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_UP)
boot_key.irq(boot_key_irq, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)
##################################################################################
def draw_help_ui():#显示帮助页面
    lcd.draw_string(60, 10, "Data Collection Assistant", text, bg)
    lcd.draw_string(20, 30, "1.Press the BOOT button to take a pi-", text, bg)
    lcd.draw_string(10, 50, "cture. The current storage directory", text, bg)
    lcd.draw_string(10, 70, "will be displayed in the lower left corner of the LCD screen.", text, bg)
    lcd.draw_string(10, 90, "corner of the LCD screen.", text, bg)

    lcd.draw_string(20, 120, "2.Long press BOOT button to switch ", text, bg)
    lcd.draw_string(10, 140, "the default storage folder path of pi-", text, bg)
    lcd.draw_string(10, 160, "ctures after taking photos.", text, bg)
    lcd.draw_string(10, 200, "--Press the BOOT button to start shoot", text, bg)
##################################################################################
def not_found_tf():#没有找到TF卡
    lcd.clear(bg)
    lcd.draw_string(10, 90, "ERROR: ", text, bg)
    lcd.draw_string(20, 110, "No TF card found", text, bg)
    lcd.draw_string(20, 130, "The Reason:", text, bg)
    lcd.draw_string(20, 150, "1.No TF card inserted", text, bg)
    lcd.draw_string(20, 170, "2.TF card model is not supported", text, bg)
    lcd.draw_string(20, 190, "3.TF card format is not FAT", text, bg)
##################################################################################
def init():#初始化相关
    i = 0
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time = 2000)
    sensor.set_vflip(1)
    sensor.run(1)
    lcd.init(type=1, freq=15000000, color=bg)
    try:
        uos.mkdir("/sd/image")#创建image文件夹，顺路TF卡检测
        for i in range(Classes_num):
            uos.mkdir("/sd/image/"+str(i))#创建image/1-10文件夹，顺路TF卡检测
            print("/sd/image/"+str(i))
    except Exception as e:
        if(str(e) == "[Errno 17] EEXIST"):
            pass
        else:
            not_found_tf()
            sys.exit(0)
    finally:
        try:
            for i in range(Classes_num):
                uos.mkdir("/sd/image/"+str(i))#创建image/1-10文件夹，顺路TF卡检测
                #print("/sd/image/"+str(i))
                lcd.draw_string(0, 224,str(claass))
        except Exception as e:
                if(str(e) == "[Errno 17] EEXIST"):
                    pass
                else:
                    not_found_tf()
                    sys.exit(0)
    draw_help_ui()
##################################################################################
def image_ui():
    global image_data
    image_data = sensor.snapshot()         # Take a picture and return the image.
    lcd.display(image_data,oft=(0,0))                # Display on LCD
    lcd.draw_string(0, 224,"/sd/image/"+str(claass)+"/")
##################################################################################
def main():#主函数
    init()
    while(True):
        if(ui_num == 1):
            image_ui()

if __name__ == '__main__':
    try:
        main()
    except:
        lcd.clear(bg)
        lcd.draw_string(10, 90, "ERROR:unknown mistake", text, bg)
        lcd.draw_string(20, 110, "Please contact sipeed for help.", text, bg)
