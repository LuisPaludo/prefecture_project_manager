from typing import List, Optional, TypedDict


class GmailMessageMetadata(TypedDict):
    id: str
    threadId: str


class GmailListMessagesResponse(TypedDict, total=False):
    messages: Optional[List[GmailMessageMetadata]]
    nextPageToken: Optional[str]
    resultSizeEstimate: Optional[int]


class MessageHeader(TypedDict):
    name: str
    value: str


class MessageBody(TypedDict, total=False):
    size: int
    data: Optional[str]
    attachmentId: Optional[str]


class MessagePart(TypedDict, total=False):
    partId: str
    mimeType: str
    filename: str
    headers: List[MessageHeader]
    body: MessageBody
    parts: Optional[List['MessagePart']]


class MessagePayload(TypedDict, total=False):
    partId: str
    mimeType: str
    filename: str
    headers: List[MessageHeader]
    body: MessageBody
    parts: Optional[List[MessagePart]]


class GmailMessage(TypedDict):
    id: str
    threadId: str
    labelIds: List[str]
    snippet: str
    payload: MessagePayload
    sizeEstimate: Optional[int]
    historyId: Optional[str]
    internalDate: Optional[str]
