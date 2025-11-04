class Candidate:
    def __init__(self, id, name, party):
        self.id = id
        self.name = name
        self.party = party

    def __str__(self):
        return f"Candidate(id={self.id}, name={self.name}, party={self.party})"