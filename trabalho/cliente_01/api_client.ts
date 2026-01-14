import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

type Office =
  | "governador"
  | "deputado_estadual"
  | "deputado_federal"
  | "senador"
  | "presidente";

type Candidate = {
  id: number;
  name: string;
  party: string;
};

type CandidatesByOffice = Record<string, Candidate[]>; // vem do servidor como dict de cargos

type VotesMap = Record<string, number | null>;

class ApiClient {
  private baseUrl: string;

  constructor(host: string = "localhost", port: number = 5000) {
    this.baseUrl = `http://${host}:${port}`;
  }

  async login(username: string, password: string): Promise<CandidatesByOffice | null> {
    const url = `${this.baseUrl}/login`;
    const payload = { username, password };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 200) {
        const data = (await res.json()) as { message?: string; candidates: CandidatesByOffice };
        console.log(`--- ${data?.message ?? "Bem-vindo"} ---`);
        return data.candidates;
      } else {
        const text = await res.text();
        console.log(`Erro no login: ${text}`);
        return null;
      }
    } catch {
      console.log(
        "Erro: Não foi possível conectar à API. Verifique se o 'api_server.py' está rodando."
      );
      return null;
    }
  }

  async submit_votes(voter_id: string, votes: VotesMap): Promise<any> {
    const url = `${this.baseUrl}/votes`;
    const payload = { voter_id, votes };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      // seu servidor tende a responder JSON, mas vamos ser robustos:
      const text = await res.text();
      try {
        return JSON.parse(text);
      } catch {
        return { error: text };
      }
    } catch {
      return { error: "Falha de conexão com o servidor." };
    }
  }
}

function upper(s: string) {
  return s.toUpperCase();
}

function isValidCandidateId(candidates: Candidate[], id: number): boolean {
  return candidates.some((c) => c.id === id);
}

async function main() {
  // Permite host/port por args:
  // npx ts-node client_ts.ts 192.168.0.10 5000
  const host = process.argv[2] ?? "localhost";
  const port = Number(process.argv[3] ?? "5000");

  const client = new ApiClient(host, port);

  const rl = readline.createInterface({ input, output });

  console.log("=== SISTEMA DE VOTAÇÃO (CLIENTE API REST - TS) ===");
  const username = (await rl.question("Usuário: ")).trim();
  const password = (await rl.question("Senha: ")).trim();

  // 1) Login
  const candidatesByOffice = await client.login(username, password);
  if (!candidatesByOffice) {
    rl.close();
    process.exit(1);
  }

  // 2) Votação
  const votes: VotesMap = {};

  for (const [office, candidatesList] of Object.entries(candidatesByOffice)) {
    console.log(`\n--- Cargo: ${upper(office)} ---`);

    if (!candidatesList || candidatesList.length === 0) {
      console.log("Nenhum candidato cadastrado.");
      votes[office] = null;
      continue;
    }

    for (const c of candidatesList) {
      console.log(`[${c.id}] ${c.name} (${c.party})`);
    }

    while (true) {
      const choice = (await rl.question(
        `Digite o ID para ${office} (ou ENTER para Nulo): `
      )).trim();

      if (choice === "") {
        votes[office] = null;
        break;
      }

      const cid = Number(choice);
      if (!Number.isInteger(cid)) {
        console.log("Digite apenas números.");
        continue;
      }

      if (!isValidCandidateId(candidatesList, cid)) {
        console.log("ID inválido!");
        continue;
      }

      votes[office] = cid;
      break;
    }
  }

  // 3) Enviar
  console.log("\n--- Finalização ---");
  const voterId = (await rl.question("Digite seu ID de eleitor: ")).trim();

  console.log("Enviando votos...");
  const result = await client.submit_votes(voterId, votes);
  console.log(result);

  rl.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});