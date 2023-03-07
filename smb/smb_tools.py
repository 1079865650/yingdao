from smb.SMBConnection import *


def download(smb_url, smb_port, smb_account, smb_password, smb_file_names, smb_service_name, smb_dir, local_file_path):
    '''
    :param smb_url: 路径
    :param smb_port: 端口
    :param smb_account: 账号
    :param smb_password: 密码
    :param smb_service_name: SMB的服务名称（一般都是第一层文件夹）
    :param smb_dir: SMB的文件所属文件夹
    :param smb_file_names: SMB的文件名字
    :param local_file_path: 本地保存路径
    :return:
    '''
    smb = SMBConnection(smb_account, smb_password, '', '', use_ntlm_v2=True)
    try:
        smb.connect(smb_url, smb_port)
        if type(smb_file_names) is not list:
            smb_file_names = [smb_file_names]

        for file_name in smb_file_names:
            with open(os.path.join(local_file_path, file_name), 'wb+') as f:
                smb.retrieveFile(smb_service_name, os.path.join(smb_dir, file_name), f)
                f.close()

        smb.close()
    except Exception as e:
        print(e)
        smb.close()
        raise e


def upload(smb_url, smb_port, smb_account, smb_password, local_file_names, local_file_path, smb_service_name, smb_dir):
    '''
    :param smb_url: 路径
    :param smb_port: 端口
    :param smb_account: 账号
    :param smb_password: 密码
    :param smb_service_name: SMB的服务名称（一般都是第一层文件夹）
    :param smb_dir: SMB的文件所属文件夹
    :param local_file_names: 本地的文件名
    :param local_file_path: 本地的文件所在路径
    :return:
    '''
    smb = SMBConnection(smb_account, smb_password, '', '', use_ntlm_v2=True)
    try:
        smb.connect(smb_url, smb_port)
        if type(local_file_names) is not list:
            local_file_names = [local_file_names]
        for file_name in local_file_names:
            with open(os.path.join(local_file_path, file_name), 'rb+') as f:
                try:
                    smb.createDirectory(smb_service_name, smb_dir)
                except:
                    print(f"文件夹创建失败!")
                smb.storeFile(smb_service_name, os.path.join(smb_dir, file_name), f)
                f.close()
        smb.close()
    except Exception as e:
        print(e)
        smb.close()
        raise e
