# Sistema de Votação Distribuída  
Implementação em Python com comunicação TCP para votação e UDP multicast para envio de notificações.

## Visão Geral  
Este projeto implementa um sistema de votação distribuída onde:  
- Eleitores se conectam via cliente TCP para realizar login e votar.  
- O servidor recebe os votos, armazena‑os, e pode apurar resultados.  
- O servidor também envia periodicamente mensagens informativas via multicast UDP aos eleitores.  
- O objetivo é demonstrar conceitos de rede distribuída, multithreading, serialização de objetos e integração de comunicação TCP/UDP.

## Funcionalidades Principais  
- Autenticação simples de eleitores (login).  
- Listagem de candidatos disponíveis para votação.  
- Registro de voto por eleitor.  
- Envio de mensagens de aviso ou informação via multicast UDP.  
- Estrutura modular: modelos, cliente, servidor, utilitários.

## Tecnologias  
- Linguagem: **Python 3.x**  
- Biblioteca padrão de sockets (`socket`, `threading`, `pickle`)  
- Serialização: `pickle` (pode ser trocada por JSON ou Protobuf)  
- Estrutura de pacotes para melhor organização do código
