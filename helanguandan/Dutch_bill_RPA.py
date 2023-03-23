# _*_ coding : utf-8 _*_
# @Time : 2023-03-07 9:12
# @Author : wws
# @File : 荷兰关单RPA
# @Project : 根据RPA_03 接着改写  解耦！！！
import base64
import datetime
import glob
import json
import os
import re
import sys

# from redis_util import *
import imap_tools.message
import requests
from imap_tools import MailBox, AND, OR, NOT
import redis
from .荷兰关单RPA_settings import *


def filter_message(attachment, send: str, file_code: str):
    date_time = datetime.datetime.now().strftime("%Y-%m-%d")
    if send == "OFR":
        file_path = pdf_storage_location + "\\" + send + "\\" + date_time + "\\" + file_code
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        for a in attachment:  # <class "imap_tools.message.MailAttachment">
            if ("Duty" in a.filename) or ("Clearance" in a.filename):
                att_data = a.payload
                f = open(pdf_storage_location + "\\" + send + "\\" + date_time + "\\" + file_code + "\\" + a.filename, "wb")
                result = f.write(att_data)
                f.close()
                break
        return file_path
    elif send == "DGF":
        file_path = pdf_storage_location + "\\" + send + "\\" + date_time + "\\" + file_code
        if not os.path.exists(file_path):  # 判断文件是否存在
            os.makedirs(file_path)
        if len(attachment) == 1:
            a = attachment[0]
            att_data = a.payload
            f = open(pdf_storage_location + "\\" + send + "\\" + date_time + "\\" + file_code + "\\" + a.filename, "wb")
            result = f.write(att_data)
            f.close()
            return file_path


def list_dict_list(list_dict: list):
    list_value = []
    for item in list_dict:
        key = list(item.keys())[0]
        value = item[key]
        list_value.append(value)
    return list_value


def add(rd_key, rd_value, expired: int):
    # redis_conn = connect_redis()  # 这种方式 没法调用 redis.Redis.close
    expired = -1
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    if expired != -1:
        add_result = redis_conn.setex(rd_key, expired, rd_value)
    else:
        add_result = redis_conn.set(rd_key, rd_value)
    redis_conn.close()
    return add_result


def exists(rd_key):
    # redis_conn = connect_redis()
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    exist = redis_conn.exists(rd_key)
    redis_conn.close()
    return True if exist > 0 else False


def delete_key(rd_key):
    # redis_conn = connect_redis()
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    delete_result = redis_conn.delete(rd_key)
    redis_conn.close()
    return True if delete_result > 0 else False


def parse_file_code(string_value, uid: str):
    pattern = re.compile(r"((?<=HBL)|(?<=File:))[\#\s\w]*[\w$]")
    a = re.search(pattern, string_value)
    if a is None:
        return None
    b = re.sub(r"\W*", "", a.group())
    if "HBL" in string_value:
        c = "HBL_" + b + "_" + uid
        return c
    elif "File:" in string_value:
        c = "File_" + b + "_" + uid
        return c


def traverse_folder(date_time):  # 遍历文件夹 拿到所有附件  参数如果传值 就不再是默认值
    if date_time == "":
        # file_path = r"F:\Users\DeskTop\Dutch\*" + "\\" + datetime.datetime.now().strftime("%Y-%m-%d") + "\\*"
        file_path = pdf_storage_location + r"\*\\" + datetime.datetime.now().strftime("%Y-%m-%d") + "\\*"
    else:
        file_path = pdf_storage_location + r"\*\\" + date_time + "\\*"

    folder_abs_list = glob.glob(file_path)
    if len(folder_abs_list) == 0:
        return None
    file_list = dict()

    for parent_folder in folder_abs_list:
        file_li = []
        for file_abs in glob.glob(parent_folder + "\\*"):
            file_li.append(file_abs)
        file_list[parent_folder] = file_li
    return file_list


