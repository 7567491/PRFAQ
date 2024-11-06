import sqlite3

def read_database():
    conn = sqlite3.connect('user/users.db')
    c = conn.cursor()
    
    # 获取表结构
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    table_schema = c.fetchone()
    print("表结构:")
    print(table_schema[0])
    print("\n")
    
    # 获取所有用户数据
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    # 获取列名
    column_names = [description[0] for description in c.description]
    print("列名:", column_names)
    print("\n用户数据:")
    for user in users:
        print("---")
        for i, value in enumerate(user):
            print(f"{column_names[i]}: {value}")
    
    conn.close()

if __name__ == "__main__":
    read_database() 