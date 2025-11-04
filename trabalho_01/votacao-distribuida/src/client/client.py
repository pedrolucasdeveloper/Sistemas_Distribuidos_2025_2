import os
import sys
import socket
import pickle

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

        login_reply = pickle.loads(self.socket.recv(4096))
        if login_reply['success']:
            # Expecting 'candidates_by_office'
            candidates_by_office = login_reply.get('candidates_by_office')
            print("Login bem-sucedido! Candidatos por cargo recebidos.")
            return candidates_by_office
        else:
            print("Login falhou!")
            return None

    def votar(self, voter_id, candidates_by_office):
        # Interactive selection per office
        votes = {}
        for office, candidates in candidates_by_office.items():
            print(f"\n--- Cargo: {office} ---")
            for c in candidates:
                print(f"{c.id}: {c.name} ({c.party})")

            # prompt user to choose candidate id (allow blank to skip)
            while True:
                choice = input(f"Escolha o id do candidato para {office} (ou Enter para nulo): ").strip()
                if choice == "":
                    votes[office] = None
                    break
                try:
                    cid = int(choice)
                except ValueError:
                    print("Entrada inválida, digite um número ou Enter.")
                    continue

                # verify selection exists in provided list
                if any(c.id == cid for c in candidates):
                    votes[office] = cid
                    break
                else:
                    print("Id não encontrado para esse cargo. Tente novamente.")

        vote_request = {'voter_id': voter_id, 'votes': votes}
        self.socket.send(pickle.dumps(vote_request))

        vote_reply = pickle.loads(self.socket.recv(4096))
        if vote_reply['success']:
            print("Votos registrados com sucesso.")
        else:
            print(f"Erro: {vote_reply.get('message', 'Erro desconhecido!')}")


if __name__ == "__main__":
    client = Client()
    username = input("Usuário: ")
    password = input("Senha: ")
    candidates_by_office = client.login(username, password)
    if candidates_by_office:
        # ask for voter id
        while True:
            vid = input("Digite seu id de eleitor (número): ").strip()
            try:
                voter_id = int(vid)
                break
            except ValueError:
                print("Id inválido. Digite um número.")

        client.votar(voter_id, candidates_by_office)