def parse_pdf(files_path: list):  # 放进去一个数组
    if len(files_path) == 0:
        return None
    body = []
    for file_path in files_path:
        if not os.path.exists(file_path):
            continue
        f = open(file_path, "rb")
        ls_f = base64.b64encode(f.read())
        f.close()
        body.append([bytes(ls_f).decode()])  # 用bytes().decode 转化为字符串
    url = "https://internal-api.zielsmart.com/v2/rpa/platform/nl/customhouse/order/pdf_analysic"
    headers = {
        "X-AUTHORIZATION-TOKEN": "3a0d9caaadb1425bb56672ba56a5c289",
        "Content-Type": "application/json",
    }
    if len(body) == 0:  # body里面是所有附件的base64 [] 可以拿到response
        return None
    res = requests.post(url=url, headers=headers, data=json.dumps(body))
    return res


def number_bill_request(hbl, number):  # hbl提单号 number集装箱号  传什么类型都可以返回200
    url = "https://internal-api.zielsmart.com/v2/rpa/platform/nl/query/clearance/info"
    headers = {
        "X-AUTHORIZATION-TOKEN": "3a0d9caaadb1425bb56672ba56a5c289",
        "Content-Type": "application/json;charset=UTF-8"
    }
    params = {
        "ladingBillHbl": hbl,
        "containerNumber": number
    }
    res = requests.post(url=url, headers=headers, json=params)  # json params
    try:
        if res.status_code != 200:
            return None
    except Exception:
        return None
    return res


