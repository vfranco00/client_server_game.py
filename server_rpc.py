# servidor_jogo.py
import rpyc
import random
from rpyc.utils.server import ThreadedServer

PORTA = 18861

class ServicoJogo(rpyc.Service):
    jogadores = {}
    proximo_id = 0
    
    cores = ["crimson", "aquamarine", "pink", "gold", "red", "brown", 
             "blue", "yellow", "orange", "purple", "white", "cyan"]

    def on_connect(self, conn):
        print(f"Nova conexão recebida. Total de jogadores agora: {len(self.jogadores)}")

    def on_disconnect(self, conn):
        if self.id_desta_desconexao is not None and self.id_desta_desconexao in ServicoJogo.jogadores:
            nome: ServicoJogo.jogadores[self.id_desta_desconexao]['username']
            del ServicoJogo.jogadores[self.id_desta_desconexao]
            print(f"Jogador desconectado: {nome} (ID: {self.id_desta_desconexao}) - Total: {len(ServicoJogo.jogadores)}")
        print("A conexão de um cliente foi perdida.")
        
    def exposed_registrar_jogador(self, username):
        meu_id = ServicoJogo.proximo_id
        
        dados_jogador = {
            'x': 0, 'y': 0,
            'color': random.choice(ServicoJogo.cores),
            'username': username
        }
        
        ServicoJogo.jogadores[meu_id] = dados_jogador
        ServicoJogo.proximo_id += 1

        self_id_desta_desconexao = meu_id
        
        print(f"Jogador registrado: {username} (ID: {meu_id}) - Total: {len(ServicoJogo.jogadores)}")
        return meu_id, dados_jogador

    def exposed_obter_estado_jogo(self):
        return list(ServicoJogo.jogadores.items())

    def exposed_atualizar_movimento(self, id, x, y):
        if id in ServicoJogo.jogadores:
            ServicoJogo.jogadores[id]['x'] = x
            ServicoJogo.jogadores[id]['y'] = y
        return "OK"
    
    def exposed_desconectar_jogador(self, id):
        if id in ServicoJogo.jogadores:
            username = ServicoJogo.jogadores[id]['username']
            del ServicoJogo.jogadores[id]
            self_id_desta_desconexao = None
            print(f"Jogador desconectado: {username} (ID: {id}) - Total: {len(ServicoJogo.jogadores)}")
        return "OK"

if __name__ == "__main__":
    print(f"Servidor de Jogo iniciado na porta {PORTA}. Aguardando jogadores...")
    t = ThreadedServer(ServicoJogo, port=PORTA)
    t.start()