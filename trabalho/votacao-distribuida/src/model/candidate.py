class Candidate:
    def __init__(self, id, name, party, office=None):
        self.id = id
        self.name = name
        self.party = party
        # office: governador, deputado_estadual, deputado_federal, senador, presidente
        self.office = office

    def __str__(self):
        return f"Candidate(id={self.id}, name={self.name}, party={self.party}, office={self.office})"