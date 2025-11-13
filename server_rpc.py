# servidor_jogo.py
import rpyc
import random
from rpyc.utils.server import ThreadedServer

PORTA = 18861

class ServicoJogo(rpyc.Service):
    # Dicionário de jogadores e contador de ID como VARIÁVEIS DE CLASSE.
    # Isso garante que a mesma lista seja compartilhada entre todas as conexões de clientes.
    jogadores = {}
    proximo_id = 0
    
    cores = ["crimson", "aquamarine", "pink", "gold", "red", "brown", 
             "blue", "yellow", "orange", "purple", "white", "cyan"]

    def on_connect(self, conn):
        print(f"Nova conexão recebida. Total de jogadores agora: {len(self.jogadores)}")

    def on_disconnect(self, conn):
        print("A conexão de um cliente foi perdida.")
        # A lógica de remover o jogador na desconexão seria implementada aqui.

    def exposed_registrar_jogador(self, username):
        meu_id = ServicoJogo.proximo_id # Acessa a variável de classe
        
        dados_jogador = {
            'x': 0, 'y': 0,
            'color': random.choice(ServicoJogo.cores),
            'username': username
        }
        
        ServicoJogo.jogadores[meu_id] = dados_jogador # Modifica a variável de classe
        ServicoJogo.proximo_id += 1
        
        print(f"Jogador registrado: {username} (ID: {meu_id}) - Total: {len(ServicoJogo.jogadores)}")
        return meu_id, dados_jogador

    def exposed_obter_estado_jogo(self):
        # Envia a lista compartilhada de jogadores
        return list(ServicoJogo.jogadores.items())

    def exposed_atualizar_movimento(self, id, x, y):
        # Atualiza a lista compartilhada de jogadores
        if id in ServicoJogo.jogadores:
            ServicoJogo.jogadores[id]['x'] = x
            ServicoJogo.jogadores[id]['y'] = y
        return "OK"
    
    def exposed_desconectar_jogador(self, id):
        if id in ServicoJogo.jogadores:
            username = ServicoJogo.jogadores[id]['username']
            del ServicoJogo.jogadores[id]
            print(f"Jogador desconectado: {username} (ID: {id}) - Total: {len(ServicoJogo.jogadores)}")
        return "OK"

if __name__ == "__main__":
    print(f"Servidor de Jogo iniciado na porta {PORTA}. Aguardando jogadores...")
    t = ThreadedServer(ServicoJogo, port=PORTA)
    t.start()