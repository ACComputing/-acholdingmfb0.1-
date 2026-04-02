#!/usr/bin/env python3.14
# AC Holding Mario Fan Builder 0.1
# (C) AC Holdings / Team Flames
# Engine: CATSAN  |  Version: 0.1
import pygame,sys,os,math,struct,random,json,subprocess,tempfile,shutil,zipfile
import xml.etree.ElementTree as ET
from collections import deque
if sys.platform!="darwin":
    import tkinter as tk; from tkinter import filedialog

def _open_level_filetypes(): return [("SMBX level (.lvl)","*.lvl"),("LunaLua (.38a)","*.38a"),("Moondust (.lvlx)","*.lvlx"),("All files","*.*")]
def _save_level_filetypes(): return [("SMBX 1.3 binary (.lvl)","*.lvl"),("LunaLua (.38a)","*.38a"),("Moondust (.lvlx)","*.lvlx"),("All files","*.*")]
def _save_dialog_initial(sn,idir):
    base=sn or""; inf=os.path.basename(base) if base else""; start=idir
    if not start and base:
        d=os.path.dirname(os.path.abspath(base))
        if d and os.path.isdir(d): start=d
    if not start: start=os.path.expanduser("~")
    if not os.path.isdir(start): start=os.path.expanduser("~")
    return start,inf
def _tk_sub_open(idir,title,ft):
    code=("import tkinter as tk\nfrom tkinter import filedialog\nroot=tk.Tk()\nroot.withdraw()\nroot.attributes('-topmost',True)\nroot.update_idletasks()\n"
        f"try:\n p=filedialog.askopenfilename(title={title!r},filetypes={ft!r},initialdir={idir!r})\n print(p or'',end='')\nfinally:\n root.destroy()\n")
    r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=600); return(r.stdout or"").strip()or None
def _tk_sub_save(idir,inf,title,dext,ft):
    code=("import tkinter as tk\nfrom tkinter import filedialog\nroot=tk.Tk()\nroot.withdraw()\nroot.attributes('-topmost',True)\nroot.update_idletasks()\n"
        f"try:\n p=filedialog.asksaveasfilename(title={title!r},defaultextension={dext!r},filetypes={ft!r},initialfile={inf!r},initialdir={idir!r})\n print(p or'',end='')\nfinally:\n root.destroy()\n")
    r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=600); return(r.stdout or"").strip()or None
def ask_open_level_path(initial_dir=None):
    start=initial_dir or os.path.expanduser("~")
    if not os.path.isdir(start): start=os.path.expanduser("~")
    fts=_open_level_filetypes()
    if sys.platform=="darwin": path=_tk_sub_open(start,"Open Level",fts)
    else:
        root=tk.Tk();root.withdraw();root.attributes("-topmost",True);root.update_idletasks()
        try: path=filedialog.askopenfilename(parent=root,title="Open Level",filetypes=fts,initialdir=start)
        finally: root.destroy()
        path=path if path else None
    return path if path else None
def ask_save_level_path(suggested_name="level.lvl",initial_dir=None):
    base=suggested_name or"level.lvl"; start,inf=_save_dialog_initial(base,initial_dir)
    ext=os.path.splitext(inf)[1].lower(); dext=ext if ext in(".lvl",".38a",".lvlx")else".lvl"
    fts=_save_level_filetypes()
    if sys.platform=="darwin": path=_tk_sub_save(start,inf,"Save Level As",dext,fts)
    else:
        root=tk.Tk();root.withdraw();root.attributes("-topmost",True);root.update_idletasks()
        try: path=filedialog.asksaveasfilename(parent=root,title="Save Level As",defaultextension=dext,filetypes=fts,initialfile=inf,initialdir=start)
        finally: root.destroy()
    if not path: return None
    if not os.path.splitext(path)[1]: path+=dext
    return path
def ask_save_json_path(suggested_name="level.json",initial_dir=None):
    base=suggested_name or"level.json"; start,inf=_save_dialog_initial(base,initial_dir)
    jt=[("JSON (*.json)","*.json"),("All files","*.*")]
    if sys.platform=="darwin": path=_tk_sub_save(start,inf,"Export Level as JSON",".json",jt)
    else:
        root=tk.Tk();root.withdraw();root.attributes("-topmost",True);root.update_idletasks()
        try: path=filedialog.asksaveasfilename(parent=root,title="Export JSON",defaultextension=".json",filetypes=jt,initialfile=inf,initialdir=start)
        finally: root.destroy()
    if not path: return None
    if not path.lower().endswith(".json"): path+=".json"
    return path

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
WINDOW_WIDTH=600; WINDOW_HEIGHT=400; SIDEBAR_WIDTH=140; MENU_HEIGHT=18
TOOLBAR_HEIGHT=24; STATUSBAR_HEIGHT=18
CANVAS_X=SIDEBAR_WIDTH; CANVAS_Y=MENU_HEIGHT+TOOLBAR_HEIGHT
CANVAS_WIDTH=WINDOW_WIDTH-SIDEBAR_WIDTH; CANVAS_HEIGHT=WINDOW_HEIGHT-CANVAS_Y-STATUSBAR_HEIGHT
GRID_SIZE=16; FPS=60; ZOOM_MIN,ZOOM_MAX=0.5,3.0; ZOOM_STEP=0.25
SYS_BG=(236,233,216); SYS_BTN_FACE=(236,233,216); SYS_BTN_LIGHT=(255,255,255)
SYS_BTN_DARK=(172,168,153); SYS_BTN_DK_SHD=(113,111,100); SYS_WINDOW=(255,255,255)
SYS_HIGHLIGHT=(0,78,152); SYS_HIGHLIGHT2=(49,106,197); SYS_TEXT=(0,0,0)
SMBX_ORANGE=(255,140,0); SMBX_ORANGE_D=(200,90,0); SMBX_GOLD=(255,210,0); SMBX_NAVY=(0,30,100)
WHITE=(255,255,255); BLACK=(0,0,0); RED=(220,0,0); GREEN=(0,180,0); BLUE=(0,0,220)
YELLOW=(255,255,0); GRAY=(128,128,128); SMBX_GRID=(60,60,80)
GRAVITY=0.5; JUMP_STRENGTH=-9; MOVE_SPEED=3; TERMINAL_VELOCITY=10
pygame.init(); pygame.display.set_caption("AC Holding Mario Fan Builder 0.1")
FONT=pygame.font.Font(None,17); FONT_MENU=pygame.font.Font(None,17)
FONT_SMALL=pygame.font.Font(None,14); FONT_TITLE=pygame.font.Font(None,24)

# NES palette used by SMBX 1.3
N={
'sk':(92,148,252),'bk':(0,0,0),'wh':(252,252,252),
'bd':(128,52,0),'bm':(184,96,32),'bl':(228,148,88),'tn':(248,196,148),
'gd':(0,120,0),'gm':(0,168,0),'gl':(88,216,84),'gv':(152,248,120),
'rd':(168,16,0),'rm':(228,0,8),'rl':(248,88,88),
'ud':(0,0,168),'um':(0,88,248),
'od':(172,124,0),'om':(228,176,0),'ol':(248,216,88),'yl':(248,248,88),
'ad':(172,80,0),'am':(228,132,40),'al':(248,184,108),
'sd':(192,120,72),'sm':(228,168,124),'sl':(248,200,164),
'xd':(60,60,60),'xm':(124,124,124),'xl':(188,188,188),
'pd':(104,52,148),'pm':(148,88,196),'pk':(248,120,188),
}

TILE_SMBX_IDS={'ground':1,'grass':2,'sand':3,'dirt':4,'brick':45,'question':34,
    'pipe_vertical':112,'pipe_horizontal':113,'platform':159,'coin':10,
    'bridge':47,'stone':48,'ice':55,'mushroom_platform':91,'pswitch':60,
    'slope_left':182,'slope_right':183,'water':196,'lava':197,
    'conveyor_left':188,'conveyor_right':189,'semisolid':190}
BGO_SMBX_IDS={'cloud':5,'bush':6,'hill':7,'fence':8,'bush_3':9,'tree':10,
    'castle':11,'waterfall':12,'sign':13,'fence2':14,'fence3':15}
NPC_SMBX_IDS={'goomba':1,'koopa_green':2,'koopa_red':3,'paratroopa_green':4,
    'paratroopa_red':5,'piranha':6,'hammer_bro':7,'lakitu':8,
    'mushroom':9,'flower':10,'star':11,'1up':12,
    'buzzy':13,'spiny':14,'cheep':15,'blooper':16,'thwomp':17,
    'bowser':18,'boo':19,'podoboo':20,'piranha_fire':21}
TILE_ID_TO_NAME={v:k for k,v in TILE_SMBX_IDS.items()}
BGO_ID_TO_NAME={v:k for k,v in BGO_SMBX_IDS.items()}
NPC_ID_TO_NAME={v:k for k,v in NPC_SMBX_IDS.items()}

themes={
 'SMB1':{'background':(92,148,252),'ground':(0,128,0),'brick':(180,80,40),'question':(255,200,0),'coin':(255,255,0),'pipe_vertical':(0,200,0),'pipe_horizontal':(0,180,0),'platform':(139,69,19),'goomba':(200,100,0),'koopa_green':(0,200,50),'koopa_red':(200,50,50),'mushroom':(255,0,200),'flower':(255,140,0),'star':(255,230,0),'bgo_cloud':(220,220,220),'bgo_bush':(0,160,0),'bgo_hill':(100,200,100),'bgo_tree':(0,120,0),'grass':(60,180,60),'sand':(220,200,100),'dirt':(150,100,60),'stone':(140,140,140),'ice':(160,220,255),'bridge':(160,100,40),'mushroom_platform':(200,100,200),'pswitch':(80,80,200),'slope_left':(180,180,0),'slope_right':(180,180,0),'water':(0,100,255),'lava':(255,80,0),'conveyor_left':(100,100,100),'conveyor_right':(100,100,100),'semisolid':(150,150,200),'1up':(0,200,0),'buzzy':(80,80,200),'spiny':(200,80,0),'cheep':(255,80,80),'blooper':(220,220,220),'thwomp':(80,80,120),'bowser':(80,200,80),'boo':(220,220,220),'podoboo':(255,80,0),'piranha_fire':(255,120,0),'paratroopa_green':(0,200,50),'paratroopa_red':(200,50,50),'piranha':(0,200,0),'hammer_bro':(0,180,80),'lakitu':(180,180,0)},
 'SMB3':{'background':(0,0,0),'ground':(160,120,80),'brick':(180,100,60),'question':(255,210,0),'coin':(255,255,100),'pipe_vertical':(0,180,0),'pipe_horizontal':(0,160,0),'platform':(100,100,100),'goomba':(255,50,50),'koopa_green':(0,200,0),'koopa_red':(200,0,0),'mushroom':(255,100,200),'flower':(255,150,0),'star':(255,255,0),'bgo_cloud':(150,150,150),'bgo_bush':(0,100,0),'bgo_hill':(80,160,80),'bgo_tree':(0,80,0),'grass':(130,100,60),'sand':(200,170,80),'dirt':(120,80,40),'stone':(110,110,110),'ice':(130,190,230),'bridge':(130,80,30),'mushroom_platform':(170,80,170),'pswitch':(60,60,170),'slope_left':(180,180,0),'slope_right':(180,180,0),'water':(0,100,255),'lava':(255,80,0),'conveyor_left':(100,100,100),'conveyor_right':(100,100,100),'semisolid':(150,150,200),'1up':(0,200,0),'buzzy':(80,80,200),'spiny':(200,80,0),'cheep':(255,80,80),'blooper':(220,220,220),'thwomp':(80,80,120),'bowser':(80,200,80),'boo':(220,220,220),'podoboo':(255,80,0),'piranha_fire':(255,120,0),'paratroopa_green':(0,200,0),'paratroopa_red':(200,0,0),'piranha':(0,180,0),'hammer_bro':(0,160,80),'lakitu':(160,160,0)},
 'SMW':{'background':(110,200,255),'ground':(200,160,100),'brick':(210,120,70),'question':(255,220,0),'coin':(255,240,0),'pipe_vertical':(0,220,80),'pipe_horizontal':(0,200,70),'platform':(180,130,70),'goomba':(210,120,0),'koopa_green':(0,220,80),'koopa_red':(220,60,60),'mushroom':(255,50,200),'flower':(255,160,0),'star':(255,240,0),'bgo_cloud':(240,240,240),'bgo_bush':(0,200,80),'bgo_hill':(120,220,120),'bgo_tree':(0,160,60),'grass':(80,200,80),'sand':(230,210,120),'dirt':(170,120,70),'stone':(160,160,160),'ice':(180,230,255),'bridge':(180,120,50),'mushroom_platform':(220,120,220),'pswitch':(100,100,220),'slope_left':(180,180,0),'slope_right':(180,180,0),'water':(0,100,255),'lava':(255,80,0),'conveyor_left':(100,100,100),'conveyor_right':(100,100,100),'semisolid':(150,150,200),'1up':(0,200,0),'buzzy':(80,80,200),'spiny':(200,80,0),'cheep':(255,80,80),'blooper':(220,220,220),'thwomp':(80,80,120),'bowser':(80,200,80),'boo':(220,220,220),'podoboo':(255,80,0),'piranha_fire':(255,120,0),'paratroopa_green':(0,220,80),'paratroopa_red':(220,60,60),'piranha':(0,220,80),'hammer_bro':(0,200,100),'lakitu':(200,200,0)},
}
current_theme='SMB1'

def get_theme_color(name): return themes[current_theme].get(name,(128,128,128))

# ─── PIXEL ART HELPERS ──────────────────────────────────────────────────────
def px(s,x,y,c):
    if 0<=x<s.get_width() and 0<=y<s.get_height(): s.set_at((x,y),c)
def pxr(s,x,y,w,h,c): pygame.draw.rect(s,c,(x,y,w,h))
def pxh(s,x,y,w,c): pygame.draw.line(s,c,(x,y),(x+w-1,y))
def pxv(s,x,y,h,c): pygame.draw.line(s,c,(x,y),(x,y+h-1))

# ─── UI HELPERS ──────────────────────────────────────────────────────────────
def draw_edge(surf,rect,raised=True):
    r=pygame.Rect(rect)
    tl=SYS_BTN_LIGHT if raised else SYS_BTN_DK_SHD; br=SYS_BTN_DK_SHD if raised else SYS_BTN_LIGHT
    tli=SYS_BTN_FACE if raised else SYS_BTN_DARK; bri=SYS_BTN_DARK if raised else SYS_BTN_FACE
    pygame.draw.line(surf,tl,r.topleft,r.topright); pygame.draw.line(surf,tl,r.topleft,r.bottomleft)
    pygame.draw.line(surf,br,r.bottomleft,r.bottomright); pygame.draw.line(surf,br,r.topright,r.bottomright)
    if r.width>4 and r.height>4:
        pygame.draw.line(surf,tli,(r.left+1,r.top+1),(r.right-1,r.top+1))
        pygame.draw.line(surf,tli,(r.left+1,r.top+1),(r.left+1,r.bottom-1))
        pygame.draw.line(surf,bri,(r.left+1,r.bottom-1),(r.right-1,r.bottom-1))
        pygame.draw.line(surf,bri,(r.right-1,r.top+1),(r.right-1,r.bottom-1))
