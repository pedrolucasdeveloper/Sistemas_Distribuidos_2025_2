import requests
import sys

class ApiClient:
    def __init__(self, host="localhost", port=5000):
        # O cliente apenas aponta para onde o servidor está
        self.base_url = f"http://{host}:{port}"

    def login(self, username, password):
        """Faz POST em /login para autenticar e buscar candidatos"""
        url = f"{self.base_url}/login"
        payload = {"username": username, "password": password}
        
        try:
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"--- {data.get('message')} ---")
                return data.get("candidates")
            else:
                print(f"Erro no login: {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            print("Erro: Não foi possível conectar à API. Verifique se o 'api_server.py' está rodando.")
            return None

    def submit_votes(self, voter_id, votes):
        url = f"{self.base_url}/votes"
        payload = {"voter_id": voter_id, "votes": votes}
        
        try:
            response = requests.post(url, json=payload)
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "Falha de conexão com o servidor."}

if __name__ == "__main__":
    client = ApiClient()

    print("=== SISTEMA DE VOTAÇÃO (CLIENTE API REST) ===")
    username = input("Usuário: ")
    password = input("Senha: ")

    # 1. Login
    candidates_by_office = client.login(username, password)

    if not candidates_by_office:
        sys.exit(1)

    # 2. Votação
    votes = {}
    for office, candidates_list in candidates_by_office.items():
        print(f"\n--- Cargo: {office.upper()} ---")
        
        if not candidates_list:
            print("Nenhum candidato cadastrado.")
            votes[office] = None
            continue

        for c in candidates_list:
            print(f"[{c['id']}] {c['name']} ({c['party']})")

        while True:
            choice = input(f"Digite o ID para {office} (ou ENTER para Nulo): ").strip()
            if choice == "":
                votes[office] = None
                break
            try:
                cid = int(choice)
                if any(c['id'] == cid for c in candidates_list):
                    votes[office] = cid
                    break
                else:
                    print("ID inválido!")
            except ValueError:
                print("Digite apenas números.")

    # 3. Enviar
    print("\n--- Finalização ---")
    voter_id = input("Digite seu ID de eleitor: ")
    
    print("Enviando votos...")
    result = client.submit_votes(voter_id, votes)
    print(result)