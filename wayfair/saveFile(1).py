import json

import arrow
import pandas as pd
import re
import requests


def logg(msg):
    print(msg)
    dir = "C:/Users/user/Documents/UiPath/Wayfair"
    #dir = os.path.dirname(__file__)
    with open(dir + "/debug.log", "a") as file:
        file.writelines(msg)


def formatPrice(price):
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
    else:
        price = 0
    return price


def formatString(param):
    if pd.isnull(param):
        return ""
    return_param = str(param)
    if str(type(return_param)) =="<type 'unicode'>":
        return_param = str(return_param)
    return return_param

def formatNumber(param):
    if pd.isnull(param):
        return 0
    param = str(param)
    ret = re.findall(r'([\d\.]+)', param)
    if ret:
        return ret[0]
    return 0


def decoration_info(dict):
    createTime = arrow.now().format("YYYY-MM-DD HH:mm:ss")
    if not dict["SKU"]:
        print("no sku, skip")
        return None

    arr = {
        'sku': dict["SKU"],
        'show_code': dict["展示码"],
        'wayfair_sku': dict["WAYFAIR SKU"],
        'owner': formatString(dict["负责人"]),
        'country': formatString(dict["国家"]),
        'site': formatString(dict["站点"]),
        'link': formatString(dict["link"]),
        'price': formatPrice(dict["price"]),
        'list_price': formatPrice(dict["list_price"]),
        'score': formatNumber(dict["评分"]),
        'comments': formatNumber(dict["评论数"]),
        'stock_tag': formatString(dict["缺货标记"]),
        'delivery': formatString(dict["发货方式"]),
        'update_time': formatString(dict["更新时间"]),
        'create_time': createTime,
        'memo': ""
    }
    return arr


def run(filePath):
    try:
        logg("get input:" + filePath)
        df = pd.read_excel(filePath, sheet_name="Sheet1", dtype=str)
        val = df.values
        sku_list = []
        print("有数据:" + str(len(val)))
        for i in val:
            d = {}
            d.update(dict(zip(df.columns, i)))
            if d["SKU"]:
                sku_list.append(decoration_info(d))

            if len(sku_list) >= 100:
                post(sku_list)
                sku_list.clear()

        if len(sku_list) > 0:
            post(sku_list)
            sku_list.clear()
        return "success"
    except Exception as e:
        logg(str(e))
        return "failed"


url = 'https://internal-api.zielsmart.com/v2/rpa/platform/wayfair/wayfair/sync_wayfair_product_info'
token = '3a0d9caaadb1425bb56672ba56a5c289'


def post(push_data):
    print(json.dumps(push_data,ensure_ascii=False))
    response = requests.post(url=url,
                             headers={'Content-Type': 'application/json;charset=utf-8', 'X-AUTHORIZATION-TOKEN': token},
                             json=push_data)
    logg("推送结果:" + response.text)


if __name__ == "__main__":
    run('/Users/zhiou/Desktop/Wayfair202302190600.xlsx')
