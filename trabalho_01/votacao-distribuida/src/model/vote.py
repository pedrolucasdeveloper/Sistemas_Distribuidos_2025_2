class Vote:
    def __init__(self, voter_id, candidate_id, timestamp):
        self.voter_id = voter_id
        self.candidate_id = candidate_id
        self.timestamp = timestamp

    def __str__(self):
        return f"Vote(voter_id={self.voter_id}, candidate_id={self.candidate_id}, timestamp={self.timestamp})"