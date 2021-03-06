#! python2

"""GIFImage by Matthew Roe"""

from PIL import Image
import pygame
from pygame.locals import *
import win32con
import win32gui
import win32api
import time
import random
import twitch_bot_utils
import logging
import os.path
import sys
import argparse

# Get monitor size 
width = win32api.GetSystemMetrics(0)
height = win32api.GetSystemMetrics(1)
logging.log(logging.INFO,"Monitor %d x %d" %(width,height))

class GIFImage(object):
    def __init__(self, filename):
        self.filename = filename
        self.image = Image.open(filename)
        self.frames = []
        self.get_frames()

        self.cur = 0
        self.ptime = time.time()

        self.running = True
        self.breakpoint = len(self.frames)-1
        self.startpoint = 0
        self.reversed = False

    def get_rect(self):
        return pygame.rect.Rect((0,0), self.image.size)

    def get_frames(self):
        image = self.image

        pal = image.getpalette()
        base_palette = []
        for i in range(0, len(pal), 3):
            rgb = pal[i:i+3]
            base_palette.append(rgb)

        all_tiles = []
        try:
            while 1:
                if not image.tile:
                    image.seek(0)
                if image.tile:
                    all_tiles.append(image.tile[0][3][0])
                image.seek(image.tell()+1)
        except EOFError:
            image.seek(0)

        all_tiles = tuple(set(all_tiles))

        try:
            while 1:
                try:
                    duration = image.info["duration"]
                except:
                    duration = 100

                duration *= .001 #convert to milliseconds!
                cons = False

                x0, y0, x1, y1 = (0, 0) + image.size
                if image.tile:
                    tile = image.tile
                else:
                    image.seek(0)
                    tile = image.tile
                if len(tile) > 0:
                    x0, y0, x1, y1 = tile[0][1]

                if all_tiles:
                    if all_tiles in ((6,), (7,)):
                        cons = True
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i+3]
                            palette.append(rgb)
                    elif all_tiles in ((7, 8), (8, 7)):
                        pal = image.getpalette()
                        palette = []
                        for i in range(0, len(pal), 3):
                            rgb = pal[i:i+3]
                            palette.append(rgb)
                    else:
                        palette = base_palette
                else:
                    palette = base_palette

                pi = pygame.image.fromstring(image.tostring(), image.size, image.mode)
                pi.set_palette(palette)
                if "transparency" in image.info:
                    pi.set_colorkey(image.info["transparency"])
                pi2 = pygame.Surface(image.size, SRCALPHA)
                if cons:
                    for i in self.frames:
                        pi2.blit(i[0], (0,0))
                pi2.blit(pi, (x0, y0), (x0, y0, x1-x0, y1-y0))

                self.frames.append([pi2, duration])
                image.seek(image.tell()+1)
        except EOFError:
            pass

    def render(self, screen, pos):
        if self.running:
            if time.time() - self.ptime > self.frames[self.cur][1]:
                if self.reversed:
                    self.cur -= 1
                    if self.cur < self.startpoint:
                        self.cur = self.breakpoint
                else:
                    self.cur += 1
                    if self.cur > self.breakpoint:
                        self.cur = self.startpoint

                self.ptime = time.time()

        screen.blit(self.frames[self.cur][0], pos)

    def seek(self, num):
        self.cur = num
        if self.cur < 0:
            self.cur = 0
        if self.cur >= len(self.frames):
            self.cur = len(self.frames)-1

    def set_bounds(self, start, end):
        if start < 0:
            start = 0
        if start >= len(self.frames):
            start = len(self.frames) - 1
        if end < 0:
            end = 0
        if end >= len(self.frames):
            end = len(self.frames) - 1
        if end < start:
            end = start
        self.startpoint = start
        self.breakpoint = end

    def pause(self):
        self.running = False

    def play(self):
        self.running = True

    def rewind(self):
        self.seek(0)
    def fastforward(self):
        self.seek(self.length()-1)

    def get_height(self):
        return self.image.size[1]
    def get_width(self):
        return self.image.size[0]
    def get_size(self):
        return self.image.size
    def length(self):
        return len(self.frames)
    def reverse(self):
        self.reversed = not self.reversed
    def reset(self):
        self.cur = 0
        self.ptime = time.time()
        self.reversed = False

    def copy(self):
        new = GIFImage(self.filename)
        new.running = self.running
        new.breakpoint = self.breakpoint
        new.startpoint = self.startpoint
        new.cur = self.cur
        new.ptime = self.ptime
        new.reversed = self.reversed
        return new
        
def set_top(hwnd,x1,y1):
    x = int(round(width/2))
    y = int(round(height/2))
    w = int(round(x1/2))
    h = int(round(y1/2))
    
    win32gui.SetWindowPos(hwnd,win32con.HWND_TOPMOST,0,0,width,height,win32con.SWP_NOACTIVATE)
    logging.log(logging.DEBUG,"SetWindowPos to HWND_TOPMOST and SWP_NOACTIVATE")
    style = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    logging.log(logging.DEBUG,"Got style %X before" % style)
    style = style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST
    logging.log(logging.DEBUG,"Setting style %X" % style)
    win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
    logging.log(logging.DEBUG,"Set style %X" % style)
    style = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    logging.log(logging.DEBUG,"Got style %X after" % style)

    
def main():
    pygame.init()
    gifs = ["scarygif1.gif","scarygif2.gif","scarygif3.gif","scarygif4.gif","scarygif5.gif","shark.gif","nyancat.gif","toasty.gif","doge.gif","dramatic.gif"]
    
    parser = argparse.ArgumentParser()
    parser.add_argument('gif_file',type=str, nargs='?',default="images/" + random.choice(gifs), help='Gif file to play')
    parser.add_argument('-duration', type=int, default=1000, help='Duration to play the Gif')

    try:
        options = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    gif_file = options.gif_file
    length = options.duration / 1000.0
 
    temp = "images/"+gif_file
    if not os.path.isfile(gif_file):
        if os.path.isfile("images/"+gif_file):
            gif_file = "images/" + gif_file
        else:
            gif_file = "images/" + random.choice(gifs)
            
    spoopy = GIFImage(gif_file)
    
    logging.log(logging.INFO,"Playing gif: %s for: %f" % (gif_file, length))
    
    screen = pygame.display.set_mode((1,1),pygame.NOFRAME)
    logging.log(logging.INFO,"Displaying gif: %s" % spoopy)
    
    while True:
        try:
            hwnd = win32gui.FindWindow(None,"pygame window")
            if hwnd:
                logging.log(logging.DEBUG,"Found window! hwnd: %s" % hwnd)
                set_top(hwnd,spoopy.get_width(),spoopy.get_height())
                break
        except win32gui.error:
            logging.log(logging.ERROR,"Error: window not found")
        time.sleep(0.001)

    
    screen = pygame.display.set_mode((width,height),pygame.NOFRAME)
    stop = time.clock()+length
    while time.clock() < stop:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return

        screen.fill((0,0,0))
        w = int(round(spoopy.get_width()/2))
        h = int(round(spoopy.get_height()/2))
        spoopy.render(screen, (int(round(width/2))-w, int(round(height/2))-h))
        pygame.display.flip()

if __name__ == "__main__":
    main()