from xmlrpc.server import SimpleXMLRPCServer
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.candidate import Candidate
from model.vote import Vote

class ElectionService:
    def __init__(self):
        # reaproveita a lógica do teu Server.__init__
        self.OFFICES = [
            'governador',
            'deputado_estadual',
            'deputado_federal',
            'senador',
            'presidente'
        ]
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

    # ESTE é o "RMI": um único método remoto doOperation
    def doOperation(self, request_json: str) -> str:
        """
        request_json: JSON com { "objectReference": "...", "methodId": "...", "arguments": {...} }
        retorna: JSON com { "success": bool, "result": ..., "error": ... }
        """
        req = json.loads(request_json)
        obj = req.get("objectReference")
        method = req.get("methodId")
        args = req.get("arguments", {})

        try:
            if obj != "ElectionService":
                raise ValueError("Objeto remoto desconhecido")

            if method == "login":
                result = self._login(args["username"], args["password"])
            elif method == "submitVotes":
                result = self._submit_votes(args["voter_id"], args["votes"])
            elif method == "getPartialResults":
                result = self._get_partial_results()
            else:
                raise ValueError(f"Método remoto desconhecido: {method}")

            reply = {"success": True, "result": result, "error": None}
        except Exception as e:
            reply = {"success": False, "result": None, "error": str(e)}

        return json.dumps(reply)

    # Métodos "locais" chamados pelo doOperation

    def _login(self, username, password):
        # se não tiver autenticação de verdade, você pode aceitar qualquer coisa
        # e devolver os candidatos por cargo em JSON (passagem por valor)
        candidates_by_office = {
            office: [
                {"id": c.id, "name": c.name, "party": c.party}
                for c in self.candidates if c.office == office
            ]
            for office in self.OFFICES
        }
        return {"candidates_by_office": candidates_by_office}

    def _submit_votes(self, voter_id, votes_map):
        if self.prazo_finalizado:
            raise ValueError("Prazo de votação encerrado.")

        stored = {}
        # votes_map = { "governador": 13, "presidente": 22, ... } ou None para nulo
        import time
        ts = time.time()
        for office, candidate_id in votes_map.items():
            if candidate_id is None:
                stored[office] = None
            else:
                valid = any(c.id == candidate_id and c.office == office
                            for c in self.candidates)
                if not valid:
                    stored[office] = None
                else:
                    stored[office] = {
                        "voter_id": voter_id,
                        "candidate_id": candidate_id,
                        "office": office,
                        "timestamp": ts,
                    }
        self.votes[voter_id] = stored
        return {"message": "Votos registrados com sucesso."}

    def _get_partial_results(self):
        # exemplo: conta votos por office/candidate
        results = {office: {} for office in self.OFFICES}
        for voter_votes in self.votes.values():
            for office, vote in voter_votes.items():
                if vote is None:
                    continue
                cid = vote["candidate_id"]
                results[office][cid] = results[office].get(cid, 0) + 1
        return results


if __name__ == "__main__":
    service = ElectionService()
    with SimpleXMLRPCServer(("localhost", 8000), allow_none=True) as server:
        # registra a função remota com exatamente o nome doOperation
        server.register_function(service.doOperation, "doOperation")
        print("Servidor RMI Python rodando na porta 8000...")
        server.serve_forever()