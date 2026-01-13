package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

type Candidate struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Party string `json:"party"`
}

type LoginResponse struct {
	Message    string                       `json:"message"`
	Candidates map[string][]Candidate       `json:"candidates"`
	Error      string                       `json:"error,omitempty"`
}

type VoteRequest struct {
	VoterID string            `json:"voter_id"`
	Votes   map[string]*int   `json:"votes"` // nil => JSON null
}

type ApiClient struct {
	BaseURL string
	Client  *http.Client
}

func NewApiClient(host string, port int) *ApiClient {
	return &ApiClient{
		BaseURL: fmt.Sprintf("http://%s:%d", host, port),
		Client: &http.Client{Timeout: 15 * time.Second},
	}
}

func (a *ApiClient) postJSON(endpoint string, payload any) (int, []byte, error) {
	url := a.BaseURL + endpoint
	bodyBytes, err := json.Marshal(payload)
	if err != nil {
		return 0, nil, err
	}

	req, err := http.NewRequest("POST", url, bytes.NewReader(bodyBytes))
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := a.Client.Do(req)
	if err != nil {
		return 0, nil, err
	}
	defer resp.Body.Close()

	respBytes, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, respBytes, nil
}

func (a *ApiClient) login(username, password string) (map[string][]Candidate, error) {
	payload := map[string]string{"username": username, "password": password}
	status, respBytes, err := a.postJSON("/login", payload)
	if err != nil {
		return nil, fmt.Errorf("não foi possível conectar à API. Verifique se o api_server.py está rodando")
	}

	if status != 200 {
		return nil, fmt.Errorf("erro no login (HTTP %d): %s", status, string(respBytes))
	}

	var lr LoginResponse
	if err := json.Unmarshal(respBytes, &lr); err != nil {
		return nil, fmt.Errorf("resposta inválida do servidor: %s", string(respBytes))
	}

	fmt.Printf("--- %s ---\n", lr.Message)
	return lr.Candidates, nil
}

func (a *ApiClient) submitVotes(voterID string, votes map[string]*int) (map[string]any, error) {
	payload := VoteRequest{VoterID: voterID, Votes: votes}
	status, respBytes, err := a.postJSON("/votes", payload)
	if err != nil {
		return map[string]any{"error": "Falha de conexão com o servidor."}, nil
	}

	// tenta JSON; se falhar, devolve como texto
	var out map[string]any
	if err := json.Unmarshal(respBytes, &out); err != nil {
		out = map[string]any{"raw": string(respBytes)}
	}
	out["http_status"] = status
	return out, nil
}

func readLine(r *bufio.Reader, prompt string) string {
	fmt.Print(prompt)
	s, _ := r.ReadString('\n')
	return strings.TrimSpace(s)
}

func main() {
	// Uso:
	// go run client_go.go
	// go run client_go.go 10.0.0.105 5000
	host := "localhost"
	port := 5000
	if len(os.Args) >= 2 {
		host = os.Args[1]
	}
	if len(os.Args) >= 3 {
		if p, err := strconv.Atoi(os.Args[2]); err == nil {
			port = p
		}
	}

	client := NewApiClient(host, port)
	reader := bufio.NewReader(os.Stdin)

	fmt.Println("=== SISTEMA DE VOTAÇÃO (CLIENTE GO - API REST) ===")
	username := readLine(reader, "Usuário: ")
	password := readLine(reader, "Senha: ")

	// 1) Login
	candidatesByOffice, err := client.login(username, password)
	if err != nil {
		fmt.Println("Erro:", err)
		os.Exit(1)
	}

	// Ordem fixa (igual ao seu servidor)
	offices := []string{"governador", "deputado_estadual", "deputado_federal", "senador", "presidente"}

	// 2) Votação
	votes := make(map[string]*int)

	for _, office := range offices {
		list, ok := candidatesByOffice[office]
		fmt.Printf("\n--- Cargo: %s ---\n", strings.ToUpper(office))

		if !ok || len(list) == 0 {
			fmt.Println("Nenhum candidato cadastrado.")
			votes[office] = nil
			continue
		}

		for _, c := range list {
			fmt.Printf("[%d] %s (%s)\n", c.ID, c.Name, c.Party)
		}

		for {
			choice := readLine(reader, fmt.Sprintf("Digite o ID para %s (ou ENTER para Nulo): ", office))
			if choice == "" {
				votes[office] = nil
				break
			}

			cid, err := strconv.Atoi(choice)
			if err != nil {
				fmt.Println("Digite apenas números.")
				continue
			}

			valid := false
			for _, c := range list {
				if c.ID == cid {
					valid = true
					break
				}
			}
			if !valid {
				fmt.Println("ID inválido!")
				continue
			}

			// precisa de variável local pra pegar endereço
			cidLocal := cid
			votes[office] = &cidLocal
			break
		}
	}

	// 3) Enviar
	fmt.Println("\n--- Finalização ---")
	voterID := readLine(reader, "Digite seu ID de eleitor: ")

	fmt.Println("Enviando votos...")
	result, _ := client.submitVotes(voterID, votes)
	pretty, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(pretty))
}