def parse_pdf_bill(pdf_json, bill_json, filename):  # folder\filer user filer parse pdf then obtain pdf_json and finally get bill_json
    pdf_bill_json = {filename: {
        'pdf_json': [],
        'bill_json': [],
        'sea_amount': []
        }
    }
    pdf_list_all = []
    # eya货柜单清关预览
    pdf_list = []
    pdf_list.append(pdf_json['containerNummber'] if ('containerNummber' in pdf_json) else '')
    pdf_list.append(pdf_json['geadresseerde'] if ('geadresseerde' in pdf_json) else '')
    pdf_list.append(pdf_json['mrn'] if ('mrn' in pdf_json) else '')
    pdf_list.append(pdf_json['totaalColli'] if ('totaalColli' in pdf_json) else '')
    pdf_list.append(pdf_json['datum'] if ('datum' in pdf_json) else '')
    pdf_list.append(pdf_json['vertegenWooddiger'] if ('vertegenWooddiger' in pdf_json) else '')
    for item in (pdf_json['toestemmingArtikel'] if ('toestemmingArtikel' in pdf_json) else ''):  # 可以遍历字符
        pdf_li = pdf_list.copy()
        pdf_li.append(item['bruto'] if ('bruto' in item) else '')
        pdf_li.append(item['netto'] if ('netto' in item) else '')
        pdf_li.append(item['ct'] if ('ct' in item) else '')
        # pdf_li.append(item['goederencode'] if ('goederencode' in item) else '')
        d = (item['goederencode'] if ('goederencode' in item) else '')
        c = re.sub(r"[^0-9]", '', d)[0:10]
        pdf_li.append(c)
        pdf_li.append(item['name'] if ('name' in item) else '')
        pdf_list_all.append(pdf_li)

    #  第二个清单
    pdf_list_02 = []
    pdf_list_02.append(pdf_json['mrn'] if ('mrn' in pdf_json) else '')
    pdf_list_02.append(pdf_json['aanvaardingsDatum'] if ('aanvaardingsDatum' in pdf_json) else '')
    pdf_list_02.append(pdf_json['datum'] if ('datum' in pdf_json) else '')
    for index, item in enumerate(pdf_json['artikel'] if ('artikel' in pdf_json) else ''):  # 可以遍历字符
        pdf_li = pdf_list_02.copy()
        # pdf_li.append(item['goederencode'] if ('goederencode' in item) else '')
        d = (item['goederencode'] if ('goederencode' in item) else '')
        c = re.sub(r"[^0-9]", '', d)[0:10]
        pdf_li.append(c)
        pdf_li.append(item['name'] if ('name' in item) else '')
        pdf_li.append(item['belastbare1'] if ('belastbare1' in item) else '')
        pdf_li.append(item['tarief1'] if ('tarief1' in item) else '')
        pdf_li.append(item['douanerechten'] if ('douanerechten' in item) else '')
        pdf_li.append(pdf_json['bedrag'] if ('bedrag' in pdf_json) else '')
        for i in pdf_li:
            pdf_list_all[index].append(i)

    # 第三个清单
    pdf_list_03 = []
    pdf_list_03.append(pdf_json['geadresseerde'] if ('geadresseerde' in pdf_json) else '')
    pdf_list_03.append(pdf_json['rechnungsNummer'] if ('rechnungsNummer' in pdf_json) else '')
    pdf_list_03.append(pdf_json['containerNummber'] if ('containerNummber' in pdf_json) else '')
    for index, item in enumerate(pdf_json['wispexTable'] if ('wispexTable' in pdf_json) else ''):
        pdf_li = pdf_list_03.copy()
        pdf_li.append(item['bruttoMasse'] if ('bruttoMasse' in item) else '')
        pdf_li.append(item['eigenMasse'] if ('eigenMasse' in item) else '')
        pdf_li.append(item['besondereMaeinheit'] if ('besondereMaeinheit' in item) else '')
        # pdf_li.append(item['zolltarifNummer'] if ('zolltarifNummer' in item) else '')
        d = (item['zolltarifNummer'] if ('zolltarifNummer' in item) else '')
        c = re.sub(r"[^0-9]", '', d)[0:10]
        pdf_li.append(c)
        pdf_li.append(item['warenbeschreibung'] if ('warenbeschreibung' in item) else '')  # AB
        table = (item['table'] if ('table' in item) else '')
        table_index_dict = {'NETTOPREIS': '', 'TRANSPORTKOSTEN': '', 'VERSICHERUNGSKOSTEN': ''}
        for index_01, item_01 in enumerate(table):
            title = str(item_01['title']).split(' ')[0]
            table_index_dict[title] = index_01
        for key in table_index_dict.keys():
            table_index = table_index_dict[key]
            if 'NETTOPREIS' == key:
                pdf_li.append(item['table'][table_index]['total'] if ('total' in item['table'][table_index]) else '')
            elif 'TRANSPORTKOSTEN' == key:
                pdf_li.append(item['table'][table_index]['total'] if ('total' in item['table'][table_index]) else '')
                pdf_li.append(item['table'][table_index]['quantity'] if ('quantity' in item['table'][table_index]) else '')
                pdf_li.append(item['table'][table_index]['currency'] if ('currency' in item['table'][table_index]) else '')
            elif 'VERSICHERUNGSKOSTEN' == key:
                pdf_li.append(item['table'][table_index]['total'] if ('total' in item['table'][table_index]) else '')  # AG

        pdf_li.append(item['zollwert'] if ('zollwert' in item) else '')
        pdf_li.append(item['zolleAufIndustrieprodukteSummary'] if ('zolleAufIndustrieprodukteSummary' in item) else '')
        pdf_li.append(item['zolleAufIndustrieprodukte'] if ('zolleAufIndustrieprodukte' in item) else '')
        pdf_li.append(item['btw'] if ('btw' in item) else '')
        pdf_li.append(item['TRAMSPORTCOSTS'] if ('TRAMSPORTCOSTS' in item) else 0.0)
        pdf_li.append(item['insgesamtPerArtikel'] if ('insgesamtPerArtikel' in item) else '')
        for i in pdf_li:
            pdf_list_all[index].append(i)

    # print(pdf_list_all)
    # print(len(pdf_list_all[0]))

    # bill_json 解析
    bill_list_all = []
    sea_amount_list = []
    for item in bill_json:
        bill_list = []
        bill_list.append(item['containerNumber'] if ('containerNumber' in item) else '')
        bill_list.append(item['exportInvoiceNumber'] if ('exportInvoiceNumber' in item) else '')
        bill_list.append(item['clearanceHscodeInfo'] if ('clearanceHscodeInfo' in item) else '')
        bill_list.append(item['hscodeNameFrom'] if ('hscodeNameFrom' in item) else '')
        bill_list.append(item['hscodeNameEn'] if ('hscodeNameEn' in item) else '')
        bill_list.append(item['declaredUnitName'] if ('declaredUnitName' in item) else '')
        bill_list.append(item['setNumber'] if ('setNumber' in item) else '')
        bill_list.append(item['pcsNumber'] if ('pcsNumber' in item) else '')
        bill_list.append(item['ctnsNumber'] if ('ctnsNumber' in item) else '')
        bill_list.append(item['declaredGrossWeight'] if ('declaredGrossWeight' in item) else '')
        bill_list.append(item['declaredNetWeight'] if ('declaredNetWeight' in item) else '')
        bill_list.append(item['declaredVolumeNumber'] if ('declaredVolumeNumber' in item) else '')
        bill_list.append(item['declaredPrice'] if ('declaredPrice' in item) else '')
        bill_list.append(item['declaredAmount'] if ('declaredAmount' in item) else '')
        bill_list.append(item['currencyCode'] if ('currencyCode' in item) else '')
        bill_list.append(item['tradeClauseCode'] if ('tradeClauseCode' in item) else '')
        bill_list.append(item['vendorShortName'] if ('vendorShortName' in item) else '')
        bill_list.append(item['productBrandCode'] if ('productBrandCode' in item) else '')
        bill_list.append(item['ladingTitleTypeName'] if ('ladingTitleTypeName' in item) else '')
        bill_list.append(item['partsBoxNumber'] if ('partsBoxNumber' in item) else '')
        bill_list.append(item['totalTaxrate'] if ('totalTaxrate' in item) else '')
        bill_list.append(item['predictTaxAmount'] if ('predictTaxAmount' in item) else '')  # partsBoxNumber predictTaxAmount 没有

        sea_list = [item['seaFreightAmount'] if ('seaFreightAmount' in item) else '']

        bill_list_all.append(bill_list)
        sea_amount_list.append(sea_list)

    pdf_bill_json[filename]['bill_json'] = bill_list_all
    pdf_bill_json[filename]['pdf_json'] = pdf_list_all
    pdf_bill_json[filename]['sea_amount'] = sea_amount_list
    return pdf_bill_json


