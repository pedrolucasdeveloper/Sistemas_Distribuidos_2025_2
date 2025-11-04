import os
import sys
import socket
import threading
import pickle
import time
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.vote import Vote
from model.candidate import Candidate
from model.user import User

# Configurações de rede
TCP_PORT = 5000
UDP_PORT = 4446
MULTICAST_GROUP = '230.0.0.1'


class Server:
    def __init__(self):
        # Offices follow Brazilian model
        self.OFFICES = [
            'governador',
            'deputado_estadual',
            'deputado_federal',
            'senador',
            'presidente'
        ]

        # Candidatos utilizados no sistema (ids inteiros para seleção por cargo)
        # Presidente
        self.candidates = [
            Candidate(13, "Luiz Inácio Lula da Silva", "PT", office='presidente'),
            Candidate(22, "Jair Bolsonaro", "PL", office='presidente'),
            Candidate(12, "Ciro Gomes", "PDT", office='presidente'),

            # Governador do Ceará
            Candidate(13, "Elmano de Freitas", "PT", office='governador'),
            Candidate(44, "Capitão Wagner", "União Brasil (UNIÃO)", office='governador'),
            Candidate(12, "Roberto Cláudio", "PDT", office='governador'),

            # Senador (Ceará)
            Candidate(131, "Camilo Santana", "PT", office='senador'),
            Candidate(700, "Kamila Cardoso", "Avante", office='senador'),
            Candidate(555, "Érika Amorim", "PSD", office='senador'),

            # Deputado Federal (Ceará) — ids internos (placeholders)
            Candidate(1001, "André Fernandes", "PL", office='deputado_federal'),
            Candidate(1002, "Júnior Mano", "PL", office='deputado_federal'),
            Candidate(1003, "Célio Studart", "PSD", office='deputado_federal'),

            # Deputado Estadual (Ceará) — ids internos (placeholders)
            Candidate(10001, "Carmelo Neto", "PL", office='deputado_estadual'),
            Candidate(10002, "Evandro Leitão", "PDT", office='deputado_estadual'),
            Candidate(10003, "Marta Gonçalves", "PL", office='deputado_estadual'),
        ]
        self.votes = {}
        self.prazo_finalizado = False

    def start(self):
        # Iniciar o servidor TCP
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', TCP_PORT))
        server_socket.listen(5)
        print(f"Servidor escutando na porta {TCP_PORT}...")

        # Iniciar thread para enviar mensagens UDP de multicast
        threading.Thread(target=self.send_multicast, daemon=True).start()

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Nova conexão de {client_address}")
            threading.Thread(target=self.client_handler, args=(client_socket,)).start()

    def client_handler(self, client_socket):
        with client_socket:
            # Recebe e processa a requisição de login
            login_request = pickle.loads(client_socket.recv(1024))
            print(f"Login solicitado: {login_request}")
            # Responde com a lista de candidatos agrupada por cargo
            candidates_by_office = {office: [c for c in self.candidates if c.office == office] for office in self.OFFICES}
            login_reply = {'success': True, 'candidates_by_office': candidates_by_office}
            client_socket.send(pickle.dumps(login_reply))

            # Recebe e processa os votos por cargo
            if self.prazo_finalizado:
                client_socket.send(pickle.dumps({'success': False, 'message': 'Prazo de votação encerrado.'}))
                return

            vote_request = pickle.loads(client_socket.recv(4096))
            print(f"Voto recebido: {vote_request}")

            # Expecting vote_request = {'voter_id': ..., 'votes': {office: candidate_id, ...}}
            voter_id = vote_request.get('voter_id')
            votes_map = vote_request.get('votes', {})

            stored = {}
            timestamp = datetime.now().timestamp()
            for office, candidate_id in votes_map.items():
                # Validate candidate exists for that office
                valid = any(c.id == candidate_id and c.office == office for c in self.candidates)
                if not valid:
                    # invalid vote - ignore or mark as null; here we record None
                    stored[office] = None
                else:
                    stored[office] = Vote(voter_id, candidate_id, timestamp, office=office)

            # Save voter's votes (overwrites previous if any)
            self.votes[voter_id] = stored
            client_socket.send(pickle.dumps({'success': True}))

    def send_multicast(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

        while not self.prazo_finalizado:
            message = "Mensagem informativa para todos os eleitores!"
            udp_socket.sendto(message.encode(), (MULTICAST_GROUP, UDP_PORT))
            print(f"Enviando mensagem multicast: {message}")
            time.sleep(5)


if __name__ == "__main__":
    server = Server()
    server.start()
