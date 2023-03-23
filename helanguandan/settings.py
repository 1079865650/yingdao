# _*_ coding : utf-8 _*_
# @Time : 2023-03-15 11:39
# @Author : wws
# @File : 荷兰关单RPA_settings
# @Project : 荷兰关单RPA+imap_tools



# 本地邮件箱配置
fs_host = 'imap.feishu.cn'
fs_username = 'wensong.wang@ziel.cn'
fs_mail_pass = 'MZquSz2dXuaTQ0ob'

# 发件人邮箱配置
fs_from_addr = 'wensong.wang@ziel.cn'
fs_from_password = 'MZquSz2dXuaTQ0ob'
fs_from_smtp_server = 'smtp.feishu.cn'


# 收件人邮箱配置
fs_to_addr_true = 'shipping-invoiceeu@songmics.de'  # 邮件正确的收件人
# fs_to_addr_true2 = 'customs@ziel.cn'
fs_to_addr = 'customs@ziel.cn'  # 邮件错误的收件人


# redis
redis_host = "eya-prod.enujjj.ng.0001.cnw1.cache.amazonaws.com.cn"
redis_port = 6379
redis_db = 8


# pdf文件存储位置
pdf_storage_location = r"D:\RPA\NL_GuanDan\guandan\pdf"
# excel存储位置
excel_storage_location = r'D:\RPA\NL_GuanDan\guandan\excel'
# excel模板位置
excel_model_location = r'D:\RPA\NL_GuanDan\荷兰关税单-加公式 模板_new_01.xlsx'
