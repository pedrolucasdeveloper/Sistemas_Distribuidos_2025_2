class Notice:
    def __init__(self, admin_id, title, body, timestamp):
        self.admin_id = admin_id
        self.title = title
        self.body = body
        self.timestamp = timestamp

    def __str__(self):
        return f"Notice(admin_id={self.admin_id}, title={self.title}, body={self.body}, timestamp={self.timestamp})"