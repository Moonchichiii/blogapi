from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = self.get_raw_token_from_cookies(request)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_raw_token_from_cookies(self, request):
        return request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])