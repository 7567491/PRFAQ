import requests

data = {
    "x-amzn-marketplace-token": "this_is_a_test_token_12345",
    "timestamp": "2024-03-21",
    "extra_info": "some additional data"
}

# 修改请求路径为 /mp
response = requests.post('http://amazonsp.com/mp', json=data, allow_redirects=False)
print(f"发送请求完成，响应状态码: {response.status_code}")

# 检查是否是重定向响应
if response.is_redirect:
    print(f"收到重定向响应！")
    print(f"重定向地址: {response.headers.get('Location')}")
    print(f"重定向状态码: {response.status_code}")
else:
    print("没有收到重定向响应")
    print(f"响应内容: {response.text}") 