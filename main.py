import numpy as np
import pygame
import random
from time import time

class Chip8:
    def __init__(self):
        # Previous initialization code remains the same
        self.memory = bytearray(4096)
        self.V = bytearray(16)
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = np.zeros((32, 64), dtype=np.uint8)
        self.keypad = bytearray(16)
        self.waiting_for_key = False
        self.key_register = 0
        
        # Font set initialization remains the same
        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        
        for i, font_byte in enumerate(self.fontset):
            self.memory[i] = font_byte

    def load_rom(self, filename):
        with open(filename, 'rb') as f:
            rom_data = f.read()
            for i, byte in enumerate(rom_data):
                self.memory[0x200 + i] = byte

    def emulate_cycle(self):
        # Don't execute next opcode if waiting for key input
        if self.waiting_for_key:
            return

        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2
        self.execute_opcode(opcode)
        
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def execute_opcode(self, opcode):
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        nnn = opcode & 0x0FFF
        nn = opcode & 0x00FF
        n = opcode & 0x000F

        # Previous opcode implementations remain...
        if opcode & 0xF000 == 0x0000:
            if opcode == 0x00E0:
                self.display.fill(0)
            elif opcode == 0x00EE:
                self.pc = self.stack.pop()
        
        elif opcode & 0xF000 == 0x1000:
            self.pc = nnn
        
        elif opcode & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = nnn
        
        elif opcode & 0xF000 == 0x3000:
            if self.V[x] == nn:
                self.pc += 2
        
        elif opcode & 0xF000 == 0x6000:
            self.V[x] = nn
        
        elif opcode & 0xF000 == 0x7000:
            self.V[x] = (self.V[x] + nn) & 0xFF
        
        elif opcode & 0xF000 == 0xA000:
            self.I = nnn

        # New input-related opcodes
        elif opcode & 0xF000 == 0xE000:
            if nn == 0x9E:  # Skip if key pressed
                if self.keypad[self.V[x]]:
                    self.pc += 2
            elif nn == 0xA1:  # Skip if key not pressed
                if not self.keypad[self.V[x]]:
                    self.pc += 2

        elif opcode & 0xF000 == 0xF000:
            if nn == 0x0A:  # Wait for key press
                self.waiting_for_key = True
                self.key_register = x
            elif nn == 0x15:  # Set delay timer
                self.delay_timer = self.V[x]
            elif nn == 0x18:  # Set sound timer
                self.sound_timer = self.V[x]
            elif nn == 0x07:  # Store delay timer in Vx
                self.V[x] = self.delay_timer
            
        elif opcode & 0xF000 == 0xD000:
            x_coord = self.V[x] & 63
            y_coord = self.V[y] & 31
            self.V[0xF] = 0
            
            for row in range(n):
                if y_coord + row >= 32:
                    break
                sprite_row = self.memory[self.I + row]
                
                for col in range(8):
                    if x_coord + col >= 64:
                        break
                    if sprite_row & (0x80 >> col):
                        pixel_pos = (y_coord + row, x_coord + col)
                        if self.display[pixel_pos]:
                            self.V[0xF] = 1
                        self.display[pixel_pos] ^= 1

class Chip8Emulator:
    def __init__(self):
        pygame.init()
        self.chip8 = Chip8()
        self.screen = pygame.display.set_mode((640, 320))
        self.clock = pygame.time.Clock()
        
        # CHIP-8 keypad layout:
        # 1 2 3 C
        # 4 5 6 D
        # 7 8 9 E
        # A 0 B F
        
        # Keyboard:
        # 1 2 3 4
        # Q W E R
        # A S D F
        # Z X C V

        # Map keyboard keys to CHIP-8 keypad
        self.key_mappings = {
            pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
            pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
            pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
            pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
        }

    def handle_input(self):
        # Reset all keys
        self.chip8.keypad = bytearray(16)
        
        # Get the current state of all keyboard keys
        keys = pygame.key.get_pressed()
        
        # Update the CHIP-8 keypad state
        for key, value in self.key_mappings.items():
            if keys[key]:
                self.chip8.keypad[value] = 1
                # If waiting for a key press, store the key and continue
                if self.chip8.waiting_for_key:
                    self.chip8.V[self.chip8.key_register] = value
                    self.chip8.waiting_for_key = False

    def run(self, rom_path):
        self.chip8.load_rom(rom_path)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Handle input
            self.handle_input()
            
            # Emulate one cycle
            self.chip8.emulate_cycle()
            
            # Draw screen
            self.screen.fill((0, 0, 0))
            for y in range(32):
                for x in range(64):
                    if self.chip8.display[y][x]:
                        pygame.draw.rect(self.screen, (255, 255, 255),
                                       (x * 10, y * 10, 10, 10))
            
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

# Usage example
if __name__ == "__main__":
    emulator = Chip8Emulator()
    emulator.run("invaders.ch8")