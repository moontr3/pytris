############## INITIALIZATION ##############

import pygame as pg
import easing_functions as easing
import draw
import random
import blocks
import colors
import glob
from pypresence import Presence

pg.init()

windowx = 1280
windowy = 720
clock = pg.time.Clock()
fps = 60
dfps = 0.0

screen = pg.display.set_mode((windowx,windowy), pg.RESIZABLE)
running = True
pg.display.set_caption('pytris')
draw.def_surface = screen
client_id = 1115042623854485534

halfx = windowx//2
halfy = windowy//2

sfx = {'.'.join(i.removeprefix('res\\sfx\\').split('.')[0:-1]): pg.mixer.Sound(i) for i in glob.glob('res\\sfx\\*')}


# app functions

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


def continue_game():
    update_presence('Ingame', player.mode_name)
    switch_menu('game')

def restart():
    global player
    player = boards[selected_board].get_board()
    switch_menu('game')
    update_presence('Ingame', player.mode_name)

def switch_menu(arg):
    global menu, finish_key
    menu = arg
    for i in buttons:
        for j in buttons[i]:
            j.hover_key = 0
    for i in menu_names_fx:
        i.end = True
    menu_names_fx.append(MenuName(menu_names[arg], arg))

    if arg == 'pause':
        update_presence('Paused', player.mode_name)
    elif arg != 'game':
        update_presence('Browsing menus')

    finish_key = 0

def exit_game():
    global running
    running = False


def play_sound(key, volume=1.0):
    channel = pg.mixer.find_channel(True)
    sfx[key].set_volume(volume)
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
        rect = pg.Rect(20,offset+20, self.size[0]+20,ease)

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
    ], level_increase=True, death=True):
        self.name = name
        self.x_size = x_size
        self.y_size = y_size
        self.level = def_level
        self.goal_type = goal_type
        self.goal = goal
        self.minoes = minoes
        self.level_increase = level_increase
        self.death = death

    def get_board(self):
        return Board(self.x_size, self.y_size, self.name, self.level, self.goal_type, self.goal, self.minoes, self.level_increase, self.death)

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

        if self.hover_key < max_num:
            self.hover_key += (max_num-self.hover_key)/7
        if self.hover_key > max_num:
            self.hover_key -= (self.hover_key-max_num)/7

        if hovered and lmb_up:
            self.func(*self.args)

    def draw(self):
        pg.draw.rect(screen, (self.hover_key,self.hover_key,self.hover_key), self.rect, border_radius=14)
        pg.draw.rect(screen, colors.transition((self.hover_key,self.hover_key,self.hover_key), (255,255,255), 0.5+self.hover_key/255/2), self.rect, 2, 14)
        draw.text(self.text, self.rect.center, size=self.text_size, horizontal_margin='m', vertical_margin='m')
        


