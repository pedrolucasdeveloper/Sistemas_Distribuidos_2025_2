import socket
import threading
import pickle
from model.vote import Vote
from model.candidate import Candidate
from model.user import User
from datetime import datetime

# Configurações de rede
TCP_PORT = 5000
UDP_PORT = 4446
MULTICAST_GROUP = '230.0.0.1'

class Server:
    def __init__(self):
        self.candidates = [
            Candidate(1, "Candidato A", "Partido X"),
            Candidate(2, "Candidato B", "Partido Y")
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
        threading.Thread(target=self.send_multicast).start()

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Nova conexão de {client_address}")
            threading.Thread(target=self.client_handler, args=(client_socket,)).start()

    def client_handler(self, client_socket):
        with client_socket:
            # Recebe e processa a requisição de login
            login_request = pickle.loads(client_socket.recv(1024))
            print(f"Login solicitado: {login_request}")

            # Responde com a lista de candidatos
            login_reply = {'success': True, 'candidates': self.candidates}
            client_socket.send(pickle.dumps(login_reply))

            # Recebe e processa o voto
            if not self.prazo_finalizado:
                vote_request = pickle.loads(client_socket.recv(1024))
                print(f"Voto recebido: {vote_request}")
                vote = Vote(vote_request['voter_id'], vote_request['candidate_id'], datetime.now().timestamp())
                self.votes[vote_request['voter_id']] = vote
                client_socket.send(pickle.dumps({'success': True}))
            else:
                client_socket.send(pickle.dumps({'success': False, 'message': 'Prazo de votação encerrado.'}))

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