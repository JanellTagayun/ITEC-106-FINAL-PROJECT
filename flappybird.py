"""
╔══════════════════════════════╗
║      FLAPPY BIRD  🐦         ║
║   Pure Python + tkinter      ║
╚══════════════════════════════╝

CONTROLS
--------
  Space / Click    Flap!

RUN
---
  python flappybird.py
"""

import tkinter as tk
import random
import math

# ──────────────────────────────────────────────
WIN_W   = 480
WIN_H   = 640
FPS_MS  = 16

GRAVITY     = 0.5
FLAP_VEL    = -9.0
MAX_FALL    = 12
PIPE_GAP    = 160
PIPE_W      = 70
PIPE_SPEED  = 3.2
PIPE_SPAWN  = 220    # px between pipes

BIRD_X  = 100
BIRD_R  = 18         # radius

# ──────────────────────────────────────────────
class FlappyBird:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flappy Bird 🐦")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                                bg="#70c5ce", highlightthickness=0)
        self.canvas.pack()

        self.best  = 0
        self.state = "waiting"   # waiting / playing / dead

        self.root.bind("<space>",          self._flap)
        self.root.bind("<Button-1>",       self._flap)
        self.root.bind("<KeyPress-space>", self._flap)

        self._build_bg()
        self._reset()
        self._loop()
        self.root.mainloop()

    # ── background (drawn once) ───────────────
    def _build_bg(self):
        self._bg_ids = []
        # sky gradient
        for y in range(0, WIN_H, 4):
            t = y / WIN_H
            r = int(112 + (180-112)*t)
            g = int(197 + (220-197)*t)
            b = int(206 + (180-206)*t)
            self._bg_ids.append(
                self.canvas.create_rectangle(0,y,WIN_W,y+4,
                    fill=f"#{r:02x}{g:02x}{b:02x}", outline=""))

        # distant city silhouette
        buildings = [(20,180,80),(110,160,60),(200,200,70),(300,150,90),
                     (400,170,55),(0,140,40),(350,190,80),(140,130,50)]
        for bx,bh,bw in buildings:
            self.canvas.create_rectangle(bx, WIN_H-60-bh, bx+bw, WIN_H-60,
                fill="#4a9999", outline="")

        # ground base
        self.canvas.create_rectangle(0, WIN_H-60, WIN_W, WIN_H,
            fill="#ded895", outline="")
        self.canvas.create_rectangle(0, WIN_H-60, WIN_W, WIN_H-48,
            fill="#6ab04c", outline="")

    # ── reset ─────────────────────────────────
    def _reset(self):
        self.bird_y   = WIN_H // 2
        self.bird_vy  = 0.0
        self.bird_rot = 0.0
        self.pipes    = []           # list of [x, gap_top_y]
        self.score    = 0
        self.frame    = 0
        self.wing_ang = 0
        self.wing_dir = 1
        self.floats   = []           # [(x,y,text,life)]
        self.particles= []           # [(x,y,vx,vy,size,color,life)]
        self.ground_x = 0.0
        self.state    = "waiting"

    # ── flap ──────────────────────────────────
    def _flap(self, ev=None):
        if self.state == "dead":
            self._reset()
            return
        if self.state == "waiting":
            self.state = "playing"
        self.bird_vy = FLAP_VEL
        # wing flap particles
        for _ in range(4):
            self.particles.append([
                BIRD_X, self.bird_y + 6,
                random.uniform(-2, 2), random.uniform(1, 4),
                random.randint(3,6), "#ffffff", 1.0
            ])

    # ── spawn pipe ────────────────────────────
    def _spawn_pipe(self):
        margin  = 90
        gap_top = random.randint(margin, WIN_H - 60 - PIPE_GAP - margin)
        self.pipes.append([WIN_W + PIPE_W, gap_top])

    # ── collision ─────────────────────────────
    def _check_hit(self):
        bx, by = BIRD_X, self.bird_y
        r = BIRD_R - 4   # slightly forgiving
        for px, gap_top in self.pipes:
            # upper pipe rect
            if (bx+r > px and bx-r < px+PIPE_W):
                if (by-r < gap_top) or (by+r > gap_top + PIPE_GAP):
                    return True
        # floor / ceiling
        if by + r >= WIN_H - 60 or by - r <= 0:
            return True
        return False

    # ── die ───────────────────────────────────
    def _die(self):
        self.state = "dead"
        if self.score > self.best:
            self.best = self.score
        # explosion particles
        for _ in range(20):
            self.particles.append([
                BIRD_X, self.bird_y,
                random.uniform(-5,5), random.uniform(-6,2),
                random.randint(5,12),
                random.choice(["#ffdd00","#ff8800","#ff4400","#ffffff"]),
                1.0
            ])

    # ── update ────────────────────────────────
    def _update(self):
        self.frame += 1

        # wing flap animation
        self.wing_ang += 12 * self.wing_dir
        if abs(self.wing_ang) > 30:
            self.wing_dir *= -1

        if self.state != "playing":
            # idle bob
            self.bird_y = WIN_H//2 + math.sin(self.frame*0.05)*10
            return

        # physics
        self.bird_vy  = min(self.bird_vy + GRAVITY, MAX_FALL)
        self.bird_y  += self.bird_vy

        # rotate bird by velocity
        self.bird_rot = max(-30, min(90, self.bird_vy * 5))

        # move ground
        self.ground_x = (self.ground_x - PIPE_SPEED) % 48

        # pipes
        if not self.pipes or self.pipes[-1][0] < WIN_W - PIPE_SPAWN:
            self._spawn_pipe()

        scored_this_frame = False
        for pipe in self.pipes:
            pipe[0] -= PIPE_SPEED
            # score when pipe passes bird
            if not scored_this_frame and pipe[0] + PIPE_W < BIRD_X and pipe[0] + PIPE_W + PIPE_SPEED >= BIRD_X:
                self.score += 1
                scored_this_frame = True
                self.floats.append([BIRD_X + 20, self.bird_y - 30, "+1", 1.0])
                # score milestone flash
                if self.score % 10 == 0:
                    self.floats.append([WIN_W//2, WIN_H//2, f"🎉 {self.score}!", 1.5])

        self.pipes = [p for p in self.pipes if p[0] > -PIPE_W - 10]

        # particles
        for pt in self.particles:
            pt[0] += pt[2]; pt[1] += pt[3]
            pt[3] += 0.2
            pt[6] -= 0.04
        self.particles = [p for p in self.particles if p[6] > 0]

        # floats
        for fl in self.floats:
            fl[1] -= 1.5
            fl[3] -= 0.03
        self.floats = [f for f in self.floats if f[3] > 0]

        # collision
        if self._check_hit():
            self._die()

    # ──────────────────────────────────────────
    #  DRAWING
    # ──────────────────────────────────────────
    def _draw_pipe(self, px, gap_top):
        gap_bot = gap_top + PIPE_GAP
        cap_h   = 18
        cap_ext = 6   # cap is wider than pipe body

        # upper pipe body
        if gap_top > 0:
            self.canvas.create_rectangle(px+4, 0, px+PIPE_W-4, gap_top,
                fill="#3ea832", outline="#2e8425", width=2, tags="pipe")
            # highlight strip
            self.canvas.create_rectangle(px+8, 0, px+16, gap_top,
                fill="#55cc44", outline="", tags="pipe")
            # upper pipe cap
            self.canvas.create_rectangle(px-cap_ext, gap_top-cap_h,
                px+PIPE_W+cap_ext, gap_top,
                fill="#3ea832", outline="#2d7a24", width=2, tags="pipe")
            self.canvas.create_rectangle(px-cap_ext+3, gap_top-cap_h+3,
                px+PIPE_W+cap_ext-3, gap_top-cap_h+8,
                fill="#55cc44", outline="", tags="pipe")

        # lower pipe body
        if gap_bot < WIN_H - 60:
            self.canvas.create_rectangle(px+4, gap_bot, px+PIPE_W-4, WIN_H-60,
                fill="#3ea832", outline="#2d7a24", width=2, tags="pipe")
            self.canvas.create_rectangle(px+8, gap_bot, px+16, WIN_H-60,
                fill="#55cc44", outline="", tags="pipe")
            # lower pipe cap
            self.canvas.create_rectangle(px-cap_ext, gap_bot,
                px+PIPE_W+cap_ext, gap_bot+cap_h,
                fill="#3ea832", outline="#2d7a24", width=2, tags="pipe")
            self.canvas.create_rectangle(px-cap_ext+3, gap_bot+3,
                px+PIPE_W+cap_ext-3, gap_bot+8,
                fill="#55cc44", outline="", tags="pipe")

    def _draw_bird(self):
        bx = BIRD_X
        by = int(self.bird_y)
        r  = BIRD_R
        rot = self.bird_rot   # degrees, positive = nose down
        wa  = self.wing_ang   # wing flap angle

        # shadow
        self.canvas.create_oval(bx-r+2, by+r-2, bx+r+2, by+r+8,
            fill="#5ab8c0",
            outline="", tags="bird")

        # ── tail feathers ─────────────────────
        tail_x = bx - r + 2
        tail_y = by
        self.canvas.create_polygon(
            tail_x, tail_y-4,
            tail_x-14, tail_y-8,
            tail_x-10, tail_y+2,
            tail_x-16, tail_y+6,
            tail_x-6,  tail_y+8,
            tail_x, tail_y+4,
            fill="#e8a020", outline="#c07010", tags="bird")

        # ── wing (below body) ──────────────────
        # wing tip offset based on flap angle
        wy_off = int(math.sin(math.radians(wa)) * 10)
        self.canvas.create_polygon(
            bx-6, by+4,
            bx-r+2, by + 10 + wy_off,
            bx+4,   by + 8 + wy_off,
            bx+r-4, by + 4,
            fill="#e8a020", outline="#c07010", tags="bird")

        # ── body ──────────────────────────────
        self.canvas.create_oval(bx-r, by-r, bx+r, by+r,
            fill="#ffdd00", outline="#e8b800", width=2, tags="bird")

        # body highlight
        self.canvas.create_oval(bx-r+4, by-r+4, bx+4, by-2,
            fill="#ffff88", outline="", tags="bird")

        # ── belly patch ───────────────────────
        self.canvas.create_oval(bx-5, by+2, bx+r-4, by+r-4,
            fill="#ffeeaa", outline="", tags="bird")

        # ── eye ───────────────────────────────
        ex = bx + 6
        ey = by - 5
        # white of eye
        self.canvas.create_oval(ex-7, ey-7, ex+7, ey+7,
            fill="#ffffff", outline="#dddddd", tags="bird")
        # pupil — looks slightly up when flying up
        py_off = max(-3, min(3, int(self.bird_vy * 0.3)))
        self.canvas.create_oval(ex-3, ey-3+py_off, ex+3, ey+3+py_off,
            fill="#222222", outline="", tags="bird")
        # shine
        self.canvas.create_oval(ex, ey-4+py_off, ex+3, ey-1+py_off,
            fill="#ffffff", outline="", tags="bird")

        # ── beak ──────────────────────────────
        # rotates slightly with bird tilt
        bk_y = by - 2 + int(rot * 0.08)
        self.canvas.create_polygon(
            bx+r-3, bk_y-3,
            bx+r+10, bk_y+1,
            bx+r-3, bk_y+5,
            fill="#ff8c00", outline="#cc6000", tags="bird")
        # beak line
        self.canvas.create_line(
            bx+r-3, bk_y+1, bx+r+8, bk_y+1,
            fill="#cc6000", width=1, tags="bird")

    def _draw_ground(self):
        # scrolling ground pattern
        self.canvas.create_rectangle(0, WIN_H-60, WIN_W, WIN_H,
            fill="#ded895", outline="", tags="ground")
        self.canvas.create_rectangle(0, WIN_H-60, WIN_W, WIN_H-48,
            fill="#6ab04c", outline="", tags="ground")
        # grass tufts
        ox = int(self.ground_x)
        for gx in range(-48+ox, WIN_W+48, 48):
            self.canvas.create_polygon(
                gx,    WIN_H-60,
                gx+6,  WIN_H-68,
                gx+12, WIN_H-60,
                fill="#5aa03c", outline="", tags="ground")
            self.canvas.create_polygon(
                gx+20, WIN_H-60,
                gx+26, WIN_H-70,
                gx+32, WIN_H-60,
                fill="#4a9030", outline="", tags="ground")
        # ground line
        self.canvas.create_line(0, WIN_H-48, WIN_W, WIN_H-48,
            fill="#4a9030", width=2, tags="ground")

    def _draw_particles(self):
        for px,py,vx,vy,sz,col,life in self.particles:
            a = max(0, min(1, life))
            # fade color toward bg
            r2,g2,b2 = int(col[1:3],16),int(col[3:5],16),int(col[5:7],16)
            br,bg,bb  = 112,197,206
            fr = int(br + (r2-br)*a)
            fg = int(bg + (g2-bg)*a)
            fb = int(bb + (b2-bb)*a)
            fade = f"#{fr:02x}{fg:02x}{fb:02x}"
            s = max(1, int(sz*life))
            self.canvas.create_oval(px-s,py-s,px+s,py+s,
                fill=fade, outline="", tags="fx")

    def _draw_floats(self):
        for fx,fy,text,life in self.floats:
            a = max(0,min(1,life))
            v = int(255*a)
            col = f"#{v:02x}{v:02x}00"
            self.canvas.create_text(int(fx),int(fy), text=text,
                font=("Arial",16,"bold"), fill=col, tags="fx")

    def _draw_hud(self):
        # score
        shadow_off = 2
        self.canvas.create_text(WIN_W//2+shadow_off, 60+shadow_off,
            text=str(self.score),
            font=("Arial",52,"bold"), fill="#555555", tags="hud")
        self.canvas.create_text(WIN_W//2, 60,
            text=str(self.score),
            font=("Arial",52,"bold"), fill="#ffffff", tags="hud")

        # best
        self.canvas.create_text(WIN_W-12, 12,
            text=f"BEST {self.best}",
            font=("Arial",14,"bold"), fill="#ffffff",
            anchor="ne", tags="hud")

    def _draw_waiting(self):
        # big title card
        self.canvas.create_rectangle(WIN_W//2-140, WIN_H//2-80,
                                      WIN_W//2+140, WIN_H//2+60,
            fill="#000000", outline="#ffffff", width=2, tags="ui")
        # drop shadow text
        self.canvas.create_text(WIN_W//2+2, WIN_H//2-46,
            text="FLAPPY BIRD", font=("Arial",26,"bold"),
            fill="#222222", stipple="gray50", tags="ui")
        self.canvas.create_text(WIN_W//2, WIN_H//2-48,
            text="FLAPPY BIRD", font=("Arial",26,"bold"),
            fill="#ffdd00", tags="ui")
        self.canvas.create_text(WIN_W//2, WIN_H//2-12,
            text="🐦", font=("Arial",24), tags="ui")
        self.canvas.create_text(WIN_W//2, WIN_H//2+22,
            text="Tap  SPACE  or  Click  to  flap!",
            font=("Arial",13), fill="#ffffff", tags="ui")

    def _draw_dead(self):
        # darken overlay (simulated with stipple)
        self.canvas.create_rectangle(0, 0, WIN_W, WIN_H,
            fill="#000000", stipple="gray25", tags="ui")

        # game over card
        self.canvas.create_rectangle(WIN_W//2-150, WIN_H//2-100,
                                      WIN_W//2+150, WIN_H//2+120,
            fill="#1a1a2e", outline="#ffdd00", width=3, tags="ui")

        self.canvas.create_text(WIN_W//2, WIN_H//2-65,
            text="GAME OVER", font=("Arial",28,"bold"),
            fill="#ff4444", tags="ui")

        self.canvas.create_text(WIN_W//2, WIN_H//2-20,
            text=f"Score:  {self.score}",
            font=("Arial",20,"bold"), fill="#ffffff", tags="ui")

        medal = "🥇" if self.score >= 20 else "🥈" if self.score >= 10 else "🥉" if self.score >= 5 else "💀"
        self.canvas.create_text(WIN_W//2, WIN_H//2+20,
            text=medal, font=("Arial",28), tags="ui")

        self.canvas.create_text(WIN_W//2, WIN_H//2+65,
            text=f"Best:  {self.best}",
            font=("Arial",16,"bold"), fill="#ffdd00", tags="ui")

        self.canvas.create_text(WIN_W//2, WIN_H//2+95,
            text="Tap  SPACE  to  restart",
            font=("Arial",12), fill="#aaaaaa", tags="ui")

    # ── main loop ─────────────────────────────
    def _loop(self):
        self._update()

        self.canvas.delete("pipe","bird","ground","fx","hud","ui")

        # pipes (behind bird)
        for px, gap_top in self.pipes:
            self._draw_pipe(int(px), gap_top)

        self._draw_ground()
        self._draw_particles()
        self._draw_bird()
        self._draw_floats()
        self._draw_hud()

        if self.state == "waiting":
            self._draw_waiting()
        elif self.state == "dead":
            self._draw_dead()

        self.root.after(FPS_MS, self._loop)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    FlappyBird()