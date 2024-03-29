############## INITIALIZATION ##############

import pygame as pg
import easing_functions as easing
import draw
import random
import blocks
import colors
import glob
from pypresence import Presence
import numpy as np
import json
import cryptocode
import os
import threading
from tkinter import Tk
from tkinter.filedialog import askopenfilename

tk = Tk()
tk.withdraw()
pg.init()

windowx = 1280
windowy = 720
clock = pg.time.Clock()
fps = 60
dfps = 0.0

# some very important variables
popups = []
loading = 0
loading_total = 0
menu = 'main'

screen = pg.display.set_mode((windowx,windowy), pg.RESIZABLE)
running = True
pg.display.set_caption('pytris')
draw.def_surface = screen
client_id = 1115042623854485534

halfx = windowx//2
halfy = windowy//2

sfx = {'.'.join(i.removeprefix('res\\sfx\\').split('.')[0:-1]): pg.mixer.Sound(i) for i in glob.glob('res\\sfx\\*')}


# app functions

def read_file(path):
    with open(path, encoding='utf-8') as f:
        data = f.read()
        ddata = cryptocode.decrypt(data[8:], data[0:8])
        return json.loads(ddata)
    
def write_file(obj, path): 
    with open(path, 'w', encoding='utf-8') as f:
        key = ''.join(random.choices('1234567890qwertyuiopasdfghjklzxcvbnm', k=8))
        data = key+cryptocode.encrypt(json.dumps(obj), key)
        f.write(data)
        return key
    

def update_presence(line1, line2=None):
    if presence:
        try:
            RPC.update(
                details=line1,
                state=line2
            )
        except:
            pass

def to_time(decimal, rounding=3):
    decimal = float(decimal)
    seconds_str = f'{0 if decimal%60 < 10 else ""}{round(decimal%60, rounding)}'
    return f'{int(decimal/60)}:{seconds_str}{"0"*((3+rounding)-len(seconds_str))}'

def to_name(string):
    string = list(string.replace(' ','-').lower())
    for i in range(len(string)):
        if string[i] not in 'qwertyuiopasdfghjklzxcvbnm1234567890-':
            string[i] = None
    return ''.join([i for i in string if i != None])


def get_class_variables(c):
    return {key:value for key, value in c.__dict__.items() if not key.startswith('__') and not callable(key)}

def continue_game():
    update_presence('Ingame', player.mode_name)
    switch_menu('game')

def restart():
    global player
    board = custom_boards if custom_game else boards
    try:
        player = board[selected_board].get_board()
    except:
        pass
    else:
        switch_menu('game')
        update_presence('Ingame', player.mode_name)

def switch_menu(arg, simple=False):
    global menu, finish_key, scroll, scroll_vel, boards_limit, selected_board, just_entered, update_scroll, custom_game
    if not simple:
        if (menu == 'custom' and arg == 'modes') or (menu == 'modes' and arg == 'custom'):
            selected_board = 0

        if arg == 'modes':
            custom_game = False
        elif arg == 'custom':
            custom_game = True

        for i in buttons:
            for j in buttons[i]:
                j.reload()

    menu = arg

    for i in menu_names_fx:
        i.end = True
    menu_names_fx.append(MenuName(menu_names[arg], arg))

    if not simple:
        if arg == 'pause':
            update_presence('Paused', player.mode_name)
        elif arg != 'game':
            update_presence('Browsing menus')

        finish_key = 0
        scroll = 0
        scroll_vel = 0

    just_entered = 2
    update_scroll = 2

def new_board():
    global custom_boards, selected_board
    custom_boards.append(BoardSettings('New Board'))
    selected_board = len(custom_boards)-1

def del_board():
    global custom_boards, selected_board
    try:
        custom_boards.pop(selected_board)
    except IndexError:
        popup('You don\'t have any boards to delete.', (60,30,30))
    except:
        popup('Unable to delete.', (60,30,30))
    else:
        selected_board -= 1
        if selected_board < 0:
            selected_board = 0

def exit_game():
    global running
    save_modes()
    running = False

def export_file():
    if len(custom_boards) > 0:
        try: os.mkdir('modes/')
        except: pass
        name = to_name(custom_boards[selected_board].name)
        write_file(custom_boards[selected_board].to_dict(), f'modes\\{name}.ptsf')
        os.system(f'explorer {os.getcwd()}\\modes')
        popup(f'Successfully exported {custom_boards[selected_board].name}!', (30,60,30))
    else:
        popup('You don\'t have any boards to export.', (60,30,30))

def import_file():
    global custom_boards, selected_board
    try:
        file = askopenfilename()
        data = read_file(file)
        custom_boards.append(BoardSettings().from_dict(data))
        selected_board = len(custom_boards)-1
        
        popup(f'Successfully imported {custom_boards[selected_board].name}!', (30,60,30))
        save_modes(False)
    except:
        popup('Importing aborted.', (60,30,30))

def move_up():
    global selected_board, custom_boards
    if selected_board > 0:
        object = custom_boards[selected_board]
        custom_boards.pop(selected_board)
        selected_board -= 1
        custom_boards.insert(selected_board, object)
    save_modes(False)

def move_down():
    global selected_board, custom_boards
    if selected_board < len(custom_boards)-1:
        object = custom_boards[selected_board]
        custom_boards.pop(selected_board)
        selected_board += 1
        custom_boards.insert(selected_board, object)
    save_modes(False)


def yes_sure():
    sure_popup.sure()

def no_take_me_back():
    sure_popup.not_sure()

def are_you_sure(obj):
    global sure_popup
    sure_popup = obj
    switch_menu('sure')


def play_sound(key, vol=1.0):
    global volume
    channel = pg.mixer.find_channel(True)
    sfx[key].set_volume(vol*volume/100)
    channel.stop()
    channel.play(sfx[key])

def popup(text, color=(30,30,30)):
    global popups
    popups.append(Popup(text, color))


# app classes

# gui/settings

class Popup:
    def __init__(self, text, color=(30,30,30)):
        self.text = text
        self.size = draw.get_text_size(text)
        self.color = color
        self.light_color = colors.transition(color, (255,255,255), 0.35)
        self.key = 0
        self.deletable = False

    def update(self):
        self.key += 1
        if self.key > 300:
            self.deletable = True

    def draw(self, offset=0):
        ease = easing.QuinticEaseOut(0,30,25).ease(min(min(25,self.key), min(25,300-self.key)))
        rect = pg.Rect(10,offset+10, self.size[0]+20,ease)

        pg.draw.rect(screen, self.color, rect, 0, 7)
        pg.draw.rect(screen, self.light_color, rect, 2, 7)
        try:
            y_size = self.size[1]*ease/30
            draw.text(self.text, rect.center, horizontal_margin='m', vertical_margin='m', rect_size_y=y_size)
        except:
            pass

        return ease


class BoardSettings:
    def __init__(self, name='Classic', x_size=10, y_size=20, def_level=0, goal_type=None, goal=0, minoes=[
            blocks.Mino('o'),
            blocks.Mino('i'),
            blocks.Mino('t'),
            blocks.Mino('l'),
            blocks.Mino('j'),
            blocks.Mino('s'),
            blocks.Mino('z')
        ], level_increase=True, death=True, garbage=False, garbage_min=0, garbage_max=0, garbage_send_limit=None,
        garbage_avoidable=True, init_garbage=[], garbage_goal=False, custom_gravity=None
    ):
        self.name = name
        self.x_size = x_size
        self.y_size = y_size
        self.level = def_level
        self.goal_type = goal_type
        self.goal = goal
        self.minoes = minoes
        self.level_increase = level_increase
        self.death = death
        self.garbage = garbage
        self.garbage_min = garbage_min
        self.garbage_max = garbage_max
        self.garbage_send_limit = garbage_send_limit
        self.garbage_avoidable = garbage_avoidable
        self.init_garbage = init_garbage
        self.garbage_goal = garbage_goal
        self.custom_gravity = custom_gravity

    def get_board(self):
        return Board(self.x_size, self.y_size, self.name, self.level, self.goal_type,
            self.goal, self.minoes, self.level_increase, self.death, self.garbage,
            self.garbage_min, self.garbage_max, self.garbage_send_limit,
            self.garbage_avoidable, self.init_garbage, self.garbage_goal, self.custom_gravity
        )
    
    def to_dict(self):
        vars = get_class_variables(self)
        cur_list = self.minoes
        vars['minoes'] = [i.to_dict() for i in cur_list]
        return vars
    
    def from_dict(self, d):
        for k,v in d.items():
            self.__dict__[k] = v

        self.minoes = [blocks.Mino().from_dict(i) for i in self.minoes]
        return self
    

class SurePopup:
    def __init__(self, lines, func, menu, switch_on_success=False):
        self.lines = lines
        self.func = func
        self.menu = menu
        self.switch_on_success = switch_on_success

    def draw(self):
        ongoing = halfy-50-len(self.lines)*30
        for i in self.lines:
            draw.text(i, (halfx,ongoing), size=24, horizontal_margin='m')
            ongoing += 30

    def sure(self):
        self.func()
        if self.switch_on_success:
            switch_menu(self.menu)

    def not_sure(self):
        switch_menu(self.menu)


