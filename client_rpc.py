import turtle
import rpyc

HOST = 'localhost'
PORTA = 18861
username = input("Digite seu nome de jogador: ")

try:
    print(f"\nConectando ao servidor em {HOST}:{PORTA}...")
    proxy = rpyc.connect(HOST, PORTA)
    meu_id, meus_dados = proxy.root.registrar_jogador(username)
    print(f"Conectado com sucesso! ID: {meu_id} | Cor: {meus_dados['color']}\n")
except Exception as e:
    print(f"\n[ERRO] Não foi possível conectar ao servidor: {e}")
    exit()

wn = turtle.Screen()
wn.title(f"Jogo Distribuído - Jogador: {username} (ID: {meu_id})")
wn.bgcolor("green")
wn.setup(width=800, height=600)
wn.tracer(0)

largura_tela = wn.window_width()
altura_tela = wn.window_height()

meu_jogador = turtle.Turtle()
meu_jogador.speed(0)
meu_jogador.shape("circle")
meu_jogador.color(meus_dados['color'])
meu_jogador.penup()

outros_jogadores = {}
ultima_posicao = (0, 0)
STEP = 15
offset_bola = 15

def move_step(dx, dy):
    global ultima_posicao
    limite_y, limite_x = altura_tela / 2, largura_tela / 2

    x, y = meu_jogador.xcor(), meu_jogador.ycor()
    nx = max(-limite_x + offset_bola, min(limite_x - offset_bola, x + dx))
    ny = max(-limite_y + offset_bola, min(limite_y - offset_bola, y + dy))

    if (nx, ny) != (x, y):
        meu_jogador.goto(nx, ny)
        if (nx, ny) != ultima_posicao:
            try:
                proxy.root.atualizar_movimento(meu_id, nx, ny)
            except EOFError:
                pass
            ultima_posicao = (nx, ny)

def go_up():    move_step(0,  STEP)
def go_down():  move_step(0, -STEP)
def go_left():  move_step(-STEP, 0)
def go_right(): move_step( STEP, 0)

def on_close():
    try:
        proxy.root.desconectar_jogador(meu_id)
    except EOFError:
        print("Conexão com o servidor já estava fechada.")
    finally:
        wn.bye()

# Controles: onkey = 1 disparo por tecla (sem auto-repeat infinito)
wn.listen()
wn.onkey(go_up, "w"); wn.onkey(go_down, "s"); wn.onkey(go_left, "a"); wn.onkey(go_right, "d")
wn.onkey(go_up, "W"); wn.onkey(go_down, "S"); wn.onkey(go_left, "A"); wn.onkey(go_right, "D")
wn.onkey(go_up, "Up"); wn.onkey(go_down, "Down"); wn.onkey(go_left, "Left"); wn.onkey(go_right, "Right")

turtle.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)

def game_loop():
    meu_jogador.clear()
    meu_x, meu_y = meu_jogador.xcor(), meu_jogador.ycor()
    meu_jogador.goto(meu_x, meu_y + 25)
    meu_jogador.write(username, align="center", font=("Arial", 12, "bold"))
    meu_jogador.goto(meu_x, meu_y)

    try:
        estado_jogo = proxy.root.obter_estado_jogo()
    except EOFError:
        estado_jogo = []
        print("Conexão com o servidor perdida. Tentando reconectar...")
        return
    
    ids_online = set()

    for id_jogador, dados in estado_jogo:
        ids_online.add(id_jogador)

        if id_jogador == meu_id:
            continue

        if id_jogador not in outros_jogadores:
            novo_jogador = turtle.Turtle()
            novo_jogador.speed(0)
            novo_jogador.shape("circle")
            novo_jogador.color(dados['color'])
            novo_jogador.penup()
            outros_jogadores[id_jogador] = novo_jogador
            print(f"Novo jogador detectado: {dados['username']} (ID: {id_jogador})")

        bolinha = outros_jogadores[id_jogador]
        bolinha.clear()

        bolinha.goto(dados['x'], dados['y'] + 25)
        bolinha.write(dados['username'], align="center", font=("Arial", 12, "bold"))
        bolinha.goto(dados['x'], dados['y'])

    ids_locais = list(outros_jogadores.keys())

    ids_locais = list(outros_jogadores.keys())
    
    for id_local in ids_locais:
        if id_local not in ids_online:
            outros_jogadores[id_local].clear() 
            outros_jogadores[id_local].hideturtle()
            del outros_jogadores[id_local]
            print(f"Jogador {id_local} removido completamente.")

    wn.update()
    wn.ontimer(game_loop, 50)

game_loop()
wn.mainloop()
