from social_core.backends.google import GoogleOAuth2

class CustomGoogleOAuth2(GoogleOAuth2):
    """
    Кастомный бэкенд GoogleOAuth2 для отключения проверки 'state'.
    Это необходимо для stateless API, где флоу начинается на фронтенде.
    """
    def validate_state(self):
        # Пропускаем проверку state
        return None