class Button:
    def __init__(self, text, offset, size, func, args=[], text_size=21, horigin='m', vorigin='m'):
        self.horigin = horigin
        self.vorigin = vorigin
        self.offset = offset
        self.size = size
        self.args = args
        self.resize()
        self.text = text
        self.func = func
        self.text_size = text_size
        self.hover_key = 0

    def reload(self):
        self.hover_key = 0

    def resize(self):
        if self.vorigin == 't':
            if self.horigin == 'm':
                offset = (self.offset[0]-self.size[0]/2+halfx, self.offset[1])
            elif self.horigin == 'r':
                offset = (self.offset[0]-self.size[0]+windowx, self.offset[1])
            else:
                offset = (self.offset[0], self.offset[1])

        if self.vorigin == 'm':
            if self.horigin == 'm':
                offset = (self.offset[0]-self.size[0]/2+halfx, self.offset[1]-self.size[1]/2+halfy)
            elif self.horigin == 'r':
                offset = (self.offset[0]-self.size[0]+windowx, self.offset[1]-self.size[1]/2+halfy)
            else:
                offset = (self.offset[0], self.offset[1]-self.size[1]/2+halfy)

        if self.vorigin == 'b':
            if self.horigin == 'm':
                offset = (self.offset[0]-self.size[0]/2+halfx, self.offset[1]-self.size[1]+windowy)
            elif self.horigin == 'r':
                offset = (self.offset[0]-self.size[0]+windowx, self.offset[1]-self.size[1]+windowy)
            else:
                offset = (self.offset[0], self.offset[1]-self.size[1]+windowy)

        self.rect = pg.Rect(offset, self.size)

    def update(self):
        hovered = self.rect.collidepoint(mouse_pos)
        max_num = 128 if hovered and mouse_press[0] else 64 if hovered else 0

        self.hover_key += (max_num-self.hover_key)/7

        if hovered:
            if lmb_up:
                self.func(*self.args)

    def draw(self):
        pg.draw.rect(screen, (self.hover_key,self.hover_key,self.hover_key), self.rect, border_radius=14)
        pg.draw.rect(screen, colors.transition((self.hover_key,self.hover_key,self.hover_key), (255,255,255), 0.5+self.hover_key/255/2), self.rect, 2, 14)
        draw.text(self.text, self.rect.center, size=self.text_size, horizontal_margin='m', vertical_margin='m')


class ListLabel:
    def __init__(self, text):
        self.text = text

    def update(self, offset):
        draw.text(self.text, (halfx,offset), size=48, horizontal_margin='m')
        return 80
    

class ListBar:
    def __init__(self, text, var, var_min, var_max, rounding=None):
        self.text = text
        self.size = draw.get_text_size(text, 24)[0]
        self.bar_size = 580-self.size
        self.var = var
        self.var_min = var_min
        self.var_max = var_max
        self.hover_key = 0
        self.var_key = var_min
        self.rounding = rounding

    def update(self, offset):
        vars = globals()
        var = vars[self.var]
        percent = (self.var_key-self.var_min)/(self.var_max-self.var_min)

        bar_offset = halfx-280+self.size
        bar_rect = pg.Rect(bar_offset, offset-2, 50+self.bar_size, 28)
        hovered = bar_rect.collidepoint(mouse_pos)
        max_num = 128 if hovered and mouse_press[0] else 64 if hovered else 0

        self.hover_key += (max_num-self.hover_key)/5
        self.var_key += (var-self.var_key)/5

        if hovered and mouse_press[0]:
            v_percent = (mouse_pos[0]-bar_offset-25)/self.bar_size
            v_var = round(v_percent*(self.var_max-self.var_min), self.rounding)+self.var_min
            v_var = min(v_var, self.var_max)
            v_var = max(v_var, self.var_min)
            var = v_var
            vars[self.var] = var

        draw.text(self.text, (halfx-300, offset), size=24)

        pg.draw.rect(screen, (0,0,0), bar_rect, 0, 14)
        pg.draw.rect(screen, colors.transition((self.hover_key,self.hover_key,self.hover_key), (255,255,255), 0.5+self.hover_key/255/2), bar_rect, 2, 14)

        rect = pg.Rect(bar_offset+percent*self.bar_size, offset-2, 50, 28)
        pg.draw.rect(screen, (self.hover_key,self.hover_key,self.hover_key), rect, 0, 14)
        pg.draw.rect(screen, colors.transition((self.hover_key,self.hover_key,self.hover_key), (255,255,255), 0.5+self.hover_key/255/2), rect, 2, 14)
        draw.text(str(var), rect.center, size=16, horizontal_margin='m', vertical_margin='m')
        
        return 35
    

class ListSeparator:
    def __init__(self, size):
        self.size = size

    def update(self, *args):
        return self.size
        


# effects

class EndCircle:
    def __init__(self, offset):
        self.key = random.random()*3.14
        self.size = random.randint(75,125)
        self.speed = random.randint(-20,20)/1000
        self.offset = offset+random.randint(-15,15)

    def update(self):
        self.key += self.speed

    def draw(self):
        sin = np.sin(self.key)
        circle_pos = (self.offset+halfx+sin*20, 150+np.cos(self.key)*20)
        size = self.size+sin*10
        pg.draw.circle(screen, (0,0,0), circle_pos, size)


class MenuName:
    def __init__(self, text, cur_menu):
        self.text = text
        self.menu = cur_menu
        self.start_key = 100
        self.end_key = 0
        self.end = False
        self.deletable = False

    def update(self):
        if self.start_key > 0:
            self.start_key -= 1

        if self.end:
            self.end_key += 1
        
        if self.end_key >= 50:
            self.deletable = True

    def draw(self):
        ease = easing.QuinticEaseOut(0,255,100).ease(100-self.start_key)
        opacity = min(255-self.end_key*5, ease)//8
        size = 200+self.end_key

        draw.text(self.text, (windowx+275-ease, -60+menu_names_offsets[self.menu]), size=size, opacity=opacity, horizontal_margin='r')


class ActionFX:
    def __init__(self, text, color=(255,255,255), small=False):
        self.text = text
        self.color = color
        self.small = small
        self.text_size = 21 if small else 36
        self.size = draw.get_text_size(text, self.text_size)

        self.alpha_key = 100
        self.size_key = 100
        
        self.deletable = False
    
    def update(self):
        if self.size_key > 0:
            self.size_key -= 1
        self.alpha_key -= 1
        if self.alpha_key <= 0:
            self.deletable = True

    def draw(self, topleft, *args):
        size_ease = easing.ExponentialEaseOut(0,self.size[0],100).ease(100-self.size_key)
        size2_ease = easing.QuinticEaseOut(self.size[1]+1-0.5*int(self.small),self.size[1],50).ease(50-self.size_key)
        alpha_ease = easing.QuinticEaseOut(0,255,100).ease(self.alpha_key)
        
        draw.text(
            self.text, (topleft[0]-5, topleft[1]+100+int(self.small)*30-size2_ease/2), self.color, self.text_size,
            horizontal_margin='r', rect_size_x=size_ease, rect_size_y=size2_ease, opacity=alpha_ease
        )

class HardDropFX:
    def __init__(self, width, x,y, length):
        self.width = width
        self.x_pos = x+1
        self.y_pos = y+1
        self.length = length
        self.key = 10

        self.deletable = False

    def update(self):
        self.key -= 1
        if self.key <= 0:
            self.deletable = True

    def draw(self, topleft, cell_size):
        surf = pg.Surface((self.width*cell_size*(0.5+self.key/20), self.length*cell_size))
        surf.fill((255,255,255))
        surf.set_alpha(int(self.key/10*85))
        screen.blit(surf, (topleft[0]+self.x_pos*cell_size-(self.width*cell_size*self.key/40), topleft[1]+self.y_pos*cell_size))

class LineClearFX:
    def __init__(self, pos):
        self.pos = pos
        self.key = 10

        self.deletable = False

    def update(self):
        self.key -= 1
        if self.key <= 0:
            self.deletable = True

    def draw(self, topleft, cell_size):
        surf = pg.Surface((cell_size*player.x_size, cell_size*(self.key/10)))
        surf.fill((255,255,255))
        surf.set_alpha(int(self.key/10*255))
        screen.blit(surf, (topleft[0], topleft[1]+(self.pos+0.5)*cell_size-(cell_size*self.key/20)))

class ScoreFX:
    def __init__(self, x, y, value, color=(255,255,255), size_add=0):
        self.value = str(value)
        self.color = color
        self.x = x
        self.y = y

        self.size = 18+size_add
        self.alpha = 160
        self.color_key = 0
        self.rotation = 0
        self.rotation_dir = random.randint(-20,20)/35
        self.x_vel = random.randint(-20,20)/10
        self.y_vel = -random.randint(2,5)

        self.deletable = False

    def update(self):
        self.alpha -= 3
        self.rotation += self.rotation_dir
        self.x += self.x_vel
        self.y += self.y_vel
        self.y_vel += 0.2
        
        if self.color_key < 50:
            self.color_key += 1
        if self.alpha <= 0:
            self.deletable = True

    def draw(self, *args):
        draw.text(self.value, (self.x,self.y),
            colors.transition((255,255,255), self.color, self.color_key/50),
            self.size, horizontal_margin='m', vertical_margin='m', rotation=self.rotation, opacity=self.alpha
        )

