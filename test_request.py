import requests

def test_endpoint():
    # 设置请求URL
    url = 'http://www.amazonsp.com/mp'
    
    # 设置请求头和数据
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Origin': 'http://www.amazonsp.com',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'
    }
    data = {
        'x-amzn-marketplace-token': 'test_token_123'
    }

    try:
        # 先测试OPTIONS请求
        options_response = requests.options(url, headers=headers)
        print("\nOPTIONS Request:")
        print(f"Status Code: {options_response.status_code}")
        print(f"Headers: {dict(options_response.headers)}")

        # 测试POST请求
        headers['Access-Control-Request-Method'] = None
        headers['Access-Control-Request-Headers'] = None
        response = requests.post(url, headers=headers, data=data)
        print("\nPOST Request:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    test_endpoint() 