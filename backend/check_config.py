from app.core.config import get_settings
s = get_settings()
print('CORS_ORIGINS:', s.CORS_ORIGINS)
print('FRONTEND_URL:', s.FRONTEND_URL)