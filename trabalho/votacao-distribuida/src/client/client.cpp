#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <curl/curl.h>
#include <nlohmann/json.hpp> // Verifica se está instalado

// Para facilitar o uso do JSON
using json = nlohmann::json;
using namespace std;

// --- Configuração ---
const string BASE_URL = "http://localhost:5000";

// --- Função Auxiliar para o CURL (Escreve a resposta numa string) ---
size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// --- Classe ApiClient ---
class ApiClient {
public:
    ApiClient() {
        curl_global_init(CURL_GLOBAL_ALL);
    }

    ~ApiClient() {
        curl_global_cleanup();
    }

    // Faz o POST e retorna o JSON de resposta (ou lança erro)
    json post_request(string endpoint, json payload) {
        CURL* curl = curl_easy_init();
        string readBuffer;
        long http_code = 0;

        if(curl) {
            string url = BASE_URL + endpoint;
            string json_str = payload.dump(); // Converte JSON para string

            struct curl_slist* headers = NULL;
            headers = curl_slist_append(headers, "Content-Type: application/json");

            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_str.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

            CURLcode res = curl_easy_perform(curl);
            
            if(res != CURLE_OK) {
                cerr << "Erro no cURL: " << curl_easy_strerror(res) << endl;
            }
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
            curl_easy_cleanup(curl);
            curl_slist_free_all(headers);
        }

        if (readBuffer.empty()) return nullptr;
        
        // Retorna o JSON parseado
        try {
            return json::parse(readBuffer);
        } catch (...) {
            return json{{"error", "Erro ao processar resposta do servidor"}};
        }
    }

    json login(string username, string password) {
        json payload = {
            {"username", username},
            {"password", password}
        };

        json response = post_request("/login", payload);

        if (response.contains("candidates")) {
            if (response.contains("message")) {
                cout << "--- " << response["message"].get<string>() << " ---" << endl;
            }
            return response["candidates"];
        } else {
            cout << "Erro no login!" << endl;
            return nullptr;
        }
    }

    json submit_votes(int voter_id, json votes) {
        json payload = {
            {"voter_id", voter_id},
            {"votes", votes}
        };
        return post_request("/votes", payload);
    }
};

// --- Função Principal ---
int main() {
    ApiClient client;
    string username, password;

    cout << "=== SISTEMA DE VOTACAO (CLIENTE C++) ===" << endl;
    
    cout << "Usuario: ";
    cin >> username;
    cout << "Senha: ";
    cin >> password;

    // 1. Login
    json candidates_by_office = client.login(username, password);

    if (candidates_by_office == nullptr || candidates_by_office.is_null()) {
        return 1;
    }

    // 2. Votação
    json votes_map; // Objeto JSON para guardar os votos

    // Limpar buffer do cin antes de usar getline
    cin.ignore(); 

    // Itera sobre os cargos (JSON Objects em C++)
    for (auto& [office, candidates_list] : candidates_by_office.items()) {
        cout << "\n--- Cargo: " << office << " ---" << endl;

        if (candidates_list.empty()) {
            cout << "Nenhum candidato cadastrado." << endl;
            votes_map[office] = nullptr;
            continue;
        }

        // Lista candidatos
        for (auto& c : candidates_list) {
            cout << "[" << c["id"] << "] " << c["name"].get<string>() 
                 << " (" << c["party"].get<string>() << ")" << endl;
        }

        while (true) {
            cout << "Digite o ID para " << office << " (ou ENTER para Nulo): ";
            string input_str;
            getline(cin, input_str);

            if (input_str.empty()) {
                votes_map[office] = nullptr; // Define como null no JSON
                cout << "Voto NULO registrado." << endl;
                break;
            }

            try {
                int cid = stoi(input_str);
                bool found = false;
                
                // Verifica se ID existe na lista
                for (auto& c : candidates_list) {
                    if (c["id"] == cid) {
                        found = true;
                        break;
                    }
                }

                if (found) {
                    votes_map[office] = cid;
                    break;
                } else {
                    cout << "ID invalido! Tente novamente." << endl;
                }

            } catch (...) {
                cout << "Entrada invalida. Digite apenas numeros." << endl;
            }
        }
    }

    // 3. Finalização
    cout << "\n--- Finalizacao ---" << endl;
    int voter_id;
    while(true) {
        cout << "Digite seu ID de eleitor: ";
        if (cin >> voter_id) {
            break;
        } else {
            cout << "ID invalido. Digite um numero." << endl;
            cin.clear();
            cin.ignore(10000, '\n');
        }
    }

    cout << "Enviando votos..." << endl;
    json result = client.submit_votes(voter_id, votes_map);

    if (result.contains("message")) {
        cout << "\n[SUCESSO]: " << result["message"].get<string>() << endl;
    } else if (result.contains("error")) {
        cout << "\n[ERRO]: " << result["error"].get<string>() << endl;
    } else {
        cout << "\n[RESPOSTA]: " << result.dump() << endl;
    }

    return 0;
}