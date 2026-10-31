import math
import random
import tkinter as tk


class JogoArcoFlecha:

  def __init__(self, root):
    self.root = root
    self.root.title("Torneio Mundial de Arco e Flecha")
    self.root.resizable(False, False)

    # Dimensões da tela
    self.largura = 950
    self.altura = 550
    self.horizonte = 302
    self.chao_flecha = 485  # altura em que a flecha "crava" no chão

    self.canvas = tk.Canvas(
        root,
        width=self.largura,
        height=self.altura,
        bg="#87CEEB",
        highlightthickness=0,
    )
    self.canvas.pack()

    # Variáveis de Jogo
    self.pontos = 0
    self.fase = 1
    self.acertos_fase_4 = 0
    self.flechas_restantes = 10
    self.erros_corpo = 0
    self.max_erros_corpo = 5

    # Estados: MIRANDO, CARREGANDO, VOANDO, GAME_OVER, VITORIA
    self.estado = "MIRANDO"

    # Arqueiro (o "pivô" é o ombro da frente; o arco fica a um braço de distância)
    self.pivo_x = 75
    self.pivo_y = 365
    self.braco_comp = 42
    self.angulo = 0.0
    self.forca = 0
    self.forca_max = 30
    self.vibracao = 0  # vibração da corda depois do disparo
    self.mao_x, self.mao_y = self.pos_descanso_mao()

    # Flecha em voo
    self.flecha_x = self.pivo_x
    self.flecha_y = self.pivo_y
    self.flecha_vx = 0
    self.flecha_vy = 0
    self.flechas_cravadas = []

    # Configuração de cada fase: quanto mais avança, mais longe e menor fica
    # o alvo, e mais rápido ele se move.
    self.fases_cfg = {
        1: {"x": 560, "escala": 1.00, "vel": 2.0},
        2: {"x": 650, "escala": 0.92, "vel": 2.6},
        3: {"x": 745, "escala": 0.84, "vel": 3.2},
        4: {"x": 845, "escala": 0.76, "vel": 3.9},
    }

    # Alvo (A pessoa e a maçã)
    self.pessoa_x = self.fases_cfg[1]["x"]
    self.pessoa_y = 370
    self.pessoa_escala = self.fases_cfg[1]["escala"]
    self.alvo_ymin = 295
    self.alvo_ymax = 420
    self.alvo_dir = 1
    self.maca_raio = 12
    self.flash_pessoa = 0

    # Animações e Reações da Plateia
    self.confetes = []
    self.textos = []
    self.tipo_reacao_plateia = None  # "POSITIVO", "NEGATIVO" ou None
    self.tempo_reacao = 0
    self.animacao_frame = 0
    self.plateia_suja = True  # precisa redesenhar a plateia?

    # Botão de reiniciar
    self.btn_reiniciar = None

    # Nuvens (movidas a cada frame sem recriar)
    self.nuvens = [
        {"x": 110, "y": 60, "esc": 1.0, "v": 0.25},
        {"x": 380, "y": 95, "esc": 0.8, "v": 0.15},
        {"x": 660, "y": 40, "esc": 1.2, "v": 0.30},
        {"x": 870, "y": 100, "esc": 0.7, "v": 0.20},
        {"x": 250, "y": 30, "esc": 0.6, "v": 0.12},
    ]

    self.criar_espectadores()
    self.criar_cenario_estatico()

    # Controles
    self.canvas.bind("<Motion>", self.atualizar_mira)
    self.canvas.bind("<Button-1>", self.iniciar_carregamento)
    self.canvas.bind("<ButtonRelease-1>", self.atirar)

    # Iniciar Loop
    self.atualizar_jogo()

  # ------------------------------------------------------------------
  # Utilidades
  # ------------------------------------------------------------------
  def misturar(self, c1, c2, t):
    """Mistura duas cores hexadecimais (t de 0 a 1)."""
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i : i + 2], 16) for i in (1, 3, 5))
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return "#%02x%02x%02x" % (r, g, b)

  def ik_braco(self, sx, sy, hx, hy, comp):
    """Calcula a posição do cotovelo de um braço de 2 segmentos."""
    dx, dy = hx - sx, hy - sy
    d = math.hypot(dx, dy)
    mx, my = (sx + hx) / 2, (sy + hy) / 2
    if d < 0.001 or d >= 2 * comp:
      return mx, my
    h = math.sqrt(comp * comp - (d / 2) ** 2)
    ux, uy = dx / d, dy / d
    n1 = (-uy, ux)
    n2 = (uy, -ux)
    # o cotovelo prefere ficar para trás/para cima
    n = n1 if (-n1[0] - n1[1]) >= (-n2[0] - n2[1]) else n2
    return mx + n[0] * h, my + n[1] * h

  # ------------------------------------------------------------------
  # Cenário estático
  # ------------------------------------------------------------------
  def criar_cenario_estatico(self):
    c = self.canvas
    W = self.largura
    H = self.horizonte

    # Céu em degradê
    faixas = 50
    for i in range(faixas):
      y0 = i * H / faixas
      y1 = (i + 1) * H / faixas + 1
      cor = self.misturar("#3F86D6", "#D6EEFF", i / (faixas - 1))
      c.create_rectangle(0, y0, W, y1, fill=cor, outline="")

    # Sol com brilho
    for r, cor in [(46, "#FFF3B0"), (36, "#FFE97A"), (27, "#FFD700")]:
      c.create_oval(860 - r, 62 - r, 860 + r, 62 + r, fill=cor, outline="")

    # Nuvens
    for i, n in enumerate(self.nuvens):
      self.desenhar_nuvem(n["x"], n["y"], n["esc"], f"nuvem{i}")

    # Montanhas (fundo e meio)
    far = "#9DB3CC"
    mid = "#6F8FB0"
    self.montanha(-40, 260, 120, 175, H, far)
    self.montanha(180, 540, 350, 150, H, far)
    self.montanha(500, 800, 640, 185, H, far)
    self.montanha(-30, 210, 60, 215, H, mid)
    self.montanha(250, 480, 385, 205, H, mid)
    self.montanha(700, 1010, 905, 190, H, mid)

    # Cidade ao fundo (prédios com janelas)
    rng = random.Random(7)
    cores_pred = ["#8795A8", "#6E7C90", "#A4B0C0", "#5F6D82", "#7D8CA3"]
    x = 0
    while x < 425:
      w = rng.randint(24, 46)
      h = rng.randint(35, 115)
      top = H - h
      c.create_rectangle(
          x, top, x + w, H, fill=rng.choice(cores_pred), outline="#4D596B"
      )
      if h > 90:
        c.create_line(x + w / 2, top, x + w / 2, top - 12, fill="#4D596B", width=2)
      for wy in range(top + 6, H - 8, 9):
        for wx in range(x + 4, x + w - 5, 8):
          if rng.random() < 0.55:
            c.create_rectangle(
                wx,
                wy,
                wx + 4,
                wy + 5,
                fill=rng.choice(["#FFE9A8", "#BFE0FF", "#FFF6D0"]),
                outline="",
            )
      x += w + rng.randint(0, 4)

    # Casinhas na frente da cidade
    x = 6
    cores_casa = ["#F4E4C1", "#E8B4A0", "#C7D9A8", "#F0D58C", "#B8D0E6"]
    cores_telhado = ["#B03A2E", "#7B3F00", "#8E2B2B", "#A04000"]
    while x < W - 30:
      w = rng.randint(26, 34)
      base = H + 2
      c.create_rectangle(
          x, base - 22, x + w, base, fill=rng.choice(cores_casa), outline="#6B5B45"
      )
      c.create_polygon(
          x - 3,
          base - 22,
          x + w / 2,
          base - 38,
          x + w + 3,
          base - 22,
          fill=rng.choice(cores_telhado),
          outline="#4E2A14",
      )
      c.create_rectangle(
          x + 4, base - 16, x + 10, base - 9, fill="#9FD3F5", outline="#555"
      )
      c.create_rectangle(
          x + w - 11, base - 14, x + w - 5, base, fill="#6B3E1F", outline=""
      )
      x += w + rng.randint(10, 24)

    # Rua distante com carrinhos
    c.create_rectangle(0, H + 2, W, H + 16, fill="#4A4A4A", outline="")
    c.create_line(0, H + 2, W, H + 2, fill="#BDBDBD", width=2)
    for xx in range(0, W, 40):
      c.create_rectangle(xx, H + 8, xx + 20, H + 10, fill="#F5F5F5", outline="")
    for cx, cor in [(70, "#D32F2F"), (210, "#1976D2"), (330, "#FBC02D")]:
      c.create_rectangle(cx, H + 4, cx + 22, H + 11, fill=cor, outline="#222")
      c.create_rectangle(cx + 5, H + 1, cx + 17, H + 5, fill=cor, outline="#222")
      c.create_oval(cx + 3, H + 9, cx + 8, H + 14, fill="black", outline="")
      c.create_oval(cx + 14, H + 9, cx + 19, H + 14, fill="black", outline="")

    # Campo gramado com faixas de perspectiva
    y = H + 16
    hb = 10.0
    i = 0
    while y < 505:
      cor = "#3E9F3E" if i % 2 == 0 else "#378F37"
      c.create_rectangle(0, y, W, min(y + hb, 505), fill=cor, outline="")
      y += hb
      hb *= 1.15
      i += 1

    # Pista de terra batida
    c.create_rectangle(0, 505, W, self.altura, fill="#A47148", outline="")
    for yy in (516, 529, 542):
      c.create_line(0, yy, W, yy, fill="#B98B5E")
    c.create_line(0, 505, W, 505, fill="#FFFFFF", width=3)

    # Árvores
    self.desenhar_arvore(28, 335, 1.0)
    self.desenhar_arvore(255, 330, 0.55)
    self.desenhar_arvore(335, 332, 0.5)
    self.desenhar_arvore(395, 334, 0.55)

    # Estrutura do auditório / arquibancada
    sx0, sx1 = 415, 935
    c.create_rectangle(sx0, 105, sx1, 346, fill="#34435C", outline="#1F2A3D", width=2)
    for xx in range(sx0 + 20, sx1, 52):
      c.create_line(xx, 125, xx, 346, fill="#3C4C69")
    # telhado
    c.create_polygon(
        sx0 - 12, 92, sx1 + 12, 92, sx1, 125, sx0, 125,
        fill="#8E2B2B", outline="#4E1414", width=2,
    )
    for xx in range(sx0 + 15, sx1, 40):
      c.create_oval(xx - 4, 126, xx + 4, 134, fill="#FFF3B0", outline="#C9B458")
    # bandeirolas
    cores_band = ["#FFD700", "#FF4500", "#1E90FF", "#32CD32", "#FF69B4"]
    for k, xx in enumerate(range(sx0 + 10, sx1 - 10, 26)):
      c.create_polygon(
          xx, 137, xx + 16, 137, xx + 8, 151,
          fill=cores_band[k % len(cores_band)], outline="",
      )
    # pilares
    for xx in (sx0, (sx0 + sx1) // 2, sx1 - 8):
      c.create_rectangle(xx, 125, xx + 8, 346, fill="#B8C0CC", outline="#6F7A8A")
    # barreira com propaganda
    c.create_rectangle(sx0 - 5, 334, sx1 + 5, 350, fill="#1C3B5E", outline="#FFD700", width=2)
    for xx in range(sx0 + 55, sx1, 110):
      c.create_text(
          xx, 342, text="ARCO & FLECHA", font=("Arial", 8, "bold"), fill="white"
      )

    # Letreiro do Torneio
    c.create_rectangle(240, 15, 710, 65, fill="#1C3B5E", outline="#FFD700", width=3)
    c.create_text(
        475,
        40,
        text="🏆 TORNEIO MUNDIAL DE TIRO AO ALVO 🏆",
        font=("Arial", 15, "bold"),
        fill="#FFD700",
    )

    # Painel do placar
    c.create_rectangle(10, 72, 240, 216, fill="#FFF8DC", outline="#8B4513", width=3)
    c.create_text(
        125, 86, text="PLACAR", font=("Arial", 11, "bold"), fill="#8B4513"
    )

  def montanha(self, xe, xd, xp, yp, yb, cor):
    c = self.canvas
    c.create_polygon(xe, yb, xp, yp, xd, yb, fill=cor, outline="")
    # topo nevado
    h = (yb - yp) * 0.28
    y = yp + h
    lx = xp + (xe - xp) * 0.28
    rx = xp + (xd - xp) * 0.28
    c.create_polygon(
        xp, yp,
        rx, y,
        xp + (rx - xp) * 0.6, y - h * 0.3,
        xp + (rx - xp) * 0.2, y + h * 0.1,
        xp + (lx - xp) * 0.4, y - h * 0.3,
        lx, y,
        fill="#F4F8FB", outline="",
    )

  def desenhar_nuvem(self, cx, cy, esc, tag):
    partes = [
        (-28, 2, 18, 11),
        (-8, -6, 22, 15),
        (14, -2, 20, 13),
        (30, 4, 15, 9),
        (0, 6, 34, 9),
    ]
    for dx, dy, rx, ry in partes:
      c_x = cx + dx * esc
      c_y = cy + dy * esc
      self.canvas.create_oval(
          c_x - rx * esc,
          c_y - ry * esc,
          c_x + rx * esc,
          c_y + ry * esc,
          fill="white",
          outline="",
          tags=(tag,),
      )

  def desenhar_arvore(self, x, y, esc=1.0):
    c = self.canvas
    c.create_rectangle(
        x - 6 * esc, y, x + 6 * esc, y + 40 * esc, fill="#8B4513", outline=""
    )
    c.create_oval(
        x - 25 * esc, y - 35 * esc, x + 25 * esc, y + 5 * esc,
        fill="#006400", outline="",
    )
    c.create_oval(
        x - 18 * esc, y - 50 * esc, x + 18 * esc, y - 10 * esc,
        fill="#228B22", outline="",
    )

  # ------------------------------------------------------------------
  # Plateia
  # ------------------------------------------------------------------
  def criar_espectadores(self):
    rng = random.Random(101)
    self.linhas_y = [190, 226, 262, 298]
    peles = ["#FFDAB9", "#E8B98A", "#C68642", "#8D5524", "#F1C27D"]
    cabelos = ["#2B1B0E", "#5A3A1A", "#C9A227", "#111111", "#8B2E16", "#777777"]
    camisas = [
        "#FF4500", "#1E90FF", "#32CD32", "#FF69B4", "#9370DB",
        "#FFD700", "#00CED1", "#FFFFFF", "#FF8C00", "#20B2AA",
    ]
    bones = [None, None, None, "#D32F2F", "#1976D2", "#FBC02D"]
    self.plateia = []
    for r, yb in enumerate(self.linhas_y):
      linha = []
      desloc = 21 if r % 2 else 0
      for col in range(11):
        linha.append({
            "x": 450 + col * 42 + desloc,
            "y": yb,
            "esc": rng.uniform(0.92, 1.08),
            "pele": rng.choice(peles),
            "cabelo": rng.choice(cabelos),
            "camisa": rng.choice(camisas),
            "bone": rng.choice(bones),
            "fase": rng.uniform(0, 6.28),
            "cadeira": "#8E2B2B" if (col + r) % 2 == 0 else "#A33A3A",
            "comp": None,
        })
      self.plateia.append(linha)

  def iniciar_reacao(self, tipo):
    self.tipo_reacao_plateia = tipo
    self.tempo_reacao = 80
    self.animacao_frame = 0
    if tipo == "POSITIVO":
      comps = ["pular", "pular", "palmas", "joinha", "punho"]
      falas = ["YEAH!", "OBA!", "BOA!!", "UHUUU!", "ISSO!"]
      cor = "#FFD700"
    else:
      comps = ["vaia", "vaia", "joinha_baixo", "punho", "corte"]
      falas = ["BUUU!", "VAIA!", "ÊÊÊ...", "AFF!", "NÃO!"]
      cor = "#FF4040"
    todos = [p for linha in self.plateia for p in linha]
    for p in todos:
      p["comp"] = random.choice(comps)
    for p in random.sample(todos, 6):
      self.textos.append({
          "x": p["x"], "y": p["y"] - 45, "txt": random.choice(falas),
          "cor": cor, "vida": 55, "tam": 11,
      })

  def desenhar_plateia(self):
    self.canvas.delete("plateia")
    t = self.animacao_frame
    reacao = self.tipo_reacao_plateia if self.tempo_reacao > 0 else None
    for r, linha in enumerate(self.plateia):
      yb = self.linhas_y[r]
      for p in linha:
        self.desenhar_espectador(p, t, reacao)
      # degrau da arquibancada (esconde as pernas da fileira)
      cor_degrau = "#B5B5B5" if r % 2 == 0 else "#A5A5A5"
      self.canvas.create_rectangle(
          425, yb + 9, 930, yb + 36,
          fill=cor_degrau, outline="#6B6B6B", tags="plateia",
      )
      self.canvas.create_line(
          425, yb + 10, 930, yb + 10, fill="#E0E0E0", width=2, tags="plateia"
      )

  def desenhar_espectador(self, p, t, reacao):
    c = self.canvas
    T = "plateia"
    px, py, s = p["x"], p["y"], p["esc"]
    ph = p["fase"]
    comp = p["comp"] if reacao else None
    pele, camisa = p["pele"], p["camisa"]

    salto = 0.0
    olhos = "normal"
    boca = "sorriso"
    polegar = None
    he = [px - 11 * s, py + 4 * s]  # mão esquerda (no colo)
    hd = [px + 11 * s, py + 4 * s]  # mão direita
    w = math.sin(t * 1.5 + ph)
    aw = abs(w)

    if reacao == "POSITIVO":
      boca = "aberta"
      if comp == "pular":
        salto = -aw * 10
        he = [px - 17 * s, py - 36 * s - w * 5 * s]
        hd = [px + 17 * s, py - 36 * s + w * 5 * s]
      elif comp == "palmas":
        salto = -aw * 3
        m = (2 + 7 * aw) * s
        he = [px - m, py - 20 * s]
        hd = [px + m, py - 20 * s]
        boca = "sorriso"
      elif comp == "joinha":
        salto = -aw * 4
        hd = [px + 17 * s, py - 24 * s - aw * 4 * s]
        polegar = "cima"
        boca = "sorriso"
      else:  # punho para o alto
        salto = -aw * 7
        hd = [px + 15 * s, py - 38 * s - aw * 6 * s]
        he = [px - 12 * s, py - 8 * s]
    elif reacao == "NEGATIVO":
      salto = 2
      olhos = "bravo"
      boca = "triste"
      if comp == "vaia":
        boca = "grande"
        he = [px - 7 * s, py - 21 * s]
        hd = [px + 7 * s, py - 21 * s]
      elif comp == "joinha_baixo":
        hd = [px + 19 * s, py - 4 * s + w * 2 * s]
        polegar = "baixo"
      elif comp == "punho":
        boca = "brava"
        hd = [px + 15 * s + w * 4 * s, py - 36 * s]
        he = [px - 12 * s, py - 6 * s]
      else:  # corte: mão passando pelo pescoço
        boca = "brava"
        hd = [px + 12 * w * s, py - 13 * s]

    y0 = py + salto
    he[1] += salto
    hd[1] += salto

    # Cadeira (encosto)
    c.create_rectangle(
        px - 12 * s, py - 22 * s, px + 12 * s, py + 12,
        fill=p["cadeira"], outline="#4A1010", tags=T,
    )
    # Tronco
    c.create_rectangle(
        px - 9 * s, y0 - 18 * s, px + 9 * s, y0 + 22,
        fill=camisa, outline="", tags=T,
    )
    # Cabeça
    c.create_oval(
        px - 9 * s, y0 - 36 * s, px + 9 * s, y0 - 18 * s,
        fill=pele, outline="", tags=T,
    )
    # Cabelo ou boné
    if p["bone"]:
      c.create_arc(
          px - 9 * s, y0 - 36 * s, px + 9 * s, y0 - 18 * s,
          start=0, extent=180, style=tk.CHORD, fill=p["bone"], outline="", tags=T,
      )
      c.create_line(
          px - 9 * s, y0 - 27 * s, px + 12 * s, y0 - 27 * s,
          fill=p["bone"], width=3, tags=T,
      )
    else:
      c.create_arc(
          px - 9 * s, y0 - 36 * s, px + 9 * s, y0 - 18 * s,
          start=0, extent=180, style=tk.CHORD, fill=p["cabelo"], outline="", tags=T,
      )
    # Olhos
    for ex in (-3.5, 3.5):
      c.create_oval(
          px + ex * s - 1.3 * s, y0 - 26 * s - 1.3 * s,
          px + ex * s + 1.3 * s, y0 - 26 * s + 1.3 * s,
          fill="black", outline="", tags=T,
      )
    if olhos == "bravo":
      c.create_line(
          px - 6 * s, y0 - 29.5 * s, px - 1.5 * s, y0 - 27.5 * s,
          fill="black", width=1, tags=T,
      )
      c.create_line(
          px + 6 * s, y0 - 29.5 * s, px + 1.5 * s, y0 - 27.5 * s,
          fill="black", width=1, tags=T,
      )
    # Boca
    if boca == "aberta":
      c.create_oval(
          px - 3 * s, y0 - 23 * s, px + 3 * s, y0 - 19 * s,
          fill="#5A0F0F", outline="", tags=T,
      )
    elif boca == "grande":
      c.create_oval(
          px - 4 * s, y0 - 24 * s, px + 4 * s, y0 - 18.5 * s,
          fill="#5A0F0F", outline="", tags=T,
      )
    elif boca == "triste":
      c.create_arc(
          px - 4 * s, y0 - 23 * s, px + 4 * s, y0 - 18 * s,
          start=20, extent=140, style=tk.ARC, outline="#5A0F0F", tags=T,
      )
    elif boca == "brava":
      c.create_line(
          px - 4 * s, y0 - 20.5 * s, px + 4 * s, y0 - 20.5 * s,
          fill="#5A0F0F", width=2, tags=T,
      )
    else:
      c.create_arc(
          px - 4 * s, y0 - 24 * s, px + 4 * s, y0 - 19 * s,
          start=200, extent=140, style=tk.ARC, outline="#7A2E2E", tags=T,
      )

    # Braços (ombros -> cotovelo -> mão)
    sh_y = y0 - 14 * s
    for ombro_x, mao in ((px - 9 * s, he), (px + 9 * s, hd)):
      ex, ey = self.ik_braco(ombro_x, sh_y, mao[0], mao[1], 10 * s)
      c.create_line(
          ombro_x, sh_y, ex, ey, mao[0], mao[1],
          fill=camisa, width=max(3, 4 * s), capstyle=tk.ROUND,
          joinstyle=tk.ROUND, tags=T,
      )
    # Mãos
    rm = 3 * s if not polegar else 3.6 * s
    for mao in (he, hd):
      c.create_oval(
          mao[0] - rm, mao[1] - rm, mao[0] + rm, mao[1] + rm,
          fill=pele, outline="", tags=T,
      )
    # Joinha
    if polegar == "cima":
      c.create_line(
          hd[0], hd[1] - rm, hd[0], hd[1] - rm - 7 * s,
          fill=pele, width=max(2, 3 * s), capstyle=tk.ROUND, tags=T,
      )
    elif polegar == "baixo":
      c.create_line(
          hd[0], hd[1] + rm, hd[0], hd[1] + rm + 7 * s,
          fill=pele, width=max(2, 3 * s), capstyle=tk.ROUND, tags=T,
      )

  # ------------------------------------------------------------------
  # Desenho dos elementos dinâmicos
  # ------------------------------------------------------------------
  def desenhar_elementos(self):
    self.canvas.delete("dinamico")

    if self.plateia_suja or self.tempo_reacao > 0:
      self.desenhar_plateia()
      self.plateia_suja = False

    self.desenhar_pessoa()

    for fc in self.flechas_cravadas:
      self.desenhar_flecha(fc[0], fc[1], fc[2], 30)

    self.desenhar_arqueiro()

    if self.estado == "VOANDO":
      ang = math.atan2(self.flecha_vy, self.flecha_vx)
      self.desenhar_flecha(self.flecha_x, self.flecha_y, ang, 38)

    for cf in self.confetes:
      self.canvas.create_oval(
          cf["x"], cf["y"], cf["x"] + 6, cf["y"] + 6,
          fill=cf["cor"], outline="", tags="dinamico",
      )

    for tx in self.textos:
      fonte = ("Arial", tx["tam"], "bold")
      self.canvas.create_text(
          tx["x"] + 1, tx["y"] + 1, text=tx["txt"], font=fonte,
          fill="black", tags="dinamico",
      )
      self.canvas.create_text(
          tx["x"], tx["y"], text=tx["txt"], font=fonte,
          fill=tx["cor"], tags="dinamico",
      )

  def desenhar_flecha(self, tip_x, tip_y, ang, comp):
    c = self.canvas
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    tx, ty = tip_x - dx * comp, tip_y - dy * comp
    # haste
    c.create_line(tx, ty, tip_x, tip_y, fill="#5C3A1E", width=3, tags="dinamico")
    # ponta metálica
    bx, by = tip_x - dx * 9, tip_y - dy * 9
    c.create_polygon(
        tip_x, tip_y, bx + px * 3.5, by + py * 3.5, bx - px * 3.5, by - py * 3.5,
        fill="#B0B0B0", outline="#444", tags="dinamico",
    )
    # penas
    for sinal in (1, -1):
      c.create_line(
          tx + dx * 9, ty + dy * 9,
          tx - dx * 2 + px * 4 * sinal, ty - dy * 2 + py * 4 * sinal,
          fill="#E74C3C", width=2, tags="dinamico",
      )

  def desenhar_pessoa(self):
    c = self.canvas
    T = "dinamico"
    s = self.pessoa_escala
    x, y = self.pessoa_x, self.pessoa_y
    medo = self.estado == "VOANDO"
    if medo:
      x += math.sin(self.animacao_frame * 9 + self.pessoa_y) * 0.8  # tremendo

    pele = "#FFDAB9"
    camisa = "#1E90FF"
    if self.flash_pessoa > 0 and (self.flash_pessoa // 2) % 2 == 0:
      camisa = "#FF2020"

    # sombra
    c.create_oval(
        x - 20 * s, y + 42 * s, x + 20 * s, y + 51 * s,
        fill="#2A6B2A", outline="", tags=T,
    )
    # pernas
    c.create_rectangle(
        x - 12 * s, y + 3 * s, x - 1 * s, y + 45 * s,
        fill="#1B3A6B", outline="black", tags=T,
    )
    c.create_rectangle(
        x + 1 * s, y + 3 * s, x + 12 * s, y + 45 * s,
        fill="#1B3A6B", outline="black", tags=T,
    )
    c.create_rectangle(
        x - 14 * s, y + 42 * s, x - 1 * s, y + 48 * s, fill="#222", outline="", tags=T
    )
    c.create_rectangle(
        x + 1 * s, y + 42 * s, x + 14 * s, y + 48 * s, fill="#222", outline="", tags=T
    )
    # braços (levantados de pânico quando a flecha voa)
    if medo:
      ml = (x - 22 * s, y - 52 * s)
      mr = (x + 22 * s, y - 52 * s)
    else:
      ml = (x - 20 * s, y - 4 * s)
      mr = (x + 20 * s, y - 4 * s)
    c.create_line(x - 14 * s, y - 34 * s, ml[0], ml[1], fill=camisa, width=6 * s, tags=T)
    c.create_line(x + 14 * s, y - 34 * s, mr[0], mr[1], fill=camisa, width=6 * s, tags=T)
    for m in (ml, mr):
      c.create_oval(
          m[0] - 3.5 * s, m[1] - 3.5 * s, m[0] + 3.5 * s, m[1] + 3.5 * s,
          fill=pele, outline="", tags=T,
      )
    # tronco
    c.create_rectangle(
        x - 14 * s, y - 40 * s, x + 14 * s, y + 5 * s,
        fill=camisa, outline="black", tags=T,
    )
    # cabeça
    c.create_oval(
        x - 15 * s, y - 70 * s, x + 15 * s, y - 40 * s,
        fill=pele, outline="black", tags=T,
    )
    # rosto
    if medo:
      for ex in (-6, 6):
        c.create_oval(
            x + ex * s - 3.5 * s, y - 58 * s - 3.5 * s,
            x + ex * s + 3.5 * s, y - 58 * s + 3.5 * s,
            fill="white", outline="black", tags=T,
        )
        c.create_oval(
            x + ex * s - 1.3 * s, y - 58 * s - 1.3 * s,
            x + ex * s + 1.3 * s, y - 58 * s + 1.3 * s,
            fill="black", outline="", tags=T,
        )
      c.create_oval(
          x - 3 * s, y - 51 * s, x + 3 * s, y - 45 * s,
          fill="#5A0F0F", outline="", tags=T,
      )
      c.create_oval(  # gota de suor
          x + 12 * s, y - 66 * s, x + 16 * s, y - 59 * s,
          fill="#6EC6FF", outline="", tags=T,
      )
    else:
      for ex in (-6, 6):
        c.create_oval(
            x + ex * s - 1.8 * s, y - 58 * s - 1.8 * s,
            x + ex * s + 1.8 * s, y - 58 * s + 1.8 * s,
            fill="black", outline="", tags=T,
        )
      c.create_arc(
          x - 6 * s, y - 52 * s, x + 6 * s, y - 44 * s,
          start=200, extent=140, style=tk.ARC, outline="#5A0F0F", width=2, tags=T,
      )

    # Maçã na cabeça (Alvo Principal)
    maca_y = y - 75 * s
    r = self.maca_raio * s
    c.create_oval(
        x - r, maca_y - r, x + r, maca_y + r,
        fill="red", outline="darkred", width=2, tags=T,
    )
    c.create_oval(
        x - r * 0.6, maca_y - r * 0.7, x - r * 0.1, maca_y - r * 0.2,
        fill="#FF8A8A", outline="", tags=T,
    )
    c.create_line(
        x, maca_y - r, x + 5 * s, maca_y - r - 7 * s, fill="green", width=2, tags=T
    )

  def desenhar_arqueiro(self):
    c = self.canvas
    T = "dinamico"
    px, py = self.pivo_x, self.pivo_y
    dx, dy = math.cos(self.angulo), math.sin(self.angulo)
    perp = (-dy, dx)
    L = self.braco_comp
    pele = "#F1C27D"
    gx, gy = px + dx * L, py + dy * L  # empunhadura do arco

    # sombra e pernas
    c.create_oval(px - 32, py + 100, px + 32, py + 111, fill="#2A6B2A", outline="", tags=T)
    c.create_line(px, py + 52, px - 14, py + 104, fill="#2C3E50", width=9, capstyle=tk.ROUND, tags=T)
    c.create_line(px, py + 52, px + 16, py + 104, fill="#2C3E50", width=9, capstyle=tk.ROUND, tags=T)
    c.create_oval(px - 26, py + 100, px - 6, py + 110, fill="#3E2410", outline="", tags=T)
    c.create_oval(px - 2, py + 100, px + 22, py + 110, fill="#3E2410", outline="", tags=T)

    # aljava com flechas nas costas
    c.create_polygon(
        px - 16, py - 8, px - 7, py - 12, px - 19, py + 32, px - 29, py + 27,
        fill="#6B3E1F", outline="#3E2410", tags=T,
    )
    for k in range(3):
      c.create_line(
          px - 17 + k * 3, py - 9 + k * 0.5, px - 21 + k * 3, py - 22,
          fill="#5C3A1E", width=2, tags=T,
      )
      c.create_line(
          px - 21 + k * 3, py - 22, px - 24 + k * 3, py - 27,
          fill="#E74C3C", width=3, tags=T,
      )

    # tronco
    c.create_polygon(
        px - 10, py - 8, px + 10, py - 8, px + 9, py + 56, px - 9, py + 56,
        fill="#C0392B", outline="#7B241C", tags=T,
    )
    c.create_rectangle(px - 9, py + 44, px + 9, py + 52, fill="#5D3A1A", outline="", tags=T)

    # cabeça com faixa na testa
    cx, cy = px + 2, py - 27
    c.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill=pele, outline="#8B5A2B", tags=T)
    c.create_arc(
        cx - 13, cy - 13, cx + 13, cy + 13, start=20, extent=160,
        style=tk.CHORD, fill="#3E2410", outline="", tags=T,
    )
    c.create_rectangle(cx - 13, cy - 5, cx + 13, cy - 1, fill="#FFD700", outline="", tags=T)
    c.create_oval(cx + 4, cy + 1, cx + 8, cy + 5, fill="black", outline="", tags=T)
    c.create_line(cx + 4, cy + 9, cx + 10, cy + 9, fill="#7A2E2E", width=2, tags=T)

    # posição da corda / flecha encaixada
    segurando = self.estado in ("MIRANDO", "CARREGANDO")
    pull = self.puxada_atual()
    nx, ny = gx - dx * pull, gy - dy * pull

    # braço de trás (puxa a corda)
    s2x, s2y = px - 4, py - 2
    ex, ey = self.ik_braco(s2x, s2y, self.mao_x, self.mao_y, 22)
    c.create_line(
        s2x, s2y, ex, ey, self.mao_x, self.mao_y,
        fill=pele, width=7, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags=T,
    )

    # arco
    pontos = []
    for i in range(11):
      tt = -1 + i * 0.2
      bx = gx + perp[0] * 42 * tt - dx * 14 * tt * tt
      by = gy + perp[1] * 42 * tt - dy * 14 * tt * tt
      pontos.extend([bx, by])
    tip1 = (pontos[0], pontos[1])
    tip2 = (pontos[-2], pontos[-1])
    c.create_line(*pontos, fill="#5C3A1E", width=7, smooth=True, tags=T)
    c.create_line(*pontos, fill="#A9743F", width=3, smooth=True, tags=T)

    # corda
    if segurando:
      mx, my = nx, ny
    else:
      amp = 0
      if self.vibracao > 0:
        amp = 7 * (self.vibracao / 14.0) * math.sin(self.vibracao * 1.9)
      mx = gx - dx * 14 + perp[0] * amp
      my = gy - dy * 14 + perp[1] * amp
    c.create_line(tip1[0], tip1[1], mx, my, tip2[0], tip2[1], fill="#F2F2F2", width=1, tags=T)

    # flecha encaixada
    if segurando:
      self.desenhar_flecha(nx + dx * 44, ny + dy * 44, self.angulo, 44)

    # braço da frente (segura o arco)
    s1x, s1y = px + 4, py - 2
    fx, fy = self.ik_braco(s1x, s1y, gx, gy, 22)
    c.create_line(
        s1x, s1y, fx, fy, gx, gy,
        fill=pele, width=7, capstyle=tk.ROUND, joinstyle=tk.ROUND, tags=T,
    )
    c.create_oval(gx - 4, gy - 4, gx + 4, gy + 4, fill=pele, outline="", tags=T)
    c.create_oval(
        self.mao_x - 4, self.mao_y - 4, self.mao_x + 4, self.mao_y + 4,
        fill=pele, outline="", tags=T,
    )

    # barra de força
    if self.estado == "CARREGANDO":
      bx0, by0 = px - 40, py + 118
      c.create_rectangle(bx0, by0, bx0 + 80, by0 + 12, fill="white", outline="black", tags=T)
      frac = self.forca / self.forca_max
      if frac < 0.5:
        cor = self.misturar("#7CFC00", "#FFD700", frac / 0.5)
      else:
        cor = self.misturar("#FFD700", "#FF4500", (frac - 0.5) / 0.5)
      c.create_rectangle(bx0, by0, bx0 + 80 * frac, by0 + 12, fill=cor, outline="", tags=T)

  # ------------------------------------------------------------------
  # Arqueiro: posições auxiliares
  # ------------------------------------------------------------------
  def pos_descanso_mao(self):
    return self.pivo_x - 4, self.pivo_y + 44

  def puxada_atual(self):
    """Distância da corda/flecha até a empunhadura do arco."""
    if self.estado == "CARREGANDO":
      return 16 + 16 * (self.forca / self.forca_max)
    return 16

  def atualizar_arqueiro(self):
    dx, dy = math.cos(self.angulo), math.sin(self.angulo)
    gx = self.pivo_x + dx * self.braco_comp
    gy = self.pivo_y + dy * self.braco_comp
    if self.estado in ("MIRANDO", "CARREGANDO"):
      pull = self.puxada_atual()
      alvo = (gx - dx * pull, gy - dy * pull)
      k = 0.8 if self.estado == "CARREGANDO" else 0.35
    else:
      alvo = self.pos_descanso_mao()
      k = 0.18
    self.mao_x += (alvo[0] - self.mao_x) * k
    self.mao_y += (alvo[1] - self.mao_y) * k
    if self.vibracao > 0:
      self.vibracao -= 1

  # ------------------------------------------------------------------
  # Controles
  # ------------------------------------------------------------------
  def atualizar_mira(self, event):
    if self.estado in ("MIRANDO", "CARREGANDO"):
      dx = event.x - self.pivo_x
      dy = event.y - self.pivo_y
      self.angulo = math.atan2(dy, dx)
      if self.angulo > math.radians(60):
        self.angulo = math.radians(60)
      elif self.angulo < math.radians(-70):
        self.angulo = math.radians(-70)
      if dx < 0:
        self.angulo = 0

  def iniciar_carregamento(self, event):
    if self.estado == "MIRANDO":
      self.estado = "CARREGANDO"
      self.forca = 5

  def atirar(self, event):
    if self.estado == "CARREGANDO":
      dx, dy = math.cos(self.angulo), math.sin(self.angulo)
      gx = self.pivo_x + dx * self.braco_comp
      gy = self.pivo_y + dy * self.braco_comp
      pull = self.puxada_atual()
      # a flecha sai da ponta (tip) da flecha encaixada
      self.flecha_x = gx - dx * pull + dx * 44
      self.flecha_y = gy - dy * pull + dy * 44
      self.flecha_vx = dx * self.forca
      self.flecha_vy = dy * self.forca
      # a mão que puxava a corda dá um "coice" para trás
      self.mao_x = gx - dx * (pull + 10)
      self.mao_y = gy - dy * (pull + 10)
      self.vibracao = 14
      self.estado = "VOANDO"

  # ------------------------------------------------------------------
  # Lógica do jogo
  # ------------------------------------------------------------------
  def atualizar_jogo(self):
    if self.estado == "CARREGANDO":
      if self.forca < self.forca_max:
        self.forca += 0.8
    elif self.estado == "VOANDO":
      self.atualizar_flecha()

    self.atualizar_efeitos()
    self.mover_alvo()
    self.mover_nuvens()
    self.atualizar_arqueiro()
    self.desenhar_hud()

    if self.erros_corpo >= self.max_erros_corpo:
      self.estado = "GAME_OVER"

    if self.estado == "GAME_OVER":
      self.mostrar_tela_final("FIM DE JOGO - A pessoa levou flechadas demais!")
    elif self.estado == "VITORIA":
      self.mostrar_tela_final("🏆 PARABÉNS! Você zerou o Torneio com Maestria!")
    else:
      self.desenhar_elementos()
      self.root.after(25, self.atualizar_jogo)

  def atualizar_flecha(self):
    vx, vy = self.flecha_vx, self.flecha_vy
    # divide o movimento em passos pequenos para a flecha rápida
    # não "atravessar" a maçã sem colidir
    passos = int(math.hypot(vx, vy) / 6) + 1
    for _ in range(passos):
      self.flecha_x += vx / passos
      self.flecha_y += vy / passos
      if self.checar_colisao_flecha():
        return
    self.flecha_vy += 0.35  # Gravidade

  def checar_colisao_flecha(self):
    s = self.pessoa_escala
    fx, fy = self.flecha_x, self.flecha_y
    maca_x = self.pessoa_x
    maca_y = self.pessoa_y - 75 * s
    raio = self.maca_raio * s

    # Colisão com a Maçã
    if math.hypot(fx - maca_x, fy - maca_y) <= raio + 4:
      self.acertou_maca()
      return True
    # Colisão com o Corpo da Pessoa
    if (
        self.pessoa_x - 14 * s <= fx <= self.pessoa_x + 14 * s
        and self.pessoa_y - 70 * s <= fy <= self.pessoa_y + 45 * s
    ):
      self.acertou_corpo()
      return True
    # Errou o alvo
    if fx > self.largura or fx < 0 or fy >= self.chao_flecha:
      self.errou()
      return True
    return False

  def acertou_maca(self):
    self.pontos += 10
    if self.pontos > 50:
      self.pontos = 50
    self.disparar_confetes()
    self.iniciar_reacao("POSITIVO")
    self.textos.append({
        "x": self.pessoa_x, "y": self.pessoa_y - 110 * self.pessoa_escala,
        "txt": "+10", "cor": "#FFD700", "vida": 50, "tam": 16,
    })

    if self.fase == 4:
      self.acertos_fase_4 += 1
      if self.acertos_fase_4 >= 5:
        self.estado = "VITORIA"
      else:
        self.flechas_restantes = 1
        self.reiniciar_tiro()
    else:
      self.flechas_restantes -= 1
      self.verificar_mudanca_fase()

  def acertou_corpo(self):
    self.erros_corpo += 1
    self.flash_pessoa = 16
    self.iniciar_reacao("NEGATIVO")
    self.textos.append({
        "x": self.pessoa_x, "y": self.pessoa_y - 110 * self.pessoa_escala,
        "txt": "AI!", "cor": "#FF4040", "vida": 50, "tam": 16,
    })
    if self.fase == 4:
      self.estado = "GAME_OVER"
    else:
      self.flechas_restantes -= 1
      self.verificar_mudanca_fase()

  def errou(self):
    # flecha cravada no chão (se caiu dentro da tela)
    if 0 < self.flecha_x < self.largura and self.flecha_y >= self.chao_flecha:
      ang = math.atan2(self.flecha_vy, self.flecha_vx)
      self.flechas_cravadas.append((self.flecha_x, self.flecha_y, ang))
      self.flechas_cravadas = self.flechas_cravadas[-8:]
    self.iniciar_reacao("NEGATIVO")
    if self.fase == 4:
      self.estado = "GAME_OVER"
    else:
      self.flechas_restantes -= 1
      self.verificar_mudanca_fase()

  def verificar_mudanca_fase(self):
    if self.flechas_restantes <= 0:
      mudou = False
      if self.fase == 1:
        self.fase = 2
        self.flechas_restantes = 7
        mudou = True
      elif self.fase == 2:
        self.fase = 3
        self.flechas_restantes = 6
        mudou = True
      elif self.fase == 3:
        self.fase = 4
        self.flechas_restantes = 1
        self.acertos_fase_4 = 0
        mudou = True
      if mudou:
        self.flechas_cravadas = []
        self.textos.append({
            "x": self.largura / 2, "y": 250, "txt": f"FASE {self.fase}!",
            "cor": "#FFD700", "vida": 70, "tam": 28,
        })
    self.reiniciar_tiro()

  def reiniciar_tiro(self):
    if self.estado not in ["GAME_OVER", "VITORIA"]:
      self.estado = "MIRANDO"
      self.forca = 0

  def mover_alvo(self):
    cfg = self.fases_cfg[self.fase]
    # desliza suavemente para a nova distância / tamanho da fase
    dx = cfg["x"] - self.pessoa_x
    if abs(dx) > 0.5:
      self.pessoa_x += max(-2.5, min(2.5, dx))
    self.pessoa_escala += (cfg["escala"] - self.pessoa_escala) * 0.05

    # movimentação vertical do alvo (mais rápida a cada fase)
    self.pessoa_y += self.alvo_dir * cfg["vel"]
    if self.pessoa_y <= self.alvo_ymin:
      self.pessoa_y = self.alvo_ymin
      self.alvo_dir = 1
    elif self.pessoa_y >= self.alvo_ymax:
      self.pessoa_y = self.alvo_ymax
      self.alvo_dir = -1

  def mover_nuvens(self):
    for i, n in enumerate(self.nuvens):
      self.canvas.move(f"nuvem{i}", n["v"], 0)
      n["x"] += n["v"]
      if n["x"] - 70 > self.largura:
        self.canvas.move(f"nuvem{i}", -(self.largura + 300), 0)
        n["x"] -= self.largura + 300

  def atualizar_efeitos(self):
    for cf in self.confetes:
      cf["x"] += cf["vx"]
      cf["y"] += cf["vy"]
      cf["vy"] += 0.12
    self.confetes = [cf for cf in self.confetes if cf["y"] < self.altura]

    for tx in self.textos:
      tx["y"] -= 0.7
      tx["vida"] -= 1
    self.textos = [tx for tx in self.textos if tx["vida"] > 0]

    if self.flash_pessoa > 0:
      self.flash_pessoa -= 1

    if self.tempo_reacao > 0:
      self.tempo_reacao -= 1
      self.animacao_frame += 0.3
      if self.tempo_reacao == 0:
        self.tipo_reacao_plateia = None
        self.plateia_suja = True  # volta para a pose sentada

  def desenhar_hud(self):
    c = self.canvas
    c.delete("placar_txt")
    cor_pontos = self.calcular_cor_pontuacao()
    distancia = round((self.pessoa_x - self.pivo_x) / 10)

    if self.fase == 4:
      linha3 = (f"Acertos: {self.acertos_fase_4}/5", "darkorange")
    else:
      linha3 = (f"Flechas Restantes: {self.flechas_restantes}", "black")

    linhas = [
        (f"Pontos: {self.pontos}/50", cor_pontos),
        (f"Fase: {self.fase}", "black"),
        linha3,
        (f"Erros na Pessoa: {self.erros_corpo}/{self.max_erros_corpo}", "red"),
        (f"Distância do alvo: {distancia} m", "#5C3A1E"),
    ]
    for i, (texto, cor) in enumerate(linhas):
      c.create_text(
          22, 108 + i * 23, text=texto, anchor="w",
          font=("Arial", 12, "bold"), fill=cor, tags="placar_txt",
      )

  def calcular_cor_pontuacao(self):
    val = self.pontos
    if val <= 10:
      return "#4A9AD6"  # Azul claro
    elif val <= 20:
      return "#2F6F9F"  # Azul intermediário
    elif val <= 30:
      return "#1C3B5E"  # Azul escuro
    elif val <= 40:
      return "#0D1B2A"  # Azul profundo
    else:
      return "#000000"  # Preto fechado (Pontuação máxima)

  def disparar_confetes(self):
    self.confetes = []
    s = self.pessoa_escala
    for _ in range(50):
      self.confetes.append({
          "x": self.pessoa_x,
          "y": self.pessoa_y - 75 * s,
          "vx": random.uniform(-4, 4),
          "vy": random.uniform(-7, -1),
          "cor": random.choice(
              ["gold", "red", "orange", "yellow", "purple", "cyan", "pink"]
          ),
      })

  # ------------------------------------------------------------------
  # Tela final / reinício
  # ------------------------------------------------------------------
  def mostrar_tela_final(self, texto_principal):
    # Limpa dinâmicos e painel de placar anterior para evitar sobreposição
    self.canvas.delete("dinamico")
    self.canvas.delete("placar_txt")
    self.canvas.delete("plateia")

    self.canvas.create_rectangle(
        0, 0, self.largura, self.altura, fill="black", tags="fim_jogo"
    )
    self.canvas.create_text(
        self.largura / 2,
        self.altura / 2 - 45,
        text=texto_principal,
        font=("Arial", 18, "bold"),
        fill="yellow",
        tags="fim_jogo",
    )
    self.canvas.create_text(
        self.largura / 2,
        self.altura / 2,
        text=f"Pontuação Final: {self.pontos} / 50 pontos",
        font=("Arial", 15),
        fill="white",
        tags="fim_jogo",
    )

    if self.btn_reiniciar is None:
      self.btn_reiniciar = tk.Button(
          self.root,
          text="Jogar Novamente",
          font=("Arial", 12, "bold"),
          bg="#FFD700",
          command=self.reiniciar_jogo,
      )
      self.canvas.create_window(
          self.largura / 2,
          self.altura / 2 + 65,
          window=self.btn_reiniciar,
          tags="fim_jogo",
      )

  def reiniciar_jogo(self):
    if self.btn_reiniciar is not None:
      self.btn_reiniciar.destroy()
      self.btn_reiniciar = None

    self.canvas.delete("fim_jogo")

    # Reseta todas as variáveis de estado
    self.pontos = 0
    self.fase = 1
    self.flechas_restantes = 10
    self.erros_corpo = 0
    self.acertos_fase_4 = 0
    self.estado = "MIRANDO"
    self.forca = 0
    self.angulo = 0.0
    self.vibracao = 0
    self.mao_x, self.mao_y = self.pos_descanso_mao()
    self.pessoa_x = self.fases_cfg[1]["x"]
    self.pessoa_y = 370
    self.pessoa_escala = self.fases_cfg[1]["escala"]
    self.alvo_dir = 1
    self.flash_pessoa = 0
    self.flechas_cravadas = []
    self.confetes = []
    self.textos = []
    self.tipo_reacao_plateia = None
    self.tempo_reacao = 0
    self.plateia_suja = True

    # Reinicia o loop principal do jogo
    self.atualizar_jogo()


if __name__ == "__main__":
  root = tk.Tk()
  app = JogoArcoFlecha(root)
  root.mainloop()