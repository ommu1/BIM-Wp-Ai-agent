# app/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Meta / WhatsApp
    whatsapp_token: str = ""
    phone_number_id: str = "1039490259245462"
    # ADD THIS LINE TO FIX THE ERROR
    whatsapp_business_account_id: str = "891235163757950" 
    verify_token: str = "bim_training_webhook_secret_2026"

    # OpenAI
    openai_api_key: str = ""

    # Google Sheets
    google_sheets_spreadsheet_id: str = ""
    google_service_account_json: str = "{}"

    # Email
    gmail_user: str = "btpai1991@gmail.com"
    gmail_app_password: str = "Abhishek_1991"

    # Business
    admin_phone: str = "919668737803"
    business_name: str = "BIM Training & Projects"
    website_url: str = "https://www.bimtrainingandprojects.com"
    privacy_policy_url: str = "https://www.bimtrainingandprojects.com/privacy-policy"
    terms_url: str = "https://www.bimtrainingandprojects.com/terms-of-service"
    upi_qr_image_url: str = ""
    upi_id: str = "bimtraining@upi"
    upi_name: str = "BIM Training and Projects"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False
        # ADD THIS TO PREVENT FUTURE CRASHES
        extra = "ignore" 

@lru_cache()
def get_settings() -> Settings:
    return Settings()