def draw_text(surf,text,pos,color=SYS_TEXT,font=FONT,center=False):
    t=font.render(str(text),True,color); r=t.get_rect(center=pos) if center else t.get_rect(topleft=pos); surf.blit(t,r)

# ─── ICON DRAWING ────────────────────────────────────────────────────────────
def draw_icon_select(s,r,c=SYS_TEXT):
    r2=r.inflate(-6,-6)
    for i in range(0,r2.width,4):
        if(i//4)%2==0: pygame.draw.line(s,c,(r2.x+i,r2.y),(min(r2.x+i+3,r2.right),r2.y)); pygame.draw.line(s,c,(r2.x+i,r2.bottom),(min(r2.x+i+3,r2.right),r2.bottom))
    for i in range(0,r2.height,4):
        if(i//4)%2==0: pygame.draw.line(s,c,(r2.x,r2.y+i),(r2.x,min(r2.y+i+3,r2.bottom))); pygame.draw.line(s,c,(r2.right,r2.y+i),(r2.right,min(r2.y+i+3,r2.bottom)))
def draw_icon_pencil(s,r,c=SYS_TEXT):
    cx,cy=r.center; pygame.draw.polygon(s,c,[(cx-1,cy+5),(cx+4,cy-2),(cx+2,cy-4),(cx-3,cy+3)],1); pygame.draw.line(s,c,(cx-1,cy+5),(cx-3,cy+7))
def draw_icon_eraser(s,r,c=SYS_TEXT): r2=r.inflate(-6,-6); pygame.draw.rect(s,c,(r2.x,r2.centery-2,r2.width,5),1)
def draw_icon_fill(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.rect(s,c,(cx-4,cy-3,6,6),1); pygame.draw.rect(s,c,(cx-3,cy-2,4,4)); pygame.draw.circle(s,c,(cx+4,cy+3),2)
def draw_icon_new(s,r,c=SYS_TEXT):
    r2=r.inflate(-6,-5); f=4; pygame.draw.polygon(s,c,[(r2.x,r2.y),(r2.right-f,r2.y),(r2.right,r2.y+f),(r2.right,r2.bottom),(r2.x,r2.bottom)],1)
    pygame.draw.line(s,c,(r2.right-f,r2.y),(r2.right-f,r2.y+f)); pygame.draw.line(s,c,(r2.right-f,r2.y+f),(r2.right,r2.y+f))
def draw_icon_open(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.rect(s,c,(cx-6,cy-1,11,7),1); pygame.draw.rect(s,c,(cx-6,cy-4,5,3),1)
def draw_icon_save(s,r,c=SYS_TEXT): r2=r.inflate(-6,-5); pygame.draw.rect(s,c,r2,1); pygame.draw.rect(s,c,(r2.x+4,r2.y+1,r2.width-8,r2.height//2-1),1); pygame.draw.rect(s,c,(r2.x+r2.width//3,r2.bottom-4,r2.width//3,4))
def draw_icon_undo(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.arc(s,c,(cx-5,cy-3,10,8),math.pi*0.3,math.pi*1.1,2); pygame.draw.polygon(s,c,[(cx-5,cy-3),(cx-8,cy),(cx-2,cy-1)])
def draw_icon_redo(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.arc(s,c,(cx-5,cy-3,10,8),math.pi*1.9,math.pi*0.7+math.pi*2,2); pygame.draw.polygon(s,c,[(cx+5,cy-3),(cx+8,cy),(cx+2,cy-1)])
def draw_icon_play(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.polygon(s,c,[(cx-3,cy-5),(cx-3,cy+5),(cx+5,cy)])
def draw_icon_props(s,r,c=SYS_TEXT): cx,cy=r.center; draw_text(s,"i",(cx,cy),c,FONT_SMALL,True); pygame.draw.circle(s,c,(cx,cy-4),1)
def draw_icon_grid(s,r,c=SYS_TEXT):
    r2=r.inflate(-5,-5)
    for i in range(0,r2.width+1,r2.width//2): pygame.draw.line(s,c,(r2.x+i,r2.y),(r2.x+i,r2.bottom))
    for i in range(0,r2.height+1,r2.height//2): pygame.draw.line(s,c,(r2.x,r2.y+i),(r2.right,r2.y+i))
def draw_icon_zoom_in(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.circle(s,c,(cx-1,cy-1),4,1); pygame.draw.line(s,c,(cx+2,cy+2),(cx+5,cy+5),2); pygame.draw.line(s,c,(cx-3,cy-1),(cx+1,cy-1)); pygame.draw.line(s,c,(cx-1,cy-3),(cx-1,cy+1))
def draw_icon_zoom_out(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.circle(s,c,(cx-1,cy-1),4,1); pygame.draw.line(s,c,(cx+2,cy+2),(cx+5,cy+5),2); pygame.draw.line(s,c,(cx-3,cy-1),(cx+1,cy-1))
def draw_icon_layer(s,r,c=SYS_TEXT):
    r2=r.inflate(-5,-5)
    for i in range(3): pygame.draw.rect(s,c,(r2.x,r2.y+i*3,r2.width,3),1)
def draw_icon_event(s,r,c=SYS_TEXT): cx,cy=r.center; pygame.draw.circle(s,c,(cx-3,cy-2),2); pygame.draw.circle(s,c,(cx+3,cy-2),2); pygame.draw.arc(s,c,(cx-5,cy,10,6),0,math.pi,2)
ICON_FNS={'select':draw_icon_select,'pencil':draw_icon_pencil,'eraser':draw_icon_eraser,'fill':draw_icon_fill,'new':draw_icon_new,'open':draw_icon_open,'save':draw_icon_save,'undo':draw_icon_undo,'redo':draw_icon_redo,'play':draw_icon_play,'props':draw_icon_props,'grid':draw_icon_grid,'zoom_in':draw_icon_zoom_in,'zoom_out':draw_icon_zoom_out,'layer':draw_icon_layer,'event':draw_icon_event}

# ─── DIALOGS ─────────────────────────────────────────────────────────────────
class Dialog:
    def __init__(self,screen,title,w,h):
        self.screen=screen;self.title=title;self.w,self.h=w,h;self.x=(WINDOW_WIDTH-w)//2;self.y=(WINDOW_HEIGHT-h)//2
        self.rect=pygame.Rect(self.x,self.y,w,h);self.done=False;self.result=None
        self._ov=pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA);self._ov.fill((0,0,0,120))
    def _draw_frame(self):
        self.screen.blit(self._ov,(0,0));pygame.draw.rect(self.screen,SYS_BTN_FACE,self.rect);draw_edge(self.screen,self.rect,True)
        tr=pygame.Rect(self.x+2,self.y+2,self.w-4,18)
        for i in range(tr.height):
            t=i/tr.height;c=(int(49*t),int(78+28*t),int(152+45*t));pygame.draw.line(self.screen,c,(tr.x,tr.y+i),(tr.right,tr.y+i))
        draw_text(self.screen,self.title,(tr.x+4,tr.y+3),WHITE,FONT_SMALL)
        xr=pygame.Rect(tr.right-16,tr.y+1,14,14);pygame.draw.rect(self.screen,(200,50,50),xr);draw_edge(self.screen,xr,True);draw_text(self.screen,"X",xr.center,WHITE,FONT_SMALL,True)
        return tr,xr
    def run(self):
        ck=pygame.time.Clock()
        while not self.done:
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: self.done=True;self.result=None
                self.handle_event(ev)
            self.draw();pygame.display.flip();ck.tick(60)
        return self.result
    def handle_event(self,ev): pass
    def draw(self): self._draw_frame()

class MessageBox(Dialog):
    def __init__(self,screen,title,message,buttons=("OK",)):
        lines=message.split('\n');w=max(260,max(FONT_SMALL.size(l)[0] for l in lines)+50);h=70+len(lines)*16+36
        super().__init__(screen,title,w,h);self.message=message;self.buttons=buttons
    def handle_event(self,ev):
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            by=self.h-34;bw=60;gap=8;total=len(self.buttons)*(bw+gap)-gap;bs=(self.w-total)//2
            for i,b in enumerate(self.buttons):
                r=pygame.Rect(self.x+bs+i*(bw+gap),self.y+by,bw,22)
                if r.collidepoint(ev.pos): self.result=b;self.done=True
    def draw(self):
        self._draw_frame();lines=self.message.split('\n')
        for i,l in enumerate(lines): draw_text(self.screen,l,(self.x+16,self.y+30+i*16),SYS_TEXT,FONT_SMALL)
        by=self.h-34;bw=60;gap=8;total=len(self.buttons)*(bw+gap)-gap;bs=(self.w-total)//2
        for i,b in enumerate(self.buttons):
            r=pygame.Rect(self.x+bs+i*(bw+gap),self.y+by,bw,22);pygame.draw.rect(self.screen,SYS_BTN_FACE,r);draw_edge(self.screen,r,True);draw_text(self.screen,b,r.center,SYS_TEXT,FONT_SMALL,True)

class InputDialog(Dialog):
    def __init__(self,screen,title,prompt,default=""):
        super().__init__(screen,title,300,100);self.prompt=prompt;self.value=default;self.cursor=len(default)
    def handle_event(self,ev):
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_RETURN: self.result=self.value;self.done=True
            elif ev.key==pygame.K_ESCAPE: self.done=True
            elif ev.key==pygame.K_BACKSPACE and self.cursor>0: self.value=self.value[:self.cursor-1]+self.value[self.cursor:];self.cursor-=1
            elif ev.key==pygame.K_LEFT: self.cursor=max(0,self.cursor-1)
            elif ev.key==pygame.K_RIGHT: self.cursor=min(len(self.value),self.cursor+1)
            elif ev.unicode and ev.unicode.isprintable(): self.value=self.value[:self.cursor]+ev.unicode+self.value[self.cursor:];self.cursor+=1
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if pygame.Rect(self.x+self.w-144,self.y+72,60,22).collidepoint(ev.pos): self.result=self.value;self.done=True
            if pygame.Rect(self.x+self.w-76,self.y+72,60,22).collidepoint(ev.pos): self.done=True
    def draw(self):
        self._draw_frame();draw_text(self.screen,self.prompt,(self.x+12,self.y+28),SYS_TEXT,FONT_SMALL)
        ir=pygame.Rect(self.x+12,self.y+44,self.w-24,18);pygame.draw.rect(self.screen,SYS_WINDOW,ir);draw_edge(self.screen,ir,False)
        draw_text(self.screen,self.value,(ir.x+3,ir.y+3),SYS_TEXT,FONT_SMALL)
        if pygame.time.get_ticks()%1000<500: cx=ir.x+3+FONT_SMALL.size(self.value[:self.cursor])[0];pygame.draw.line(self.screen,BLACK,(cx,ir.y+2),(cx,ir.y+15))
        for lbl,bx in[("OK",self.w-144),("Cancel",self.w-76)]:
            r=pygame.Rect(self.x+bx,self.y+72,60,22);pygame.draw.rect(self.screen,SYS_BTN_FACE,r);draw_edge(self.screen,r,True);draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)

class PropertiesDialog(Dialog):
    def __init__(self,screen,level):
        super().__init__(screen,"Level Properties",340,300);self.level=level;self.section=level.current_section()
        self.fields={'name':level.name,'author':level.author,'width':str(self.section.width//GRID_SIZE),'height':str(self.section.height//GRID_SIZE),'time':str(level.time_limit)}
        self.active_field=None;self.cursors={k:len(v) for k,v in self.fields.items()};self.theme_sel=current_theme
    def _fr(self,fy): return pygame.Rect(self.x+120,self.y+fy,200,16)
    def handle_event(self,ev):
        labels=[('name','Level Name:',40),('author','Author:',60),('width','Width(tiles):',80),('height','Height(tiles):',96),('time','Time Limit:',112)]
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            self.active_field=None
            for key,_,fy in labels:
                if self._fr(fy).collidepoint(ev.pos): self.active_field=key
            bgs=[(92,148,252),(0,0,40),(0,0,0),(255,140,60),(30,20,10),(0,80,160)]
            for i,col in enumerate(bgs):
                if pygame.Rect(self.x+8+i*52,self.y+196,50,14).collidepoint(ev.pos): self.section.bg_color=col
            for i,tn in enumerate(themes.keys()):
                if pygame.Rect(self.x+8+i*76,self.y+228,72,16).collidepoint(ev.pos): self.theme_sel=tn
            if pygame.Rect(self.x+self.w-132,self.y+self.h-32,58,22).collidepoint(ev.pos): self._apply();self.result='ok';self.done=True
            if pygame.Rect(self.x+self.w-68,self.y+self.h-32,58,22).collidepoint(ev.pos): self.done=True
        if ev.type==pygame.KEYDOWN and self.active_field:
            k=self.active_field;v=self.fields[k];c=self.cursors[k]
            if ev.key==pygame.K_RETURN: self.active_field=None
            elif ev.key==pygame.K_BACKSPACE and c>0: self.fields[k]=v[:c-1]+v[c:];self.cursors[k]=c-1
            elif ev.key==pygame.K_LEFT: self.cursors[k]=max(0,c-1)
            elif ev.key==pygame.K_RIGHT: self.cursors[k]=min(len(v),c+1)
            elif ev.unicode and ev.unicode.isprintable(): self.fields[k]=v[:c]+ev.unicode+v[c:];self.cursors[k]=c+1
    def _apply(self):
        global current_theme;self.level.name=self.fields['name'];self.level.author=self.fields['author']
        try: self.section.width=max(10,int(self.fields['width']))*GRID_SIZE;self.section.height=max(5,int(self.fields['height']))*GRID_SIZE;self.level.time_limit=max(0,int(self.fields['time']))
        except: pass
        current_theme=self.theme_sel
    def draw(self):
        self._draw_frame()
        labels=[('name','Level Name:',40),('author','Author:',60),('width','Width(tiles):',80),('height','Height(tiles):',96),('time','Time Limit:',112)]
        for key,lbl,fy in labels:
            draw_text(self.screen,lbl,(self.x+8,self.y+fy+1),SYS_TEXT,FONT_SMALL);ir=self._fr(fy);pygame.draw.rect(self.screen,SYS_WINDOW,ir);draw_edge(self.screen,ir,False)
            draw_text(self.screen,self.fields[key],(ir.x+3,ir.y+2),SYS_TEXT,FONT_SMALL)
            if self.active_field==key and pygame.time.get_ticks()%1000<500:
                cx=ir.x+3+FONT_SMALL.size(self.fields[key][:self.cursors[key]])[0];pygame.draw.line(self.screen,BLACK,(cx,ir.y+1),(cx,ir.y+14))
        draw_text(self.screen,"Background:",(self.x+8,self.y+182),SYS_TEXT,FONT_SMALL)
        bgs=[(92,148,252),(0,0,40),(0,0,0),(255,140,60),(30,20,10),(0,80,160)];names=['Sky','Night','Black','Sunset','Cave','Water']
        for i,col in enumerate(bgs):
            r=pygame.Rect(self.x+8+i*52,self.y+196,50,14);pygame.draw.rect(self.screen,col,r);draw_edge(self.screen,r,self.section.bg_color!=col)
            draw_text(self.screen,names[i][:5],(r.x+2,r.y+2),WHITE if sum(col)<300 else BLACK,FONT_SMALL)
        draw_text(self.screen,"Theme:",(self.x+8,self.y+214),SYS_TEXT,FONT_SMALL)
        for i,tn in enumerate(themes.keys()):
            r=pygame.Rect(self.x+8+i*76,self.y+228,72,16);sel=(tn==self.theme_sel)
            pygame.draw.rect(self.screen,SYS_HIGHLIGHT if sel else SYS_BTN_FACE,r);draw_edge(self.screen,r,not sel);draw_text(self.screen,tn,r.center,WHITE if sel else SYS_TEXT,FONT_SMALL,True)
        for lbl,bx in[("OK",self.w-132),("Cancel",self.w-68)]:
            r=pygame.Rect(self.x+bx,self.y+self.h-32,58,22);pygame.draw.rect(self.screen,SYS_BTN_FACE,r);draw_edge(self.screen,r,True);draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)

class LayerDialog(Dialog):
    def __init__(self,screen,section):
        super().__init__(screen,"Layer Manager",280,260);self.section=section;self.sel=section.current_layer_idx
        self.new_name=section.layers[self.sel].name if section.layers else"";self.cursor=len(self.new_name)
    def handle_event(self,ev):
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            for i,layer in enumerate(self.section.layers):
                r=pygame.Rect(self.x+8,self.y+30+i*18,self.w-16,16)
                if r.collidepoint(ev.pos): self.sel=i;self.new_name=layer.name;self.cursor=len(self.new_name)
                if pygame.Rect(r.right-14,r.y+2,12,12).collidepoint(ev.pos): layer.visible=not layer.visible
            if pygame.Rect(self.x+8,self.y+self.h-66,56,20).collidepoint(ev.pos):
                nm=InputDialog(self.screen,"New Layer","Name:",f"Layer {len(self.section.layers)+1}").run()
                if nm: self.section.layers.append(Layer(nm))
            if pygame.Rect(self.x+70,self.y+self.h-66,56,20).collidepoint(ev.pos) and len(self.section.layers)>1:
                self.section.layers.pop(self.sel);self.sel=max(0,self.sel-1);self.section.current_layer_idx=self.sel
            if pygame.Rect(self.x+132,self.y+self.h-66,80,20).collidepoint(ev.pos) and self.section.layers: self.section.layers[self.sel].name=self.new_name
            if pygame.Rect(self.x+self.w-132,self.y+self.h-38,56,22).collidepoint(ev.pos): self.section.current_layer_idx=self.sel;self.result='ok';self.done=True
            if pygame.Rect(self.x+self.w-70,self.y+self.h-38,56,22).collidepoint(ev.pos): self.done=True
        if ev.type==pygame.KEYDOWN:
            v=self.new_name;c=self.cursor
            if ev.key==pygame.K_BACKSPACE and c>0: self.new_name=v[:c-1]+v[c:];self.cursor=c-1
            elif ev.key==pygame.K_LEFT: self.cursor=max(0,c-1)
            elif ev.key==pygame.K_RIGHT: self.cursor=min(len(v),c+1)
            elif ev.unicode and ev.unicode.isprintable(): self.new_name=v[:c]+ev.unicode+v[c:];self.cursor=c+1
    def draw(self):
        self._draw_frame();draw_text(self.screen,"Layers:",(self.x+10,self.y+22),SYS_TEXT,FONT_SMALL)
        for i,layer in enumerate(self.section.layers):
            r=pygame.Rect(self.x+8,self.y+30+i*18,self.w-16,16);bg=SYS_HIGHLIGHT if i==self.sel else SYS_WINDOW
            pygame.draw.rect(self.screen,bg,r);draw_edge(self.screen,r,False);col=WHITE if i==self.sel else SYS_TEXT
            draw_text(self.screen,layer.name,(r.x+3,r.y+2),col,FONT_SMALL);pygame.draw.circle(self.screen,GREEN if layer.visible else RED,(r.right-8,r.centery),4)
        draw_text(self.screen,"Name:",(self.x+8,self.y+self.h-86),SYS_TEXT,FONT_SMALL)
        ir=pygame.Rect(self.x+50,self.y+self.h-88,self.w-58,18);pygame.draw.rect(self.screen,SYS_WINDOW,ir);draw_edge(self.screen,ir,False)
        draw_text(self.screen,self.new_name,(ir.x+3,ir.y+2),SYS_TEXT,FONT_SMALL)
        if pygame.time.get_ticks()%1000<500: cx=ir.x+3+FONT_SMALL.size(self.new_name[:self.cursor])[0];pygame.draw.line(self.screen,BLACK,(cx,ir.y+2),(cx,ir.y+14))
        for lbl,bx,bw in[("Add",8,56),("Delete",70,56),("Rename",132,80)]:
            r=pygame.Rect(self.x+bx,self.y+self.h-66,bw,20);pygame.draw.rect(self.screen,SYS_BTN_FACE,r);draw_edge(self.screen,r,True);draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)
        for lbl,bx in[("OK",self.w-132),("Close",self.w-70)]:
            r=pygame.Rect(self.x+bx,self.y+self.h-38,56,22);pygame.draw.rect(self.screen,SYS_BTN_FACE,r);draw_edge(self.screen,r,True);draw_text(self.screen,lbl,r.center,SYS_TEXT,FONT_SMALL,True)

# ─── DATA ────────────────────────────────────────────────────────────────────
class Event:
    def __init__(self,name="New Event",trigger="0",actions=None,eid=0,msg=""): self.name=name;self.trigger=trigger;self.actions=actions or[];self.id=eid;self.msg=msg
class Warp:
    def __init__(self,**kw): self.__dict__.update(kw)
class CharacterStart:
    def __init__(self,cid=0,state=0,x=0,y=0,w=0,h=0,cx=0,cy=0): self.id=cid;self.state=state;self.x=x;self.y=y;self.w=w;self.h=h;self.cx=cx;self.cy=cy

class GameObject(pygame.sprite.Sprite):
    def __init__(self,x,y,obj_type,layer=0,event_id=-1,flags=0):
        super().__init__();self.rect=pygame.Rect(x,y,GRID_SIZE,GRID_SIZE);self.layer=layer;self.obj_type=obj_type;self.event_id=event_id;self.flags=flags

# ─── SMBX 1.3 TILE RENDERING (NES pixel art) ────────────────────────────────
class Tile(GameObject):
    def __init__(self,x,y,tile_type,layer=0,event_id=-1,flags=0,contents=0,contained_npc_id=0,special_data=0):
        super().__init__(x,y,tile_type,layer,event_id,flags);self.tile_type=tile_type;self.is_solid=tile_type not in['coin','water','lava']
        self.contents=contents;self.contained_npc_id=contained_npc_id;self.special_data=special_data;self.update_image()
    def update_image(self):
        S=GRID_SIZE;s=pygame.Surface((S,S),pygame.SRCALPHA);tt=self.tile_type
        if tt=='ground':
            s.fill(N['bm'])
            pxh(s,0,3,S,N['bk']);pxh(s,0,7,S,N['bk']);pxh(s,0,11,S,N['bk']);pxh(s,0,15,S,N['bk'])
            for row,yo in enumerate([0,4,8,12]):
                xo=4 if row%2==0 else 0
                for vx in range(xo,S,8): pxv(s,vx,yo,4,N['bk'])
                for vx in range(xo,S,8): pxh(s,vx+1,yo,min(6,S-vx-1),N['bl'])
            pxr(s,0,0,S,2,N['gm']);pxh(s,0,0,S,N['gl'])
        elif tt=='grass':
            pxr(s,0,0,S,2,N['gm']);pxh(s,0,0,S,N['gl'])
            for tx in[2,6,10,14]: px(s,tx,2,N['gm'])
        elif tt=='brick':
            s.fill(N['bm']);pxr(s,0,0,S,1,N['bk']);pxr(s,0,0,1,S,N['bk']);pxr(s,S-1,0,1,S,N['bk']);pxr(s,0,S-1,S,1,N['bk'])
            pxh(s,1,7,S-2,N['bk']);pxv(s,4,1,6,N['bk']);pxv(s,11,1,6,N['bk']);pxv(s,8,8,7,N['bk'])
            pxh(s,1,1,S-2,N['bl']);pxv(s,1,1,6,N['bl']);pxh(s,1,8,7,N['bl']);pxh(s,9,8,6,N['bl'])
            pxh(s,1,6,S-2,N['bd']);pxh(s,1,14,S-2,N['bd'])
        elif tt=='question':
            s.fill(N['om']);pxr(s,0,0,S,1,N['bk']);pxr(s,0,0,1,S,N['bk']);pxr(s,S-1,0,1,S,N['bk']);pxr(s,0,S-1,S,1,N['bk'])
            pxh(s,1,1,S-2,N['ol']);pxv(s,1,1,S-2,N['ol']);pxh(s,1,S-2,S-2,N['od']);pxv(s,S-2,1,S-2,N['od'])
            for rx,ry in[(2,2),(S-3,2),(2,S-3),(S-3,S-3)]: px(s,rx,ry,N['bd'])
            pxh(s,5,3,5,N['bk']);px(s,5,4,N['bk']);px(s,10,4,N['bk']);px(s,10,5,N['bk']);px(s,9,6,N['bk'])
            px(s,8,7,N['bk']);px(s,7,8,N['bk']);px(s,7,9,N['bk']);px(s,7,11,N['bk']);px(s,7,12,N['bk'])
        elif tt=='pipe_vertical':
            s.fill(N['gd']);pxr(s,2,0,S-4,S,N['gm']);pxv(s,3,0,S,N['gl']);pxv(s,4,0,S,N['gv'])
            pxr(s,0,0,S,4,N['gd']);pxr(s,1,0,S-2,3,N['gm']);pxh(s,1,0,S-2,N['gl']);pxv(s,1,0,3,N['gl']);pxv(s,3,0,3,N['gv'])
            pxv(s,0,0,S,N['bk']);pxv(s,S-1,0,S,N['bk']);pxh(s,0,0,S,N['bk'])
        elif tt=='pipe_horizontal':
            s.fill(N['gd']);pxr(s,0,2,S,S-4,N['gm']);pxh(s,0,3,S,N['gl']);pxh(s,0,4,S,N['gv'])
            pxr(s,0,0,4,S,N['gd']);pxr(s,0,1,3,S-2,N['gm']);pxv(s,0,1,S-2,N['gl']);pxh(s,0,1,3,N['gl']);pxh(s,0,3,3,N['gv'])
            pxh(s,0,0,S,N['bk']);pxh(s,0,S-1,S,N['bk']);pxv(s,0,0,S,N['bk'])
        elif tt=='coin':
            pxv(s,6,3,10,N['od']);pxv(s,7,2,12,N['om']);pxv(s,8,2,12,N['ol']);pxv(s,9,3,10,N['od'])
            px(s,7,3,N['ol']);px(s,8,3,N['yl'])
        elif tt=='stone':
            s.fill(N['xm']);pxr(s,0,0,S,1,N['xl']);pxr(s,0,0,1,S,N['xl']);pxr(s,S-1,0,1,S,N['xd']);pxr(s,0,S-1,S,1,N['xd'])
            pxh(s,1,7,S-2,N['xd']);pxv(s,7,0,7,N['xd']);pxv(s,3,8,8,N['xd']);pxv(s,11,8,8,N['xd'])
        elif tt=='ice':
            s.fill((160,220,248));pxr(s,0,0,S,1,(200,240,255));pxr(s,0,0,1,S,(200,240,255))
            pxr(s,S-1,0,1,S,(100,180,220));pxr(s,0,S-1,S,1,(100,180,220));pxr(s,3,3,2,2,(240,252,255));px(s,10,5,(240,252,255))
        elif tt=='bridge':
            pxr(s,0,4,S,4,N['bm']);pxh(s,0,4,S,N['bl']);pxh(s,0,7,S,N['bd'])
            pxr(s,0,10,S,4,N['bm']);pxh(s,0,10,S,N['bl']);pxh(s,0,13,S,N['bd'])
            pxv(s,2,0,S,N['bd']);pxv(s,S-3,0,S,N['bd'])
        elif tt=='sand':
            s.fill(N['tn'])
            for sy in range(0,S,3):
                for sx in range(0,S,4): px(s,(sx+sy)%S,sy,N['sd'])
        elif tt=='dirt':
            s.fill(N['bm'])
            for dy in range(0,S,4):
                for dx in range(0,S,5): px(s,(dx+dy*2)%S,dy,N['bd'])
        elif tt=='slope_left':
            for row in range(S): pxh(s,0,row,row+1,N['bm']);px(s,row,row,N['bl'])
        elif tt=='slope_right':
            for row in range(S): pxh(s,S-row-1,row,row+1,N['bm']);px(s,S-1-row,row,N['bl'])
        elif tt=='water': s.fill((0,88,248,80));[px(s,wx,0,(88,168,248,140)) for wx in range(0,S,4)]
        elif tt=='lava':
            s.fill((200,48,0,180));pxh(s,0,0,S,(248,120,0));pxh(s,0,1,S,(248,88,0))
            for lx in[3,9,13]: px(s,lx,2,(248,200,0))
        elif tt=='semisolid':
            pxr(s,0,0,S,3,N['bm']);pxh(s,0,0,S,N['bl']);pxh(s,0,2,S,N['bd'])
            for sy in range(4,S,2):
                for sx in range(0,S,2):
                    if(sx+sy)%4==0: px(s,sx,sy,N['bm'])
        elif tt=='platform':
            s.fill(N['bm']);pxh(s,0,0,S,N['bl']);pxh(s,0,1,S,N['bl']);pxh(s,0,S-1,S,N['bd']);pxv(s,0,0,S,N['bl']);pxv(s,S-1,0,S,N['bd'])
            for yy in range(3,S-1,4):
                for xx in range(2,S-1,4): px(s,xx,yy,N['bd'])
        elif tt=='mushroom_platform':
            s.fill(N['rm']);pxh(s,0,0,S,N['rl']);pxh(s,0,S-1,S,N['rd']);pxr(s,3,3,3,3,N['wh']);pxr(s,10,5,3,3,N['wh'])
        elif tt=='pswitch':
            s.fill(N['um']);pxr(s,0,0,S,1,(88,148,248));pxr(s,0,0,1,S,(88,148,248));pxr(s,S-1,0,1,S,(0,0,120));pxr(s,0,S-1,S,1,(0,0,120))
            pxv(s,5,3,10,N['wh']);pxh(s,6,3,4,N['wh']);pxh(s,6,7,4,N['wh']);pxv(s,10,3,5,N['wh'])
        elif tt in('conveyor_left','conveyor_right'):
            s.fill(N['xm']);pxh(s,0,0,S,N['xl']);pxh(s,0,S-1,S,N['xd'])
            cx=S//2
            if tt=='conveyor_left':
                for i in range(4): px(s,cx-i,7+i,N['yl']);px(s,cx-i,8-i,N['yl'])
            else:
                for i in range(4): px(s,cx+i,7+i,N['yl']);px(s,cx+i,8-i,N['yl'])
        else:
            c=get_theme_color(tt);s.fill(c)
            pxr(s,0,0,S,1,tuple(min(255,x+40) for x in c));pxr(s,0,0,1,S,tuple(min(255,x+40) for x in c))
            pxr(s,S-1,0,1,S,tuple(max(0,x-40) for x in c));pxr(s,0,S-1,S,1,tuple(max(0,x-40) for x in c))
        self.image=s

# ─── SMBX 1.3 BGO RENDERING ─────────────────────────────────────────────────
class BGO(GameObject):
    def __init__(self,x,y,bgo_type,layer=0,event_id=-1,flags=0,z_layer="Default",sx=GRID_SIZE,sy=GRID_SIZE):
        super().__init__(x,y,bgo_type,layer,event_id,flags);self.bgo_type=bgo_type;self.z_layer=z_layer;self.sx=sx;self.sy=sy;self.update_image()
    def update_image(self):
        S=GRID_SIZE;s=pygame.Surface((S,S),pygame.SRCALPHA);bt=self.bgo_type
        if bt=='cloud':
            pygame.draw.ellipse(s,N['wh'],(2,6,12,8));pygame.draw.ellipse(s,N['wh'],(0,8,8,7));pygame.draw.ellipse(s,N['wh'],(8,7,8,8))
            pygame.draw.ellipse(s,(200,228,252),(3,7,10,6));px(s,5,9,N['bk']);px(s,10,9,N['bk'])
        elif bt=='bush':
            pygame.draw.ellipse(s,N['gm'],(1,6,14,10));pygame.draw.ellipse(s,N['gl'],(3,7,10,7))
            px(s,5,8,N['gv']);px(s,9,9,N['gv'])
        elif bt=='bush_3':
            pygame.draw.ellipse(s,N['gm'],(0,4,16,12));pygame.draw.ellipse(s,N['gl'],(2,5,12,9))
        elif bt=='hill':
            for row in range(S):
                w=(row*S)//S;x0=(S-w)//2
                if w>0: pxh(s,x0,row,w,N['gm'])
                if w>2: px(s,x0+w//3,row,N['gl'])
        elif bt=='tree':
            pxr(s,6,10,4,6,N['bm']);pxv(s,6,10,6,N['bd']);pxv(s,9,10,6,N['bl'])
            pygame.draw.circle(s,N['gm'],(8,6),6);pygame.draw.circle(s,N['gl'],(7,5),3)
        elif bt=='fence':
            for fx in[1,5,9,13]: pxr(s,fx,2,2,14,N['bm']);pxv(s,fx,2,14,N['bl'])
            pxh(s,0,5,S,N['bd']);pxh(s,0,11,S,N['bd'])
        elif bt=='castle':
            pxr(s,2,4,12,12,N['xm']);pxr(s,2,4,12,1,N['xl'])
            for cx in[2,6,10]: pxr(s,cx,0,3,4,N['xm']);pxh(s,cx,0,3,N['xl'])
            pxr(s,6,8,4,5,N['bk']);pxh(s,6,8,4,N['xd'])
        elif bt=='waterfall':
            s.fill((0,88,248,60))
            for wy in range(0,S,3): pxv(s,4,wy,2,(88,168,248,100));pxv(s,11,wy,2,(88,168,248,100))
        elif bt=='sign':
            pxr(s,7,8,2,8,N['bd']);pxr(s,2,2,12,7,N['bl']);pxr(s,2,2,12,1,N['bm']);pxr(s,2,8,12,1,N['bd'])
        else:
            c=get_theme_color('bgo_'+bt);pygame.draw.rect(s,c,(2,2,S-4,S-4))
        self.image=s

# ─── SMBX 1.3 NPC RENDERING ─────────────────────────────────────────────────
class NPC(GameObject):
    def __init__(self,x,y,npc_type,layer=0,event_id=-1,flags=0,direction=1,special_data=0,is_not_moving=0,is_tangible=1,event_die=-1,event_talk=-1):
        super().__init__(x,y,npc_type,layer,event_id,flags);self.npc_type=npc_type;self.direction=direction
        self.special_data=special_data;self.is_not_moving=is_not_moving;self.is_tangible=is_tangible
        self.event_die=event_die;self.event_talk=event_talk;self.velocity=pygame.Vector2(direction*(0 if is_not_moving else 1),0)
        self.state='normal';self.frame=0;self.update_image()
    def update_image(self):
        S=GRID_SIZE;s=pygame.Surface((S,S),pygame.SRCALPHA);nt=self.npc_type
        if nt=='goomba':
            pygame.draw.ellipse(s,N['bm'],(1,1,14,10));pygame.draw.ellipse(s,N['bl'],(2,2,12,7))
            pxr(s,4,4,3,3,N['wh']);pxr(s,9,4,3,3,N['wh']);px(s,5,5,N['bk']);px(s,6,5,N['bk']);px(s,10,5,N['bk']);px(s,9,5,N['bk'])
            pxh(s,5,8,6,N['bk']);pxr(s,1,11,5,4,N['bd']);pxr(s,10,11,5,4,N['bd']);pxr(s,5,10,6,2,N['tn'])
        elif nt.startswith('koopa'):
            ir='red' in nt;sc=N['rm'] if ir else N['gm'];sl=N['rl'] if ir else N['gl'];sd=N['rd'] if ir else N['gd']
            pygame.draw.ellipse(s,sc,(2,5,12,10));pygame.draw.ellipse(s,sl,(4,6,8,6));pxh(s,3,14,10,sd)
            pygame.draw.circle(s,N['gl'] if not ir else N['sl'],(8,3),4);pxr(s,6,2,2,2,N['wh']);px(s,7,2,N['bk'])
            pxr(s,2,13,4,2,N['am']);pxr(s,10,13,4,2,N['am'])
        elif nt.startswith('paratroopa'):
            ir='red' in nt;sc=N['rm'] if ir else N['gm'];sl=N['rl'] if ir else N['gl']
            pygame.draw.ellipse(s,sc,(2,5,12,10));pygame.draw.ellipse(s,sl,(4,6,8,6))
            pygame.draw.circle(s,N['gl'] if not ir else N['sl'],(8,3),4);pxr(s,6,2,2,2,N['wh']);px(s,7,2,N['bk'])
            pxr(s,0,2,3,5,N['wh']);pxr(s,13,2,3,5,N['wh'])
        elif nt=='mushroom':
            pygame.draw.ellipse(s,N['rm'],(1,0,14,10));pxr(s,3,2,3,3,N['wh']);pxr(s,10,3,3,2,N['wh'])
            px(s,5,7,N['bk']);px(s,10,7,N['bk']);pxr(s,4,9,8,6,N['tn']);pxv(s,4,9,6,N['sd']);pxv(s,11,9,6,N['sd'])
        elif nt=='1up':
            pygame.draw.ellipse(s,N['gm'],(1,0,14,10));pxr(s,3,2,3,3,N['wh']);pxr(s,10,3,3,2,N['wh'])
            px(s,5,7,N['bk']);px(s,10,7,N['bk']);pxr(s,4,9,8,6,N['tn'])
        elif nt=='flower':
            for ai in range(4):
                a=ai*math.pi/2;cx,cy=int(8+3*math.cos(a)),int(4+3*math.sin(a));pygame.draw.circle(s,N['rm'],(cx,cy),3)
            pygame.draw.circle(s,N['am'],(8,4),2);pygame.draw.circle(s,N['yl'],(8,4),1)
            pxv(s,7,8,6,N['gm']);pxv(s,8,8,6,N['gm']);pxh(s,4,10,3,N['gl']);pxh(s,9,12,3,N['gl'])
        elif nt=='star':
            pts=[];[pts.append((int(8+(7 if i%2==0 else 3)*math.cos(i*math.pi*2/10-math.pi/2)),int(8+(7 if i%2==0 else 3)*math.sin(i*math.pi*2/10-math.pi/2)))) for i in range(10)]
            pygame.draw.polygon(s,N['om'],pts);pygame.draw.polygon(s,N['ol'],pts,1);px(s,6,7,N['bk']);px(s,10,7,N['bk'])
        elif nt=='piranha':
            pygame.draw.ellipse(s,N['rm'],(1,0,14,8));pxr(s,3,2,2,2,N['wh']);pxr(s,9,1,2,2,N['wh'])
            pxh(s,1,7,14,N['bk']);[px(s,tx,6,N['wh']) for tx in[3,5,7,9,11]]
            pxr(s,6,8,4,8,N['gm']);pxv(s,6,8,8,N['gd']);pxv(s,9,8,8,N['gl'])
        elif nt=='piranha_fire':
            pygame.draw.ellipse(s,N['am'],(1,0,14,8));pxr(s,3,2,2,2,N['rm']);pxh(s,1,7,14,N['bk'])
            [px(s,tx,6,N['wh']) for tx in[3,5,7,9,11]];pxr(s,6,8,4,8,N['gm'])
        elif nt=='boo':
            pygame.draw.ellipse(s,N['wh'],(1,1,14,12));pygame.draw.ellipse(s,(240,240,248),(2,2,12,9))
            pxr(s,4,4,3,3,N['bk']);pxr(s,9,4,3,3,N['bk']);pxh(s,5,9,6,N['bk']);px(s,6,10,N['bk']);px(s,9,10,N['bk'])
            pygame.draw.polygon(s,N['wh'],[(4,13),(8,11),(12,13),(10,15),(6,15)])
        elif nt=='thwomp':
            s.fill(N['xm']);pxr(s,0,0,S,1,N['xl']);pxr(s,0,0,1,S,N['xl']);pxr(s,S-1,0,1,S,N['xd']);pxr(s,0,S-1,S,1,N['xd'])
            pxr(s,3,4,4,3,N['wh']);pxr(s,9,4,4,3,N['wh']);pxr(s,4,5,2,2,N['bk']);pxr(s,10,5,2,2,N['bk'])
            pxh(s,3,3,4,N['xd']);pxh(s,9,3,4,N['xd'])
            for tx in[4,6,8,10]: pxr(s,tx,10,2,3,N['wh']);px(s,tx,12,N['xl'])
        elif nt=='bowser':
            pygame.draw.ellipse(s,N['gm'],(2,3,12,12));pygame.draw.ellipse(s,N['bm'],(3,5,10,8))
            pygame.draw.circle(s,N['gl'],(8,2),4);px(s,6,1,N['rm']);px(s,10,1,N['rm'])
            px(s,6,2,N['wh']);px(s,7,2,N['bk']);px(s,9,2,N['wh']);px(s,10,2,N['bk'])
        elif nt=='podoboo':
            pygame.draw.circle(s,N['rm'],(8,8),6);pygame.draw.circle(s,N['am'],(8,7),4);pygame.draw.circle(s,N['yl'],(8,6),2)
            px(s,6,8,N['bk']);px(s,10,8,N['bk'])
        elif nt=='hammer_bro':
            pygame.draw.ellipse(s,N['gm'],(3,0,10,6));pxr(s,5,4,6,4,N['sl']);px(s,6,5,N['bk']);px(s,9,5,N['bk'])
            pxr(s,4,8,8,5,N['gm']);pxh(s,4,8,8,N['gl']);pxr(s,3,13,4,2,N['am']);pxr(s,9,13,4,2,N['am'])
        elif nt=='lakitu':
            pygame.draw.ellipse(s,N['wh'],(0,8,16,8));pygame.draw.ellipse(s,N['gm'],(4,0,8,9))
            pxr(s,5,2,6,5,N['sl']);px(s,6,3,N['bk']);px(s,9,3,N['bk'])
            pxr(s,5,3,2,2,(200,200,248));pxr(s,9,3,2,2,(200,200,248))
        elif nt=='buzzy':
            pygame.draw.ellipse(s,N['ud'],(1,3,14,10));pygame.draw.ellipse(s,N['um'],(3,4,10,7))
            pxr(s,3,7,2,3,N['wh']);px(s,4,8,N['bk']);pxr(s,2,12,4,3,N['sl']);pxr(s,10,12,4,3,N['sl'])
        elif nt=='spiny':
            pygame.draw.ellipse(s,N['rm'],(1,4,14,10))
            for so in[2,5,8,11]: px(s,so,2,N['am']);px(s,so,3,N['am'])
            pxr(s,3,7,2,3,N['wh']);px(s,4,8,N['bk']);pxr(s,2,13,4,2,N['sl']);pxr(s,10,13,4,2,N['sl'])
        elif nt=='cheep':
            pygame.draw.ellipse(s,N['rm'],(2,3,12,10));pygame.draw.ellipse(s,N['rl'],(4,5,8,6))
            pxr(s,4,6,2,2,N['wh']);px(s,5,6,N['bk']);pygame.draw.polygon(s,N['rd'],[(13,8),(15,5),(15,11)]);pxr(s,6,3,3,2,N['rd'])
        elif nt=='blooper':
            pygame.draw.ellipse(s,N['wh'],(2,0,12,12));pxr(s,4,4,3,3,N['bk']);pxr(s,9,4,3,3,N['bk'])
            for tx in[3,6,9,12]: pxv(s,tx,11,4,N['wh'])
        else:
            c=get_theme_color(nt);pygame.draw.rect(s,c,(2,2,S-4,S-4));pygame.draw.circle(s,N['bk'],(S//2,6),1)
        self.image=s
    def update(self,solid_tiles,player,events):
        if self.npc_type not in('lakitu','podoboo','piranha_fire'): self.velocity.y=min(self.velocity.y+GRAVITY,TERMINAL_VELOCITY)
        self.rect.x+=self.velocity.x;self._collide(solid_tiles,'x');self.rect.y+=self.velocity.y;self._collide(solid_tiles,'y')
    def _collide(self,tiles,axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if axis=='x': self.rect.right=t.rect.left if self.velocity.x>0 else t.rect.right;self.velocity.x*=-1
                elif axis=='y': self.rect.bottom=t.rect.top if self.velocity.y>0 else t.rect.bottom;self.velocity.y=0
                if t.tile_type=='lava': self.kill()

# ─── SMBX 1.3 MARIO PLAYER ──────────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__();self.rect=pygame.Rect(x,y,GRID_SIZE,GRID_SIZE);self.direction=1;self.velocity=pygame.Vector2(0,0)
        self.on_ground=False;self.powerup_state=0;self.invincible=0;self.coins=0;self.score=0;self.jump_held=False
        self.variable_jump_timer=0;self.level_start=(x,y);self.update_image()
    def update_image(self):
        S=GRID_SIZE;s=pygame.Surface((S,S),pygame.SRCALPHA)
        # NES Mario pixel art
        pxh(s,3,0,5,N['rm']);pxh(s,2,1,9,N['rm']);pxh(s,2,2,10,N['rm'])
        pxh(s,2,3,3,N['bm']);px(s,5,3,N['sm']);px(s,6,3,N['bm']);px(s,7,3,N['sm'])
        px(s,1,4,N['bm']);px(s,2,4,N['sm']);px(s,3,4,N['bm']);pxh(s,4,4,3,N['sm']);px(s,7,4,N['bk']);px(s,8,4,N['sm'])
        pxh(s,2,5,3,N['sm']);pxh(s,5,5,4,N['sl'])
        pxh(s,3,6,2,N['rm']);pxh(s,5,6,3,N['um']);pxh(s,8,6,2,N['rm'])
        px(s,2,7,N['rm']);pxh(s,3,7,2,N['um']);px(s,5,7,N['rm']);pxh(s,6,7,2,N['um']);px(s,8,7,N['rm']);pxh(s,9,7,2,N['um'])
        pxh(s,2,8,2,N['um']);pxh(s,4,8,5,N['um']);pxh(s,9,8,2,N['um']);px(s,3,8,N['om']);px(s,8,8,N['om'])
        pxh(s,3,9,7,N['um']);pxh(s,3,10,7,N['um'])
        pxh(s,2,11,3,N['bm']);pxh(s,8,11,3,N['bm']);pxh(s,1,12,4,N['bm']);pxh(s,8,12,4,N['bm'])
        pxh(s,1,13,4,N['bd']);pxh(s,8,13,4,N['bd'])
        if self.direction<0: s=pygame.transform.flip(s,True,False)
        self.image=s
    def update(self,solid_tiles,npc_group,events):
        keys=pygame.key.get_pressed();self.velocity.x=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.velocity.x=-MOVE_SPEED;self.direction=-1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.velocity.x=MOVE_SPEED;self.direction=1
        if keys[pygame.K_SPACE]:
            if self.on_ground and not self.jump_held: self.velocity.y=JUMP_STRENGTH;self.on_ground=False;self.jump_held=True;self.variable_jump_timer=8
            elif self.variable_jump_timer>0 and self.velocity.y<0: self.velocity.y-=0.4;self.variable_jump_timer-=1
        else: self.jump_held=False;self.variable_jump_timer=0
        self.velocity.y=min(self.velocity.y+GRAVITY,TERMINAL_VELOCITY)
        self.rect.x+=self.velocity.x;self._collide(solid_tiles,'x')
        self.rect.y+=self.velocity.y;self.on_ground=False;self._collide(solid_tiles,'y')
        for npc in pygame.sprite.spritecollide(self,npc_group,False):
            if not npc.is_tangible: continue
            if self.velocity.y>0 and self.rect.bottom<=npc.rect.centery: npc.kill();self.velocity.y=JUMP_STRENGTH*0.7;self.score+=100
            elif self.invincible<=0:
                if self.powerup_state>0: self.powerup_state=0;self.invincible=120;self.update_image()
                else: self.rect.topleft=self.level_start;self.score=max(0,self.score-50);self.coins=0;self.invincible=60
        if self.invincible>0: self.invincible-=1
    def _collide(self,tiles,axis):
        for t in tiles:
            if self.rect.colliderect(t.rect):
                if t.tile_type=='lava': self.rect.topleft=self.level_start;self.invincible=60;return
                if axis=='x': self.rect.right=t.rect.left if self.velocity.x>0 else t.rect.right;self.velocity.x=0
                elif axis=='y':
                    if self.velocity.y>0: self.rect.bottom=t.rect.top;self.on_ground=True
                    else: self.rect.top=t.rect.bottom
                    self.velocity.y=0
    def draw(self,surf,camera_offset):
        if self.invincible>0 and(self.invincible//5)%2==0: return
        surf.blit(self.image,self.rect.move(camera_offset))

class Camera:
    def __init__(self,w,h): self.camera=pygame.Rect(0,0,w,h);self.width=w;self.height=h;self.zoom=1.0
    def update(self,target):
        x=min(0,max(-(self.width-CANVAS_WIDTH/self.zoom),-target.rect.centerx+(CANVAS_WIDTH//2)/self.zoom))
        y=min(0,max(-(self.height-CANVAS_HEIGHT/self.zoom),-target.rect.centery+(CANVAS_HEIGHT//2)/self.zoom))
        self.camera=pygame.Rect(x,y,self.width,self.height)
    def move(self,dx,dy):
        self.camera.x=max(-(self.width-CANVAS_WIDTH/self.zoom),min(0,self.camera.x+dx/self.zoom))
        self.camera.y=max(-(self.height-CANVAS_HEIGHT/self.zoom),min(0,self.camera.y+dy/self.zoom))

class Layer:
    def __init__(self,name="Default",visible=True,locked=False):
        self.name=name;self.visible=visible;self.locked=locked;self.tiles=pygame.sprite.Group();self.bgos=pygame.sprite.Group();self.npcs=pygame.sprite.Group();self.tile_map={}
    def add_tile(self,t): self.tiles.add(t);self.tile_map[(t.rect.x,t.rect.y)]=t
    def remove_tile(self,t): self.tiles.remove(t);self.tile_map.pop((t.rect.x,t.rect.y),None)

class Section:
    def __init__(self,w=80,h=24):
        self.width=w*GRID_SIZE;self.height=h*GRID_SIZE;self.layers=[Layer("Default"),Layer("Destroyed Blocks"),Layer("Spawned NPCs")]
        self.current_layer_idx=0;self.bg_color=(92,148,252);self.bg_type=0;self.music=1;self.music_file=""
        self.events=[];self.warps=[];self.phys_env_zones=[];self.start_x=32;self.start_y=300;self.locked=False
    def current_layer(self): return self.layers[self.current_layer_idx]
    def get_solid_tiles(self): return[t for l in self.layers if l.visible for t in l.tiles if t.is_solid]

class Level:
    def __init__(self):
        self.sections=[Section()];self.current_section_idx=0;self.name="Untitled";self.author="Unknown";self.description=""
        self.time_limit=400;self.level_id=0;self.stars=0;self.initial_lives=3;self.initial_coins=0;self.max_coins=0
        self.character_starts=[CharacterStart(i) for i in range(5)];self.luna_config={}
    def current_section(self): return self.sections[self.current_section_idx]
    def current_layer(self): return self.current_section().current_layer()

# ─── FILE I/O (compact) ─────────────────────────────────────────────────────
def read_lvl(fn):
    lv=Level()
    try:
        with open(fn,'rb') as f:
            if f.read(4)!=b'LVL\x1a': return lv
            f.read(4);lv.name=f.read(32).decode('utf-8',errors='ignore').strip('\x00');lv.author=f.read(32).decode('utf-8',errors='ignore').strip('\x00')
            lv.time_limit=struct.unpack('<I',f.read(4))[0];lv.stars=struct.unpack('<I',f.read(4))[0];f.read(4);f.read(128-f.tell()%128 or 128)
            ns=struct.unpack('<I',f.read(4))[0];lv.sections=[]
            for _ in range(ns):
                sec=Section();sec.width=struct.unpack('<I',f.read(4))[0];sec.height=struct.unpack('<I',f.read(4))[0]
                r,g,b=struct.unpack('<BBB',f.read(3));f.read(1);sec.bg_color=(r,g,b)
                sec.start_x=struct.unpack('<I',f.read(4))[0];sec.start_y=struct.unpack('<I',f.read(4))[0];sec.music=struct.unpack('<I',f.read(4))[0]
                nb=struct.unpack('<I',f.read(4))[0]
                for __ in range(nb):
                    x,y,tid,li,eid,fl=struct.unpack('<IIIIII',f.read(24))
                    if tid in TILE_ID_TO_NAME:
                        while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                        sec.layers[li].add_tile(Tile(x,y,TILE_ID_TO_NAME[tid],li,eid,fl))
                nbg=struct.unpack('<I',f.read(4))[0]
                for __ in range(nbg):
                    x,y,tid,li,fl=struct.unpack('<IIIII',f.read(20))
                    if tid in BGO_ID_TO_NAME:
                        while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                        sec.layers[li].bgos.add(BGO(x,y,BGO_ID_TO_NAME[tid],li,flags=fl))
                nn=struct.unpack('<I',f.read(4))[0]
                for __ in range(nn):
                    x,y,tid,li,eid,fl,dr,sp=struct.unpack('<IIIIIIII',f.read(32))
                    if tid in NPC_ID_TO_NAME:
                        while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                        sec.layers[li].npcs.add(NPC(x,y,NPC_ID_TO_NAME[tid],li,eid,fl,1 if dr else-1,sp))
                f.read(struct.unpack('<I',f.read(4))[0]*64)
                ne=struct.unpack('<I',f.read(4))[0]
                for __ in range(ne):
                    nl=struct.unpack('<B',f.read(1))[0];nm=f.read(nl).decode('utf-8')
                    trig=struct.unpack('<I',f.read(4))[0];ac=struct.unpack('<I',f.read(4))[0]
                    for ___ in range(ac): f.read(12)
                    sec.events.append(Event(nm,str(trig),[],len(sec.events)))
                lv.sections.append(sec)
    except Exception as e: print("Load error:",e)
    return lv

def write_lvl(fn,lv):
    with open(fn,'wb') as f:
        f.write(b'LVL\x1a');f.write(struct.pack('<I',1));f.write(lv.name.encode('utf-8')[:31].ljust(32,b'\x00'));f.write(lv.author.encode('utf-8')[:31].ljust(32,b'\x00'))
        f.write(struct.pack('<I',lv.time_limit));f.write(struct.pack('<I',lv.stars));f.write(struct.pack('<I',0));f.write(b'\x00'*64);f.write(struct.pack('<I',len(lv.sections)))
        for sec in lv.sections:
            f.write(struct.pack('<II',sec.width,sec.height));f.write(struct.pack('<BBB',*sec.bg_color[:3]));f.write(b'\x00')
            f.write(struct.pack('<III',sec.start_x,sec.start_y,sec.music))
            bl=[(t.rect.x,t.rect.y,TILE_SMBX_IDS.get(t.tile_type,1),li,t.event_id,t.flags) for li,l in enumerate(sec.layers) for t in l.tiles]
            f.write(struct.pack('<I',len(bl)));[f.write(struct.pack('<IIIIII',*b)) for b in bl]
            bg=[(b.rect.x,b.rect.y,BGO_SMBX_IDS.get(b.bgo_type,5),li,b.flags) for li,l in enumerate(sec.layers) for b in l.bgos]
            f.write(struct.pack('<I',len(bg)));[f.write(struct.pack('<IIIII',*b)) for b in bg]
            np=[(n.rect.x,n.rect.y,NPC_SMBX_IDS.get(n.npc_type,1),li,n.event_id,n.flags,1 if n.direction>0 else 0,n.special_data) for li,l in enumerate(sec.layers) for n in l.npcs]
            f.write(struct.pack('<I',len(np)));[f.write(struct.pack('<IIIIIIII',*n)) for n in np]
            f.write(struct.pack('<I',0));f.write(struct.pack('<I',len(sec.events)))
            for ev in sec.events: nb=ev.name.encode('utf-8');f.write(struct.pack('<B',len(nb)));f.write(nb);f.write(struct.pack('<II',0,0))

def read_lvlx(fn):
    lv=Level()
    try:
        tree=ET.parse(fn);root=tree.getroot();head=root.find("head")
        if head is not None:
            t=head.findtext("title");a=head.findtext("author")
            if t: lv.name=t
            if a: lv.author=a
        lv.sections=[]
        for se in root.findall("section"):
            sec=Section()
            def gi(e,a,d=0):
                try: return int(e.get(a,d))
                except: return d
            sec.width=gi(se,"size_right",1280);sec.height=gi(se,"size_bottom",384);sec.music=gi(se,"music_id",1)
            sec.bg_color=(gi(se,"bgcolor_r",92),gi(se,"bgcolor_g",148),gi(se,"bgcolor_b",252))
            for bl in se.findall("block"):
                tid=gi(bl,"id");x=(gi(bl,"x")//GRID_SIZE)*GRID_SIZE;y=(gi(bl,"y")//GRID_SIZE)*GRID_SIZE;li=gi(bl,"layer",0)
                if tid in TILE_ID_TO_NAME:
                    while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                    sec.layers[li].add_tile(Tile(x,y,TILE_ID_TO_NAME[tid],layer=li))
            for bg in se.findall("bgo"):
                tid=gi(bg,"id");x=(gi(bg,"x")//GRID_SIZE)*GRID_SIZE;y=(gi(bg,"y")//GRID_SIZE)*GRID_SIZE;li=gi(bg,"layer",0)
                if tid in BGO_ID_TO_NAME:
                    while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                    sec.layers[li].bgos.add(BGO(x,y,BGO_ID_TO_NAME[tid],layer=li))
            for ne in se.findall("npc"):
                tid=gi(ne,"id");x=(gi(ne,"x")//GRID_SIZE)*GRID_SIZE;y=(gi(ne,"y")//GRID_SIZE)*GRID_SIZE;li=gi(ne,"layer",0);dr=gi(ne,"direction",1)
                if tid in NPC_ID_TO_NAME:
                    while len(sec.layers)<=li: sec.layers.append(Layer(f"Layer {len(sec.layers)+1}"))
                    sec.layers[li].npcs.add(NPC(x,y,NPC_ID_TO_NAME[tid],layer=li,direction=1 if dr>0 else-1))
            lv.sections.append(sec)
        if not lv.sections: lv.sections=[Section()]
    except Exception as e: print("LVLX error:",e)
    return lv

def write_lvlx(fn,lv):
    root=ET.Element("root");root.set("type","LevelFile");root.set("fileformat","LVLX")
    head=ET.SubElement(root,"head");ET.SubElement(head,"title").text=lv.name;ET.SubElement(head,"author").text=lv.author
    t=ET.SubElement(head,"timer");t.set("value",str(lv.time_limit))
    for si,sec in enumerate(lv.sections):
        se=ET.SubElement(root,"section");se.set("id",str(si));se.set("size_right",str(sec.width));se.set("size_bottom",str(sec.height));se.set("music_id",str(sec.music))
        se.set("bgcolor_r",str(sec.bg_color[0]));se.set("bgcolor_g",str(sec.bg_color[1]));se.set("bgcolor_b",str(sec.bg_color[2]))
        for li,layer in enumerate(sec.layers):
            for tile in layer.tiles:
                bl=ET.SubElement(se,"block");bl.set("id",str(TILE_SMBX_IDS.get(tile.tile_type,1)));bl.set("x",str(tile.rect.x));bl.set("y",str(tile.rect.y));bl.set("layer",str(li))
            for bgo in layer.bgos:
                bg=ET.SubElement(se,"bgo");bg.set("id",str(BGO_SMBX_IDS.get(bgo.bgo_type,5)));bg.set("x",str(bgo.rect.x));bg.set("y",str(bgo.rect.y));bg.set("layer",str(li))
            for npc in layer.npcs:
                ne=ET.SubElement(se,"npc");ne.set("id",str(NPC_SMBX_IDS.get(npc.npc_type,1)));ne.set("x",str(npc.rect.x));ne.set("y",str(npc.rect.y));ne.set("layer",str(li));ne.set("direction",str(npc.direction))
    tree=ET.ElementTree(root)
    if hasattr(ET,'indent'): ET.indent(tree,space="  ")
    tree.write(fn,encoding="utf-8",xml_declaration=True)

def read_38a(fn):
    td=tempfile.mkdtemp(prefix="smbx38a_")
    try:
        with zipfile.ZipFile(fn,"r") as zf: zf.extractall(td)
        lp=os.path.join(td,"level.lvl")
        if not os.path.exists(lp):
            for r,_d,files in os.walk(td):
                if"level.lvl"in files: lp=os.path.join(r,"level.lvl");break
        return read_lvl(lp) if os.path.exists(lp) else Level()
    finally: shutil.rmtree(td,ignore_errors=True)
def write_38a(fn,lv):
    td=tempfile.mkdtemp(prefix="smbx38a_")
    try:
        write_lvl(os.path.join(td,"level.lvl"),lv)
        with zipfile.ZipFile(fn,"w",zipfile.ZIP_DEFLATED) as zf:
            for wr,_d,files in os.walk(td):
                for f in files: full=os.path.join(wr,f);zf.write(full,os.path.relpath(full,td))
    finally: shutil.rmtree(td,ignore_errors=True)

def detect_format(fn):
    ext=os.path.splitext(fn)[1].lower()
    if ext==".38a": return"38a"
    if ext==".lvlx": return"lvlx"
    try:
        with open(fn,"rb") as f:
            m=f.read(4)
            if m==b"LVL\x1a": return"lvl"
            f.seek(0)
            if f.read(2)==b"PK": return"38a"
            f.seek(0);c=f.read(256).lstrip()
            if c.startswith(b"<?xml") or c.startswith(b"<"): return"lvlx"
    except OSError: pass
    return"unknown"
def smart_read(fn):
    fmt=detect_format(fn)
    try:
        if fmt=="38a": return read_38a(fn)
        if fmt=="lvlx": return read_lvlx(fn)
        if fmt=="lvl": return read_lvl(fn)
    except Exception as e: print("Load error:",e)
    return read_lvl(fn)
def smart_write(fn,lv):
    ext=os.path.splitext(fn)[1].lower()
    if ext==".lvlx": write_lvlx(fn,lv)
    elif ext==".38a": write_38a(fn,lv)
    else: write_lvl(fn,lv)

# ─── MENU SYSTEM ─────────────────────────────────────────────────────────────
class MenuItem:
    def __init__(self,label,callback=None,shortcut="",checkable=False,checked=False,separator=False):
        self.label=label;self.callback=callback;self.shortcut=shortcut;self.checkable=checkable;self.checked=checked;self.separator=separator;self.enabled=True
class DropMenu:
    IH=16;PAD=4
    def __init__(self,items):
        self.items=items;self.hovered=-1;w=max((FONT_SMALL.size(i.label+("  "+i.shortcut if i.shortcut else""))[0]+24) for i in items if not i.separator)
        self.w=max(120,w);self.h=sum(5 if i.separator else self.IH for i in items)+self.PAD*2
    def draw(self,surf,x,y):
        r=pygame.Rect(x,y,self.w,self.h);pygame.draw.rect(surf,SYS_BTN_FACE,r);draw_edge(surf,r,True);cy=y+self.PAD
        for i,item in enumerate(self.items):
            if item.separator: pygame.draw.line(surf,SYS_BTN_DARK,(x+3,cy+2),(x+self.w-3,cy+2));cy+=5;continue
            ir=pygame.Rect(x+2,cy,self.w-4,self.IH)
            if i==self.hovered and item.enabled: pygame.draw.rect(surf,SYS_HIGHLIGHT,ir)
            col=WHITE if i==self.hovered and item.enabled else(GRAY if not item.enabled else SYS_TEXT)
            if item.checkable: draw_text(surf,"+" if item.checked else" ",(x+6,cy+2),col,FONT_SMALL)
            draw_text(surf,item.label,(x+18,cy+2),col,FONT_SMALL)
            if item.shortcut: sw=FONT_SMALL.size(item.shortcut)[0];draw_text(surf,item.shortcut,(x+self.w-sw-4,cy+2),col,FONT_SMALL)
            cy+=self.IH
    def hit_item(self,pos,ox,oy):
        cy=oy+self.PAD
        for i,item in enumerate(self.items):
            if item.separator: cy+=5;continue
            if pygame.Rect(ox+2,cy,self.w-4,self.IH).collidepoint(pos): return i
            cy+=self.IH
        return-1
    def update_hover(self,pos,ox,oy): self.hovered=self.hit_item(pos,ox,oy)

class MenuBar:
    BAR_H=MENU_HEIGHT
    def __init__(self,md):
        self.menus=[];self.open_idx=-1;x=2
        for label,items in md: w=FONT_MENU.size(label)[0]+12;dm=DropMenu(items);self.menus.append([label,x,w,dm]);x+=w
    def handle_event(self,ev):
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            mx,my=ev.pos
            if my<self.BAR_H:
                for i,(lbl,bx,bw,dm) in enumerate(self.menus):
                    if bx<=mx<bx+bw: self.open_idx=-1 if self.open_idx==i else i;return True
            elif self.open_idx>=0:
                lbl,bx,bw,dm=self.menus[self.open_idx];idx=dm.hit_item(ev.pos,bx,self.BAR_H)
                if idx>=0:
                    item=dm.items[idx]
                    if item.enabled and item.callback: item.callback()
                    if item.checkable: item.checked=not item.checked
                self.open_idx=-1;return True
            else: self.open_idx=-1
        if ev.type==pygame.MOUSEMOTION and self.open_idx>=0:
            lbl,bx,bw,dm=self.menus[self.open_idx];dm.update_hover(ev.pos,bx,self.BAR_H)
            for i,(l2,bx2,bw2,dm2) in enumerate(self.menus):
                if bx2<=ev.pos[0]<bx2+bw2 and ev.pos[1]<self.BAR_H: self.open_idx=i
        if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: self.open_idx=-1
        return False
    def draw(self,surf):
        pygame.draw.rect(surf,SMBX_NAVY,(0,0,WINDOW_WIDTH,self.BAR_H));pygame.draw.line(surf,SMBX_ORANGE,(0,self.BAR_H-1),(WINDOW_WIDTH,self.BAR_H-1))
        for i,(lbl,bx,bw,dm) in enumerate(self.menus):
            r=pygame.Rect(bx,1,bw,self.BAR_H-2)
            if i==self.open_idx: pygame.draw.rect(surf,SMBX_ORANGE,r);draw_text(surf,lbl,(bx+6,2),BLACK,FONT_MENU)
            else: draw_text(surf,lbl,(bx+6,2),WHITE,FONT_MENU)
        if self.open_idx>=0: lbl,bx,bw,dm=self.menus[self.open_idx];dm.draw(surf,bx,self.BAR_H)

class ToolbarButton:
    def __init__(self,rect,ik,cb=None,tip="",toggle=False): self.rect=pygame.Rect(rect);self.icon_key=ik;self.callback=cb;self.tooltip=tip;self.hovered=False;self.pressed=False;self.toggle=toggle;self.active=False
    def handle_event(self,ev):
        if ev.type==pygame.MOUSEMOTION: self.hovered=self.rect.collidepoint(ev.pos)
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if self.rect.collidepoint(ev.pos): self.pressed=True;return True
        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
            if self.pressed and self.rect.collidepoint(ev.pos) and self.callback:
                if self.toggle: self.active=not self.active
                self.callback()
            self.pressed=False
        return False
    def draw(self,surf):
        su=self.pressed or(self.toggle and self.active);bg=SYS_BTN_FACE
        if su: bg=(180,177,160)
        elif self.hovered: bg=(248,246,238)
        pygame.draw.rect(surf,bg,self.rect)
        if su or self.hovered: draw_edge(surf,self.rect,not su)
        fn=ICON_FNS.get(self.icon_key)
        if fn: off=(1,1) if su else(0,0);fn(surf,self.rect.move(off[0],off[1]),SMBX_NAVY if not self.active else SMBX_ORANGE)

class Sidebar:
    def __init__(self):
        self.rect=pygame.Rect(0,CANVAS_Y,SIDEBAR_WIDTH,CANVAS_HEIGHT);self.categories=["Tiles","BGOs","NPCs","Layers"];self.current_category="Tiles"
        self.items={"Tiles":list(TILE_SMBX_IDS.keys()),"BGOs":list(BGO_SMBX_IDS.keys()),"NPCs":list(NPC_SMBX_IDS.keys()),"Layers":[]}
        self.selected_item='ground';self.tab_h=16;self.title_h=16
    def draw(self,surf,level):
        pygame.draw.rect(surf,SYS_BTN_FACE,self.rect);draw_edge(surf,self.rect,False)
        tr=pygame.Rect(self.rect.x+1,self.rect.y+1,self.rect.width-2,self.title_h)
        for i in range(tr.height): t=i/tr.height;c=(int(49*t),int(78+28*t),int(152+45*t));pygame.draw.line(surf,c,(tr.x,tr.y+i),(tr.right,tr.y+i))
        draw_text(surf,"Item Palette",(tr.x+3,tr.y+2),WHITE,FONT_SMALL);pygame.draw.line(surf,SMBX_ORANGE,(tr.x,tr.bottom),(tr.right,tr.bottom))
        ty=self.rect.y+self.title_h+2;tw=self.rect.width//len(self.categories)
        for i,cat in enumerate(self.categories):
            r=pygame.Rect(self.rect.x+i*tw,ty,tw,self.tab_h);sel=(cat==self.current_category)
            if sel: pygame.draw.rect(surf,SYS_WINDOW,r);pygame.draw.line(surf,SMBX_ORANGE,(r.x,r.bottom-1),(r.right,r.bottom-1))
            else: pygame.draw.rect(surf,SYS_BG,r)
            draw_text(surf,cat[:3],r.center,SMBX_NAVY if sel else GRAY,FONT_SMALL,True)
        ct=pygame.Rect(self.rect.x+1,ty+self.tab_h,self.rect.width-2,self.rect.height-self.title_h-self.tab_h-3);pygame.draw.rect(surf,SYS_WINDOW,ct)
        if self.current_category=="Layers": self._draw_layers(surf,ct,level)
        else: self._draw_items(surf,ct)
    def _draw_items(self,surf,area):
        items=self.items[self.current_category];cols=4;cell=min(area.width//cols,28)
        for i,item in enumerate(items):
            ci=i%cols;ri=i//cols;r=pygame.Rect(area.x+3+ci*cell,area.y+3+ri*cell,cell-2,cell-2)
            if r.bottom>area.bottom: break
            if item==self.selected_item: pygame.draw.rect(surf,SMBX_ORANGE,r.inflate(2,2))
            pv=pygame.Surface((cell-2,cell-2),pygame.SRCALPHA)
            if self.current_category=="Tiles": obj=Tile(0,0,item)
            elif self.current_category=="BGOs": obj=BGO(0,0,item)
            else: obj=NPC(0,0,item)
            pv.blit(pygame.transform.scale(obj.image,(cell-2,cell-2)),(0,0));surf.blit(pv,r)
            if item==self.selected_item: pygame.draw.rect(surf,SMBX_ORANGE,r,1)
    def _draw_layers(self,surf,area,level):
        y=area.y+3;sec=level.current_section()
        for i,layer in enumerate(sec.layers):
            r=pygame.Rect(area.x+2,y,area.width-4,14)
            if r.bottom>area.bottom: break
            pygame.draw.rect(surf,SYS_HIGHLIGHT if i==sec.current_layer_idx else SYS_WINDOW,r)
            draw_text(surf,layer.name[:16],(r.x+3,r.y+1),WHITE if i==sec.current_layer_idx else SYS_TEXT,FONT_SMALL)
            pygame.draw.circle(surf,GREEN if layer.visible else RED,(r.right-6,r.centery),3);y+=16
    def handle_click(self,pos,level):
        ty=self.rect.y+self.title_h+2;tw=self.rect.width//len(self.categories)
        for i,cat in enumerate(self.categories):
            if pygame.Rect(self.rect.x+i*tw,ty,tw,self.tab_h).collidepoint(pos): self.current_category=cat;return True
        ct=pygame.Rect(self.rect.x+1,ty+self.tab_h,self.rect.width-2,self.rect.height-self.title_h-self.tab_h-3)
        if self.current_category=="Layers":
            y=ct.y+3;sec=level.current_section()
            for i,layer in enumerate(sec.layers):
                r=pygame.Rect(ct.x+2,y,ct.width-4,14)
                if r.collidepoint(pos):
                    if pos[0]>r.right-12: layer.visible=not layer.visible
                    else: sec.current_layer_idx=i
                    return True
                y+=16
        else:
            items=self.items[self.current_category];cols=4;cell=min(ct.width//cols,28)
            for i,item in enumerate(items):
                if pygame.Rect(ct.x+3+(i%cols)*cell,ct.y+3+(i//cols)*cell,cell-2,cell-2).collidepoint(pos): self.selected_item=item;return True
        return False

# ─── EDITOR ──────────────────────────────────────────────────────────────────
class Editor:
    def __init__(self,level,screen,initial_path=None):
        self.screen=screen;self.level=level;self.camera=Camera(level.current_section().width,level.current_section().height)
        self.playtest_mode=False;self.player=None;self.undo_stack=[];self.redo_stack=[];self.sidebar=Sidebar()
        self.drag_draw=False;self.drag_erase=False;self.current_file=initial_path;self.selection=[];self.clipboard=[]
        self.tool='pencil';self.grid_enabled=True;self.mouse_pos=(0,0);self.tooltip_text="";self.status_msg=""
        self._build_menu();self._build_toolbar()
    def _build_menu(self):
        MI=MenuItem
        fi=[MI("New Level",self.cmd_new,"Ctrl+N"),MI("Open Level...",self.cmd_open,"Ctrl+O"),MI("Save",self.cmd_save,"Ctrl+S"),MI("Save As...",self.cmd_save_as,"Shift+S"),MI("",separator=True),MI("Export JSON",self.cmd_export_json),MI("",separator=True),MI("Exit",self.cmd_exit,"Alt+F4")]
        ei=[MI("Undo",self.undo,"Ctrl+Z"),MI("Redo",self.redo,"Ctrl+Y"),MI("",separator=True),MI("Cut",self.cut_selection,"Ctrl+X"),MI("Copy",self.copy_selection,"Ctrl+C"),MI("Paste",self.paste_clipboard,"Ctrl+V"),MI("Delete",self.delete_selected,"Del"),MI("",separator=True),MI("Select All",self.select_all,"Ctrl+A"),MI("Deselect",self.deselect_all,"Esc")]
        vi=[MI("Zoom In",self.cmd_zoom_in,"Ctrl+="),MI("Zoom Out",self.cmd_zoom_out,"Ctrl+-"),MI("Reset Zoom",self.cmd_zoom_reset,"Ctrl+0"),MI("",separator=True),MI("Toggle Grid",self.cmd_toggle_grid,"G",checkable=True,checked=True),MI("",separator=True),MI("Theme: SMB1",lambda:self.cmd_set_theme('SMB1')),MI("Theme: SMB3",lambda:self.cmd_set_theme('SMB3')),MI("Theme: SMW",lambda:self.cmd_set_theme('SMW'))]
        li=[MI("Level Properties...",self.cmd_properties,"F4"),MI("",separator=True),MI("Layer Manager...",self.cmd_layer_manager),MI("",separator=True),MI("Set Start Pos",self.cmd_set_start),MI("Clear All",self.cmd_clear_all)]
        ti=[MI("Select",self.set_tool_select,"S"),MI("Pencil",self.set_tool_pencil,"P"),MI("Eraser",self.set_tool_erase,"E"),MI("Fill",self.set_tool_fill,"F")]
        te=[MI("Playtest",self.toggle_playtest,"F5"),MI("",separator=True),MI("Reset Player",self.cmd_reset_player)]
        hi=[MI("Controls...",self.cmd_help,"F1"),MI("About...",self.cmd_about)]
        self.menubar=MenuBar([("File",fi),("Edit",ei),("View",vi),("Level",li),("Tools",ti),("Test",te),("Help",hi)])
    def _build_toolbar(self):
        items=[("new",self.cmd_new,"New (Ctrl+N)"),("open",self.cmd_open,"Open (Ctrl+O)"),("save",self.cmd_save,"Save (Ctrl+S)"),None,("undo",self.undo,"Undo (Ctrl+Z)"),("redo",self.redo,"Redo (Ctrl+Y)"),None,("select",self.set_tool_select,"Select [S]"),("pencil",self.set_tool_pencil,"Pencil [P]"),("eraser",self.set_tool_erase,"Eraser [E]"),("fill",self.set_tool_fill,"Fill [F]"),None,("grid",self.cmd_toggle_grid,"Toggle Grid [G]",True),("zoom_in",self.cmd_zoom_in,"Zoom In"),("zoom_out",self.cmd_zoom_out,"Zoom Out"),None,("layer",self.cmd_layer_manager,"Layers"),("props",self.cmd_properties,"Properties [F4]"),None,("play",self.toggle_playtest,"Playtest [F5]",True)]
        self.toolbar_btns=[];x=SIDEBAR_WIDTH+3
        for item in items:
            if item is None: x+=6;continue
            if len(item)==4: ik,cb,tip,tog=item;self.toolbar_btns.append(ToolbarButton((x,MENU_HEIGHT+2,20,20),ik,cb,tip,toggle=tog))
            else: ik,cb,tip=item;self.toolbar_btns.append(ToolbarButton((x,MENU_HEIGHT+2,20,20),ik,cb,tip))
            x+=22
    def cmd_new(self):
        if MessageBox(self.screen,"New Level","Start a new level?",("Yes","No")).run()=="Yes":
            self.level=Level();self.current_file=None;self.camera=Camera(self.level.current_section().width,self.level.current_section().height)
            self.undo_stack.clear();self.redo_stack.clear();self.selection.clear();self.status("New level.")
    def cmd_open(self):
        fn=ask_open_level_path(initial_dir=os.path.dirname(self.current_file) if self.current_file else None)
        if fn and os.path.exists(fn): self.level=smart_read(fn);self.current_file=fn;self.camera=Camera(self.level.current_section().width,self.level.current_section().height);self.status(f"Opened: {os.path.basename(fn)}")
        elif fn: MessageBox(self.screen,"Error",f"File not found:\n{fn}").run()
    def cmd_save(self):
        if not self.current_file: self.cmd_save_as();return
        smart_write(self.current_file,self.level);self.status(f"Saved: {os.path.basename(self.current_file)}")
    def cmd_save_as(self):
        fn=ask_save_level_path(suggested_name=self.current_file or"level.lvl")
        if fn: self.current_file=fn;smart_write(fn,self.level);self.status(f"Saved as: {os.path.basename(fn)}")
    def cmd_export_json(self):
        fn=ask_save_json_path()
        if not fn: return
        sec=self.level.current_section();data={"name":self.level.name,"author":self.level.author,"tiles":[],"bgos":[],"npcs":[]}
        for li,layer in enumerate(sec.layers):
            for t in layer.tiles: data["tiles"].append({"x":t.rect.x,"y":t.rect.y,"type":t.tile_type,"layer":li})
            for b in layer.bgos: data["bgos"].append({"x":b.rect.x,"y":b.rect.y,"type":b.bgo_type,"layer":li})
            for n in layer.npcs: data["npcs"].append({"x":n.rect.x,"y":n.rect.y,"type":n.npc_type,"layer":li})
        with open(fn,'w') as f: json.dump(data,f,indent=2)
        MessageBox(self.screen,"Export","Exported to:\n"+os.path.basename(fn)).run()
    def cmd_exit(self):
        if MessageBox(self.screen,"Exit","Exit AC Holding Mario Fan Builder 0.1?",("Yes","No")).run()=="Yes": pygame.quit();sys.exit()
    def cmd_zoom_in(self): self.camera.zoom=min(ZOOM_MAX,round(self.camera.zoom+ZOOM_STEP,2));self.status(f"Zoom:{int(self.camera.zoom*100)}%")
    def cmd_zoom_out(self): self.camera.zoom=max(ZOOM_MIN,round(self.camera.zoom-ZOOM_STEP,2));self.status(f"Zoom:{int(self.camera.zoom*100)}%")
    def cmd_zoom_reset(self): self.camera.zoom=1.0;self.status("Zoom: 100%")
    def cmd_toggle_grid(self):
        self.grid_enabled=not self.grid_enabled;self.status("Grid: "+("ON" if self.grid_enabled else"OFF"))
        for btn in self.toolbar_btns:
            if btn.icon_key=='grid': btn.active=self.grid_enabled
    def cmd_set_theme(self,theme):
        global current_theme;current_theme=theme
        for l in self.level.current_section().layers:
            for t in l.tiles: t.update_image()
            for b in l.bgos: b.update_image()
            for n in l.npcs: n.update_image()
        self.status(f"Theme: {theme}")
    def cmd_properties(self):
        PropertiesDialog(self.screen,self.level).run();self.camera=Camera(self.level.current_section().width,self.level.current_section().height)
        for l in self.level.current_section().layers:
            for t in l.tiles: t.update_image()
    def cmd_layer_manager(self): LayerDialog(self.screen,self.level.current_section()).run()
    def cmd_set_start(self):
        wx,wy=self.get_mouse_world();gx,gy=self.world_to_grid(wx,wy);self.level.current_section().start_x=gx;self.level.current_section().start_y=gy;self.status(f"Start: {gx},{gy}")
    def cmd_clear_all(self):
        if MessageBox(self.screen,"Clear All","Clear ALL from level? Cannot undo!",("Yes","No")).run()=="Yes":
            for l in self.level.current_section().layers: l.tiles.empty();l.bgos.empty();l.npcs.empty();l.tile_map.clear()
            self.undo_stack.clear();self.redo_stack.clear();self.selection.clear();self.status("Cleared.")
    def cmd_reset_player(self):
        if self.player: sec=self.level.current_section();self.player.rect.topleft=(sec.start_x,sec.start_y);self.player.velocity.update(0,0)
    def cmd_help(self):
        MessageBox(self.screen,"Controls","EDITOR:\n Left Click - Place/Select\n Right Click - Delete\n Arrows - Scroll\nG - Grid  Ctrl+Z/Y - Undo/Redo\n Ctrl+C/V/X - Copy/Paste/Cut\nCtrl+A - Select All  F5 - Playtest\n Ctrl+=/-  Zoom In/Out\n\nPLAYTEST:\n Arrow/WASD - Move  Space - Jump\n Esc - Back to editor").run()
    def cmd_about(self):
        MessageBox(self.screen,"About","AC Holding Mario Fan Builder 0.1\n\n(C) 1985-2026 Nintendo\n(C) 1999-2026 A.C Holdings\n\nMario is owned by (C) Nintendo\n\nCATSAN Engine  Python 3.14").run()
    def set_tool_select(self): self.tool='select';self.status("Tool: Select")
    def set_tool_pencil(self): self.tool='pencil';self.status("Tool: Pencil")
    def set_tool_erase(self): self.tool='erase';self.status("Tool: Eraser")
    def set_tool_fill(self): self.tool='fill';self.status("Tool: Fill")
    def toggle_playtest(self):
        if self.menubar.open_idx>=0: self.menubar.open_idx=-1
        self.playtest_mode=not self.playtest_mode
        if self.playtest_mode:
            sec=self.level.current_section();self.player=Player(sec.start_x,sec.start_y);self.player.level_start=(sec.start_x,sec.start_y)
            self.camera.update(self.player);self.status("PLAYTEST  Esc=exit")
        else: self.player=None;self.status("Editor")
        for btn in self.toolbar_btns:
            if btn.icon_key=='play': btn.active=self.playtest_mode
    def status(self,msg): self.status_msg=msg
    def push_undo(self,a): self.undo_stack.append(a);self.redo_stack.clear()
    def undo(self):
        if not self.undo_stack: self.status("Nothing to undo");return
        a=self.undo_stack.pop();a['undo']();self.redo_stack.append(a);self.status("Undo")
    def redo(self):
        if not self.redo_stack: self.status("Nothing to redo");return
        a=self.redo_stack.pop();a['redo']();self.undo_stack.append(a);self.status("Redo")
    def world_to_grid(self,wx,wy): return(int(wx)//GRID_SIZE)*GRID_SIZE,(int(wy)//GRID_SIZE)*GRID_SIZE
    def get_mouse_world(self): mx,my=self.mouse_pos;return((mx-SIDEBAR_WIDTH)/self.camera.zoom-self.camera.camera.x,(my-CANVAS_Y)/self.camera.zoom-self.camera.camera.y)
    def canvas_to_world(self,sx,sy): return((sx-SIDEBAR_WIDTH)/self.camera.zoom-self.camera.camera.x,(sy-CANVAS_Y)/self.camera.zoom-self.camera.camera.y)
    def place_object(self,gx,gy):
        layer=self.level.current_layer()
        if layer.locked: return
        if self.sidebar.current_category=="NPCs":
            npc=NPC(gx,gy,self.sidebar.selected_item,layer=layer);layer.npcs.add(npc)
            self.push_undo({'undo':lambda l=layer,n=npc:l.npcs.remove(n),'redo':lambda l=layer,n=npc:l.npcs.add(n)})
        elif self.sidebar.current_category=="BGOs":
            bgo=BGO(gx,gy,self.sidebar.selected_item,layer=layer);layer.bgos.add(bgo)
            self.push_undo({'undo':lambda l=layer,b=bgo:l.bgos.remove(b),'redo':lambda l=layer,b=bgo:l.bgos.add(b)})
        else:
            if(gx,gy) in layer.tile_map: return
            tile=Tile(gx,gy,self.sidebar.selected_item,layer=layer);layer.add_tile(tile)
            self.push_undo({'undo':lambda l=layer,t=tile:l.remove_tile(t),'redo':lambda l=layer,t=tile:l.add_tile(t)})
    def erase_object(self,gx,gy,wx=None,wy=None):
        layer=self.level.current_layer()
        if layer.locked: return
        pt=(float(wx),float(wy)) if wx is not None else None
        if pt:
            for grp,name in[(layer.npcs,"NPC"),(layer.bgos,"BGO")]:
                for obj in list(grp):
                    if obj.rect.collidepoint(pt): grp.remove(obj);self.push_undo({'undo':lambda g=grp,o=obj:g.add(o),'redo':lambda g=grp,o=obj:g.remove(o)});self.status(f"Removed {name}");return
            for tk,tile in list(layer.tile_map.items()):
                if tile.rect.collidepoint(pt): layer.remove_tile(tile);self.push_undo({'undo':lambda l=layer,t=tile:l.add_tile(t),'redo':lambda l=layer,k=tk:l.remove_tile(l.tile_map[k]) if k in l.tile_map else None});self.status("Removed tile");return
        else:
            if(gx,gy) in layer.tile_map:
                tile=layer.tile_map[(gx,gy)];layer.remove_tile(tile)
                self.push_undo({'undo':lambda l=layer,t=tile:l.add_tile(t),'redo':lambda l=layer,k=(gx,gy):l.remove_tile(l.tile_map[k]) if k in l.tile_map else None})
    def fill_area(self,sx,sy):
        layer=self.level.current_layer()
        if layer.locked: return
        target=self.sidebar.selected_item;start=(sx,sy)
        old_type=layer.tile_map[start].tile_type if start in layer.tile_map else None
        if old_type==target: return
        queue=deque([start]);visited=set();new_tiles=[]
        while queue:
            x,y=queue.popleft()
            if(x,y) in visited: continue
            visited.add((x,y))
            if old_type is None:
                if(x,y) in layer.tile_map: continue
            else:
                if(x,y) not in layer.tile_map or layer.tile_map[(x,y)].tile_type!=old_type: continue
            if(x,y) in layer.tile_map: layer.remove_tile(layer.tile_map[(x,y)])
            t=Tile(x,y,target,layer=layer);layer.add_tile(t);new_tiles.append(t)
            sec=self.level.current_section()
            for dx,dy in[(GRID_SIZE,0),(-GRID_SIZE,0),(0,GRID_SIZE),(0,-GRID_SIZE)]:
                nx,ny=x+dx,y+dy
                if 0<=nx<sec.width and 0<=ny<sec.height: queue.append((nx,ny))
        if new_tiles: self.push_undo({'undo':lambda l=layer,nt=new_tiles:[l.remove_tile(t) for t in nt],'redo':lambda l=layer,nt=new_tiles:[l.add_tile(t) for t in nt]})
    def handle_select(self,gx,gy,ev):
        layer=self.level.current_layer();obj=None
        if(gx,gy) in layer.tile_map: obj=layer.tile_map[(gx,gy)]
        else:
            for n in layer.npcs:
                if n.rect.x==gx and n.rect.y==gy: obj=n;break
            if not obj:
                for b in layer.bgos:
                    if b.rect.x==gx and b.rect.y==gy: obj=b;break
        if obj:
            mods=pygame.key.get_mods()
            if mods&pygame.KMOD_SHIFT:
                if obj in self.selection: self.selection.remove(obj)
                else: self.selection.append(obj)
            else: self.selection=[obj]
    def copy_selection(self): self.clipboard=[(o.rect.x,o.rect.y,o.obj_type,o.layer) for o in self.selection];self.status(f"Copied {len(self.clipboard)}")
    def cut_selection(self): self.copy_selection();[self._delete_object(o) for o in self.selection];self.selection.clear()
    def paste_clipboard(self):
        if not self.clipboard: return
        wx,wy=self.get_mouse_world();bx,by=self.world_to_grid(wx,wy);ox,oy=self.clipboard[0][0],self.clipboard[0][1]
        for x,y,ot,li in self.clipboard:
            nx,ny=bx+(x-ox),by+(y-oy);sec=self.level.current_section()
            if ot in TILE_SMBX_IDS: sec.layers[li].add_tile(Tile(nx,ny,ot,li))
            elif ot in BGO_SMBX_IDS: sec.layers[li].bgos.add(BGO(nx,ny,ot,li))
            elif ot in NPC_SMBX_IDS: sec.layers[li].npcs.add(NPC(nx,ny,ot,li))
        self.status(f"Pasted {len(self.clipboard)}")
    def select_all(self):
        self.selection.clear();layer=self.level.current_layer()
        self.selection.extend(layer.tiles.sprites());self.selection.extend(layer.bgos.sprites());self.selection.extend(layer.npcs.sprites())
        self.status(f"Selected {len(self.selection)}")
    def deselect_all(self): self.selection.clear()
    def delete_selected(self): [self._delete_object(o) for o in self.selection];self.selection.clear()
    def _delete_object(self,obj):
        li=obj.layer if isinstance(obj.layer,int) else 0;layer=self.level.current_section().layers[li]
        if isinstance(obj,Tile): layer.remove_tile(obj)
        elif isinstance(obj,BGO): layer.bgos.remove(obj)
        elif isinstance(obj,NPC): layer.npcs.remove(obj)
    def handle_event(self,ev):
        if ev.type==pygame.QUIT: return False
        if self.menubar.handle_event(ev): return True
        for btn in self.toolbar_btns: btn.handle_event(ev)
        if ev.type==pygame.MOUSEMOTION:
            self.mouse_pos=ev.pos;self.tooltip_text=""
            for btn in self.toolbar_btns:
                if btn.rect.collidepoint(ev.pos): self.tooltip_text=btn.tooltip
        if ev.type==pygame.KEYDOWN:
            mods=pygame.key.get_mods();ctrl=mods&pygame.KMOD_CTRL
            if ev.key==pygame.K_ESCAPE:
                if self.playtest_mode: self.toggle_playtest()
                elif self.menubar.open_idx>=0: self.menubar.open_idx=-1
                else: self.deselect_all()
            if not self.playtest_mode and not ctrl:
                if ev.key==pygame.K_s: self.set_tool_select()
                if ev.key==pygame.K_p: self.set_tool_pencil()
                if ev.key==pygame.K_e: self.set_tool_erase()
                if ev.key==pygame.K_f: self.set_tool_fill()
                if ev.key==pygame.K_g: self.cmd_toggle_grid()
                if ev.key==pygame.K_LEFT: self.camera.move(GRID_SIZE,0)
                if ev.key==pygame.K_RIGHT: self.camera.move(-GRID_SIZE,0)
                if ev.key==pygame.K_UP: self.camera.move(0,GRID_SIZE)
                if ev.key==pygame.K_DOWN: self.camera.move(0,-GRID_SIZE)
                if ev.key==pygame.K_F4: self.cmd_properties()
                if ev.key==pygame.K_F5: self.toggle_playtest()
                if ev.key==pygame.K_F1: self.cmd_help()
                if ev.key==pygame.K_DELETE: self.delete_selected()
            if ctrl:
                if ev.key==pygame.K_n: self.cmd_new()
                if ev.key==pygame.K_o: self.cmd_open()
                if ev.key==pygame.K_s: self.cmd_save()
                if ev.key==pygame.K_z: self.undo()
                if ev.key==pygame.K_y: self.redo()
                if ev.key==pygame.K_c: self.copy_selection()
                if ev.key==pygame.K_v: self.paste_clipboard()
                if ev.key==pygame.K_x: self.cut_selection()
                if ev.key==pygame.K_a: self.select_all()
                if ev.key in(pygame.K_EQUALS,pygame.K_PLUS): self.cmd_zoom_in()
                if ev.key==pygame.K_MINUS: self.cmd_zoom_out()
                if ev.key==pygame.K_0: self.cmd_zoom_reset()
        if ev.type==pygame.MOUSEBUTTONDOWN:
            if self.sidebar.rect.collidepoint(ev.pos) and ev.button==1: self.sidebar.handle_click(ev.pos,self.level)
            elif ev.pos[1]>CANVAS_Y and ev.pos[0]>SIDEBAR_WIDTH and not self.playtest_mode and self.menubar.open_idx<0:
                wx,wy=self.canvas_to_world(ev.pos[0],ev.pos[1]);gx,gy=self.world_to_grid(wx,wy)
                if ev.button==1:
                    if self.tool=='pencil': self.drag_draw=True;self.place_object(gx,gy)
                    elif self.tool=='erase': self.drag_erase=True;self.erase_object(gx,gy,wx,wy)
                    elif self.tool=='select': self.handle_select(gx,gy,ev)
                    elif self.tool=='fill': self.fill_area(gx,gy)
                elif ev.button in(2,3): self.drag_erase=True;self.erase_object(gx,gy,wx,wy)
                elif ev.button==4: self.cmd_zoom_in()
                elif ev.button==5: self.cmd_zoom_out()
        if ev.type==pygame.MOUSEMOTION and not self.playtest_mode:
            if self.drag_draw or self.drag_erase:
                wx,wy=self.canvas_to_world(ev.pos[0],ev.pos[1]);gx,gy=self.world_to_grid(wx,wy)
                if self.drag_draw: self.place_object(gx,gy)
                elif self.drag_erase: self.erase_object(gx,gy,wx,wy)
        if ev.type==pygame.MOUSEBUTTONUP:
            if ev.button in(1,2,3): self.drag_draw=False;self.drag_erase=False
        return True
    def update(self):
        if self.playtest_mode and self.player:
            sec=self.level.current_section();solid=sec.get_solid_tiles()
            npcs=pygame.sprite.Group()
            for l in sec.layers:
                if l.visible: npcs.add(l.npcs.sprites())
            self.player.update(solid,npcs,sec.events)
            for npc in npcs: npc.update(solid,self.player,sec.events)
            self.camera.update(self.player)
    def draw(self,surf):
        surf.fill(SYS_BG);pygame.draw.rect(surf,SYS_BTN_FACE,(0,MENU_HEIGHT,WINDOW_WIDTH,TOOLBAR_HEIGHT))
        pygame.draw.line(surf,SMBX_ORANGE,(SIDEBAR_WIDTH,MENU_HEIGHT+TOOLBAR_HEIGHT-1),(WINDOW_WIDTH,MENU_HEIGHT+TOOLBAR_HEIGHT-1))
        pygame.draw.line(surf,SYS_BTN_DARK,(SIDEBAR_WIDTH,MENU_HEIGHT),(SIDEBAR_WIDTH,MENU_HEIGHT+TOOLBAR_HEIGHT))
        for btn in self.toolbar_btns: btn.draw(surf)
        self.sidebar.draw(surf,self.level)
        cr=pygame.Rect(SIDEBAR_WIDTH,CANVAS_Y,CANVAS_WIDTH,CANVAS_HEIGHT);surf.set_clip(cr);surf.fill(self.level.current_section().bg_color)
        if self.grid_enabled:
            z=self.camera.zoom;cam=self.camera.camera;sc=int(-cam.x//GRID_SIZE);ec=sc+int(CANVAS_WIDTH/(GRID_SIZE*z))+2
            sr=int(-cam.y//GRID_SIZE);er=sr+int(CANVAS_HEIGHT/(GRID_SIZE*z))+2
            for c in range(sc,ec):
                ppx=int(c*GRID_SIZE*z+cam.x*z)+SIDEBAR_WIDTH
                if cr.left<ppx<cr.right: pygame.draw.line(surf,SMBX_GRID,(ppx,cr.y),(ppx,cr.bottom))
            for r in range(sr,er):
                py=int(r*GRID_SIZE*z+cam.y*z)+CANVAS_Y
                if cr.top<py<cr.bottom: pygame.draw.line(surf,SMBX_GRID,(cr.x,py),(cr.right,py))
        sec=self.level.current_section()
        for layer in sec.layers:
            if not layer.visible: continue
            for bgo in layer.bgos:
                ppx=int((bgo.rect.x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;py=int((bgo.rect.y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
                sz=max(1,int(GRID_SIZE*self.camera.zoom));surf.blit(pygame.transform.scale(bgo.image,(sz,sz)),(ppx,py))
            for tile in layer.tiles:
                ppx=int((tile.rect.x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;py=int((tile.rect.y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
                sz=max(1,int(GRID_SIZE*self.camera.zoom));surf.blit(pygame.transform.scale(tile.image,(sz,sz)),(ppx,py))
            for npc in layer.npcs:
                ppx=int((npc.rect.x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;py=int((npc.rect.y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
                sz=max(1,int(GRID_SIZE*self.camera.zoom));surf.blit(pygame.transform.scale(npc.image,(sz,sz)),(ppx,py))
        if not self.playtest_mode:
            sz=max(1,int(GRID_SIZE*self.camera.zoom))
            for obj in self.selection:
                ppx=int((obj.rect.x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;py=int((obj.rect.y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
                r=pygame.Rect(ppx,py,sz,sz);pygame.draw.rect(surf,SMBX_ORANGE,r,2);pygame.draw.rect(surf,WHITE,r.inflate(2,2),1)
        sx=int((sec.start_x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;sy=int((sec.start_y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
        sz=max(1,int(GRID_SIZE*self.camera.zoom))
        if not self.playtest_mode: pygame.draw.rect(surf,GREEN,(sx,sy,sz,sz),2);draw_text(surf,"S",(sx+2,sy+1),GREEN,FONT_SMALL)
        if self.playtest_mode and self.player:
            ppx=int((self.player.rect.x+self.camera.camera.x)*self.camera.zoom)+SIDEBAR_WIDTH;py=int((self.player.rect.y+self.camera.camera.y)*self.camera.zoom)+CANVAS_Y
            sz=max(1,int(GRID_SIZE*self.camera.zoom))
            if not(self.player.invincible>0 and(self.player.invincible//5)%2==0): surf.blit(pygame.transform.scale(self.player.image,(sz,sz)),(ppx,py))
        surf.set_clip(None);pygame.draw.line(surf,SMBX_ORANGE,(SIDEBAR_WIDTH,CANVAS_Y),(WINDOW_WIDTH,CANVAS_Y));draw_edge(surf,cr,False)
        sb_y=WINDOW_HEIGHT-STATUSBAR_HEIGHT;pygame.draw.rect(surf,SMBX_NAVY,(0,sb_y,WINDOW_WIDTH,STATUSBAR_HEIGHT));pygame.draw.line(surf,SMBX_ORANGE,(0,sb_y),(WINDOW_WIDTH,sb_y))
        def panel(ppx,pw,text,col=SMBX_GOLD): draw_text(surf,text,(ppx+3,sb_y+3),col,FONT_SMALL)
        mode="PLAY" if self.playtest_mode else self.tool.upper();panel(SIDEBAR_WIDTH+2,90,f"{mode}",SMBX_ORANGE if self.playtest_mode else SMBX_GOLD)
        panel(SIDEBAR_WIDTH+82,120,f"Lyr:{self.level.current_layer().name[:8]}")
        wx,wy=self.get_mouse_world();gx,gy=self.world_to_grid(wx,wy);panel(SIDEBAR_WIDTH+202,90,f"X:{int(gx//GRID_SIZE)} Y:{int(gy//GRID_SIZE)}")
        panel(SIDEBAR_WIDTH+292,70,f"Z:{int(self.camera.zoom*100)}%")
        if self.playtest_mode and self.player: panel(SIDEBAR_WIDTH+362,180,f"Coins:{self.player.coins} Score:{self.player.score}")
        elif self.status_msg: panel(SIDEBAR_WIDTH+362,WINDOW_WIDTH-SIDEBAR_WIDTH-365,self.status_msg)
        if self.tooltip_text:
            tx,ty=self.mouse_pos;ty-=18;tw=FONT_SMALL.size(self.tooltip_text)[0]+8;tr=pygame.Rect(tx,max(CANVAS_Y,ty),tw,14)
            pygame.draw.rect(surf,(255,255,210),tr);draw_edge(surf,tr,True);draw_text(surf,self.tooltip_text,(tr.x+4,tr.y+2),BLACK,FONT_SMALL)
        pygame.draw.line(surf,SMBX_ORANGE,(SIDEBAR_WIDTH,MENU_HEIGHT),(SIDEBAR_WIDTH,WINDOW_HEIGHT-STATUSBAR_HEIGHT));self.menubar.draw(surf)

# ─── MAIN MENU ───────────────────────────────────────────────────────────────
def main_menu(screen):
    clock=pygame.time.Clock();hovered=-1
    btns=[pygame.Rect(WINDOW_WIDTH//2-90,200,180,26),pygame.Rect(WINDOW_WIDTH//2-90,232,180,26),pygame.Rect(WINDOW_WIDTH//2-90,264,180,26)]
    labels=["New Level","Open Level","Quit"]
    stars=[(random.randint(0,WINDOW_WIDTH),random.randint(0,WINDOW_HEIGHT),random.random()) for _ in range(40)]
    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: return"QUIT"
            if ev.type==pygame.MOUSEMOTION:
                hovered=-1
                for i,r in enumerate(btns):
                    if r.collidepoint(ev.pos): hovered=i
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                for i,r in enumerate(btns):
                    if r.collidepoint(ev.pos): return["NEW","LOAD","QUIT"][i]
        screen.fill((0,20,60));t=pygame.time.get_ticks()
        for sx,sy,sz in stars: bri=int(128+127*math.sin(t/600+sx));pygame.draw.circle(screen,(bri,bri,bri),(int(sx),int(sy)),max(1,int(sz*2)))
        # NES-style ground with actual tile graphics
        for gx in range(0,WINDOW_WIDTH,GRID_SIZE):
            gt=Tile(0,0,'ground');screen.blit(gt.image,(gx,WINDOW_HEIGHT-40));screen.blit(gt.image,(gx,WINDOW_HEIGHT-24))
            gt2=Tile(0,0,'brick');screen.blit(gt2.image,(gx,WINDOW_HEIGHT-56))
        qt=Tile(0,0,'question');screen.blit(pygame.transform.scale(qt.image,(24,24)),(80,WINDOW_HEIGHT-80))
        screen.blit(pygame.transform.scale(qt.image,(24,24)),(WINDOW_WIDTH-104,WINDOW_HEIGHT-80))
        pt=Tile(0,0,'pipe_vertical')
        for po in range(3): screen.blit(pygame.transform.scale(pt.image,(24,24)),(WINDOW_WIDTH-60,WINDOW_HEIGHT-56-po*24))
        wr=pygame.Rect(WINDOW_WIDTH//2-150,40,300,270);s=pygame.Surface((wr.w,wr.h),pygame.SRCALPHA);s.fill((0,0,0,180));screen.blit(s,wr.topleft);draw_edge(screen,wr,True)
        tb=pygame.Rect(wr.x+2,wr.y+2,wr.w-4,20)
        for i in range(tb.height): t_=i/tb.height;c=(int(49*t_),int(78+28*t_),int(152+45*t_));pygame.draw.line(screen,c,(tb.x,tb.y+i),(tb.right,tb.y+i))
        pygame.draw.line(screen,SMBX_ORANGE,(tb.x,tb.bottom),(tb.right,tb.bottom))
        draw_text(screen,"AC Holding Mario Fan Builder 0.1",(tb.x+4,tb.y+3),WHITE,FONT_SMALL)
        draw_text(screen,"AC Holding",(wr.centerx,wr.y+56),SMBX_ORANGE,FONT_TITLE,True)
        draw_text(screen,"Mario Fan Builder",(wr.centerx,wr.y+78),WHITE,FONT_TITLE,True)
        draw_text(screen,"Version 0.1",(wr.centerx,wr.y+102),SMBX_GOLD,FONT_SMALL,True)
        draw_text(screen,"(C) AC Holdings / Team Flames",(wr.centerx,wr.y+118),GRAY,FONT_SMALL,True)
        draw_text(screen,"CATSAN Engine  |  Python 3.14",(wr.centerx,wr.y+132),(100,100,130),FONT_SMALL,True)
        for i,(r,lbl) in enumerate(zip(btns,labels)):
            sel=(i==hovered)
            if sel:
                for j in range(r.height): t_=j/r.height;c=(int(49*t_),int(78+28*t_),int(152+45*t_));pygame.draw.line(screen,c,(r.x,r.y+j),(r.right,r.y+j))
            else: pygame.draw.rect(screen,(20,20,60),r)
            draw_edge(screen,r,not sel);draw_text(screen,lbl,r.center,SMBX_GOLD if sel else WHITE,FONT,True)
        pygame.display.flip();clock.tick(60)

def main():
    screen=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT));pygame.display.set_caption("AC Holding Mario Fan Builder 0.1");clock=pygame.time.Clock()
    while True:
        result=main_menu(screen)
        if result=="QUIT": pygame.quit();sys.exit()
        level=Level();loaded_from=None
        if result=="LOAD":
            fn=ask_open_level_path()
            if fn and os.path.exists(fn): level=smart_read(fn);loaded_from=fn
        editor=Editor(level,screen,initial_path=loaded_from);running=True
        while running:
            for ev in pygame.event.get():
                res=editor.handle_event(ev)
                if res is False: pygame.quit();sys.exit()
            editor.update();editor.draw(screen);pygame.display.flip();clock.tick(FPS)

if __name__=="__main__": main()
