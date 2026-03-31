import httpx
import datetime

BASE_URL = 'http://localhost:8000'
timestamp = int(datetime.datetime.now().timestamp())
username = f'test{timestamp}'
password = 'Pass1234'
email = f'{username}@test.com'

print(f'Testing Auth: Register as {username}')
reg = httpx.post(
    f'{BASE_URL}/api/v1/auth/register',
    json={'username': username, 'email': email, 'password': password, 'first_name': 'Test', 'last_name': 'User'},
    timeout=10
)
print(f'Register: {reg.status_code}')
if reg.status_code != 201:
    print(f'Error: {reg.json()}')
else:
    print('Registered OK')
    login = httpx.post(
        f'{BASE_URL}/api/v1/auth/login',
        json={'username': username, 'password': password, 'device_name': 'Test'},
        timeout=10
    )
    print(f'Login: {login.status_code}')
    if login.status_code == 200:
        print('SUCCESS - Authentication verified!')
    else:
        print(f'Error: {login.json()}')
