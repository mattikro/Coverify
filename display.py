import random
import time

import board
import displayio
import framebufferio
import rgbmatrix
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font


#font = bitmap_font.load_font('font-16.bdf')

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, height=64, bit_depth=4,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD,
        board.MTX_ADDRE
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)
display = framebufferio.FramebufferDisplay(matrix)


def image(filename='img.bmp'):
    BITMAP = displayio.OnDiskBitmap(filename)
    TILEGRID = displayio.TileGrid(BITMAP, pixel_shader=BITMAP.pixel_shader)
    GROUP = displayio.Group()
    GROUP.append(TILEGRID)
    display.show(GROUP)
    display.refresh()


def qrcode(qr_data, *, qr_size=1, x=0, y=0, qr_color=0x000000, text=[]):  # pylint: disable=invalid-name
    """Display a QR code
    :param qr_data: The data for the QR code.
    :param int qr_size: The scale of the QR code.
    :param x: The x position of upper left corner of the QR code on the display.
    :param y: The y position of upper left corner of the QR code on the display.
    """
    import adafruit_miniqr

    # generate the QR code
    for qrtype in range(1, 6):
        try:
            qrcode = adafruit_miniqr.QRCode(qr_type=qrtype)
            qrcode.add_data(qr_data)
            qrcode.make()
            break
        except RuntimeError:
            pass
            # print("Trying with larger code")
    else:
        raise RuntimeError("Could not make QR code")
    # monochrome (2 color) palette
    palette = displayio.Palette(2)
    palette[0] = 0xFFFFFF
    palette[1] = qr_color

    # pylint: disable=invalid-name
    # bitmap the size of the matrix, plus border, monochrome (2 colors)
    qr_bitmap = displayio.Bitmap(
        qrcode.matrix.width + 2, qrcode.matrix.height + 2, 2
    )
    for i in range(qr_bitmap.width * qr_bitmap.height):
        qr_bitmap[i] = 0

    # transcribe QR code into bitmap
    for xx in range(qrcode.matrix.width):
        for yy in range(qrcode.matrix.height):
            qr_bitmap[xx + 1, yy + 1] = 1 if qrcode.matrix[xx, yy] else 0

    # display the QR code
    qr_sprite = displayio.TileGrid(qr_bitmap, pixel_shader=palette, x=32 - int(qr_bitmap.width / 2),
                                   y=32 - int(qr_bitmap.height / 2))


    GROUP = displayio.Group()
    for item in text:
        GROUP.append(item)

    GROUP.append(qr_sprite)
    display.show(GROUP)
    display.refresh()

def clock(time):
    print(time)
    GROUP = displayio.Group()
    GROUP.append(label.Label(font, text=time, color=0x280029, x=0, y=8))
    display.show(GROUP)
    display.refresh()