def start(start_time=datetime.datetime.now().strftime("%Y-%m-%d")):
    mail_pass = fs_mail_pass
    with MailBox(fs_host).login(fs_username, mail_pass, initial_folder="INBOX") as mailbox:
        a = str(start_time).split('-')
        criteria = AND(date_gte=datetime.date(int(a[0]), int(a[1]), int(a[2])))
        uid_list = []  # 存放所有下载附件 的邮件id
        for msg in mailbox.fetch(criteria, charset="utf-8"):
            sender = msg.from_
            uid = msg.uid
            redis_uid = "email:uid" + uid
            # exist = exists(redis_uid)  # 从redis判断
            # if exist:
            #     continue
            subject = msg.subject
            attachments = msg.attachments
            if "customs@ziel.cn" in sender:  # test
                if ("OFR" in subject) and ("HBL" in subject) and ("NLRTM" in subject):
                    file_code = parse_file_code(subject, uid=uid)  # 文件 File: or HBL
                    if file_code is None:
                        continue
                    file_name = filter_message(attachments, send="OFR", file_code=file_code)
                    if file_name is None:
                        continue
                    item = {"OFR": uid}
                    uid_list.append(item)
                    # download_appendix(attachments, file_name)
                elif ("DGF" in subject) or ("CDZ" in subject):
                    file_code = parse_file_code(subject, uid=uid)  # 文件 File: or HBL
                    if file_code is None:
                        continue
                    file_name = filter_message(attachments, send="DGF", file_code=file_code)
                    if file_name is None:
                        continue
                    item = {"DGF": uid}
                    uid_list.append(item)
        return uid_list


