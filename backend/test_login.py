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
        print(f'Login response: {response.json()}')
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f'Token: {token[:30]}...')
            
            # Test /auth/me
            headers = {'Authorization': f'Bearer {token}'}
            me_response = await client.get('http://localhost:8000/api/v1/auth/me', headers=headers)
            print(f'Me status: {me_response.status_code}')
            print(f'Me response: {me_response.json()}')

asyncio.run(test())