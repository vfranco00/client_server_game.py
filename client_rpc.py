import turtle
import rpyc
import uuid
import paho.mqtt.client as mqtt
import json

HOST = 'localhost'
PORTA = 18861
username = input("Digite seu nome de jogador: ")

mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
topic_base = "turtle_game_distribuido_vfranco" 

class GerenciadorPartida:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f"jogador_{uuid.uuid4()}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.estado_atual = 0
        self.jogadores_na_fila = set()
        self.meu_uuid = str(uuid.uuid4())
        self.fila_mudou = False

        try:
            self.client.connect(mqtt_broker, mqtt_port, 60)
            self.client.loop_start()
            print("Conectado ao MQTT.")
        except Exception as e:
            print(f"Erro MQTT: {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"MQTT Conectado! Cod: {rc}")
        client.subscribe(f"{topic_base}/fila")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            acao = payload.get("acao")
            id_jogador = payload.get("id")
            
            if "fila" in topic:
                if acao == "entrar":
                    self.jogadores_na_fila.add(id_jogador)
                    self.fila_mudou = True
                    
                    if id_jogador != self.meu_uuid and self.estado_atual == 1:
                        msg_presenca = json.dumps({"acao": "presenca", "id": self.meu_uuid})
                        self.client.publish(f"{topic_base}/fila", msg_presenca)

                elif acao == "presenca":
                    self.jogadores_na_fila.add(id_jogador)
                    self.fila_mudou = True

                elif acao == "sair":
                    if id_jogador in self.jogadores_na_fila:
                        self.jogadores_na_fila.remove(id_jogador)
                        self.fila_mudou = True
                
                print(f"[MQTT] Fila atual: {len(self.jogadores_na_fila)} jogadores.")

                if len(self.jogadores_na_fila) >= 3 and self.estado_atual == 1:
                    self.iniciar_confirmacao()
                    
        except Exception as e:
            print(f"Erro proc. mensagem: {e}")

    def buscar_partida(self):
        self.estado_atual = 1
        self.jogadores_na_fila.clear()
        self.jogadores_na_fila.add(self.meu_uuid)
        self.fila_mudou = True
        
        msg = json.dumps({"acao": "entrar", "id": self.meu_uuid})
        self.client.publish(f"{topic_base}/fila", msg)
    
    def cancelar_busca(self):
        self.estado_atual = 0
        msg = json.dumps({"acao": "sair", "id": self.meu_uuid})
        self.client.publish(f"{topic_base}/fila", msg)
        self.jogadores_na_fila.clear()

    def iniciar_confirmacao(self):
        self.estado_atual = 2
        self.fila_mudou = True

matchmaking = GerenciadorPartida()

try:
    print(f"Conectando RPyC {HOST}:{PORTA}...")
    proxy = rpyc.connect(HOST, PORTA)
    meu_id, meus_dados = proxy.root.registrar_jogador(username)
except Exception as e:
    print(f"Erro RPyC: {e}")
    exit()

wn = turtle.Screen()
wn.title(f"Jogo Distribuído - {username}")
wn.setup(800, 600)
wn.tracer(0) 

pen_gui = turtle.Turtle()
pen_gui.hideturtle(); pen_gui.speed(0); pen_gui.penup()

pen_dinamica = turtle.Turtle()
pen_dinamica.hideturtle(); pen_dinamica.speed(0); pen_dinamica.penup()

def desenhar_botao(pen, x, y, w, h, texto, cor):
    pen.goto(x - w/2, y - h/2)
    pen.fillcolor(cor)
    pen.begin_fill()
    for _ in range(2):
        pen.forward(w); pen.left(90); pen.forward(h); pen.left(90)
    pen.end_fill()
    pen.goto(x, y - 10)
    pen.color("black")
    pen.write(texto, align="center", font=("Arial", 12, "bold"))

def setup_tela_menu():
    wn.bgcolor("lightgray")
    pen_gui.clear()
    pen_dinamica.clear()
    pen_gui.goto(0, 100)
    pen_gui.write("JOGO DISTRIBUÍDO", align="center", font=("Arial", 24, "bold"))
    desenhar_botao(pen_gui, 0, 0, 200, 50, "BUSCAR PARTIDA", "green")

def setup_tela_procurando():
    wn.bgcolor("lightblue")
    pen_gui.clear()
    pen_gui.goto(0, 100)
    pen_gui.write("Procurando partida...", align="center", font=("Arial", 18, "bold")) 
    desenhar_botao(pen_gui, 0, -50, 200, 50, "CANCELAR BUSCA", "red")
    atualizar_texto_fila()

def setup_tela_encontrada():
    wn.bgcolor("yellow")
    pen_gui.clear()
    pen_dinamica.clear()
    pen_gui.goto(0, 100)
    pen_gui.write("PARTIDA ENCONTRADA!", align="center", font=("Arial", 18, "bold"))
    desenhar_botao(pen_gui, -100, 0, 150, 50, "ACEITAR", "green")
    desenhar_botao(pen_gui, 100, 0, 150, 50, "RECUSAR", "red")

def atualizar_texto_fila():
    pen_dinamica.clear()
    pen_dinamica.goto(0, 50)
    pen_dinamica.color("black")
    pen_dinamica.write(f"Jogadores na fila: {len(matchmaking.jogadores_na_fila)}/3", 
                       align="center", font=("Arial", 14, "normal"))

def tratar_clique(x, y):
    st = matchmaking.estado_atual
    
    if st == 0: # Menu
        if -100 < x < 100 and -25 < y < 25:
            matchmaking.buscar_partida()
            setup_tela_procurando()

    elif st == 1: # Procurando
        if -100 < x < 100 and -75 < y < -25:
            matchmaking.cancelar_busca()
            setup_tela_menu()

    elif st == 2: # Encontrada
        if -175 < x < -25 and -25 < y < 25: # Aceitar
            matchmaking.estado_atual = 3
            pen_gui.clear()
            pen_dinamica.clear()
            wn.bgcolor("green")
            game_loop()
        if 25 < x < 175 and -25 < y < 25: # Recusar
            matchmaking.cancelar_busca()
            setup_tela_menu()

wn.onclick(tratar_clique)

largura_tela = wn.window_width()
altura_tela = wn.window_height()
meu_jogador = turtle.Turtle()
meu_jogador.speed(0)
meu_jogador.shape("circle")
meu_jogador.color(meus_dados['color'])
meu_jogador.penup()
meu_jogador.hideturtle()
outros_jogadores = {}
ultima_posicao = (0, 0)
STEP = 15
offset_bola = 15

def move_step(dx, dy):
    if matchmaking.estado_atual != 3: return
    global ultima_posicao
    limite_y, limite_x = altura_tela / 2, largura_tela / 2
    x, y = meu_jogador.xcor(), meu_jogador.ycor()
    nx = max(-limite_x + offset_bola, min(limite_x - offset_bola, x + dx))
    ny = max(-limite_y + offset_bola, min(limite_y - offset_bola, y + dy))
    if (nx, ny) != (x, y):
        meu_jogador.goto(nx, ny)
        if (nx, ny) != ultima_posicao:
            try: proxy.root.atualizar_movimento(meu_id, nx, ny)
            except: pass
            ultima_posicao = (nx, ny)

def go_up():    move_step(0,  STEP)
def go_down():  move_step(0, -STEP)
def go_left():  move_step(-STEP, 0)
def go_right(): move_step( STEP, 0)
def on_close():
    try: proxy.root.desconectar_jogador(meu_id); matchmaking.client.loop_stop()
    except: pass
    finally: wn.bye()

wn.listen()
wn.onkey(go_up, "w"); wn.onkey(go_down, "s"); wn.onkey(go_left, "a"); wn.onkey(go_right, "d")
wn.onkey(go_up, "W"); wn.onkey(go_down, "S"); wn.onkey(go_left, "A"); wn.onkey(go_right, "D")
wn.onkey(go_up, "Up"); wn.onkey(go_down, "Down"); wn.onkey(go_left, "Left"); wn.onkey(go_right, "Right")
turtle.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)

