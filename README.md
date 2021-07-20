# `DataAssitant`项目说明
## 项目背景
大二在sipeed实习(3月-7月)时所编著，因为Maxihub后端自动训练脚本也是我在开发，所以编写一个能够规范产出数据集的预处理软件非常重要。大大提高用户使用Maixhub时的使用体验。
## 开发环境建立
```bash
conda create -n dataassitant python=3.7.4
conda activate dataassitant
pip install -r requirements.txt
```
---
## 代码运行
```bash
python DataAssistant.py
```
---
## 打包为.exe文件
### 打包工具版本
```
pyinstaller==3.6
```
### 打包命令
```python
pyinstaller -F -w -i sipeed.ico DataAssistant.py
```
### PS👀️ 
0. 打包请在纯净python环境下进行，否则将会有很多不必要的第三方包被打包，从而导致生成的.exe文件过大
1. 打包目录下需要包含如下文件：
> 1. DataAssistant.py
> 2. sipeed.ico
> 3. config.ini
---
## 版本特性说明：
> V1.0 :支持目标分类数据集的预处理

> V1.1 :新增目标检测数据集预处理

> V1.2 :新增目标检测数据集预自动标注(Siammask)
---
## Bug汇总：
- [x] 处理中程序出现未响应.(解决方案:新进程解决)
- [ ]仅支持在Windows10以下运行(实测windows7无法运行)
---
## 打包好的zip下载:
本项目 Release页面