# date_time 筛选日期 不填默认今天
def parse_pdf_bill_findings(uid_list, date_time=""):
    uid_all = []
    for uid_item in uid_list:
        key = list(uid_item.keys())[0]
        uid = uid_item[key]
        uid_all.append(uid)

    problem_uid = []  # 存放所有问题邮件uid
    pdf_bill_data = []  # 存放所有pdf,bill的数据  file_list每个下载附件下面的pdf 解析比对数据放入[]
    # 遍历文件夹 读取pdf
    file_list = traverse_folder(date_time)  # file_list <class "dict"> 所有 folder\file  file_list 可能是None 如果是None 没有筛选附件

    # print("=====file_list", file_list)
    file_list_list = []
    for key in file_list.keys():
        uid = str(key).split("\\")[-1].split("_")[2]
        if uid not in uid_all:
            file_list_list.append(key)
    for i in file_list_list:
        file_list.pop(i)

    print("=====file_list", file_list)
    for key in file_list.keys():
        order_uid = str(key).split("\\")[-1].split("_")
        order_code = order_uid[1]
        email_uid = order_uid[2]
        file_path = file_list[key]  # files_path <class "list"> all attachments below the message
        res = parse_pdf(file_path)
        if res is None:
            item = {"problem_pdf_request": email_uid}  # 附件pdf解析失败
            problem_uid.append(item)
            continue
        if res.status_code != 200:
            item = {"problem_pdf_request": email_uid}  # 附件pdf解析失败
            problem_uid.append(item)
            continue
        if res.json()['success'] != True:
            item = {"problem_pdf_request": email_uid}  # 附件pdf解析失败
            problem_uid.append(item)
            continue
        pdf_json = res.json()  # 解析pdf后的json数据
        if pdf_json["msg"] == "MoreMRN":
            item = {"problem_MoreMRN": email_uid}  # 邮件出现两个关单
            problem_uid.append(item)
            continue
        # print(pdf_json)
        if pdf_json["data"]["geadresseerde"] != "EUZIEL INTERNATIONAL GMBH":
            item = {"problem_address": email_uid}  # 不属于德国公司
            problem_uid.append(item)
            continue

        container_number = pdf_json["data"]["containerNummber"]  # 集装箱号
        print('hbl=order_code, number=container_number', order_code, container_number)
        res_bill = number_bill_request(hbl=order_code, number=container_number)  # 发送请求 返回bill数据
        if res_bill is None:
            item = {"problem_bill_request": email_uid}  # 提单号请求失败
            problem_uid.append(item)
            continue
        if "data" not in res_bill.json():
            item = {"problem_bill_request": email_uid}  # 提单号请求失败
            problem_uid.append(item)
            continue
        bill_json = res_bill.json()["data"]
        if "containerNumber" not in bill_json[0]:  # 判断是否拿到订单的详情数据
            item = {"problem_bill_request": email_uid}  # 提单号 请求失败
            problem_uid.append(item)
            continue
        # 数据都没问题 提取数据
        try:
            a = parse_pdf_bill(pdf_json=pdf_json['data'], bill_json=bill_json,
                               filename=order_code + '_' + email_uid)
        except Exception:
            item = {"problem_parse_pdf_bill": email_uid}
            problem_uid.append(item)
            continue
        a_data = a[list(a.keys())[0]]
        # print("=====pdf_json", len(a_data['pdf_json']), a_data['pdf_json'])
        # print("=====bill_json", len(a_data['bill_json']), a_data['bill_json'])
        # print("=====sea_amount", len(a_data['sea_amount']), a_data['sea_amount'])
        if len(a_data['pdf_json']) != len(a_data['bill_json']) or len(a_data['pdf_json']) != len(a_data['sea_amount']) or len(a_data['bill_json']) != len(a_data['sea_amount']):
            item = {"problem_parse_pdf_bill": email_uid}
            problem_uid.append(item)
            continue
        pdf_bill_data.append(a)  # for 里面
    return pdf_bill_data, problem_uid


