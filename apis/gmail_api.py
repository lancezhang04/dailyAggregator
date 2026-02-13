import os.path
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError


class GmailClient:
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def __init__(
        self,
        credentials_path="playground/gmail_api/credentials.json",
        token_path="playground/gmail_api/token.json",
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    # If refresh fails, delete token and re-authenticate
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def send_email(self, to: str, subject: str, content: str, html_content: str = None):
        """Sends an email using the Gmail API."""
        try:
            service = build("gmail", "v1", credentials=self.creds)
            message = EmailMessage()
            message["To"] = to
            message["From"] = "me"
            message["Subject"] = subject

            # Add plain text part
            message.set_content(content)

            # Add HTML part if provided
            if html_content:
                message.add_alternative(html_content, subtype="html")

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message}
            send_message = (
                service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            print(f'Message Id: {send_message["id"]}')
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        return send_message
