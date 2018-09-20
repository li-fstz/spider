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
        if (r.text == 'success'):
            print ('Password Login Success')
            s.cookies.set ('XH', name)
            return s
        else:
            return None

def search (s):
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
                print (len(allData) + 1, i['XM_MingCheng'])
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
    if (len (allData) == 0):
        print ('暂时没有可选课程')
        exit ()
    return allData

def load (user = 'spider'):
    config = configparser.ConfigParser()
    config.read ('config.ini')
    s = None
    if (not user in config):
        print ('新建账户 - %s' % user)
        name = input ('请输入学号：')
        password = getpass.getpass ('请输入密码：')
        s = login (name, password)
        if (s == None):
            print ('学号或密码错误！')
            exit ()
        else:
            config.read_dict ({user: {
                                    'name': name, 
                                    'password': password, 
                                    'cookies': s.cookies['ASP.NET_SessionId'],
                                }})
            with open ('config.ini', 'w') as f:
                config.write (f)
    else:
        s = login (config[user]['name'], config[user]['password'], config[user]['cookies'])
        if (s == None):
            print ('学号或密码错误，%s 账户信息无效，以被删除！' % user)
            config.remove_section (user)
            with open ('config.ini', 'w') as f:
                config.write (f)
            exit ()
        else:
            config[user]['cookies'] = s.cookies['ASP.NET_SessionId']
            with open ('config.ini', 'w') as f:
                config.write (f)
    return s

def choice (s, data):
    id = int (input ("请输入序号（输入0取消选课）："))
    if (id > len(data) or id < 0):
        print ('输入错误')
        exit ()
    elif (id == 0):
        print ('取消选课')
        exit ()
    r = s.post ('http://222.27.192.13/WLSYJXGL/ajax/XuanKeByXS_ID.aspx', data = data[id - 1])
    if (r.text == '1'):
        print ('选课成功')
    else:
        print ('选课失败')

if (len (sys.argv) == 1 or sys.argv[1] == 'spider'):
    print ('查询模式 - 使用 spider 账户')
    s = load ()
    search (s)
else:
    print ('选课模式 - 使用 %s 账户' % sys.argv[1])
    s = load (sys.argv[1])
    data = search (s)
    choice (s, data)