def filter_error_email(uid_list, problem_uid):
    # 根据邮件正常，异常 分类邮件id
    problem_uid_int = []  # 问题邮件的id int类型
    for pro_uid in problem_uid:  # 提取问题邮件的uid
        for key in pro_uid.keys():
            uid = pro_uid[key]
            problem_uid_int.append(uid)
    # print("=========problem_uid", problem_uid)
    # 在下载附件的uid 移除有问题的uid
    index_list = []
    for rig_uid in enumerate(uid_list):
        for key in rig_uid[1].keys():  # dict
            uid = rig_uid[1][key]
            if uid in problem_uid_int:
                index_list.append(int(rig_uid[0]))
                # index_list.insert(0, rig_uid[0])
                index_list.sort(reverse=True)
    print("=========uid_list before pop", uid_list)
    if len(index_list) != 0:
        for index in index_list:
            uid_list.pop(index)
    return uid_list  # 正确的uid 错误的uid


def process_correct_message(uid_list):
    mail_pass = fs_mail_pass
    with MailBox(fs_host).login(fs_username, mail_pass, initial_folder="INBOX") as mailbox:
        processed_uid = []  # 成功处理的uid
        for uid_item in uid_list:
            keys = dict(uid_item).keys()
            for file_name in keys:
                try:
                    uid = uid_item[file_name]
                    mail_index = mailbox.uids().index(uid)
                    # add("email:uid"+uid, 1, -1)  # 添加redis
                except ValueError:
                    print("error of list query data:" + str(ValueError) + " and uid:" + uid_item[file_name])
                    continue
                processed_uid.append(uid)
                mailbox.move(mailbox.uids()[mail_index], file_name)
        print("ID of all messages moved:", processed_uid)
        return processed_uid


import smtplib
# email 用于构建邮件内容
from email.mime.text import MIMEText
# 构建邮件头
from email.header import Header
def send_email_by_judge(uid_list, problem_uid, bedrag_list_all):
    date_time = datetime.datetime.now().strftime("%Y-%m-%d")
    mail_pass = fs_mail_pass
    with MailBox(fs_host).login(fs_username, mail_pass, initial_folder="INBOX") as mailbox:
        criteria = AND(date_gte=datetime.date(2023, 2, 21))
        uid_subject_dict = dict()
        for msg in mailbox.fetch(criteria, charset="utf-8"):
            uid = msg.uid
            subject = msg.subject
            uid_subject_dict[uid] = subject
        print(uid_subject_dict)
        # 发送成功邮件集合
        sending_succeeded_uid = []
        # 发送邮件详情
        from_addr = fs_from_addr
        password = fs_from_password
        smtp_server = fs_from_smtp_server

        for right in uid_list:
            key = list(right.keys())[0]
            uid = str(right[key])
            print(uid, type(uid), "=======uid")
            bedrag = bedrag_list_all[uid]
            try:
                to_addr = fs_to_addr_true
                # subject = uid_subject_list[uid]
                subject = (date_time+'的核对正常的关单明细')
                content = uid_subject_dict[uid] + '\t'*3 + "核对正常,关税为:" + str(bedrag)

                msg = MIMEText(content, 'plain', 'utf-8')
                msg['Subject'] = Header(subject, 'utf-8')  # 邮件主题
                msg['From'] = Header('PRA核对')  # 发送者
                smtpobj = smtplib.SMTP_SSL(smtp_server)
                # 建立连接--qq邮箱服务和端口号（可百度查询）
                smtpobj.connect(smtp_server, 465)
                # 登录--发送者账号和口令
                smtpobj.login(from_addr, password)
                # 发送邮件
                smtpobj.sendmail(from_addr, to_addr, msg.as_string())
                sending_succeeded_uid.append(uid)
                print("邮件发送成功")
            except smtplib.SMTPException:
                print("无法发送邮件")
            finally:
                pass
                # 关闭服务器
                # smtpobj.quit()

        # 处理错误的邮件
        for left in problem_uid:
            key = list(left.keys())[0]
            uid = str(left[key])
            try:
                # to_addr = '2983003951@qq.com'
                # subject = uid_subject_list[uid]
                subject = (date_time+'的核对异常的关单明细')
                content = uid_subject_dict[uid] + '\t'*3 + "核对异常,请人工核查"

                msg = MIMEText(content, 'plain', 'utf-8')
                msg['From'] = Header('PRA核对')  # 发送者
                msg['Subject'] = Header(subject, 'utf-8')  # 邮件主题
                smtpobj = smtplib.SMTP_SSL(smtp_server)
                # 建立连接--qq邮箱服务和端口号（可百度查询）
                smtpobj.connect(smtp_server, 465)
                # 登录--发送者账号和口令
                smtpobj.login(from_addr, password)
                # 发送邮件
                smtpobj.sendmail(from_addr, fs_to_addr, msg.as_string())
                sending_succeeded_uid.append(uid)
                print("邮件发送成功")
            except smtplib.SMTPException:
                print("无法发送邮件")
            finally:
                # 关闭服务器
                # smtpobj.quit()
                pass
        return sending_succeeded_uid


