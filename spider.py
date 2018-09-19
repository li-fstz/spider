import requests
from bs4 import BeautifulSoup
import re
import time
import json
import html
import sys
import configparser
import getpass

def login (name, password, cookies = ''):
    s = requests.session ()
    if (cookies):
        s.cookies.set ('XH', name)
        s.cookies.set ('ASP.NET_SessionId', cookies, domain = '222.27.192.13', path = '/')
        r = s.get ('http://222.27.192.13/WLSYJXGL/XSYW_XueShengDaiXuanShiYanXiangMU.aspx')
        soup = BeautifulSoup (r.text, "html.parser")
        if (soup.find ('title').text == '待选实验课'):
            print ('Cookies Login Success')
            return s
        else:
            return login (name,password)
    else:
        url = "http://222.27.192.13/SJZCPT/DLGL/LoginSign.aspx?Name=%s&Password=%s&jueSe=2&flag=login" % (name, password)
        r = s.post (url)
        if r.text == 'success':
            print ('Password Login Success')
            s.cookies.set ('XH', name)
            return s
        else:
            return None

def choice (s):
    r = s.get ('http://222.27.192.13/WLSYJXGL/XSYW_XueShengDaiXuanShiYanXiangMU.aspx')
    soup = BeautifulSoup (r.text, "html.parser")
    XueQi_ID = soup.find ('input', id = 'hf_XueQi_ID')['value']
    XS_ID = soup.find ('input', id = 'hf_XS_ID')['value']
    data = {
        's': time.strftime ('%a %b %d %Y %X', time.localtime()) + ' GMT 0800 (中国标准时间)',
        'tbx_XMMC': '',
        'tbx_XMBH': '',
        'hf_XueQi_ID': XueQi_ID,
        'hf_XS_ID': XS_ID,
        'hf_DivSearch': 'TRUE',
        'page': '1',
        'rows': '20',
    }
    r = s.get ('http://222.27.192.13/WLSYJXGL/ajax/GetDaiXuanKeChengDt.aspx', data = data)

    d = json.loads (r.text)
    allData = []
    cnt = 0
    for i in d['rows']:
        data = {
            'XM_ID': i['XM_ID'],
            'XueQi_ID': XueQi_ID,
            'XS_ID': XS_ID,
        }
        r = s.post ('http://222.27.192.13/WLSYJXGL/ajax/GetXueShengXuanKePiCiAJAX.aspx', data = data)
        text = html.unescape (r.text)
        it = re.finditer (r'<b>指导教师：</b>(.{1,5})\s+.{30,50}<b>地点：</b>(.{10,40})\s+<b>时间：</b>(.{10,40})<(br|BR)></td><td>(\d+)</td><td>(\d+)</td><td>(\d+)</td><td>((<p style=\'color:red\'>已满</p>)|(<a.{70,80}【选课】</a>))', text)
        for match in it: 
            if (match.group(7) != match.group(5)):
                cnt += 1
                print (cnt, i['XM_MingCheng'])
                print (match.group(1), match.group(2), match.group(3))
                sch = re.search (r'XuanKeClick\((\d+),(\d+),(\d+),(\d+)\)', match.group(8))
                data = {
                    'SYJXZ_ID': sch.group(2),
                    'XS_ID': XS_ID,
                    'XH': s.cookies['XH'],
                    'yiXuan': sch.group(3),
                    'xiaXian': sch.group(4),
                }
                allData.append (data)
    if (cnt == 0):
        print ('暂时没有可选课程')
    else:
        id = int (input ("请输入序号：")) - 1
        if (id > cnt - 1):
            print ('输入错误')
            exit ()
        r = s.post ('http://222.27.192.13/WLSYJXGL/ajax/XuanKeByXS_ID.aspx', data=allData[id])
        if (r.text == '1'):
            print ('选课成功')
        else:
            print ('选课失败')

config = configparser.ConfigParser()
config.read ('config.ini')
s = None
if (not 'spider' in config):
    name = input ('请输入学号：')
    password = getpass.getpass ('请输入密码：')
    s = login (name, password)
    if (s == None):
        print ('学号或密码错误！')
        exit ()
    else:
        config.read_dict ({'spider': {
                                'name': name, 
                                'password': password, 
                                'cookies': s.cookies['ASP.NET_SessionId'],
                            }})
        with open ('config.ini', 'w') as f:
            config.write (f)
else:
    s = login (config['spider']['name'], config['spider']['password'], config['spider']['cookies'])
    if (s == None):
        print ('学号或密码错误！')
        config.remove_section ('spider')
        with open ('config.ini', 'w') as f:
            config.write (f)
        exit ()
    else:
        config['spider']['cookies'] = s.cookies['ASP.NET_SessionId']
        with open ('config.ini', 'w') as f:
            config.write (f)
choice (s)