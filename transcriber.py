from notion_client import Client
import secrets_txt as secrets  # Ensure you have a secrets.py file with your tokens
import logging
notion = Client(auth=secrets.Notion_secret)
response = notion.pages.create(
    parent={"database_id": secrets.database_id},
    properties={
        "Timestamp": {"date": {"start": "2025-04-18T14:30:22"}},
        "Type": {"select": {"name": "test"}},
        "Content": {"rich_text": [{"text": {"content": "Test"}}]}
    }
)
print(response)