def game_loop():
    if matchmaking.estado_atual != 3: return
    if not meu_jogador.isvisible(): meu_jogador.showturtle()
    
    meu_jogador.clear()
    mx, my = meu_jogador.xcor(), meu_jogador.ycor()
    meu_jogador.goto(mx, my + 25); meu_jogador.write(username, align="center", font=("Arial", 10, "bold")); meu_jogador.goto(mx, my)

    try: estado_jogo = proxy.root.obter_estado_jogo()
    except: return
    ids_online = set()

    for id_jogador, dados in estado_jogo:
        ids_online.add(id_jogador)
        if id_jogador == meu_id: continue
        if id_jogador not in outros_jogadores:
            novo = turtle.Turtle(); novo.speed(0); novo.shape("circle"); novo.color(dados['color']); novo.penup()
            outros_jogadores[id_jogador] = novo
        
        b = outros_jogadores[id_jogador]
        b.clear()
        b.goto(dados['x'], dados['y'] + 25); b.write(dados['username'], align="center", font=("Arial", 10, "bold")); b.goto(dados['x'], dados['y'])

    ids_locais = list(outros_jogadores.keys())
    for id_local in ids_locais:
        if id_local not in ids_online:
            outros_jogadores[id_local].clear(); outros_jogadores[id_local].hideturtle(); del outros_jogadores[id_local]
    
    wn.update()
    wn.ontimer(game_loop, 50)

ultimo_estado = -1

def loop_geral():
    global ultimo_estado
    
    if matchmaking.estado_atual != ultimo_estado:
        if matchmaking.estado_atual == 0: setup_tela_menu()
        elif matchmaking.estado_atual == 1: setup_tela_procurando()
        elif matchmaking.estado_atual == 2: setup_tela_encontrada()
        ultimo_estado = matchmaking.estado_atual

    if matchmaking.estado_atual == 1 and matchmaking.fila_mudou:
        atualizar_texto_fila()
        matchmaking.fila_mudou = False
        wn.update()
    
    if matchmaking.estado_atual != 3:
        wn.update()
        wn.ontimer(loop_geral, 100)

setup_tela_menu()
loop_geral()
wn.mainloop()