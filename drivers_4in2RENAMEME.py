# Modified EPD4in2.py for V2

from PIL import Image
from papertty.drivers.drivers_base import GPIO
from papertty.drivers.drivers_consts import EPD4in2const
from papertty.drivers.drivers_partial import WavesharePartial

class EPD4in2(WavesharePartial, EPD4in2const):
    """WaveShare 4.2" V2 """

    def __init__(self):
        super(WavesharePartial, self).__init__(name='4.2"',
                                               width=400,
                                               height=300)
        self.supports_partial = True
        self.frame_buffer = [0x00] * (self.width * self.height // 8)

    def set_setting(self, command, data):
        self.send_command(command)
        self.send_data(data)

    def set_resolution(self):
        self.set_setting(self.RESOLUTION_SETTING,
                         [(self.width >> 8) & 0xff,
                          self.width & 0xff,
                          (self.height >> 8) & 0xff,
                          self.height & 0xff])

    def reset(self):
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(200)
        self.digital_write(self.RST_PIN, GPIO.LOW)
        self.delay_ms(200)
        self.digital_write(self.RST_PIN, GPIO.HIGH)
        self.delay_ms(200)

    def send_command(self, command):
        self.digital_write(self.DC_PIN, GPIO.LOW)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        self.spi_transfer([command])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    def send_data(self, data):
        self.digital_write(self.DC_PIN, GPIO.HIGH)
        self.digital_write(self.CS_PIN, GPIO.LOW)
        if isinstance(data, list):
            self.spi_transfer(data)
        else:
            self.spi_transfer([data])
        self.digital_write(self.CS_PIN, GPIO.HIGH)

    def wait_until_idle(self):
        self.send_command(self.GET_STATUS)
        while self.digital_read(self.BUSY_PIN) == 0:
            self.send_command(self.GET_STATUS)
            self.delay_ms(100)

    def turn_on_display(self):
        self.send_command(self.DISPLAY_REFRESH)
        self.delay_ms(100)
        self.wait_until_idle()

    def full_set_lut(self):
        self.set_setting(self.VCOM_LUT, self.LUT_VCOM0)
        self.set_setting(self.W2W_LUT, self.LUT_WW)
        self.set_setting(self.B2W_LUT, self.LUT_BW)
        self.set_setting(self.W2B_LUT, self.LUT_WB)
        self.set_setting(self.B2B_LUT, self.LUT_BB)

    def partial_set_lut(self):
        self.set_setting(self.VCOM_LUT, self.PARTIAL_LUT_VCOM1)
        self.set_setting(self.W2W_LUT, self.PARTIAL_LUT_WW1)
        self.set_setting(self.B2W_LUT, self.PARTIAL_LUT_BW1)
        self.set_setting(self.W2B_LUT, self.PARTIAL_LUT_WB1)
        self.set_setting(self.B2B_LUT, self.PARTIAL_LUT_BB1)

    def gray_set_lut(self):
        self.set_setting(self.VCOM_LUT, self.GRAY_LUT_VCOM)
        self.set_setting(self.W2W_LUT, self.GRAY_LUT_WW)
        self.set_setting(self.B2W_LUT, self.GRAY_LUT_BW)
        self.set_setting(self.W2B_LUT, self.GRAY_LUT_WB)
        self.set_setting(self.B2B_LUT, self.GRAY_LUT_BB)

    def init_bw(self):
        self.reset()
        self.set_setting(self.POWER_SETTING, [0x03, 0x00, 0x2b, 0x2b, 0x13])
        self.set_setting(self.BOOSTER_SOFT_START, [0x17, 0x17, 0x17])
        self.send_command(self.POWER_ON)
        self.wait_until_idle()
        self.set_setting(self.PANEL_SETTING, [0xbf, 0x0d])
        self.set_setting(self.PLL_CONTROL, [0x3c])
        self.set_resolution()
        self.set_setting(self.VCM_DC_SETTING, [0x12])
        self.set_setting(self.VCOM_AND_DATA_INTERVAL_SETTING, [0x97])
        self.full_set_lut()

    def init_gray(self):
        self.reset()
        self.set_setting(self.POWER_SETTING, [0x03, 0x00, 0x2b, 0x2b, 0x13])
        self.set_setting(self.BOOSTER_SOFT_START, [0x17, 0x17, 0x17])
        self.send_command(self.POWER_ON)
        self.wait_until_idle()
        self.set_setting(self.PANEL_SETTING, [0x3f])
        self.set_setting(self.PLL_CONTROL, [0x3c])
        self.set_resolution()
        self.set_setting(self.VCM_DC_SETTING, [0x12])
        self.set_setting(self.VCOM_AND_DATA_INTERVAL_SETTING, [0x97])

    def init(self, partial=True, gray=False):
        self.partial_refresh = partial
        self.gray = gray

        if self.epd_init() != 0:
            return -1

        if self.gray:
            self.init_gray()
        else:
            self.init_bw()

    def clear(self):
        width = int(self.width // 8)
        height = int(self.height)

        self.send_command(self.DATA_START_TRANSMISSION_1)
        for i in range(width * height):
            self.send_data(0xff)

        self.send_command(self.DATA_START_TRANSMISSION_2)
        for i in range(width * height):
            self.send_data(0xff)

        self.send_command(self.DISPLAY_REFRESH)
        self.delay_ms(10)
        self.turn_on_display()

    def fill(self, color, fillsize):
        div, rem = divmod(self.height, fillsize)
        image = Image.new('1', (self.width, fillsize), color)

        for i in range(div):
            self.draw(0, i * fillsize, image)

        if rem != 0:
            image = Image.new('1', (self.width, rem), color)
            self.draw(0, div * fillsize, image)

    def display_full(self):
        width = int(self.width // 8)
        height = int(self.height)

        self.send_command(self.DATA_START_TRANSMISSION_2)
        for i in range(height):
            for j in range(width):
                self.send_data(self.frame_buffer[i * width + j])

        self.turn_on_display()

    def display_partial(self, x_start, y_start, x_end, y_end):
        width = self.width // 8

        x_start = int(x_start if x_start % 8 == 0 else x_start // 8 * 8 + 8)
        x_end = int(x_end if x_end % 8 == 0 else x_end // 8 * 8 + 8)

        self.set_setting(self.VCOM_AND_DATA_INTERVAL_SETTING, [0xf7])
        self.delay_ms(100)

        self.set_setting(self.VCM_DC_SETTING, [0x08])
        self.set_setting(self.VCOM_AND_DATA_INTERVAL_SETTING, [0x47])
        self.partial_set_lut()

        self.send_command(self.PARTIAL_IN)
        self.set_setting(self.PARTIAL_WINDOW,
                         [x_start     // 256, x_start     % 256,
                          (x_end - 1) // 256, (x_end - 1) % 256,
                          y_start     // 256, y_start     % 256,
                          (y_end - 1) // 256, (y_end - 1) % 256,
                          0x28])

        self.send_command(self.DATA_START_TRANSMISSION_1)
        for j in range(y_end - y_start):
            idx = (y_start + j) * width + x_start // 8
            for i in range((x_end - x_start) // 8):
                self.send_data(self.frame_buffer[idx + i])

        self.send_command(self.DATA_START_TRANSMISSION_2)
        for j in range(y_end - y_start):
            idx = (y_start + j) * width + x_start // 8
            for i in range((x_end - x_start) // 8):
                self.send_data(~self.frame_buffer[idx + i])

        self.send_command(self.DISPLAY_REFRESH)
        self.delay_ms(10)
        self.turn_on_display()

    def sleep(self):
        self.send_command(self.POWER_OFF)
        self.wait_until_idle()
        self.set_setting(self.DEEP_SLEEP, [0xa5])

    def frame_buffer_to_image(self):
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
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

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
        if self.partial_refresh:
            self.set_frame_buffer(x, y, image)
            self.display_partial(x, y, x + image.width, y + image.height)
        else:
            self.set_frame_buffer(0, 0, image)
            self.display_full()
