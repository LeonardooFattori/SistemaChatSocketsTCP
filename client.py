import socket
import threading
import sys
import datetime

class ChatClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.running = True
        self.receive_thread = None

    def connect(self):
        """Conecta ao servidor"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print("Conectado ao servidor!")
            return True
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            return False

    def login(self):
        """Realiza o login no servidor"""
        try:
            # Aguarda solicitação de nome
            msg = self.client_socket.recv(1024).decode('utf-8')
            if msg == "NOME":
                while True:
                    username = input("Digite seu nome: ").strip()
                    if username:
                        self.client_socket.send(username.encode('utf-8'))
                        break
                    print("Nome não pode ser vazio!")
                
                # Aguarda resposta do servidor
                response = self.client_socket.recv(1024).decode('utf-8')
                if response == "NOME_INVALIDO":
                    print("Nome já está em uso. Tente novamente.")
                    return False
                elif response == "CONECTADO":
                    self.username = username
                    print(f"Bem-vindo ao chat, {username}!")
                    print("Comandos disponíveis: /list, /msg [usuário] [mensagem], /exit")
                    return True
            return False
        except Exception as e:
            print(f"Erro durante login: {e}")
            return False

    def receive_messages(self):
        """Thread para receber mensagens do servidor"""
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"\n{message}")
                # Re-imprime o prompt
                if self.running:
                    sys.stdout.write("Você: ")
                    sys.stdout.flush()
            except Exception as e:
                if self.running:
                    print(f"\n[ERRO] Conexão perdida: {e}")
                break
        
        self.running = False
        print("\nDesconectado do servidor.")

    def send_messages(self):
        """Envia mensagens para o servidor"""
        while self.running:
            try:
                message = input("Você: ").strip()
                if not message:
                    continue
                
                if message.lower() in ['/exit', '/quit']:
                    self.running = False
                    break
                
                self.client_socket.send(message.encode('utf-8'))
            except Exception as e:
                if self.running:
                    print(f"Erro ao enviar mensagem: {e}")
                break
        
        self.disconnect()

    def disconnect(self):
        """Desconecta do servidor"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        print("Desconectado.")

    def run(self):
        """Executa o cliente"""
        if not self.connect():
            return
        
        if not self.login():
            self.disconnect()
            return
        
        # Inicia thread de recebimento
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        # Thread principal envia mensagens
        self.send_messages()

def main():
    """Função principal"""
    print("=== CHAT MULTIPLAYER ===\n")
    
    # Configurações de conexão
    host = input("Host (padrão localhost): ").strip() or 'localhost'
    port = input("Porta (padrão 5555): ").strip()
    port = int(port) if port else 5555
    
    client = ChatClient(host, port)
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário")
        client.disconnect()

if __name__ == "__main__":
    main()