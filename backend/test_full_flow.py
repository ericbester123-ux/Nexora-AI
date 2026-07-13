import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        # Test login
        response = await client.post('http://localhost:8000/api/v1/auth/login', json={
            'email': 'admin@nexora.ai',
            'password': 'XeroaAI!'
        })
        print(f'Login status: {response.status_code}')
        if response.status_code != 200:
            print(f'Login failed: {response.text}')
            return
        
        data = response.json()
        token = data.get('access_token')
        refresh = data.get('refresh_token')
        print(f'Token: {token[:30]}...')
        print(f'Refresh: {refresh[:30]}...')
        
        # Simulate what frontend does - store tokens
        # Then test /auth/me with the token
        headers = {'Authorization': f'Bearer {token}'}
        me_response = await client.get('http://localhost:8000/api/v1/auth/me', headers=headers)
        print(f'Me status: {me_response.status_code}')
        if me_response.status_code == 200:
            print(f'Me response: {me_response.json()}')
        
        # Test refresh token
        refresh_response = await client.post('http://localhost:8000/api/v1/auth/refresh', json={
            'refresh_token': refresh
        })
        print(f'Refresh status: {refresh_response.status_code}')
        if refresh_response.status_code == 200:
            print(f'New token: {refresh_response.json().get("access_token")[:30]}...')
        
        # Test login with wrong password
        wrong_response = await client.post('http://localhost:8000/api/v1/auth/login', json={
            'email': 'admin@nexora.ai',
            'password': 'wrongpassword'
        })
        print(f'Wrong password status: {wrong_response.status_code}')
        print(f'Wrong password response: {wrong_response.json()}')

asyncio.run(test())