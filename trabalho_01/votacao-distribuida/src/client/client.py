import socket
import pickle
from model.user import User
from model.vote import Vote

TCP_PORT = 5000

class Client:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', TCP_PORT))

    def login(self, username, password):
        login_request = {'username': username, 'password': password}
        self.socket.send(pickle.dumps(login_request))

        login_reply = pickle.loads(self.socket.recv(1024))
        if login_reply['success']:
            print(f"Login bem-sucedido! Candidatos disponíveis: {login_reply['candidates']}")
            return login_reply['candidates']
        else:
            print("Login falhou!")
            return None

    def votar(self, voter_id, candidate_id):
        vote_request = {'voter_id': voter_id, 'candidate_id': candidate_id}
        self.socket.send(pickle.dumps(vote_request))

        vote_reply = pickle.loads(self.socket.recv(1024))
        if vote_reply['success']:
            print(f"Voto registrado para o candidato {candidate_id}.")
        else:
            print(f"Erro: {vote_reply.get('message', 'Erro desconhecido!')}")

if __name__ == "__main__":
    client = Client()
    client.login('eleitor1', 'senha123')
    client.votar(1, 1)  # Eleitor 1 votando no Candidato 1