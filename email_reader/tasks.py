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

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

@shared_task(name='prefecture_project_manager.tasks.list_emails')
def list_emails():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("email_reader/token.json"):
        creds = Credentials.from_authorized_user_file("email_reader/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "email_reader/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("email_reader/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        q = 'from:(atendimento.corporativo@copel.com)'
        result: GmailListMessagesResponse = service.users().messages().list(userId='me').execute()
        messages: Optional[List[GmailMessageMetadata]] = result.get('messages')

        if not messages:
            print("No labels found.")
            return
        for msg in messages:
            try:
                txt: GmailMessage = service.users().messages().get(userId='me', id=msg['id']).execute()

                payload: MessagePayload = txt['payload']
                headers: List[MessageHeader] = payload['headers']

                subject: str = ""
                sender: str = ""
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']

                parts: MessagePart = payload.get('parts', [])[0]
                body: MessageBody = parts.get('body')
                data: Optional[str] = body.get('data') if body else None

                print("Subject: ", subject)
                print("From: ", sender)

                if data is not None:
                    data = data.replace("-", "+").replace("_", "/")
                    decoded_data: bytes = base64.b64decode(data)
                    decoded_data_str: str = decoded_data.decode('utf-8')
                    print("Message: ", decoded_data_str)
                else:
                    print('\n')
            except:
                pass

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")