class TimerFX:
    def __init__(self, text, color=(255,255,255)):
        self.text = text
        self.key = 255
        self.color = color

        self.deletable = False

    def update(self):
        self.key -= 3
        if self.key <= 0:
            self.deletable = True

    def draw(self, topleft, cell_size):
        alpha_ease = easing.QuinticEaseOut(0,1,255).ease(self.key)
        size_ease = easing.QuinticEaseIn(0,1,255).ease(self.key)
        alpha2_ease = easing.QuarticEaseOut(0,1,100).ease(min(100, 255-self.key))
        size = 100+size_ease*70

        draw.text(self.text,
            (topleft[0]+player.x_size/2*cell_size, topleft[1]+player.y_size/2*cell_size), self.color,
            int(size), opacity=min(int(alpha2_ease*255), int(alpha_ease*255)), horizontal_margin='m', vertical_margin='m'
        )
        draw.text(self.text, 
            (topleft[0]+player.x_size/2*cell_size, topleft[1]+player.y_size/2*cell_size), self.color,
            int(size+(255-self.key)/4), opacity=min(int(alpha2_ease*255), self.key), horizontal_margin='m', vertical_margin='m'
        )

class ModeFX:
    def __init__(self, text):
        self.text = text
        self.key = 255

        self.deletable = False

    def update(self):
        self.key -= 2
        if self.key <= 0:
            self.deletable = True

    def draw(self, topleft, cell_size):
        alpha_ease = easing.QuinticEaseOut(0,255,100).ease(min(100,self.key))
        alpha2_ease = easing.QuarticEaseOut(0,255,100).ease(min(100, 255-self.key))
        size = min(int(alpha2_ease), int(alpha_ease))

        draw.text(self.text,
            (topleft[0]+player.x_size/2*cell_size-4+self.key/255*16, topleft[1]+player.y_size/2*cell_size+90), (255,255,255),
            int(size/10), opacity=255, horizontal_margin='m', vertical_margin='m'
        )
        draw.text(self.text,
            (topleft[0]+player.x_size/2*cell_size-8+self.key/255*32, topleft[1]+player.y_size/2*cell_size+90), (255,255,255),
            int(50-size/20), opacity=size//10, horizontal_margin='m', vertical_margin='m'
        )

class ExWarningFX:
    def __init__(self):
        self.key = 0
        self.deletable = False
    
    def update(self):
        self.key += 1
        if self.key >= 30:
            self.deletable = True

    def draw(self, topleft, cell_size):
        rect = pg.Rect(
            (topleft[0]-self.key,topleft[1]-self.key),
            (player.x_size*cell_size+self.key*2, player.y_size*cell_size+self.key*2)
        )
        pg.draw.rect(screen, (255,50,50), rect, int((30-self.key)/1.6)+1)


# game logic

class Block:
    def __init__(self, pos, letter):
        self.pos = list(pos)
        self.letter = letter
        self.color = blocks.mino_colors[letter]
        self.appear_key = 15
        self.v_offset = 0

    def update(self):
        if self.appear_key > 0:
            self.appear_key -= 1
        if round(self.v_offset,2) != 0.0:
            self.v_offset /= 1.2
        elif self.v_offset != 0:
            self.v_offset = 0

class FallingMino:
    def __init__(self, mino, width):
        self.pos = [int(width/2)-1, -2]
        self.mino = mino
        self.color = mino.color
        self.blocks = mino.pos
        self.rotation = 0
        self.update_width()

    def update_width(self):
        self.width = []
        for i in self.blocks:
            if i[0] not in self.width:
                self.width.append(i[0])
        self.width.sort()

