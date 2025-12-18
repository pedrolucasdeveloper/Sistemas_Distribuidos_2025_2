import json
import xmlrpc.client

class RmiClient:
    def __init__(self, host="localhost", port=8000):
        url = f"http://{host}:{port}/"
        self.proxy = xmlrpc.client.ServerProxy(url, allow_none=True)

    def do_operation(self, object_ref, method_id, arguments: dict):
        request = {
            "objectReference": object_ref,
            "methodId": method_id,
            "arguments": arguments,
        }
        request_json = json.dumps(request)
        reply_json = self.proxy.doOperation(request_json)
        reply = json.loads(reply_json)
        return reply


if __name__ == "__main__":
    client = RmiClient()

    username = input("Usuário: ")
    password = input("Senha: ")

    # chamada remota login
    resp = client.do_operation(
        "ElectionService",
        "login",
        {"username": username, "password": password}
    )

    if not resp["success"]:
        print("Login falhou:", resp["error"])
        exit(1)

    candidates_by_office = resp["result"]["candidates_by_office"]
    print("Login ok! Cargos e candidatos recebidos.")

    # interação similar ao client.py antigo, mas agora montando JSON
    votes = {}
    for office, candidates in candidates_by_office.items():
        print(f"\n--- Cargo: {office} ---")
        for c in candidates:
            print(f'{c["id"]}: {c["name"]} ({c["party"]})')

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
            if any(c["id"] == cid for c in candidates):
                votes[office] = cid
                break
            else:
                print("Id não encontrado para esse cargo. Tente novamente.")

    voter_id = int(input("\nDigite seu id de eleitor (número): "))

    resp = client.do_operation(
        "ElectionService",
        "submitVotes",
        {"voter_id": voter_id, "votes": votes}
    )

    if resp["success"]:
        print(resp["result"]["message"])
    else:
        print("Erro ao registrar votos:", resp["error"])