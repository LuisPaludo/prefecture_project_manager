import base64
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from celery import shared_task
from typing import List, Optional

from email_reader.migrations.interface.message_interface import GmailListMessagesResponse, GmailMessageMetadata, \
    GmailMessage, MessagePayload, MessageHeader, MessagePart, MessageBody

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_text_from_parts(parts: List[MessagePart] | None) -> Optional[str]:
    text = ""
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            body_data: Optional[str] = part.get('body', {}).get('data')
            if body_data:
                data = body_data.replace("-", "+").replace("_", "/")
                decoded_data = base64.b64decode(data)
                text += decoded_data.decode('utf-8', errors='replace')

        # Recursively check nested parts
        if part.get('parts'):
            text += get_text_from_parts(part['parts'])

    return text

def get_email_content(message: GmailMessage) -> str:
    payload = message.get('payload', {})

    if payload.get('body', {}).get('data'):
        body_data = payload['body']['data']
        data = body_data.replace("-", "+").replace("_", "/")
        decoded_data = base64.b64decode(data)
        return decoded_data.decode('utf-8', errors='replace')

    elif payload.get('parts'):
        return get_text_from_parts(payload['parts'])

    return "No readable content found"

def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if os.path.exists("email_reader/token.json"):
        creds = Credentials.from_authorized_user_file("email_reader/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "email_reader/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("email_reader/token.json", "w") as token:
            token.write(creds.to_json())

    return creds

def get_messages(creds: Credentials, q: str) -> List[GmailMessage] | None:
    service = build("gmail", "v1", credentials=creds)
    result: GmailListMessagesResponse = service.users().messages().list(userId='me', q=q).execute()
    messages_ids = result.get('messages')

    if not messages_ids:
        print("No messages found.")
        return None

    messages: List[GmailMessage] = []

    def add(id: int | None = None, msg: GmailMessage | None = None, err: str | None = None) -> None:
        if err:
            print(err)
        else:
            messages.append(msg)

    batch = service.new_batch_http_request()
    for msg in messages_ids:
        batch.add(service.users().messages().get(userId='me', id=msg['id']), add)
    batch.execute()

    return messages

@shared_task(name='prefecture_project_manager.tasks.list_emails')
def list_emails():
    creds = get_credentials()
    q = 'from:(atendimento.corporativo@copel.com)'

    try:
        messages = get_messages(creds, q)
        for msg in messages:
            try:
                # Get headers
                payload = msg['payload']
                headers = payload['headers']

                # Look for Subject and Sender Email in the headers
                subject = ""
                sender = ""
                date = ""
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']
                    if d['name'] == 'Date':
                        date = d['value']

                print(f"ID: {msg['id']}")
                print(f"Subject: {subject}")
                print(f"From: {sender}")
                print(f"Date: {date}")

                content = get_email_content(msg)
                print(f"Content:\n{content}\n")

                print("-" * 80)

            except Exception as e:
                print(f"Error processing message: {e}")

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")