# effects

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
    def __init__(self, x_size, y_size, mode_name, level, goal_type, goal, minoes, level_increase, death):
        self.x_size = x_size
        self.y_size = y_size
        self.cell_size = board_size
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
        self.combo_key = 0
        self.btb_key = 0

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

        self.held = None
        self.just_held = False
        self.blocks = []
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
            self.add_score(x, y, action_score//2, (255,255,0), 24)

    # resets back-to-back
    def reset_btb(self):
        self.btb = -1

    # checks if current piece has beel t-spun
    def is_tspin(self):
        if self.falling_mino == None:
            return False, False
        if self.falling_mino.mino.letter != 't':
            return False, False
        
        return True, False

    # checks if any of blocks in the blocks list collide with anything on the board
    def collision(self, blocks):
        for block in blocks:
            if block[0] < 0 or block[0] > self.x_size-1 or block[1] > self.y_size-1:
                return True
            for i in self.blocks:
                if block == i.pos:
                    return True
        return False

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

    # checks for line clears
    def line_clear_check(self):
        cleared_lines = []
        lines = {}

        # getting which lines are cleared
        for i in self.blocks:
            if i.pos[1] not in lines:
                lines[i.pos[1]] = 0
            lines[i.pos[1]] += 1
            
        for i in lines:
            if lines[i] == self.x_size:
                cleared_lines.append(i)

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
            self.add_fx(ActionFX(f'{"MINI " if mini_tspin else ""}T-SPIN', (200,100,200), small=True))

        self.lines += len(cleared_lines)
        btb_added = False
        if len(cleared_lines) != 0:
            self.combo += 1
            self.combo_key = 20
            self.add_fx(ActionFX(line_clear_titles[len(cleared_lines)-1]))

            self.lines_left -= len(cleared_lines)
            if self.lines_left <= 0:
                self.lines_left += 10
                if self.level < 14:
                    self.level += 1
                    
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
                score = pc_pts[len(cleared_lines)+int(self.btb > 0)]*(self.level+1)
                self.add_score(center_x, center_y, score, (255,255,255), 36)
                self.add_btb(center_x, center_y, score)

        else:
            self.combo = -1


        if not btb_added and (
            len(cleared_lines) > 0 or\
            len(self.blocks) == 0
        ):
            self.reset_btb()

    # replaces current tetromino with the next one from the queue
    def next(self):
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
            self.next()
        else:
            self.held, self.falling_mino = self.falling_mino.mino, FallingMino(self.held, self.x_size)
            self.lowest = self.falling_mino.pos[1]
            self.calculate_drop()
            self.drop()
            

    # stops the current tetromino and places it on the board
    def stop(self):
        for i in self.falling_mino.blocks:
            self.blocks.append(Block((
                i[0]+self.falling_mino.pos[0],
                i[1]+self.falling_mino.pos[1]
            ), self.falling_mino.mino.letter))

        self.just_held = False
        self.next()
        self.pieces.append(self.frames)

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

            self.shake = 10
            play_sound('glass')

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
            self.drop_frames += 1 
            cur_sdf = 1 if keys['soft'] == 0 else sdf
            if self.drop_frames*cur_sdf >= drop_timers[self.level]:
                self.drop_frames = 0
                self.drop(keys['soft'] != 0)

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

        # grid
        pg.draw.rect(screen, (0,0,0), pg.Rect(board_topleft, (self.x_size*self.cell_size, self.y_size*self.cell_size)))
        for y in range(self.y_size):
            for x in range(self.x_size):
                pg.draw.rect(screen, (128,128,128), (ongoingx, ongoingy, self.cell_size+1,self.cell_size+1), 1)

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
            for j in i.pos:
                pg.draw.rect(screen, i.color, (
                    board_topleft[0]+self.x_size*self.cell_size+30+j[0]*15,
                    board_topleft[1]+j[1]*15+ongoing,
                    15,15
                ))
            ongoing += 50

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

        draw.text(str(int(self.vis_score)), (
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
        if self.goal_type == 'lines':
            string = f'{self.lines}/{self.goal}'
        else:
            string = f'{self.lines}L'

        draw.text(string, (
            board_topleft[0]+self.x_size*self.cell_size+10, board_topleft[1]+self.y_size*self.cell_size-60+39*int(self.allow_drop or self.dead)
        ), size=21)


        # level
        size = draw.text(f'Lv{self.level+1}', (
            board_topleft[0]+self.x_size*self.cell_size+10, board_topleft[1]+self.y_size*self.cell_size-90+39*int(self.allow_drop or self.dead)
        ), size=21)[0]

        if self.level_increase:
            draw.text(f'{self.lines_left}', (
                board_topleft[0]+self.x_size*self.cell_size+20+size, board_topleft[1]+self.y_size*self.cell_size-90+39*int(self.allow_drop or self.dead)
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


# app variables

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
    BoardSettings('Sprint 100L', goal_type='lines', goal=100),
    BoardSettings('TETR.IO Blitz', goal_type='time', goal=120),
    BoardSettings('TETR.IO Blitz 4-Wide',4, goal_type='time', goal=120),
    BoardSettings('Freeroam M123', minoes=m123),
    BoardSettings('Zen M123', minoes=m123, level_increase=False, death=False),
    BoardSettings('Sprint M123 40L', minoes=m123, goal_type='lines', goal=40),
    BoardSettings('Sprint M123 4-Wide 40L', 4, minoes=m123, goal_type='lines', goal=40),
    BoardSettings('TETR.IO Blitz M123', minoes=m123, goal_type='time', goal=120),
    BoardSettings('TETR.IO Blitz M123 4-Wide', 4, minoes=m123, goal_type='time', goal=120),
    BoardSettings('Freeroam 4-Wide', 4),
    BoardSettings('Sprint 4-Wide 40L', 4, goal_type='lines', goal=40),
    BoardSettings('1S test', 10, goal_type='time', goal=1),
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
    'forfeit': [pg.K_ESCAPE],
    'reset': [pg.K_r],
}
presses = {i: 0 for i in keybinds}
drop_timers = [
    60,
    47,
    37,
    28,
    21,
    16,
    11,
    8,
    6,
    4,
    3,
    2,
    1,
    1,
    1,
    1
]
line_clear_pts = [
    100,
    300,
    500,
    800
]
pc_pts = [
    800,
    1200,
    1800,
    2000,
    3200    
]
line_clear_titles = [
    'SINGLE',
    'DOUBLE',
    'TRIPLE',
    'TETRIS',
    'QUINTUPLE'
]

popups = []
menu_names_fx = [MenuName('pytris','main')]
arr = 2
das = 8
sdf = 20
bg_dim = 0.7
board_size = 30
presence = True
finish_key = 0
debug_overlay = False
overlay_elements = {
    "FPS": "dfps",
    "Menu": "menu",
    "Popups": "popups_len",
    "Blocks": "blocks_on_board",
    "Piece position": "piece_pos",
    "Piece blocks": "piece_blocks",
    "Piece letter": "piece_letter"
}

buttons = {
    "main": [
        Button('Play', (0,-40), (300,60), switch_menu, ['modes'], 24),
        Button('Options', (0,40), (300,60), switch_menu, ['options'], 24),
        Button('Exit game', (0,120), (300,60), exit_game, [], 24)
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
        Button('Handling', (0,-150), (300,60), switch_menu, ['handling']),
    },
    "handling": {
        Button('Back', (20,20), (100,50), switch_menu, ['options'], 18, 'l','t'),
    },
    "custom": {
        Button('Start', (-20,-20), (200,90), restart, [], 26, 'r','b'),
        Button('Back', (-20,-120), (200,50), switch_menu, ['main'], 18, 'r','b'),
        Button('Built-in', (-20,-180), (200,50), switch_menu, ['modes'], 18, 'r','b')
    }
}
menu_names = {
    "main": "pytris",
    "modes": "scenarios",
    "lose": "try again",
    "finish": "congrats",
    "pause": "paused",
    "custom": "custom",
    "options": "options",
    "handling": "handling",
    "game": ""
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
    "custom":0
}
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

menu = 'main'
player: Board = None


# preparing

if presence:
    try:
        RPC = Presence(client_id)
        RPC.connect()
    except:
        popup('Failed connecting to Discord', (60,30,30))



# main loop

while running:

############## INPUT ##############

    events = pg.event.get()
    mouse_pos = pg.mouse.get_pos()
    mouse_press = pg.mouse.get_pressed(5)
    mouse_moved = pg.mouse.get_rel()
    keys = pg.key.get_pressed()
    lmb_up = False
    mouse_wheel = 0



############## PROCESSING EVENTS ##############

    for event in events:
        if event.type == pg.QUIT:
            running = False 

        if event.type == pg.VIDEORESIZE:
            windowx = event.w
            windowy = event.h
            if windowx <= 640:
                windowx = 640
            if windowy <= 640:
                windowy = 640
            halfx = windowx//2
            halfy = windowy//2
            screen = pg.display.set_mode((windowx,windowy), pg.RESIZABLE)

            for i in buttons:
                for j in buttons[i]:
                    j.resize()

        if event.type == pg.MOUSEWHEEL:
            mouse_wheel = event.y

        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                lmb_up = True

        if event.type == pg.KEYDOWN:
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
    
    bg_color_key += 1

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



############## PAUSE ##############

    if menu == 'pause':
        player.draw()



############## GAMEMODE SELECTOR ##############

    if menu == 'modes':
        ongoing = 20
        for index, i in enumerate(boards):
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



############## GAME LOGIC ##############

    if menu == 'game':
        player.update(presses)
        player.draw()

        if not player.forfeited and player.death_key > 120:
            switch_menu('lose')
            update_presence('Lost', player.mode_name)
        if player.forfeited and player.death_key > 50:
            switch_menu('modes')
        if player.win_key > 120:
            switch_menu('finish')

            if player.goal_type == 'lines':
                arg = f'{to_time(player.frames/60, 1)} • {player.score} points'
            if player.goal_type == 'time':
                arg = f'{player.score} • {player.lines} lines'
            update_presence(f'Finished • {arg}', player.mode_name)



############## FINISH & LOSE ##############

    if menu == 'finish':
        if finish_key < 50:
            finish_key += 1

        ease = easing.QuinticEaseOut(0,1,50).ease(finish_key)
        rect = pg.Rect(20,20,windowx-40,ease*200)

        if player.goal_type == 'lines':
            string = f'{to_time(player.frames/60, 3)}'
            sec_string = f'{player.score} • {player.lines}/{player.goal} LINES'
        if player.goal_type == 'time':
            string = f'{player.score}'
            sec_string = f'{player.lines} LINES • {to_time(player.goal, 1)}'

        pg.draw.rect(screen, (0,0,0), rect, 0, 14)
        pg.draw.rect(screen, (128,128,128), rect, 2, 14)

        draw.text(string, (halfx,rect.top+10), size=int(100*ease), horizontal_margin='m')
        draw.text(sec_string, (halfx,rect.bottom-25), size=int(36*ease), horizontal_margin='m', vertical_margin='b')



############## BUTTONS ##############

    try:
        for i in buttons[menu]:
            i.draw()
            i.update()
    except:
        pass



############## POPUPS ##############

    ongoing = 0
    to_remove = []
    
    for i in popups:
        i.update()
        ongoing += i.draw(ongoing)+10
        if i.deletable:
            to_remove.append(i)

    for i in to_remove:
        popups.remove(i)



############## DEBUG OVERLAY ##############

    if debug_overlay:
        popups_len = len(popups)

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
            move_timeout = 'Player not initialized'
            blocks_on_board = 'Player not initialized'
            piece_blocks = 'Player not initialized'
            piece_pos = 'Player not initialized'
            piece_letter = 'Player not initialized'

        ongoing = 5
        var = globals()

        for i in overlay_elements:
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing+1), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing-1), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing+1), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing-1), (0,0,0), 13, 'sys', antialias=False)
            
            draw.text(f'{i}: {var[overlay_elements[i]]}', (4,ongoing), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (6,ongoing), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing+1), (0,0,0), 13, 'sys', antialias=False)
            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing-1), (0,0,0), 13, 'sys', antialias=False)

            draw.text(f'{i}: {var[overlay_elements[i]]}', (5,ongoing), size=13, style='sys', antialias=False)
            ongoing += 15
            



############## UPDATING SCREEN ##############

    pg.display.flip()
    clock.tick(fps)
    dfps = round(clock.get_fps(), 2)