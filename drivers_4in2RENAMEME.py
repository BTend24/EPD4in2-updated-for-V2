from PIL import Image
from papertty.drivers.drivers_base import GPIO
from papertty.drivers.drivers_consts import EPD4in2v2const
from papertty.drivers.drivers_partial import WavesharePartial

class EPD4in2v2(WavesharePartial, EPD4in2v2const):
    """WaveShare 4.2" """

    # code adapted from  epd_4in2.c
    # https://github.com/waveshare/e-paper/blob/8973995e53cb78bac6d1f8a66c2d398c18392f71/raspberrypi%26jetsonnano/c/lib/e-paper/epd_4in2.c

    def __init__(self):
        super(WavesharePartial, self).__init__(name='4.2"',
                                               width=400,
                                               height=300)
        self.supports_partial = True
        self.frame_buffer = [0xff] * (self.width * self.height // 8)
        self.update_counter = 0  # Add a counter

    def wait_until_idle(self):
        while self.digital_read(self.BUSY_PIN) == 1:
            self.delay_ms(20)

    def set_setting(self, command, data):
        print(f"set_setting")
        self.send_command(command)
        self.send_data(data)

    def set_resolution(self):
        print(f"set_resolution")
        self.set_setting(self.RESOLUTION_SETTING,
                         [(self.width >> 8) & 0xff,
                          self.width & 0xff,
                          (self.height >> 8) & 0xff,
                          self.height & 0xff])

    def reset(self):
        print(f"reset")
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(100)
        self.digital_write(self.RST_PIN, GPIO.LOW)
        self.delay_ms(2)
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(100)

    def send_command(self, command):
        self.digital_write(self.DC_PIN, GPIO.LOW)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        self.spi_transfer([command])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    def send_data(self, data):
        self.digital_write(self.DC_PIN, GPIO.HIGH)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        if type(data) == list:
            for d in data:
                self.spi_transfer([d])
        else:
            self.spi_transfer([data])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    def turn_on_display(self):
        print(f"turn_on_display")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xF7)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_fast(self):
        print(f"turn_on_display_fast")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def turn_on_display_partial(self):
        print(f"turn_on_display_partial")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xFF)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()
        
    def turn_on_display_4gray(self):
        print(f"turn_on_display_4gray")
        self.send_command(0x22) #Display Update Control
        self.send_data(0xCF)
        self.send_command(0x20) #Activate Display Update Sequence
        self.wait_until_idle()

    def init(self, partial=True, gray=False, **kwargs):
        print(f"init")
        self.partial_refresh = partial
        self.gray = gray

        if self.epd_init() != 0:
            return -1

        self.reset()
        self.wait_until_idle()

        self.send_command(0x12) #SWRESET
        self.wait_until_idle()

        self.send_command(0x21)  # Display update control
        self.send_data(0x40)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x03)  # X-mode

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.wait_until_idle()

        self.clear()

    def init_fast(self, partial=True, gray=False, **kwargs):
        print(f"init_fast")
        self.partial_refresh = partial
        self.gray = gray

        if self.epd_init() != 0:
            return -1

        self.reset()
        self.wait_until_idle()

        self.send_command(0x12) #SWRESET
        self.wait_until_idle()

        self.send_command(0x21)  # Display update control
        self.send_data(0x40)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x05)

        self.send_command(0x1A)
        self.send_data(0x5A)  

        self.send_command(0x22)  # Load temperature value
        self.send_data(0x91)  
        self.send_command(0x20)  
        self.wait_until_idle()

        self.send_command(0x11)  # data  entry  mode
        self.send_data(0x03)  # X-mode

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.wait_until_idle()

    def clear(self):
        print(f"clear")
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        self.send_data([0xff] * int(self.height * linewidth))

        self.send_command(0x26)
        self.send_data([0xff] * int(self.height * linewidth))

        self.turn_on_display()

    def fill(self, color, fillsize):
        print(f"fill: color {color}, fillsize {fillsize}")
        div, rem = divmod(self.height, fillsize)
        image = Image.new('1', (self.width, fillsize), color)

        for i in range(div):
            self.draw(0, i * fillsize, image)

        if rem != 0:
            image = Image.new('1', (self.width, rem), color)
            self.draw(0, div * fillsize, image)

    def display_full(self):
        print(f"display_full")
        self.send_command(0x24)
        self.send_data(self.frame_buffer)

        self.send_command(0x26)
        self.send_data(self.frame_buffer)

        self.turn_on_display()

    def display_partial(self):
        print(f"display partial")
 
        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x44) 
        self.send_data(0x00)
        self.send_data(0x31)  
        
        self.send_command(0x45) 
        self.send_data(0x00)
        self.send_data(0x00)  
        self.send_data(0x2B)
        self.send_data(0x01)

        self.send_command(0x4E) 
        self.send_data(0x00)

        self.send_command(0x4F) 
        self.send_data(0x00)
        self.send_data(0x00) 

        self.send_command(0x24) # WRITE_RAM

        self.send_data(self.frame_buffer)  
        self.turn_on_display_partial()

    def sleep(self):
        print(f"sleep")
        self.send_command(0x10)  # DEEP_SLEEP
        self.send_data(0x01)

    def frame_buffer_to_image(self):
        print(f"frame_buffer_to_image")
        im = Image.new('1', (self.width, self.height), "white")
        pi = im.load()

        for j in range(self.height):
            idxj = j * self.width // 8
            for i in range(self.width):
                idiv, irem = divmod(i, 8)
                mask = 0b10000000 >> irem
                idxi = idiv
                pi[i, j] = self.frame_buffer[idxi + idxj] & mask

        return im

    def set_frame_buffer(self, x, y, image):
        print(f"set_frame_buffer, {x}, {y}, {image}")
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        print(f"running loop on image of size {imwidth}x{imheight}")

        for j in range(imheight):
            idxj = (y + j) * self.width // 8
            for i in range(imwidth):
                idiv, irem = divmod(x + i, 8)
                mask = 0b10000000 >> irem
                idxi = idiv

                if pixels[i, j] != 0:
                    self.frame_buffer[idxi + idxj] |= mask
                else:
                    self.frame_buffer[idxi + idxj] &= ~mask

    def draw(self, x, y, image):
        print(f"draw, x:{x}, y:{y}, image:{image}")
        self.set_frame_buffer(x, y, image)

        if self.partial_refresh:
            self.display_partial()
        else:
            self.display_full()
        
        self.update_counter += 1
        if self.update_counter > 10:
            print("Update counter exceeded, breaking loop")
            return
