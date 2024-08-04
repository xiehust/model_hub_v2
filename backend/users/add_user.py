
import sys
sys.path.append('./')
from db_management.database import DatabaseWrapper
from logger_config import setup_logger
database = DatabaseWrapper()


def add_user(username:str,password:str,groupname:str):
    try:
        database.add_user(username,password,groupname)
    except Exception as e:
        print(e)
        return False
    return True

if __name__ == "__main__":
    print("请输入用户名:")
    username = input()
    print("请输入用户密码:")
    pwd = input()
    print("请输入用户组[admin,default]:")
    groupname = input()
    if groupname not in ['admin','default']:
        print("用户组错误,必须是[admin,default]")
        exit(1)
    ret = add_user(username,pwd,groupname)
    if ret:
        print(f"添加用户成功:{username}/{pwd}/{groupname}")
    else:
        print("添加用户失败")