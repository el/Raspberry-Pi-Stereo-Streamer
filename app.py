#!/usr/bin/env python

import sys, os
import inspect
import gi
import ctypes
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, Gtk, Gdk, GstVideo

class Printer:
       def __init__ (self, PrintableClass):
           for name in dir(PrintableClass):
               value = getattr(PrintableClass,name)
           #    if  '_' not in str(name).join(str(value)):
               print '  .%s: %r' % (name, value)

gdkdll = ctypes.CDLL ("libgdk-3-0.dll")

ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]  

class App_Main:
    def __init__(self, debug):

        print("Player Started")

        self.stream_started = False

        gst_pipe = "multicast-group=224.1.1.1 auto-multicast=true"
        gst_pipe += " ! application/x-rtp,payload=96,media=video,clock-rate=90000,encoding-name=H264"
        gst_pipe += " ! rtph264depay ! avdec_h264 ! autovideosink"

        # Set up the gstreamer pipeline
        if (debug):
            self.left_player = Gst.parse_launch ("videotestsrc pattern=ball ! autovideosink")
            self.right_player = Gst.parse_launch ("videotestsrc ! autovideosink")
            self.audio_player = Gst.parse_launch ("audiotestsrc ! autoaudiosink")
        else:
            self.left_player = Gst.parse_launch ("udpsrc port=5001 " + gst_pipe)
            self.right_player = Gst.parse_launch ("udpsrc port=5000 " + gst_pipe)
            self.audio_player = Gst.parse_launch ("udpsrc multicast-group=224.1.1.1" 
                + " auto-multicast=true port=5002 ! application/x-rtp, media=audio, " 
                + "clock-rate=48000, payload=96, encoding-name=X-GST-OPUS-DRAFT-SPITTKA-00"
                + " ! rtpopusdepay ! opusdec ! autoaudiosink")
        busl = self.left_player.get_bus()
        busr = self.right_player.get_bus()
        busa = self.audio_player.get_bus()

        busl.view = "Left"
        busr.view = "Right"
        button = self.color_swatch_new("blue")
        img = Gtk.Image.new_from_stock(Gtk.STOCK_STOP, Gtk.IconSize.MENU)


        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("RPi Streamer")
        window.set_default_size(1920, 1080)
        screen = window.get_screen()
        window.fullscreen()
        window.connect("destroy", Gtk.main_quit, "WM destroy")

        whbox = Gtk.HBox()
        window.add(whbox)
        busl.window = Gtk.DrawingArea()
        busr.window = Gtk.DrawingArea()
        whbox.pack_start(busl.window, True, True, 0)
        whbox.pack_start(busr.window, True, True, 0)

        window.realize()
        window.show_all()


        busl.add_signal_watch()
        busl.enable_sync_message_emission()
        busl.connect("message", self.on_message)
        busl.connect("sync-message::element", self.on_sync_message)
        busr.add_signal_watch()
        busr.enable_sync_message_emission()
        busr.connect("message", self.on_message)
        busr.connect("sync-message::element", self.on_sync_message)

        busl.hnd = gdkdll.gdk_win32_window_get_handle(ctypes.pythonapi.PyCapsule_GetPointer(busl.window.get_property("window").__gpointer__, None))
        busr.hnd = gdkdll.gdk_win32_window_get_handle(ctypes.pythonapi.PyCapsule_GetPointer(busr.window.get_property("window").__gpointer__, None))

        self.left_player.set_state(Gst.State.PLAYING)
        self.right_player.set_state(Gst.State.PLAYING)
        self.audio_player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.left_player.set_state(Gst.State.NULL)
            self.right_player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.left_player.set_state(Gst.State.NULL)
            self.right_player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

    def on_sync_message(self, bus, message):
        print(bus.view + " Player Started")
        struct = message.get_structure()
        if not struct:
            return
        message_name = struct.get_name()

        if message_name == "prepare-window-handle":

            #get the gdk window and the corresponding c gpointer
            drawingareawnd = bus.window.get_property("window")
            drawingareawnd.ensure_native()
        #    self.left_window.realize()
         
            #make sure to call ensure_native before e.g. on realize
            if not drawingareawnd.has_native():
                print("Your window is gonna freeze as soon as you move or resize it...")
            #get the win32 handle

            # Assign the viewport
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", False)
            imagesink.set_window_handle(bus.hnd)
            if (self.stream_started):
            else:
                self.stream_started = True

    def color_swatch_new(self, str_color):
        rgba = Gdk.RGBA(0.5,0.5,1,1)
        area = Gtk.DrawingArea()
        area.set_size_request(1920, 1080)
        area.override_background_color(0, rgba)

        return area


def main():
    debug = True #& False
    Gst.init(None)
    App_Main(debug)
    GObject.threads_init()
    Gtk.main()

if __name__ == "__main__":
    main()