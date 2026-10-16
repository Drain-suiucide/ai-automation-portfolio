import enum


class UserRole(str, enum.Enum):
    viewer = "viewer"
    agent = "agent"
    manager = "manager"
    admin = "admin"


class MailboxProvider(str, enum.Enum):
    gmail = "gmail"
    outlook = "outlook"
    imap = "imap"


class EmailDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"