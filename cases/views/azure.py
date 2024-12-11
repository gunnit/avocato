# storage_backend.py
import os

from storages.backends.azure_storage import AzureStorage


class AzureMediaStorage(AzureStorage):
    account_name = os.getenv("AZURE_ACCOUNT_NAME", "")  # Azure account name
    account_key = os.getenv("AZURE_STORAGE_CREDENTIAL", "")  # Azure account key
    azure_container = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "")  # Blob container name
    expiration_secs = None  # Set expiration time for the URLs (None = no expiration)
    account_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
