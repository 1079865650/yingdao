import json
from asyncore import write
from dataclasses import replace
import os
import pymysql
import arrow
import pandas as pd
import re
import sys
import requests


def logg(msg):
    return
    dir = "C:/Users/user/Documents/UiPath/Wayfair"
    dir = os.path.dirname(__file__)
    with open(dir + "/debug.log", "a") as file:
        file.writelines(msg)


def formatPrice(dict, price):
    price = dict[price] if price in dict else 0
    if pd.isnull(price):
        return 0
    price = str(price)
    ret = re.findall(r'([\d\.\,]+)', price)
    if ret:
        price = ret[0]
        tmp_price = price.split(",")
        if len(tmp_price[-1]) == 2:
            price = price.replace(".", "").replace(",", ".")
        else:
            price = price.replace(",", "")
        price = float(price)
    else:
        price = 0
    return price


def getPrice(price):
    tmp_price = price.split(",")
    if len(tmp_price[-1]) == 2:
        price = price.replace(".", "").replace(",", ".")
    else:
        price = price.replace(",", "")
    price = float(price)
    return price


def formatString(dict, param):
    param = dict[param] if param in dict else ""
    if pd.isnull(param):
        return ""
    return str(param)


def formatNumber(dict, param):
    param = dict[param] if param in dict else 0
    if pd.isnull(param):
        return 0
    param = str(param)
    ret = re.findall(r'([\d\.]+)', param)
    if ret:
        return float(ret[0])
    return 0


def formatOffer(dict, param):
    param = dict[param] if param in dict else ""
    if pd.isnull(param):
        return ""
    param = str(param)
    param = param.replace("Featured Offer: --", "--")
    ret = re.findall(r'([\d\.\,]{3,})', param)
    if ret and len(ret) > 1:
        price1 = getPrice(ret[0])
        price2 = getPrice(ret[1])
        return f"{price1} + {price2}"
    else:
        return param


def save(dict):
    if not dict["sku"]:
        print("no sku, skip")
        return None
    torf = formatString(dict, "isCarExist")
    torf = "true" if torf == "1.0" else torf
    torf = "false" if torf == "0.0" else torf
    arr = {
        "status": formatString(dict, "status"),
        "sku": dict["sku"],
        "site": dict["site"],
        "inner_link": formatString(dict, "inner link") if formatString(dict, "inner link") != "" else formatString(dict, "innerlink"),
        "title": formatString(dict, "title"),
        "platform": formatString(dict, "platform link"),
        "asin": formatString(dict, "asin"),
        "fbm_available": formatNumber(dict, "FBM_Available"),
        "fba_available": formatNumber(dict, "FBA_Available"),
        "price": formatPrice(dict, "price"),
        "shipping_fee": formatPrice(dict, "shipping fee"),
        "featured_offer": formatOffer(dict, "featured offer"),
        "competitive_price": formatPrice(dict, "competitive price"),
        "is_car_exist": torf,
        "update_time": dict["update_time"],
        "country": formatString(dict, "country"),
        "fulfilled_by": formatString(dict, "Fulfilled by"),
    }
    return arr


def run(filePath):
    try:
        logg("file:" + filePath)
        df = pd.read_excel(filePath, sheet_name=None)
        save_list = []
        for i in df.keys():
            val = df[i].values
            for k in val:
                d = {}
                d.update(dict(zip(df[i].columns, k)))
                if not "site" in d:
                    d["site"] = i
                arr = save(d)
                save_list.append(arr)
                if len(save_list) >= 100:
                    post(save_list)
                    save_list.clear()
        if len(save_list) > 0:
            post(save_list)
            save_list.clear()
        return "success"
    except Exception as e:
        logg(str(e))
        print(str(e))
        return "failed"

url = 'https://internal-api.zielsmart.com/v2/rpa/platform/amazon/buybox/sync/amz_sku_status'
token = '3a0d9caaadb1425bb56672ba56a5c289'

def post(push_data):
    print(json.dumps(push_data, ensure_ascii=False))
    response = requests.post(url=url,
                             headers={'Content-Type': 'application/json;charset=utf-8', 'X-AUTHORIZATION-TOKEN': token},
                             json=push_data)
    print("推送结果:" + response.text)
if __name__ == "__main__":
    #logg("got:" + sys.argv[1])
    run("/Users/zhiou/Desktop/Amazon-US-20230316 1501.xlsx")
    # print(run(r"C:\Users\user\Documents\UiPath\EU_Amz_status_update\data\Amazon.-all-2022-09-29 1301.xlsx"))
    # print(run("/Users/yanghui/Documents/code/python/bda_lin_application/RPA/Amazon-US-20220926 1548.xlsx"))
