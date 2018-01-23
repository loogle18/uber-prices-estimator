from os import environ


environment = environ.get("ENVIRONMENT", "development")
debug_mode = environment == "development"
uber_client_token = environ.get("UBER_CLIENT_TOKEN")
google_api_key = environ.get("GOOGLE_API_KEY")
app_user_login = environ.get("APP_USER_LOGIN")
app_user_password = environ.get("APP_USER_PASSWORD")
