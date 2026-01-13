from flask import Flask, request, jsonify
import sys
import os
import time

# Adiciona o diretório pai ao path para conseguir importar as models que estão em ../model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.candidate import Candidate
from model.vote import Vote
from model.user import User
from model.notice import Notice

app = Flask(__name__)

class ElectionService:
    def __init__(self):
        self.OFFICES = [
            'governador', 'deputado_estadual', 'deputado_federal', 'senador', 'presidente'
        ]
        
        # Inicialização dos Candidatos (Baseado nos dados do seu servidor anterior)
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

            # Deputado Federal (Ceará)
            Candidate(1001, "André Fernandes", "PL", office='deputado_federal'),
            Candidate(1002, "Júnior Mano", "PL", office='deputado_federal'),
            Candidate(1003, "Célio Studart", "PSD", office='deputado_federal'),

            # Deputado Estadual (Ceará)
            Candidate(10001, "Carmelo Neto", "PL", office='deputado_estadual'),
            Candidate(10002, "Evandro Leitão", "PDT", office='deputado_estadual'),
            Candidate(10003, "Marta Gonçalves", "PL", office='deputado_estadual'),
        ]
        
        # Armazenamento em memória dos votos
        self.votes = {}  # Formato: {voter_id: {office: vote_data}}
        
        # Inicialização dos Avisos (Corrigido para 4 argumentos conforme notice.py)
        ts = time.time()
        self.notices = [
            # Argumentos: admin_id, title, body, timestamp
            Notice(1, "Eleição 2024", "O horário de votação encerra às 17h.", ts),
            Notice(1, "Documentos", "É obrigatório apresentar documento oficial com foto.", ts)
        ]
        
        self.prazo_finalizado = False

# Instancia o serviço globalmente para ser usado pelas rotas
service = ElectionService()

# --- ROTA 1: LOGIN (Recupera Candidatos) ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Instancia o User para cumprir o requisito (passando os 3 argumentos que descobrimos)
    user = User(username, password, "voter") 
    
    # Agrupa os candidatos
    candidates_by_office = {
        office: [
            {"id": c.id, "name": c.name, "party": c.party}
            for c in service.candidates if c.office == office
        ]
        for office in service.OFFICES
    }
    
    # --- CORREÇÃO AQUI ---
    # Usamos a variável 'username' diretamente para evitar o erro de atributo desconhecido
    return jsonify({
        "message": f"Bem-vindo, {username}",
        "candidates": candidates_by_office
    }), 200

# --- ROTA 2: VOTAR ---
@app.route('/votes', methods=['POST'])
def submit_votes():
    """
    Recebe JSON: { "voter_id": "123", "votes": { "presidente": 13, "governador": null } }
    Retorna: Confirmação ou erro.
    """
    if service.prazo_finalizado:
        return jsonify({"error": "Prazo de votação encerrado."}), 403

    data = request.json
    voter_id = data.get('voter_id')
    votes_map = data.get('votes', {})
    
    if not voter_id:
        return jsonify({"error": "voter_id é obrigatório"}), 400

    stored_votes = {}
    ts = time.time()

    for office, candidate_id in votes_map.items():
        if candidate_id is None:
            stored_votes[office] = None
        else:
            # Valida se o candidato existe para aquele cargo específico
            valid_candidate = next(
                (c for c in service.candidates if c.id == candidate_id and c.office == office), 
                None
            )
            
            if not valid_candidate:
                # Se candidato não existe ou cargo errado, considera voto nulo
                stored_votes[office] = None 
            else:
                # Cria objeto Vote
                vote_obj = Vote(voter_id, candidate_id, ts, office=office)
                
                # Serializa para armazenar no dicionário
                stored_votes[office] = {
                    "voter_id": vote_obj.voter_id,
                    "candidate_id": vote_obj.candidate_id,
                    "office": vote_obj.office,
                    "timestamp": vote_obj.timestamp
                }

    # Salva os votos do eleitor
    service.votes[voter_id] = stored_votes
    return jsonify({"message": "Votos registrados com sucesso."}), 201

# --- ROTA 3: RESULTADOS PARCIAIS ---
@app.route('/results', methods=['GET'])
def get_results():
    """Retorna a contagem de votos por cargo."""
    results = {office: {} for office in service.OFFICES}
    
    for voter_votes in service.votes.values():
        for office, vote_data in voter_votes.items():
            if vote_data is None:
                continue
            
            cid = vote_data["candidate_id"]
            # Converte ID para string pois chaves de JSON devem ser strings
            cid_str = str(cid)
            results[office][cid_str] = results[office].get(cid_str, 0) + 1
            
    return jsonify(results), 200

# --- ROTA 4: AVISOS (Usa a entidade Notice) ---
@app.route('/notices', methods=['GET'])
def get_notices():
    """Retorna avisos gerais da eleição."""
    notices_list = [
        {
            "admin_id": n.admin_id,
            "title": n.title,
            "body": n.body,
            "timestamp": n.timestamp
        } 
        for n in service.notices
    ]
    return jsonify(notices_list), 200

if __name__ == '__main__':
    print("API REST da Eleição rodando em http://localhost:5000")
    # 'host=0.0.0.0' permite acesso externo se necessário
    app.run(host='0.0.0.0', port=5000, debug=True)