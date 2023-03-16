from asyncore import write
from dataclasses import replace
import os
import pymysql
import arrow
import pandas as pd
import re
import sys

MYSQL_INFO = {
    "host": "10.0.3.51",
    "port": 2883,
    "user": "edw_ods@mysql_demo#ziel_test_1",
    "passwd": "nw2^&aPAU&HN7",
    "db": "edw_ods",
}

def init_mysql(mysql_info):
    host = mysql_info["host"]
    user = mysql_info["user"]
    passwd = mysql_info["passwd"]
    db = mysql_info["db"]
    port = mysql_info["port"]
    conn = pymysql.connect(
        host=host, user=user, password=passwd, database=db, port=port
    )
    cur = conn.cursor()
    return conn, cur

def re_reconnect_mysql(mysql_conn):
    mysql_conn.ping(reconnect=True)


mysql_conn, mysql_cur = init_mysql(MYSQL_INFO)

def logg(msg):
    return
    dir = "C:/Users/user/Documents/UiPath/Wayfair"
    dir = os.path.dirname(__file__)
    with open(dir + "/debug.log", "a") as file:
        file.writelines(msg)

def need_insert(sku, site):
    re_reconnect_mysql(mysql_conn)
    sql = f"select count(*) from amz_sku_status where sku='{sku}' and site='{site}'"
    mysql_cur.execute(sql)
    result = mysql_cur.fetchone()
    count = result[0]
    if count:
        return False
    else:
        return True

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
    curTime = arrow.now().format("YYYY-MM-DD HH:mm:ss")
    sql = """INSERT INTO amz_sku_status(status,sku,site,inner_link,title,platform,asin,fbm_available,fba_available,price,shipping_fee,featured_offer,competitive_price,is_car_exist,update_time,country,Fulfilled_by)
    select %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s from dual
    where not exists (SELECT asin FROM amz_sku_status where sku=%s and site=%s and update_time=%s)
    """
    if not dict["sku"]:
        print("no sku, skip")
        return None
    torf = formatString(dict, "isCarExist")
    torf = "true" if torf == "1.0" else torf
    torf = "false" if torf == "0.0" else torf
    arr = [
        formatString(dict, "status"),
        dict["sku"],
        dict["site"],
        formatString(dict, "inner link") if formatString(dict, "inner link") != "" else formatString(dict, "innerlink"),
        formatString(dict, "title"),
        formatString(dict, "platform link"),
        formatString(dict, "asin"),
        formatNumber(dict, "FBM_Available"),
        formatNumber(dict, "FBA_Available"),
        formatPrice(dict, "price"),
        formatPrice(dict, "shipping fee"),
        formatOffer(dict, "featured offer"),
        formatPrice(dict, "competitive price"),
        torf,
        dict["update_time"],
        formatString(dict, "country"),
        formatString(dict, "Fulfilled by"),

        dict["sku"],
        dict["site"],
        dict["update_time"]
    ]
    try:
        logg("insert:" + str(arr))
        re_reconnect_mysql(mysql_conn)
        mysql_cur.execute(
            sql,
            arr,
        )
    except Exception as e:
        print(e)
        logg(str(e))
        return None

def run(filePath):
    try:
        logg("file:" + filePath)
        re_reconnect_mysql(mysql_conn)
        df = pd.read_excel(filePath, sheet_name=None)
        for i in df.keys():
            val = df[i].values
            for k in val:
                d = {}
                d.update(dict(zip(df[i].columns, k)))
                if not "site" in d:
                    d["site"] = i
                save(d)
        return "success"
    except Exception as e:
        logg(str(e))
        print(str(e))
        return "failed"

if __name__ == "__main__":
    #logg("got:" + sys.argv[1])
    print(run(sys.argv[1]))
    #print(run(r"C:\Users\user\Documents\UiPath\EU_Amz_status_update\data\Amazon.-all-2022-09-29 1301.xlsx"))
    #print(run("/Users/yanghui/Documents/code/python/bda_lin_application/RPA/Amazon-US-20220926 1548.xlsx"))