class Board:
    def __init__(
            self, x_size, y_size, mode_name, level, goal_type, goal,
            minoes, level_increase, death, garbage, garbage_min,
            garbage_max, garbage_send_limit, garbage_avoidable,
            init_garbage, garbage_goal, custom_gravity
        ):
        self.stats = {       
            'Time spent': '',
            'Lines cleared': 0,
            'Garbage lines cleared': 0,
            'Garbage lines received': 0,
            'Lines sent': 0,
            'Pieces placed': 0,
            'Pieces per second': 0,
            'Singles': 0,
            'Doubles': 0,
            'Triples': 0,
            'Tetrises': 0,
            'Perfect clears': 0,
            'T-Spins': 0,
            'Mini T-Spins': 0,
        }
        if level_increase:
            self.stats['Level'] = 1
        if not death:
            self.stats['Times died'] = 0
        if custom_gravity != None:
            if custom_gravity != 0:
                self.stats['Custom gravity'] = f'{round(1/custom_gravity, 4)}G ({custom_gravity} frames)'
            else:
                self.stats['Custom gravity'] = f'∞G (0 frames)'
        if not garbage:
            self.stats.pop('Garbage lines received')
            self.stats.pop('Garbage lines cleared')
            self.stats.pop('Lines sent')

        self.x_size = x_size
        self.y_size = y_size
        self.blocks = []
        self.cell_size = board_size
        self.custom_gravity = custom_gravity
        self.mode_name = mode_name
        self.offset = [0,0]

        self.goal = goal
        self.goal_type = goal_type

        self.score = 0
        self.vis_score = 0
        self.level = level
        self.level_increase = level_increase
        self.lines_left = 10
        self.frames = 0
        self.drop_frames = 0
        self.epld = 30
        self.taps_left = 15
        self.btb = -1
        self.lowest = -2
        self.lines = 0
        self.combo = -1

        self.garbage_enabled = garbage
        self.garbage = 0
        self.garbage_key = 0.0
        self.garbage_min = garbage_min
        self.garbage_max = garbage_max
        self.garbage_send_limit = garbage_send_limit
        self.garbage_avoidable = garbage_avoidable
        self.garbage_goal = garbage_goal
        self.lines_sent = 0
        self.targets = []
        for i in init_garbage:
            self.garbage = i
            self.add_garbage()

        self.death = death
        self.death_key = 0
        self.dead = False
        self.won = False
        self.win_key = 0
        self.playing = False
        self.timer = 4
        self.timer_frames = 20
        self.shake = 0
        self.forfeit_timer = 0
        self.reset_timer = 0
        self.just_reset = False
        self.forfeited = False
        self.warning_key = 0
        self.warning = False
        self.ex_warning = False
        self.ex_warning_fxs = []
        self.ex_warning_timeout = 0
        self.ex_warning_sound_timeout = 0

        self.held = None
        self.just_held = False
        self.falling_mino = None
        self.allow_drop = True

        self.bag = list(minoes)
        self.queue = []
        self.minoes = minoes
        self.fill_queue()
        self.board_topleft = (0,0)

        self.effects = []
        self.add_fx(ModeFX(mode_name))

        self.pieces = []

    # a shortcut for adding an effect on the board
    def add_fx(self, fx):
        self.effects.append(fx)

    # adds score and creates an effect
    def add_score(self, x,y, score, color=(255,255,255), size=0):
        self.score += score
        self.add_fx(ScoreFX(x,y, score, color, size))

    # handles back-to-back
    def add_btb(self, x,y, action_score):
        self.btb += 1
        if self.btb > 0:
            play_sound('b2b',0.8)
            self.add_score(x, y, action_score//2, (255,255,0), 24)

    # resets back-to-back
    def reset_btb(self):
        if self.btb > 0:
            play_sound('b2b_lost',0.65)
        self.btb = -1

    # checks if current piece has been t-spun
    def is_tspin(self):
        if self.falling_mino == None:
            return False, False
        if self.falling_mino.mino.letter != 't':
            return False, False
        
        return True, False

    # checks if any of the blocks in the blocks list collide with anything on the board
    def collision(self, blocks):
        for block in blocks:
            if block[0] < 0 or block[0] > self.x_size-1 or block[1] > self.y_size-1:
                return True
            for i in self.blocks:
                if block == i.pos:
                    return True
        return False
    
    # recalculates whether the board should light up red
    def recalculate_warning(self):
        max_height = self.y_size
        for i in self.blocks:
            if i.pos[1] < max_height:
                max_height = i.pos[1]
        max_height -= self.garbage

        if max_height < 3:
            self.warning = True
            self.ex_warning = max_height < 1
        else:
            self.warning = False
            self.ex_warning = False


    # fills the queue
    def fill_queue(self):
        while len(self.queue) < 6:
            index = random.randint(0, len(self.bag)-1)
            self.queue.append(self.bag[index])
            self.bag.pop(index)

            if len(self.bag) <= 0:
                self.bag = list(self.minoes)

    # writes True to self.allow_drop if the tetromino is allowed to move down 1 row
    def calculate_drop(self):
        self.allow_drop = not self.collision([
            [
                i[0]+self.falling_mino.pos[0],
                i[1]+self.falling_mino.pos[1]+1
            ] for i in self.falling_mino.blocks
        ])

    # sends garbage
    def send_garbage(self, lines):
        if self.garbage_enabled:
            if self.garbage > 0:
                self.garbage -= lines
                if self.garbage < 0:
                    lines += self.garbage
                    self.garbage = 0
            
            for i in self.targets:
                i.send_garbage(lines)

            self.lines_sent += lines
            self.stats['Lines sent'] += lines
            self.recalculate_warning()

    # receives garbage
    def recv_garbage(self, lines):
        if self.garbage_enabled and lines > 0:
            garbage_lines = []
            init_garbage = int(self.garbage)
            for i in self.blocks:
                if i.letter == 'garbage' and i.pos[1] not in garbage_lines:
                    garbage_lines.append(i.pos[1])

            if self.garbage_send_limit != None:
                self.garbage += min(self.garbage_send_limit-len(garbage_lines), lines)
                self.garbage = max(0, self.garbage)
                if self.garbage_send_limit > 0 and self.garbage > self.garbage_send_limit:
                    self.garbage = self.garbage_send_limit
            else:
                self.garbage += lines

            self.stats['Garbage lines received'] += abs(init_garbage-self.garbage)

            if init_garbage != self.garbage:
                self.shake += 3+int(abs(init_garbage-self.garbage)/2)
            self.recalculate_warning()

    # adds garbage to board
    def add_garbage(self):
        if self.garbage_enabled and self.garbage > 0:
            for i in self.blocks:
                i.pos[1] -= self.garbage
                i.v_offset = -self.garbage

            hole_pos = random.randint(0,self.x_size-1)
            for i in range(self.garbage):
                for j in range(self.x_size):
                    if j == hole_pos: continue
                    self.blocks.append(Block(
                        (j, self.y_size-1-i),
                        'garbage'
                    ))

            self.shake = 5+self.garbage
            self.garbage = 0

    # checks for line clears
    def line_clear_check(self):
        cleared_lines = []
        garbage_cleared_lines = []
        lines = {}

        # getting which lines are cleared
        for i in self.blocks:
            if i.letter == 'garbage' and i.pos[1] not in garbage_cleared_lines:
                garbage_cleared_lines.append(i.pos[1])
            if i.pos[1] not in lines:
                lines[i.pos[1]] = 0
            lines[i.pos[1]] += 1
            
        for i in lines:
            if lines[i] == self.x_size:
                cleared_lines.append(i)
            elif i in garbage_cleared_lines:
                garbage_cleared_lines.remove(i)

        # deleting lines
        self.blocks = [i for i in self.blocks if i.pos[1] not in cleared_lines]
        cleared_lines.sort()

        # moving lines down
        for i in cleared_lines:
            for j in self.blocks:
                if j.pos[1] < i:
                    j.pos[1] += 1
                    j.v_offset += 1
            self.add_fx(LineClearFX(i))

        # adding score
        tspin, mini_tspin = self.is_tspin()
        if tspin:
            if mini_tspin: self.stats['Mini T-Spins'] += 1
            else: self.stats['T-Spins'] += 1

            self.add_fx(ActionFX(f'{"MINI " if mini_tspin else ""}T-SPIN', (200,100,200), small=True))

        if not self.garbage_goal:
            self.lines += len(cleared_lines)
        else:
            self.lines += len(garbage_cleared_lines)

        self.stats['Lines cleared'] += len(cleared_lines)
        if self.garbage_enabled:
            self.stats['Garbage lines cleared'] += len(garbage_cleared_lines)

        btb_added = False
        if len(cleared_lines) != 0:
            self.combo += 1
            if self.combo > 0:
                play_sound(f'combo{min(4,self.combo)}', 0.85)
            play_sound(f'lines{len(cleared_lines)}')
            self.add_fx(ActionFX(line_clear_titles[len(cleared_lines)-1]))

            if tspin and not mini_tspin:
                garbage = len(cleared_lines)*2
            else:
                garbage = garbage_line_clear[len(cleared_lines)-1]

            if len(self.blocks) == 0: garbage += 10
            if self.btb > 0: garbage += 1

            self.send_garbage(garbage)
            self.stats[line_clear_stat_keys[len(cleared_lines)-1]] += 1

            if self.level_increase:
                self.lines_left -= len(cleared_lines)
                if self.lines_left <= 0:
                    self.lines_left += 10
                    if self.level < 14:
                        self.level += 1
                        self.stats['Level'] += 1
                    
            avg = sum(cleared_lines)/len(cleared_lines)
            points = line_clear_pts[len(cleared_lines)-1]*(self.level+1)

            center_x = self.board_topleft[0]+self.x_size/2*self.cell_size
            center_y = self.board_topleft[1]+avg*self.cell_size

            self.add_score(center_x, center_y, points, (255,255,255), 8+len(cleared_lines)*6)

            if len(cleared_lines) >= 4:
                btb_added = True
                self.add_btb(center_x, center_y, points)

            if len(self.blocks) == 0:
                btb_added = True
                score = pc_pts[len(cleared_lines)-1+int(self.btb > 0)]*(self.level+1)
                self.add_score(center_x, center_y, score, (255,255,255), 36)
                self.add_btb(center_x, center_y, score)
                play_sound('pc', 0.85)
                self.stats['Perfect clears'] += 1

        else:
            self.combo = -1

        if not btb_added and (
            len(cleared_lines) > 0 or\
            len(self.blocks) == 0
        ):
            self.reset_btb()

        self.recalculate_warning()
        try:
            self.recv_garbage(max(0, random.randint(self.garbage_min,self.garbage_max)))
        except:
            pass

        if not self.garbage_avoidable or len(cleared_lines) == 0:
            self.add_garbage()

    # replaces current tetromino with the next one from the queue
    def next(self, check=True):
        if check:
            self.line_clear_check()
        self.falling_mino = FallingMino(self.queue[0], self.x_size)
        self.lowest = self.falling_mino.pos[1]
        self.calculate_drop()
        self.drop()
        self.queue.pop(0)
        self.fill_queue()

    # hold a piece or replace current piece with the held one
    def hold(self):
        if self.just_held:
            return
        self.just_held = True

        if self.held == None:
            self.held = self.falling_mino.mino
            self.next(False)
        else:
            self.held, self.falling_mino = self.falling_mino.mino, FallingMino(self.held, self.x_size)
            self.lowest = self.falling_mino.pos[1]
            self.calculate_drop()
            self.drop()
        play_sound('hold', 0.7)
            

    # stops the current tetromino and places it on the board
    def stop(self):
        for i in self.falling_mino.blocks:
            self.blocks.append(Block((
                i[0]+self.falling_mino.pos[0],
                i[1]+self.falling_mino.pos[1]
            ), self.falling_mino.mino.letter))

        self.just_held = False
        self.next()
        if len(self.pieces) != 0:
            self.pieces.append(self.frames-sum(self.pieces))
        else:
            self.pieces.append(self.frames)
        self.stats['Pieces placed'] += 1

        if self.collision([[
            i[0]+self.falling_mino.pos[0],
            i[1]+self.falling_mino.pos[1]]
        for i in self.falling_mino.blocks]):
            if self.death:
                self.dead = True
                self.add_fx(TimerFX('LOSE', (255,40,40)))
                play_sound('fail')
            else:
                self.blocks = []
                self.garbage = 0
                self.stats['Times died'] += 1
                self.recalculate_warning()

            self.shake = 10
            play_sound('glass')

    # sonic drops current tetromino
    def sonic_drop(self):
        # dropping piece
        initial_pos = int(self.falling_mino.pos[1])
        dropped = 0
        while self.allow_drop:
            self.drop()
            self.calculate_drop()
            dropped += 1

        play_sound('harddrop')

        # calculating width
        self.add_fx(HardDropFX(len(self.falling_mino.width), self.falling_mino.pos[0]+self.falling_mino.width[0],initial_pos, dropped))
        self.add_score(
            self.board_topleft[0]+self.falling_mino.pos[0]*self.cell_size,
            self.board_topleft[1]+self.falling_mino.pos[1]*self.cell_size,
        dropped, self.falling_mino.color)

    # hard drops current tetromino
    def hard_drop(self):
        # dropping piece
        initial_pos = int(self.falling_mino.pos[1])
        dropped = 0
        while self.allow_drop:
            self.drop()
            self.calculate_drop()
            dropped += 1

        play_sound('harddrop')

        # calculating width
        self.add_fx(HardDropFX(len(self.falling_mino.width), self.falling_mino.pos[0]+self.falling_mino.width[0],initial_pos, dropped))
        self.add_score(
            self.board_topleft[0]+self.falling_mino.pos[0]*self.cell_size,
            self.board_topleft[1]+self.falling_mino.pos[1]*self.cell_size,
        dropped*2, self.falling_mino.color)
        self.stop()
    
    # drops current tetromino 1 row if possible
    def drop(self, soft=False):
        if self.allow_drop:
            self.falling_mino.pos[1] += 1
            self.epld = 30

            if self.lowest < self.falling_mino.pos[1]:
                self.lowest = self.falling_mino.pos[1]
                self.taps_left = 15

            self.calculate_drop()

            if soft:
                play_sound('softdrop', 0.3)
                self.add_score(
                    self.board_topleft[0]+self.falling_mino.pos[0]*self.cell_size,
                    self.board_topleft[1]+self.falling_mino.pos[1]*self.cell_size,
                1, self.falling_mino.color)

    # moves current tetromino left if possible
    def left(self):
        if not self.collision([
            [
                i[0]+self.falling_mino.pos[0]-1,
                i[1]+self.falling_mino.pos[1]
            ] for i in self.falling_mino.blocks
        ]):
            self.falling_mino.pos[0] -= 1
            self.epld = 30
            if not self.allow_drop:
                play_sound('move', 0.3)
                self.taps_left -= 1

    # moves current tetromino right if possible
    def right(self):
        if not self.collision([
            [
                i[0]+self.falling_mino.pos[0]+1,
                i[1]+self.falling_mino.pos[1]
            ] for i in self.falling_mino.blocks
        ]):
            self.falling_mino.pos[0] += 1
            self.epld = 30
            if not self.allow_drop:
                play_sound('move', 0.3)
                self.taps_left -= 1

    # rotates clockwise
    def rotate(self, counterclockwise=False):
        if not counterclockwise:
            new_rotation = self.falling_mino.rotation+1 if self.falling_mino.rotation+1 <= 3 else 0
        else:
            new_rotation = self.falling_mino.rotation-1 if self.falling_mino.rotation-1 >= 0 else 3
        new_positions = blocks.positions[self.falling_mino.mino.letter][new_rotation]

        index = 0
        for i in blocks.rotations_indexes:
            if i == [self.falling_mino.rotation,new_rotation]:
                rotation_index = index
            index += 1

        for i in blocks.rotations[self.falling_mino.mino.letter][rotation_index]:
            new_blocks = [[
                j[0]+self.falling_mino.pos[0]+i[0],
                j[1]+self.falling_mino.pos[1]+i[1]
            ] for j in new_positions]

            if not self.collision(new_blocks):
                play_sound('rotate', 0.3)
                self.falling_mino.blocks = new_positions
                self.falling_mino.rotation = new_rotation
                self.falling_mino.pos[0] += i[0]
                self.falling_mino.pos[1] += i[1]
                self.falling_mino.update_width()
                self.epld = 30
                if not self.allow_drop:
                    self.taps_left -= 1
                break


    def update(self, keys):
        if not self.dead and self.playing:
            if self.falling_mino == None:
                self.next()

            # placing piece
            self.calculate_drop()

            if not self.allow_drop:
                self.epld -= 1
                if self.epld <= 0 or self.taps_left <= 0:
                    self.epld = 30
                    self.stop()

            # dropping piece
            if self.allow_drop:
                self.drop_frames += 1
            elif self.drop_frames != 0:
                self.drop_frames = 0 

            gravity = (drop_timers[self.level] if self.custom_gravity == None else self.custom_gravity)
            try: gravity_key = (keys['soft']+1)%int(gravity/sdf)
            except: gravity_key = 0
            if gravity_key == 0 and keys['soft'] != 0:
                self.drop(True)
                self.calculate_drop()
            while self.drop_frames >= gravity and self.allow_drop:
                self.drop_frames -= gravity
                self.drop()
                self.calculate_drop()

            # moving left
            if (\
                (keys['left']-das >= 0 and (keys['left']-das) % arr == 0)\
                or keys['left'] == 1)\
                and (keys['left'] < keys['right'] if keys['right'] != 0 else True):
                    self.left()

            # moving right
            if (\
                (keys['right']-das >= 0 and (keys['right']-das) % arr == 0)\
                or keys['right'] == 1)\
                and (keys['right'] < keys['left'] if keys['left'] != 0 else True):
                    self.right()

            # hard dropping
            if keys['hard'] == 1:
                self.hard_drop()

            # sonic dropping
            if keys['sonic'] == 1:
                self.sonic_drop()

            # rotating clockwise
            if keys['rotate_c'] == 1:
                self.rotate()

            # hard dropping
            if keys['rotate_cc'] == 1:
                self.rotate(True)

            # hard dropping
            if keys['hold'] == 1:
                self.hold()
                
            self.frames += 1

        # stats
        self.stats['Time spent'] = f'{to_time(self.frames/60)} ({self.frames} frames)'
        if len(self.pieces) != 0:
            self.stats['Pieces per second'] = round(sum(self.pieces)/len(self.pieces)/60, 2)
        else:
            self.stats['Pieces per second'] = 0.0

        # game ending
        end = False

        if self.goal_type == 'time' and self.frames/60 >= self.goal and self.playing:
            self.frames = self.goal*60
            end = True
        if self.goal_type == 'lines' and self.lines >= self.goal and self.playing:
            end = True

        if end:
            self.won = True
            self.add_fx(TimerFX('FINISH', (255,255,70)))
            play_sound('finish')
            self.playing = False
            self.shake = 7

        if self.dead:
            self.death_key += 1
            self.cell_size -= self.death_key/700
            if self.forfeited:
                self.offset[1] += self.death_key/1.7
                self.cell_size -= 0.2

        if self.won:
            self.win_key += 1

        # timer
        if self.timer > 0:
            self.timer_frames -= 1
            if self.timer_frames <= 0:
                self.timer -= 1
                self.timer_frames = 60
                
                if self.timer > 0:
                    self.add_fx(TimerFX(str(self.timer)))
                    play_sound(f'timer{self.timer}')
                else:
                    self.add_fx(TimerFX('GO'))
                    play_sound('timergo')
                    self.playing = True

        # pause, exit and reset
        if keys['forfeit'] > 0 and self.forfeit_timer < 200:
            self.forfeit_timer += 1
        if keys['reset'] > 0 and not self.just_reset and not keys['forfeit'] and self.reset_timer < 100:
            self.reset_timer += 1

        if keys['forfeit'] == 0 and self.forfeit_timer > 0:
            if self.forfeit_timer > 60:
                self.forfeited = True
                self.dead = True
                self.shake = 7
                play_sound('fail')
            else:
                switch_menu('pause')
            self.forfeit_timer = 0

        if keys['reset'] == 0 and self.reset_timer > 0:
            if self.reset_timer > 30:
                restart()
            self.reset_timer = 0

        # shake
        if self.shake > 0:
            self.shake -= 1


    def draw(self):
        # updating
        if self.falling_mino == None and self.playing:
            self.next()

        corner_rounding = int(self.cell_size/4)
            
        board_topleft = (
            halfx-self.x_size/2*self.cell_size+random.randint(-self.shake,self.shake)+self.offset[0],
            halfy-self.y_size/2*self.cell_size+random.randint(-self.shake,self.shake)+self.offset[1]
        )
        self.board_topleft = board_topleft
        ongoingx = board_topleft[0]
        ongoingy = board_topleft[1]

        # warning fx
        if self.playing and not self.dead:
            to_delete = []
            for i in self.ex_warning_fxs:
                i.draw(self.board_topleft, self.cell_size)
                i.update()
                if i.deletable:
                    to_delete.append(i)
            for i in to_delete:
                self.ex_warning_fxs.remove(i)

            if self.ex_warning:
                self.ex_warning_timeout -= 1
                self.ex_warning_sound_timeout -= 1
                if self.ex_warning_timeout <= 0:
                    self.ex_warning_timeout = 20
                    self.ex_warning_fxs.append(ExWarningFX())
                if self.ex_warning_sound_timeout <= 0:
                    self.ex_warning_sound_timeout = 75
                    play_sound('warning')
            else:
                self.ex_warning_timeout = 0
                self.ex_warning_sound_timeout = 0

        # grid
        self.warning_key = self.warning_key+(int(self.warning)-self.warning_key)/20
        color = colors.transition((grid_brightness,grid_brightness,grid_brightness), (255,0,0), self.warning_key)

        pg.draw.rect(screen, (self.warning_key*60,0,0), pg.Rect(board_topleft, (self.x_size*self.cell_size, self.y_size*self.cell_size)))
        for y in range(self.y_size):
            for x in range(self.x_size):
                pg.draw.rect(screen, color, (ongoingx, ongoingy, self.cell_size+1,self.cell_size+1), 1)

                ongoingx += self.cell_size
            ongoingy += self.cell_size
            ongoingx = board_topleft[0]

        # blocks
        index = 0
        for i in self.blocks:
            i.update() # this func is here because yep
            rect = pg.Rect(
                i.pos[0]*self.cell_size+board_topleft[0],
                (i.pos[1]-i.v_offset)*self.cell_size+board_topleft[1],
                self.cell_size, self.cell_size
            )
            pg.draw.rect(screen, i.color, rect, border_radius=corner_rounding)
            if i.appear_key > 1:
                key = i.appear_key/15
                pg.draw.rect(screen, 
                    colors.transition(i.color, (255,255,255), key),
                    rect, border_radius=corner_rounding
                )
            index += 1

        if not self.dead and self.playing:
            # falling tetromino
            color = self.falling_mino.color if self.allow_drop else colors.transition(
                (0,0,0), self.falling_mino.color, self.epld/60+0.5
            )
            for i in self.falling_mino.blocks:
                pg.draw.rect(screen, color, (
                    (self.falling_mino.pos[0]+i[0])*self.cell_size+board_topleft[0],
                    (self.falling_mino.pos[1]+i[1])*self.cell_size+board_topleft[1],
                    self.cell_size, self.cell_size
                ), border_radius=corner_rounding)
            
            # ghost piece
            ghost_offset = 0
            ghost_can_move = not self.collision([[
                    i[0]+self.falling_mino.pos[0],
                    i[1]+self.falling_mino.pos[1]+1
                ] for i in self.falling_mino.blocks])
            while ghost_can_move:
                ghost_offset += 1
                ghost_can_move = not self.collision([[
                        i[0]+self.falling_mino.pos[0],
                        i[1]+self.falling_mino.pos[1]+ghost_offset+1
                    ] for i in self.falling_mino.blocks])
                    
            if ghost_offset != 0:
                for i in self.falling_mino.blocks:
                    pg.draw.rect(screen, self.falling_mino.color, (
                        (self.falling_mino.pos[0]+i[0])*self.cell_size+board_topleft[0],
                        (self.falling_mino.pos[1]+i[1]+ghost_offset)*self.cell_size+board_topleft[1],
                        self.cell_size, self.cell_size
                    ), 3, corner_rounding)
                
            # next tetromino
            for i in self.queue[0].pos:
                pg.draw.rect(screen, (128,128,128), (
                    (i[0]+int(self.x_size/2)-1)*self.cell_size+board_topleft[0],
                    (i[1]-2)*self.cell_size+board_topleft[1],
                    self.cell_size, self.cell_size
                ), 3, corner_rounding)

            # ep lock down indicator
            if not self.allow_drop:
                rect = pg.Rect(
                    board_topleft[0]+self.x_size*self.cell_size,
                    board_topleft[1]+self.y_size*self.cell_size-30,
                40,30)
                bar_rect = pg.Rect(
                    board_topleft[0]+self.x_size*self.cell_size,
                    board_topleft[1]+self.y_size*self.cell_size-30,
                self.epld/3*4,30)

                pg.draw.rect(screen, (180,180,180), rect, border_top_right_radius=7, border_bottom_right_radius=7)
                pg.draw.rect(screen, (255,255,255), bar_rect, border_top_right_radius=7, border_bottom_right_radius=7)
                draw.text(str(self.taps_left), rect.center, (0,0,0), horizontal_margin='m', vertical_margin='m')


        # next queue
        ongoing = 5
        for i in self.queue:
            height = []
            for j in i.pos:
                if j[1] not in height:
                    height.append(j[1])
                height.sort()

                pg.draw.rect(screen, i.color, (
                    board_topleft[0]+self.x_size*self.cell_size+30+j[0]*self.cell_size//2,
                    board_topleft[1]+(j[1]-height[0])*self.cell_size//2+ongoing,
                    self.cell_size//2,self.cell_size//2
                ))
            ongoing += len(height)*self.cell_size//2+20

        # hold piece
        if self.held != None:
            for i in self.held.pos:
                pg.draw.rect(screen, (128,128,128) if self.just_held else self.held.color, (
                    board_topleft[0]-60+i[0]*15,
                    board_topleft[1]+i[1]*15+5,
                    15,15
                ))


        # scoring
        if self.score > round(self.vis_score,2):
            offset = min(6, (self.score-self.vis_score)/40)
            rect_y = draw.get_text_size(str(int(self.vis_score)), 28)[1]+offset
            self.vis_score += (self.score-self.vis_score)/10
        else:
            offset = 0
            rect_y = None

        draw.text(str(round(self.vis_score)), (
            board_topleft[0]-10, board_topleft[1]+self.y_size*self.cell_size-90-offset/2
        ), size=28, horizontal_margin='r', rect_size_y=rect_y)


        # timer
        if self.goal_type == 'time':
            string = to_time(self.goal-self.frames/60)
        else:
            string = to_time(self.frames/60)

        draw.text(string, (
            board_topleft[0]-10, board_topleft[1]+self.y_size*self.cell_size-43
        ), size=21, horizontal_margin='r')

        draw.text(f'{self.frames}F', (
            board_topleft[0]-10, board_topleft[1]+self.y_size*self.cell_size-16
        ), size=16, horizontal_margin='r')


        # lines
        offset = 39*int(self.allow_drop or self.dead)

        if self.goal_type == 'lines':
            string = f'{self.lines}/{self.goal}'
        else:
            string = f'{self.lines}L'

        draw.text(string, (
            board_topleft[0]+self.x_size*self.cell_size+10, board_topleft[1]+self.y_size*self.cell_size-60+offset
        ), size=21)


        # garbage
        if self.garbage_enabled:
            size = draw.text(f'{self.lines_sent}L→', (
                board_topleft[0]+self.x_size*self.cell_size+10, board_topleft[1]+self.y_size*self.cell_size-130+offset
            ), size=21)[0]

            self.garbage_key = self.garbage_key+(self.garbage-self.garbage_key)/7

            if self.garbage_key > 0:
                pg.draw.rect(screen, (255,255,255),
                    (board_topleft[0]-10, board_topleft[1]+(self.y_size-self.garbage_key)*self.cell_size,
                    10,self.garbage_key*self.cell_size), border_top_left_radius=7
                )


        # level
        size = draw.text(f'Lv{self.level+1}', (
            board_topleft[0]+self.x_size*self.cell_size+10, board_topleft[1]+self.y_size*self.cell_size-90+offset
        ), size=21)[0]

        if self.level_increase:
            draw.text(f'{self.lines_left}', (
                board_topleft[0]+self.x_size*self.cell_size+20+size, board_topleft[1]+self.y_size*self.cell_size-90+offset
            ), size=21, opacity=128)

        
        # btb
        if self.btb > 0:
            draw.text(f'B2B x{self.btb}', (
                board_topleft[0]-10, board_topleft[1]+self.y_size*self.cell_size-120
            ), (255,255,128), horizontal_margin='r')
        
        # combo
        if self.combo > 0:
            draw.text(f'COMBO {self.combo}', (
                board_topleft[0]-10, board_topleft[1]+self.y_size*self.cell_size-160
            ), (255,255,255), 21, horizontal_margin='r')


        # effects
        to_remove = []
        for i in self.effects:
            i.draw(board_topleft, self.cell_size)
            i.update()
            if i.deletable:
                to_remove.append(i)

        for i in to_remove:
            self.effects.remove(i)


        # pause and reset
        if self.forfeit_timer > 0:
            ease = easing.SineEaseOut(0,1,200).ease(self.forfeit_timer)
            pos_ease = easing.ExponentialEaseOut(0,70,100).ease(min(100,self.forfeit_timer))
            rect = pg.Rect(3,windowy-pos_ease, windowx-6,100)
            bar_rect = pg.Rect(3,windowy-pos_ease, ease*(windowx-6),100)
            f_key = 0 if self.forfeit_timer < 60 else max(0, 90-self.forfeit_timer)

            pg.draw.rect(screen, (50,15,15), rect, 0, 14)
            pg.draw.line(screen, (100,25,25), (windowx/2.2,windowy-pos_ease+5), (windowx/2.2,windowy), 5)
            pg.draw.rect(screen, (110+f_key*3,30+f_key,30+f_key), bar_rect, 0, 14)
            pg.draw.rect(screen, (170,60,60), rect, 5, 14)

            if self.forfeit_timer < 60:
                draw.text('PAUSE', (bar_rect.right-20, windowy+37-pos_ease), size=40, vertical_margin='m', horizontal_margin='r')
            else:
                draw.text(
                    'FORFEIT', (bar_rect.right-20+random.randint(-1,1), windowy+37-pos_ease+random.randint(-1,1)),
                    size=40+int(f_key/3), vertical_margin='m', horizontal_margin='r'
                )

        if self.reset_timer > 0:
            ease = easing.SineEaseOut(0,1,100).ease(self.reset_timer)
            pos_ease = easing.ExponentialEaseOut(0,70,50).ease(min(50,self.reset_timer))
            rect = pg.Rect(3,windowy-pos_ease, windowx-6,100)
            bar_rect = pg.Rect(3,windowy-pos_ease, ease*(windowx-6),100)
            f_key = 0 if self.reset_timer < 30 else max(0, 45-self.reset_timer)

            pg.draw.rect(screen, (50,50,15), rect, 0, 14)
            pg.draw.line(screen, (100,100,25), (windowx/2.2,windowy-pos_ease+5), (windowx/2.2,windowy), 5)
            pg.draw.rect(screen, (110+f_key*3,110+f_key*3,30+f_key), bar_rect, 0, 14)
            pg.draw.rect(screen, (170,170,60), rect, 5, 14)

            if self.reset_timer < 30:
                draw.text('RESTART', (bar_rect.right-20, windowy+37-pos_ease), size=40, vertical_margin='m', horizontal_margin='r')
            else:
                draw.text(
                    'RESTART', (bar_rect.right-20+random.randint(-1,1), windowy+37-pos_ease+random.randint(-1,1)),
                    size=40+int(f_key/3), vertical_margin='m', horizontal_margin='r'
                )

# save functions
    
def load_modes(show_popup=True):
    global custom_boards, selected_board

    selected_board = 0
    custom_boards = []
    try:
        data = read_file('save/modes.ptsf')
    except:
        data = {'modes': []}
        if not os.path.exists('save/'):
            os.mkdir('save/')
        write_file({'modes': []}, 'save/modes.ptsf')
    for i in data['modes']:
        custom_boards.append(BoardSettings().from_dict(i))

    if show_popup:
        popup(f'Loaded {len(custom_boards)} scenarios', (30,60,30))

def save_modes(show_popup=True):
    global loading, loading_total, menu
    modes = {'modes': [i.to_dict() for i in custom_boards]}
    write_file(modes, 'save/modes.ptsf')
    if show_popup:
        popup(f'Saved {len(custom_boards)} scenarios', (30,60,30))


def load_settings():
    data = read_file('save/settings.ptsf')
    vars = globals()
    for i in data:
        vars[i] = data[i]

def save_settings():
    vars = globals()
    data = {i:vars[i] for i in vars if i in settings_vars}
    write_file(data, 'save/settings.ptsf')


# app variables

settings_vars = [
    'arr',
    'das',
    'sdf',
    'volume',
    'bg_dim',
    'bg_speed'
]

m123 = [
    blocks.Mino('i3'),
    blocks.Mino('i2'),
    blocks.Mino('l3'),
    blocks.Mino('o1')
]
boards = [
    BoardSettings('Freeroam'),
    BoardSettings('Zen', level_increase=False, death=False),
    BoardSettings('Sprint 40L', goal_type='lines', goal=40),
    BoardSettings('Sprint 20L', goal_type='lines', goal=20),
    BoardSettings('Sprint 10L', goal_type='lines', goal=10),
    BoardSettings('Marathon 100L', goal_type='lines', goal=100),
    BoardSettings('Marathon 150L', goal_type='lines', goal=150),
    BoardSettings('TETR.IO Blitz', goal_type='time', goal=120),
    BoardSettings('TETR.IO Blitz 4-Wide',4, goal_type='time', goal=120),
    BoardSettings('TETR.IO Blitz Dig',goal_type='time', goal=120, garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=10, garbage_avoidable=False, init_garbage=[1 for i in range(10)], garbage_goal=True),
    BoardSettings('Freeroam M123', minoes=m123),
    BoardSettings('Zen M123', minoes=m123, level_increase=False, death=False),
    BoardSettings('Sprint M123 40L', minoes=m123, goal_type='lines', goal=40),
    BoardSettings('Sprint M123 4-Wide 40L', 4, minoes=m123, goal_type='lines', goal=40),
    BoardSettings('TETR.IO Blitz M123', minoes=m123, goal_type='time', goal=120),
    BoardSettings('TETR.IO Blitz M123 4-Wide', 4, minoes=m123, goal_type='time', goal=120),
    BoardSettings('Freeroam 4-Wide', 4),
    BoardSettings('Sprint 4-Wide 40L', 4, goal_type='lines', goal=40),
    BoardSettings('Dig 20L', goal_type='lines', goal=20, garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=10, garbage_avoidable=False, init_garbage=[1 for i in range(10)], garbage_goal=True),
    BoardSettings('Dig5 20L', goal_type='lines', goal=20, garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=5, garbage_avoidable=False, init_garbage=[1 for i in range(5)], garbage_goal=True),
    BoardSettings('Dig 40L', goal_type='lines', goal=40, garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=10, garbage_avoidable=False, init_garbage=[1 for i in range(10)], garbage_goal=True),
    BoardSettings('Dig5 40L', goal_type='lines', goal=40, garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=5, garbage_avoidable=False, init_garbage=[1 for i in range(5)], garbage_goal=True),
    BoardSettings('Freeroam Dig', garbage=True, garbage_min=1,garbage_max=1, garbage_send_limit=10, garbage_avoidable=False, init_garbage=[1 for i in range(10)]),
    BoardSettings('Big 40L', 5,10,goal_type='lines', goal=40),
    BoardSettings('Big 20L', 5,10,goal_type='lines', goal=20),
]
selected_board = 0
keybinds = {
    'pause': [pg.K_ESCAPE, pg.K_F1],
    'hold': [pg.K_LSHIFT,pg.K_RSHIFT,pg.K_c],
    'rotate_cc': [pg.K_LCTRL,pg.K_RCTRL,pg.K_z],
    'rotate_c': [pg.K_UP, pg.K_x],
    'left': [pg.K_LEFT],
    'right': [pg.K_RIGHT],
    'soft': [pg.K_DOWN],
    'hard': [pg.K_SPACE],
    'sonic': [],
    'forfeit': [pg.K_ESCAPE],
    'reset': [pg.K_r],
}
presses = {i: 0 for i in keybinds}
drop_timers = [ # precalculated values
    60.0,
    47.58,
    37.068,
    28.364,
    21.312,
    15.72,
    11.381,
    8.084,
    5.633,
    3.849,
    2.579,
    1.693,
    1.089,
    0.686,
    0.424,
    0.256
]
line_clear_pts = [
    100,
    300,
    500,
    800,
    1500,
]
pc_pts = [
    800,
    1200,
    1800,
    2000,
    3200    
]
garbage_line_clear = [
    0,
    1,
    2,
    4
]
line_clear_titles = [
    'SINGLE',
    'DOUBLE',
    'TRIPLE',
    'TETRIS'
]
line_clear_stat_keys = [
    'Singles',
    'Doubles',
    'Triples',
    'Tetrises'
]

end_screen_fx = []
menu_names_fx = [MenuName('pytris','main')]
arr = 2
das = 8
sdf = 20
bg_dim = 0.7
bg_speed = 1.0
volume = 100
board_size = 30
grid_brightness = 128
presence = True
update_scroll = False
finish_key = 0
debug_overlay = False
just_entered = True
custom_game = False
scroll = 0
scroll_vel = 0
scroll_limit = 0
update_scroll = True
overlay_elements = {
    "FPS": "dfps",
    "Menu": "menu",
    "Popups": "popups_len",
    "Blocks": "blocks_on_board",
    "Piece position": "piece_pos",
    "Piece blocks": "piece_blocks",
    "Piece letter": "piece_letter",
    "Built-in modes": "boards_len",
    "Custom modes": "cboards_len",
    "Loading progress": "loading_prog",
}
options_elements = [
    ListLabel('Gameplay'),
    ListBar('ARR', 'arr', 1, 5),
    ListBar('DAS', 'das', 1, 20),
    ListBar('SDF', 'sdf', 2, 40),
    ListBar('Volume', 'volume', 0, 100),

    ListSeparator(30),

    ListLabel('Style'),
    ListBar('BG dim', 'bg_dim', 0,1, 2),
    ListBar('BG color change speed', 'bg_speed', 0.5,5, 1),
]
buttons = {
    "main": [
        Button('Play', (0,-40), (300,60), switch_menu, ['modes'], 24),
        Button('Options', (0,40), (300,60), switch_menu, ['options'], 24),
        Button('Exit game', (0,120), (300,60), are_you_sure, [SurePopup(['Are you sure you want to exit the game?'], exit_game, 'main')], 24)
    ],
    "game": [
        Button('Pause', (20,20), (75,40), switch_menu, ['pause'], 16, 'l','t'),
        Button('Restart', (20,70), (95,40), restart, [], 16, 'l','t')
    ],
    "pause": [
        Button('Continue', (20,20), (100,40), continue_game, [], 16, 'l','t'),
        Button('Restart', (20,70), (95,40), restart, [], 16, 'l','t'),
        Button('Quit', (20,120), (70,40), switch_menu, ['main'], 16, 'l','t')
    ],
    "modes": [
        Button('Start', (-20,-20), (200,90), restart, [], 26, 'r','b'),
        Button('Back', (-20,-120), (200,50), switch_menu, ['main'], 18, 'r','b'),
        Button('Custom', (-20,-180), (200,50), switch_menu, ['custom'], 18, 'r','b')
    ],
    "finish": [
        Button('Back', (20,-20), (70,50), switch_menu, ['main'], 18, 'l','b'),
        Button('New game', (100,-20), (110,50), restart, [], 18, 'l','b')
    ],
    "lose": [
        Button('Back', (20,-20), (70,50), switch_menu, ['main'], 18, 'l','b'),
        Button('New game', (100,-20), (110,50), restart, [], 18, 'l','b')
    ],
    "options": {
        Button('Back', (20,20), (100,50), switch_menu, ['main'], 18, 'l','t'),
        Button('Save', (140,20), (100,50), save_settings, [], 18, 'l','t'),
    },
    "custom": {
        Button('Start', (-20,-20), (200,90), restart, [], 26, 'r','b'),
        Button('Back', (-20,-120), (200,50), switch_menu, ['main'], 18, 'r','b'),
        Button('Built-in', (-20,-180), (200,50), switch_menu, ['modes'], 18, 'r','b'),
        Button('Save', (-125,-240), (95,50), save_modes, [], 18, 'r','b'),
        Button('Load', (-20,-240), (95,50), are_you_sure, [SurePopup(
            ['Are you sure you want to load scenarios?','All unsaved changes will be overwritten!'],
        load_modes, 'custom', True)], 18, 'r','b'),
        Button('Export', (-20,-300), (95,50), export_file, [], 18, 'r','b'),
        Button('Import', (-125,-300), (95,50), import_file, [], 18, 'r','b'),
        Button('+', (-190,-360), (30,30), new_board, [], 26, 'r','b'),
        Button('×', (-147,-360), (30,30), are_you_sure, [SurePopup(
            ['Are you sure you want to delete a custom board?','This action cannot be undone!'],
        del_board, 'custom', True)], 26, 'r','b'),
        Button('⋯', (-105,-360), (30,30), new_board, [], 26, 'r','b'),
        Button('↓', (-62,-360), (30,30), move_down, [], 26, 'r','b'),
        Button('↑', (-20,-360), (30,30), move_up, [], 26, 'r','b'),
    },
    "sure": {
        Button('Yes, sure', (0,50), (300,60), yes_sure, [], 24),
        Button('No, take me back!', (0,130), (300,60), no_take_me_back, [], 24),
    },
    "loading": {}
}
menu_names = {
    "main": "pytris",
    "modes": "scenarios",
    "lose": "try again",
    "finish": "congrats",
    "pause": "paused",
    "custom": "custom",
    "options": "options",
    "game": "",
    "sure": "sure?",
    "loading": "loading"
}
menu_names_offsets = {
    "main":0,
    "modes":0,
    "lose":0,
    "finish":200,
    "pause":0,
    "game":0,
    "options":0,
    "handling":0,
    "custom":0,
    "sure":0,
    "loading":0,
}
scrolling_supported = [
    'options',
    'modes',
    'custom',
    'finish'
]
bg_colors = [
    (200,80,80),
    (200,200,80),
    (80,200,80),
    (80,200,200),
    (80,80,200),
    (200,80,200),
    (200,80,80)
]
bg_color_key = 0
bg_color_base = 0

player: Board = None
sure_popup: SurePopup = None


# preparing

load_modes(False)

try:
    load_settings()
except:
    save_settings()

if presence:
    try:
        RPC = Presence(client_id)
        RPC.connect()
    except:
        popup('Failed connecting to Discord', (60,30,30))
else:
    popup('Presence disabled')



# main loop

while running:

############## INPUT ##############

    events = pg.event.get()
    mouse_pos = pg.mouse.get_pos()
    mouse_press = pg.mouse.get_pressed(5)
    mouse_moved = pg.mouse.get_rel()
    keys = pg.key.get_pressed()
    just_pressed = []
    hotkey_pressed = False
    lmb_up = False
    lmb_down = False
    mouse_wheel = 0



############## PROCESSING EVENTS ##############

    for event in events:
        if event.type == pg.QUIT:
            exit_game()

        if event.type == pg.VIDEORESIZE:
            windowx = event.w
            windowy = event.h
            if windowx <= 960:
                windowx = 960
            if windowy <= 640:
                windowy = 640
            halfx = windowx//2
            halfy = windowy//2
            screen = pg.display.set_mode((windowx,windowy), pg.RESIZABLE)

            for i in buttons:
                for j in buttons[i]:
                    j.resize()

            update_scroll = True

        if event.type == pg.MOUSEWHEEL:
            mouse_wheel = event.y

        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                lmb_up = True

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                lmb_down = True

        if event.type == pg.KEYDOWN:
            just_pressed.append(event.key)

            if event.key == pg.K_F3:
                debug_overlay = not debug_overlay


    for i in keybinds:
        pressed = False
        for key in keybinds[i]:
            if keys[key]:
                pressed = True

        if pressed:
            presses[i] += 1
        elif presses[i] != 0:
            presses[i] = 0



############## BG COLOR ##############

    bg_color = colors.transition(
        colors.transition(bg_colors[bg_color_base], (0,0,0), bg_dim), 
        colors.transition(bg_colors[bg_color_base+1], (0,0,0), bg_dim),
        bg_color_key/255
    )
    screen.fill(bg_color)
    
    bg_color_key += bg_speed

    if bg_color_key > 255:
        bg_color_base += 1
        bg_color_key = 0

        if bg_color_base >= len(bg_colors)-1:
            bg_color_base = 0



############## MENU NAMES ##############

    to_remove = []
    for i in menu_names_fx:
        i.update()
        i.draw()
        if i.deletable:
            to_remove.append(i)

    for i in to_remove:
        menu_names_fx.remove(i)



############## MAIN MENU ##############

    if menu == 'main':
        draw.text('pytris', (halfx, 100), size=72, style='tetris', horizontal_margin='m')

        # hotkeys
        if not hotkey_pressed:
            hotkey_pressed = True

            if pg.K_SPACE in just_pressed:
                switch_menu('modes')
            else:
                hotkey_pressed = False



############## PAUSE ##############

    if menu == 'pause':
        player.draw()

        # hotkeys
        if not hotkey_pressed:
            hotkey_pressed = True

            if pg.K_q in just_pressed:
                switch_menu('main')
            elif pg.K_r in just_pressed:
                restart()
            else:
                hotkey_pressed = False



############## GAMEMODE SELECTOR ##############

    if menu == 'modes' or menu == 'custom':
        # scrolling
        if menu == 'custom': cur_list = custom_boards
        else: cur_list = boards

        if update_scroll:
            scroll_limit = max(0, len(cur_list)*30-windowy+40)
            
        # mode list
        ongoing = 20-scroll

        for index, i in enumerate(cur_list):
            size = draw.get_text_size(i.name)[0]
            rect = pg.Rect(20,ongoing,size+20,30)
            color = (10 if index%2 == 0 else 30) if selected_board != index else 100

            if rect.collidepoint(mouse_pos):
                color += 10
                if lmb_up:
                    selected_board = index

            pg.draw.rect(screen, (color,color,color), rect, 0, 7)
            draw.text(i.name, (30,rect.centery), vertical_margin='m')
            ongoing += 30

        # hotkeys
        if not hotkey_pressed:
            hotkey_pressed = True

            if pg.K_ESCAPE in just_pressed:
                switch_menu('main')
            elif pg.K_SPACE in just_pressed:
                restart()
            else:
                hotkey_pressed = False



############## GAME LOGIC ##############

    if menu == 'game':
        player.update(presses)
        player.draw()

        if not player.forfeited and player.death_key > 120:
            switch_menu('lose')
            update_presence('Lost', player.mode_name)
        if player.forfeited and player.death_key > 50:
            switch_menu('modes' if not custom_game else 'custom')
        if player.win_key > 120:
            switch_menu('finish')

            if player.goal_type == 'lines':
                arg = f'{to_time(player.frames/60, 1)} • {player.score} points'
            if player.goal_type == 'time':
                arg = f'{player.score} • {player.lines} lines'
            update_presence(f'Finished • {arg}', player.mode_name)



############## FINISH & LOSE ##############

    if menu == 'finish':
        if update_scroll:
            scroll_limit = max(0, len(player.stats)*30-windowy+400)

        if finish_key < 50:
            finish_key += 1

        ease = easing.QuinticEaseOut(0,1,50).ease(finish_key)
        if player.goal_type == 'lines':
            string = f'{to_time(player.frames/60, 3)}'
            sec_string = f'{player.score} • {player.lines}/{player.goal} LINES'
        if player.goal_type == 'time':
            string = f'{player.score}'
            sec_string = f'{player.lines} LINES • {to_time(player.goal, 1)}'

        # these wiggly ass circles
        if just_entered:
            size = draw.get_text_size(string, 100)[0]
            sec_size = draw.get_text_size(sec_string, 36)[0]
            size = max(size, sec_size)

            ongoing = -size/2+int(size%30)
            for i in range(int(size/30)):
                end_screen_fx.append(EndCircle(ongoing))
                ongoing += 30

        # name and stats
        draw.text(player.mode_name, (halfx,300-scroll), size=40, horizontal_margin='m')

        ongoing = 380-scroll
        for index, i in enumerate(player.stats):
            draw.text(i, (halfx-300, ongoing), horizontal_margin='l', opacity=255-100*(index%2))
            draw.text(str(player.stats[i]), (halfx+300, ongoing), horizontal_margin='r', opacity=255-100*(index%2))
            ongoing += 30

        # score
        for i in end_screen_fx:
            i.update()
            i.draw()

        draw.text(string, (halfx,125), size=int(100*ease), horizontal_margin='m', vertical_margin='m')
        draw.text(sec_string, (halfx,205), size=int(36*ease), horizontal_margin='m', vertical_margin='m')



############## OPTIONS ##############

    if menu == 'options':
        ongoing = 50-scroll
        for i in options_elements:
            ongoing += i.update(ongoing)

        if update_scroll:
            scroll_limit = max(0, ongoing+50-windowy)



############## SURE POPUP ##############

    if menu == 'sure':
        sure_popup.draw()



############## LOADING BAR ##############

    if menu == 'loading':
        percent = loading/loading_total
        pg.draw.rect(screen, (255,255,255), (halfx-300, halfy, percent*600, 4), 0, 2)
        pg.draw.rect(screen, (255,255,255), (halfx-300, halfy, 600, 4), 1, 2)



############## BUTTONS ##############

    for i in buttons[menu]:
        i.draw()
        i.update()



############## SCROLLING ##############

    if menu in scrolling_supported:
        if scroll < 0: scroll = 0
        if scroll > scroll_limit: scroll = scroll_limit

        if mouse_wheel != 0:
            scroll_vel -= mouse_wheel*15

        scroll += scroll_vel
        scroll_vel /= 1.3

        # scroll bar
        if scroll_limit > 0:
            end_pos = (windowy/(scroll_limit+windowy))*(windowy-6)
            start_pos = 3+(scroll/scroll_limit)*(windowy-end_pos-6)
            pg.draw.rect(screen, (255,255,255), (windowx-7, start_pos, 4, end_pos), 0, 2)



############## POPUPS ##############

    ongoing = 0
    to_remove = []
    
    for i in popups:
        i.update()
        ongoing += i.draw(ongoing)+5
        if i.deletable:
            to_remove.append(i)

    for i in to_remove:
        popups.remove(i)



############## DEBUG OVERLAY ##############

    if debug_overlay:
        popups_len = len(popups)
        boards_len = len(boards)
        cboards_len = len(custom_boards)
        try:
            loading_prog = f'{loading}/{loading_total} {round(loading/loading_total*100, 1)}'
        except:
            loading_prog = f'{loading}/{loading_total}'

        if player != None:
            blocks_on_board = len(player.blocks)

            if player.falling_mino != None:
                piece_blocks = len(player.falling_mino.blocks)
                piece_pos = player.falling_mino.pos
                piece_letter = player.falling_mino.mino.letter
            else:
                piece_blocks = 'No falling piece'
                piece_pos = 'No falling piece'
                piece_letter = 'No falling piece'
        else:
            blocks_on_board = 'Player not initialized'
            piece_blocks = 'Player not initialized'
            piece_pos = 'Player not initialized'
            piece_letter = 'Player not initialized'

        ongoing = 5
        var = globals()

        for i in overlay_elements:
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing+1), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing-1), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing+1), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing-1), (0,0,0), 8, 'sys', antialias=False)
            
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing+1), (0,0,0), 8, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing-1), (0,0,0), 8, 'sys', antialias=False)

            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing), size=8, style='sys', antialias=False)
            ongoing += 10
            



############## UPDATING SCREEN ##############

    pg.display.flip()
    clock.tick(fps)
    dfps = round(clock.get_fps(), 2)
    if just_entered > 0: just_entered -= 1
    if update_scroll > 0: update_scroll -= 1