import socket
import threading
import datetime

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.clients = {}  # Dicionário para armazenar {socket: username}
        self.usernames = set()  # Conjunto para nomes de usuário únicos
        self.server_socket = None
        self.running = True

    def start(self):
        """Inicia o servidor e aceita conexões"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            print(f"[SERVIDOR] Iniciado em {self.host}:{self.port}")
            print("[SERVIDOR] Aguardando conexões...")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"[SERVIDOR] Nova conexão de {address}")
                    
                    # Inicia thread para lidar com o cliente
                    thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    thread.daemon = True
                    thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"[SERVIDOR] Erro ao aceitar conexão: {e}")
                    break
                    
        except Exception as e:
            print(f"[SERVIDOR] Erro ao iniciar: {e}")
        finally:
            self.stop()

    def handle_client(self, client_socket):
        """Gerencia a comunicação com um cliente"""
        username = None
        
        try:
            # Solicita nome de usuário
            client_socket.send("NOME".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            # Valida nome de usuário
            if not username or username in self.usernames:
                client_socket.send("NOME_INVALIDO".encode('utf-8'))
                client_socket.close()
                return
            
            # Registra o cliente
            self.clients[client_socket] = username
            self.usernames.add(username)
            
            # Envia confirmação
            client_socket.send("CONECTADO".encode('utf-8'))
            
            # Notifica todos sobre o novo usuário
            self.broadcast(f"Sistema: {username} entrou no chat", client_socket)
            
            # Envia lista de usuários para o novo cliente
            self.send_user_list(client_socket)
            
            print(f"[SERVIDOR] {username} conectado")
            
            # Loop principal de recebimento de mensagens
            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    
                    # Processa a mensagem
                    self.process_message(message, client_socket, username)
                    
                except Exception as e:
                    print(f"[SERVIDOR] Erro ao receber mensagem de {username}: {e}")
                    break
                    
        except Exception as e:
            print(f"[SERVIDOR] Erro com cliente {username or 'desconhecido'}: {e}")
        finally:
            # Remove o cliente
            self.remove_client(client_socket, username)

    def process_message(self, message, client_socket, username):
        """Processa mensagens recebidas"""
        if message.startswith('/'):
            # Comandos especiais
            self.handle_command(message, client_socket, username)
        else:
            # Mensagem pública
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {username}: {message}"
            self.broadcast(formatted_msg, client_socket)

    def handle_command(self, command, client_socket, username):
        """Processa comandos do cliente"""
        parts = command.split(' ', 2)
        cmd = parts[0].lower()
        
        if cmd == '/list':
            # Lista usuários online
            users_list = ', '.join(sorted(self.usernames))
            response = f"Usuários online ({len(self.usernames)}): {users_list}"
            client_socket.send(response.encode('utf-8'))
            
        elif cmd == '/msg' and len(parts) >= 3:
            # Mensagem privada
            target = parts[1]
            message = parts[2]
            self.send_private_message(username, target, message, client_socket)
            
        elif cmd == '/help':
            help_msg = """
Comandos disponíveis:
  /list           - Lista todos os usuários online
  /msg [usuário] [mensagem] - Envia mensagem privada
  /exit           - Sai do chat
  /help           - Mostra esta ajuda
            """
            client_socket.send(help_msg.encode('utf-8'))
            
        elif cmd in ['/exit', '/quit']:
            client_socket.close()
            
        else:
            client_socket.send("Comando desconhecido. Digite /help para ajuda.".encode('utf-8'))

    def send_private_message(self, sender, target, message, sender_socket):
        """Envia uma mensagem privada"""
        if target not in self.usernames:
            sender_socket.send(f"Usuário '{target}' não encontrado.".encode('utf-8'))
            return
        
        # Encontra o socket do destinatário
        target_socket = None
        for sock, name in self.clients.items():
            if name == target:
                target_socket = sock
                break
        
        if target_socket:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] [Privado de {sender}]: {message}"
            try:
                target_socket.send(formatted_msg.encode('utf-8'))
                sender_socket.send(f"[Privado para {target}]: {message}".encode('utf-8'))
            except:
                sender_socket.send(f"Erro ao enviar mensagem para {target}".encode('utf-8'))
        else:
            sender_socket.send(f"Usuário '{target}' não está online.".encode('utf-8'))

    def broadcast(self, message, sender_socket=None):
        """Envia mensagem para todos os clientes"""
        for client in list(self.clients.keys()):
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    pass

    def send_user_list(self, client_socket):
        """Envia a lista de usuários para um novo cliente"""
        users_list = ', '.join(sorted(self.usernames))
        message = f"Sistema: Usuários online: {users_list}"
        client_socket.send(message.encode('utf-8'))

    def remove_client(self, client_socket, username):
        """Remove um cliente do servidor"""
        if client_socket in self.clients:
            del self.clients[client_socket]
        
        if username and username in self.usernames:
            self.usernames.remove(username)
            self.broadcast(f"Sistema: {username} saiu do chat")
            print(f"[SERVIDOR] {username} desconectado")
        
        try:
            client_socket.close()
        except:
            pass

    def stop(self):
        """Para o servidor"""
        self.running = False
        
        # Fecha todas as conexões
        for client in list(self.clients.keys()):
            try:
                client.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[SERVIDOR] Servidor encerrado")

def main():
    """Função principal"""
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Interrompido pelo usuário")
        server.stop()

if __name__ == "__main__":
    main()