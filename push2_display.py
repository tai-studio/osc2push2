import argparse

import push2_python
import cairo
import numpy
import random
import time

# from pythonosc.udp_client import SimpleUDPClient
from OSCServer.oscServer import OSCServer
import queue
from typing import Any, List



# Init Push2
push = push2_python.Push2()

# Init dictionary to store the state
state = dict()
state["bg_color"] = (random.random(), random.random(), random.random())


# ////////////////


def createOscHandlersFor(oscServer):
    def set_RGB(queue: queue.Queue):
        def handler(unused_address: str, *args: List[Any]):
            try:
                queue.put((float(args[0]), float(args[1]),
                          float(args[2])))
            except IndexError:
                print("OSC msg /rgb requires 3 arguments [float]")
                print(f"\tgot: {args}")
        return handler

    oscServer.addCmd("/rgb", set_RGB)


# /////////////////


# Function that generates the contents of the frame do be displayed
def generate_display_frame():

    # Prepare cairo canvas
    WIDTH, HEIGHT = push2_python.constants.DISPLAY_LINE_PIXELS, push2_python.constants.DISPLAY_N_LINES
    surface = cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # Draw rectangle with width proportional to encoders' value
    ctx.set_source_rgb(*state["bg_color"])
    ctx.rectangle(20, 20, WIDTH-40, HEIGHT-40)
    ctx.fill()

    # # Add text with encoder name and value
    # ctx.set_source_rgb(1, 1, 1)
    # font_size = HEIGHT//3
    # ctx.set_font_size(font_size)
    # ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    # ctx.move_to(10, font_size * 2)
    # ctx.show_text("{0}: {1}".format(encoder_name, encoder_value))

    # Turn canvas into numpy array compatible with push.display.display_frame method
    buf = surface.get_data()
    frame = numpy.ndarray(shape=(HEIGHT, WIDTH), dtype=numpy.uint16, buffer=buf)
    frame = frame.transpose()
    return frame




# Draw method that will generate the frame to be shown on the display
def draw():
    frame = generate_display_frame()
    push.display.display_frame(frame, input_format=push2_python.constants.FRAME_FORMAT_RGB565)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=50055, help="The port to listen on")

    args = parser.parse_args()

    # OSC interface
    oscServer = OSCServer(ip=args.ip, port=args.port)

    print(
        f"listening to OSC messages from {args.ip} sent to {args.port}")
    oscServer.start()
    createOscHandlersFor(oscServer)


    # Now start infinite loop so the app keeps running
    print('App runnnig...')
    while True:
        state["bg_color"] = oscServer.getLastValFor("/rgb", state["bg_color"])
        draw()
        time.sleep(1.0/30)  # Sart drawing loop, aim at ~30fps