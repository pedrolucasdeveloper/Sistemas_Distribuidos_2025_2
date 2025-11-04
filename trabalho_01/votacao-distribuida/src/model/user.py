class User:
    def __init__(self, id, name, role):
        self.id = id
        self.name = name
        self.role = role  # "eleitor" ou "administrador"

    def __str__(self):
        return f"User(id={self.id}, name={self.name}, role={self.role})"
