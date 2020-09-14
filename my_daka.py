# -*- coding = utf-8 -*-
# @Time : 2020/8/30 13:39
# @Author : luohx
# @File : my_daka.py
# @Software: PyCharm

import time
import pytz
import smtplib
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from email.header import Header
from email.mime.text import MIMEText

from verification_code import VerificationCode


class DaKa:
    def __init__(self, reg_url, user_info):
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        self.user_info = user_info
        self.reg_url = reg_url
        # self.driver = webdriver.Chrome(options=chrome_options)  # 窗口不弹出
        self.driver = webdriver.Chrome()

    def login(self):
        login_result = False
        self.driver.get(self.reg_url)  # 打开登录界面，需要关掉电脑的代理设置
        time.sleep(4)

        self.driver.save_screenshot('pictures.png')
        ver_code_pos = (1388, 291, 1505, 333)  # 验证码位置(left,top,right,bottom)，需根据自己的屏幕分辨率调整截图位置
        ver_code = VerificationCode('pictures.png', ver_code_pos)
        uid = self.user_info['uid']
        pwd = self.user_info['pwd']
        vercode = ver_code.image_str()
        if vercode is None:
            return login_result

        self.driver.find_element_by_xpath("//input[@placeholder='请输入学号']").send_keys(uid)
        self.driver.find_element_by_xpath("//input[@placeholder='请输入密码']").send_keys(pwd)
        self.driver.find_element_by_xpath("//input[@placeholder='请输入验证码']").send_keys(vercode)

        last_url = self.driver.current_url
        self.driver.find_element_by_xpath("//button[1]").click()  # 登录
        time.sleep(3)

        # 判断网页是否跳转
        if self.driver.current_url != last_url:
            login_result = True
            self.driver.switch_to.window(self.driver.window_handles[0])  # 跳转页面
        else:
            login_result = False
        return login_result

    def daka(self):
        result = True
        self.driver.find_element_by_xpath("/html/body/div[1]/div/div[1]/div[2]/a").click()
        time.sleep(3)
        self.driver.switch_to.window(self.driver.window_handles[0])  # 跳转页面
        t = int(datetime.fromtimestamp(int(time.time()),
                                       pytz.timezone('Asia/Shanghai')).strftime('%H'))
        if 7 <= t < 9:
            self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[3]/button").click()
            self.send_email("早晨体温打卡成功")
        elif 12 <= t < 14:
            self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[5]/button").click()
            self.send_email("中午体温打卡成功")
        elif 20 <= t < 22:
            self.driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[7]/button").click()
            self.send_email("晚上体温打卡成功")
        else:
            print("未到打卡时间")
            self.send_email("发生错误，未到打卡时间打卡")
            result = False
        self.driver.close()  # 关闭网页
        return result

    def send_email(self, msg):
        my_sender = '********'  # 发件人邮箱账号
        my_user = self.user_info['mail']  # 收件人邮箱账号
        qq_code = '**********'
        smtp_server = 'smtp.qq.com'
        smtp_port = 465

        stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
        stmp.login(my_sender, qq_code)

        message = MIMEText(msg, 'plain', 'utf-8')  # 发送内容
        message['From'] = Header("无情的打卡机器人", 'utf-8')  # 发件人
        message['To'] = Header("管理员", 'utf-8')  # 收件人
        subject = '体温打卡汇报'
        message['Subject'] = Header(subject, 'utf-8')  # 邮件标题

        try:
            stmp.sendmail(my_sender, my_user, message.as_string())
        except Exception as e:
            print('邮件发送失败--' + str(e))
        print('邮件发送成功')

    def close(self):
        self.driver.close()  # 关闭网页


def main():
    login_url = r'http://xsgl.gdut.edu.cn/index.php/mobile/student/task-temperature?version-checking-redirection=8' \
                r'.473923891538044 '

    file = open("user_info.json", encoding="utf-8")
    info = json.load(file)
    user_info = info['useraccount']

    for each_user in user_info:
        times = 10
        result = False
        while times >= 0:
            my_daka = DaKa(login_url, each_user)
            if my_daka.login():
                result = my_daka.daka()
                break
            else:
                my_daka.close()
            times = times - 1
        if result:
            print(each_user['username'] + "打卡成功")
        else:
            print(each_user['username'] + "打卡失败")


if __name__ == '__main__':
    main()