def mkdir_file(filename):
    folder_path = excel_storage_location + '\\' + datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = folder_path + '\\' + filename + '.xlsx'
    if not os.path.exists(folder_path):
        # os.mkdir(file_path)
        os.makedirs(folder_path)  # 先创建 open file 的前置 folder
    with open(excel_model_location, 'rb') as f:
        data = f.read()
        # f.close()
    with open(file_path, 'wb') as d:  # 如果没有会创建 有的话会覆盖
        d.write(data)
        # d.close()
    return file_path


def add_redis(sending_succeeded_uid):
    for i in sending_succeeded_uid:
        add("email:uid"+i, 1, -1)  # 添加redis


def classify_files(validity: list, invalidity: list):
    validity_uid = list_dict_list(validity)
    invalidity_uid = list_dict_list(invalidity)
    g = os.walk(excel_storage_location + '\\' + datetime.datetime.now().strftime("%Y-%m-%d"))
    validity_email = []
    invalidity_email = []
    for path, dir_list, file_list in g:
        for file_name in file_list:
            absolute_path = os.path.join(path, file_name)
            uid = re.findall(r'(?<=_)\d+(?=\.)', absolute_path)[0]
            if uid in validity_uid:
                validity_email.append(absolute_path)
            elif uid in invalidity_uid:
                invalidity_email.append(absolute_path)

    excel_path = os.path.join(excel_storage_location, datetime.datetime.now().strftime("%Y-%m-%d"))
    for dir1 in os.listdir(excel_path):  # file folder  all will be printed out
        cur_path = os.path.join(excel_path, dir1)  # full path
        if os.path.isdir(cur_path):
            continue

        new_file_path = ''
        if cur_path in validity_email:
            new_file_path_previous = os.path.join(excel_path, 'validity')
            new_file_path = os.path.join(new_file_path_previous, dir1)
        elif cur_path in invalidity_email:
            new_file_path_previous = os.path.join(excel_path, 'invalidity')
            new_file_path = os.path.join(new_file_path_previous, dir1)
        else:
            continue
        if not os.path.exists(new_file_path_previous):
            os.makedirs(new_file_path_previous)
        if os.path.isdir(cur_path):  # is folder return true   is file return false  cur_path will not destroy the original folder  dir cut the previous folder directly
            if not os.path.exists(new_file_path):
                os.mkdir(new_file_path)
        else:
            # with open(cur_path, 'rb') as f:
            #     data = f.read()
            #     os.remove(cur_path)
            #     # f.close()
            # with open(new_file_path, 'wb') as d:  # if not a file will be created if any it will cover the content
            #     d.write(data)
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
            os.rename(cur_path, new_file_path)


def absolute_path_pdf(time_date=datetime.datetime.now().strftime('%Y-%m-%d')):
    a = traverse_folder(time_date)
    absolute_path = []
    for i in a.keys():
        path = str(a[i][0])
        ch_index = path.rfind("\\")
        file_path = path[0:ch_index]
        file_name = path[ch_index+1:]
        item = [file_path, file_name]
        absolute_path.append(item)
    return absolute_path







def aa():
    print("can enter")







# start()
