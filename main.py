import numpy
import pyglet
import sys


class CPU(pyglet.window.Window):

    memory = [0]*4096 # max 4096
    gpio = [0]*16 # max 16
    display_buffer = [0]*32*64 # 64*32
    stack = []
    key_inputs = [0]*16
    fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
            0x20, 0x60, 0x20, 0x20, 0x70, # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
            0x90, 0x90, 0xF0, 0x10, 0x10, # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
            0xF0, 0x10, 0x20, 0x40, 0x40, # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90, # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
            0xF0, 0x80, 0x80, 0x80, 0xF0, # C
            0xE0, 0x90, 0x90, 0x90, 0xE0, # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
            0xF0, 0x80, 0xF0, 0x80, 0x80  # F
            ]
    
    opcode = 0
    index = 0
    pc = 0
    
    delay_timer = 0
    sound_timer = 0
        
    should_draw = False
    key_wait = False

    funcmap = None # armazena opcodes
    vx = 0 # armazena valores de registros
    vy = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.funcmap = {0x0000: self._0ZZZ,
                        0x00e0: self._00E0,
                        0x00ee: self._00EE,
                        0x1000: self._1NNN,
                        0x2000: self._2NNN,
                        0x3000: self._3XKK,
                        0x4000: self._4XKK,
                        0x5000: self._5XY0,
                        0x6000: self._6XKK,
                        0x7000: self._7XKK,
                        0x8000: self._8ZZZ,
                        0x8FF0: self._8XY0,
                        0x8FF1: self._8XY1,
                        0x8FF2: self._8XY2,
                        0x8FF3: self._8XY3,
                        0x8FF4: self._8XY4,
                        0x8FF5: self._8XY5,
                        0x8FF6: self._8XY6,
                        0x8FF7: self._8XY7,
                        0x8FFE: self._8XYE,
                        0x9000: self._9XY0,
                        0xA000: self._ANNN,
                        0xB000: self._BNNN,
                        0xC000: self._CXKK
                        }


    def initialize(self):
        self.clear()
        self.should_draw = False
        self.key_inputs = [0]*16
        self.display_buffer = [0]*64*32 # resolução do display

        # Memória
        self.memory = [0]*4096

        # Registros básicos - general purpose
        self.gpio = [0]*16

        # Registros de timer
        self.sound_timer = 0
        self.delay_timer = 0

        # Registro de index
        self.index = 0

        # Program counter - o offset 0x200 é necessário devido ao fato de que o interpretador é armazenado no topo da memória
        self.pc = 0x200 

        # Stack
        self.stack = []

        # Código de operação
        self.opcode = 0

        i = 0
        while i < 80:
            self.memory[i] = self.fonts[i]
            i += 1

    def _0ZZZ(self):
        extracted_op = self.opcode & 0xf0ff
        try:
            self.funcmap[extracted_op]()
        except KeyError:
            print(f'Opcode {extracted_op} não existe')

    def _8ZZZ(self):
        extracted_op = self.opcode & 0xf00f
        extracted_op += 0x0ff0
        try:
            self.funcmap[extracted_op]()
        except KeyError:
            print(f'Opcode {extracted_op} não existe')

    def _00E0(self):
        print("Limpa a tela")
        self.display_buffer = [0]*64*32 # 64*32
        self.should_draw = True

    def _00EE(self):
        print("Retorna de uma subrotina")
        self.pc = self.stack.pop() # Direciona o ponteiro para o último membro da stack
    
    def _1NNN(self):
        print(f'Salta o ponteiro para o endereço {self.opcode}')
        self.pc = self.opcode & 0x0fff

    def _2NNN(self):
        self.stack.append(self.pc)
        self.pc = self.opcode & 0x0fff

    def _3XKK(self):
        print('Compara 2 registros adjacentes, e, se iguais, incrementa o program counter')
        if self.gpio[self.vx] == (self.opcode & 0x00ff):
            self.pc += 2

    def _4XKK(self):
        print('Compara 2 registros adjacentes, e, se diferentas, incrementa o program counter')
        if self.gpio[self.vx] != (self.opcode & 0x00ff):
            self.pc += 2

    def _5XY0(self):
        print('blabla')
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.pc += 2

    def _6XKK(self):
        print('a')
        self.gpio[self.vx] = (self.opcode & 0x00ff)

    def _7XKK(self):
        self.gpio[self.vx] += (self.opcode & 0x00ff)

    def _8XY0(self):
        self.gpio[self.vx] = self.gpio[self.vy]

    def _8XY1(self):
        self.gpio[self.vx] = (self.vx | self.vy)

    def _8XY2(self):
        self.gpio[self.vx] = (self.vx & self.vy)

    def _8XY3(self):
        self.gpio[self.vx] = (self.vx ^ self.vy)

    def _8XY4(self):
        if self.gpio[self.vx] + self.gpio[self.vy] > 0xff:
            self.gpio[-1] = 1
        else:
            self.gpio[-1] = 0

        self.gpio[self.vx] += self.gpio[self.vy]
        self.gpio[self.vx] &= 0x00ff

    def _8XY5(self):
        if self.gpio[self.vx] > self.gpio[self.vy]:
            self.gpio[-1] = 1
        else:
            self.gpio[-1] = 0

        self.gpio[self.vx] -= self.gpio[self.vy]
        self.gpio[self.vx] &= 0x00ff

    def _8XY6(self):
        raise NotImplementedError

    def _8XY7(self):
        if self.gpio[self.vy] > self.gpio[self.vx]:
            self.gpio[-1] = 1
        else:
            self.gpio[-1] = 0

        self.gpio[self.vx] = self.gpio[self.vy] - self.gpio[self.vx]
        self.gpio[self.vx] &= 0x00ff
    
    def _8XYE(self):
        raise NotImplementedError

    def _9XY0(self):
        if self.gpio[self.vx] != self.gpio[self.vy]:
            self.pc += 2

    def _ANNN(self):
        self.index = self.opcode & 0x0fff

    def _BNNN(self):
        self.pc = (self.opcode & 0x0fff) + self.gpio[0]

    def _CXKK(self):
        rand = numpy.random.randint(0, 256)
        self.gpio[self.vx] = rand & (self.opcode & 0x0ff)

    def _DXYN(self):
        raise NotImplementedError

    def main_loop(self):
        
        self.initialize()
        self.load_rom(sys.argv[1])

        while not self.has_exit:
            self.dispatch_events()
            self.cycle()
            self.draw()

    def on_key_press(self, symbol, modifiers):
        return super().on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        return super().on_key_release(symbol, modifiers)
    
    def load_rom(self, rom_path): # Carrega o rom_path na memória
        print(f'Carregando o room {rom_path}')
        with open(rom_path, "rb").read() as rom:
            i = 0
            while i < len(rom):
                self.memory[i+0x200] = ord(rom[i])
                i += 1

    def cycle(self):
        self.opcode = self.memory[self.pc]

        # Cada opcode têm o formato XXXX, mas na maioria dos casos 
        # basta que o primeiro nibble (dígito hexadecimal, 4 bits)
        # seja identificado para que o opcode possa ser determinado

        self.vx = (self.opcode & 0x0f00) >> 8 # Segundo e terceiro nibbles contendo os endereços 
        self.vy = (self.opcode & 0x00f0) >> 4 # de registro para certos opcodes que os exigem

        extracted_op = self.opcode & 0xf000 # Primeiro nibble
        try:
            self.funcmap[extracted_op]()
        except KeyError:
            print(f'O opcode {extracted_op} não existe')

        self.pc += 2

        if self.delay_timer > 0:
            self.delay_timer -= 1

        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                pass

if __name__ == '__main__':
    cpu = CPU()
    cpu.main_loop()
