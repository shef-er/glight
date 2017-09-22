#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk

import glight

class GlightUi:

    def __init__(self):
        self.gladefile = "glight-ui.glade"
        self.builder = Gtk.Builder()

        self.registry = None # type: glight.GDeviceRegistry
        self.proxy = None # type: glight.GlightController

        self.device_states = None

        self.selected_device = None
        self.devices = None
        self.device_store = None
        self.window = None

        self.device_store = None
        self.device_tree = None
        self.btn_color_field = None
        self.btn_color_complete = None
        self.btn_color_breathe = None

        self.btn_set = None
        self.lbl_not_supported = None

        self.adj_speed_breathe = None
        self.adj_brightness_breathe = None
        self.adj_speed_cycle = None
        self.adj_brightness_cycle = None

        self.pages = ["complete", "fields", "breathe", "cycle"]

        self.setup_backend()
        self.init_ui()

    def init_ui(self):
        self.builder.add_from_file(self.gladefile)

        self.window = self.builder.get_object("window")
        self.window.set_title("GLight-UI")

        self.device_store = self.builder.get_object("devices")  # type: ListStore
        self.device_tree = self.builder.get_object("device_tree")

        self.btn_color_complete = self.builder.get_object("btn_color_complete")
        self.btn_color_breathe = self.builder.get_object("btn_color_breathe")

        self.btn_set = {}
        self.lbl_not_supported = {}
        for page in self.pages:
            self.btn_set[page] = self.builder.get_object("btn_{0}_set".format(page))
            self.lbl_not_supported[page] = self.builder.get_object("lbl_not_supported_{0}".format(page))

        self.btn_color_field = []
        for i in range(1, 6):
            self.btn_color_field.append(self.builder.get_object("btn_color_field_{0}".format(i)))

        self.adj_speed_breathe = self.builder.get_object("adj_speed_breathe")
        self.adj_brightness_breathe = self.builder.get_object("adj_brightness_breathe")
        self.adj_speed_cycle = self.builder.get_object("adj_speed_cycle")
        self.adj_brightness_cycle = self.builder.get_object("adj_brightness_cycle")

        self.sync_ui()

        self.builder.connect_signals(self)
        self.window.show()

    def setup_backend(self):
        self.proxy = glight.GlightController(glight.GlightController.BACKEND_DBUS)
        self.registry = glight.GDeviceRegistry()

    def sync_ui(self):
        self.device_store.clear()
        self.devices = self.proxy.list_devices()
        for device_name_short, device_name in self.devices.iteritems():
            print "Added '{0}' ({1})".format(device_name_short, device_name)
            self.device_store.append([device_name, device_name_short])

    def get_device_base(self, device_name_short):
        """
        :param device_name_short: str
        :return: glight.GDevice
        """
        return self.registry.get_known_device(device_name_short)

    def update_ui(self):
        """"""

        if self.selected_device is None:
            pass
        else:
            device = self.get_device_base(self.selected_device) # type: glight.GDevice

            self.adj_brightness_breathe.set_lower(device.bright_spec.min_value)
            self.adj_brightness_breathe.set_upper(device.bright_spec.max_value)
            self.adj_brightness_breathe.set_value(device.bright_spec.max_value)

            self.adj_speed_breathe.set_lower(device.speed_spec.min_value)
            self.adj_speed_breathe.set_upper(device.speed_spec.max_value)
            self.adj_speed_breathe.set_value(device.speed_spec.min_value)

            self.adj_brightness_cycle.set_lower(device.bright_spec.min_value)
            self.adj_brightness_cycle.set_upper(device.bright_spec.max_value)
            self.adj_brightness_cycle.set_value(device.bright_spec.max_value)

            self.adj_speed_cycle.set_lower(device.speed_spec.min_value)
            self.adj_speed_cycle.set_upper(device.speed_spec.max_value)
            self.adj_speed_cycle.set_value(device.speed_spec.min_value)

            fields_supported = device.field_spec.max_value > 1
            self.btn_set["fields"].set_sensitive(fields_supported)
            self.lbl_not_supported["fields"].set_visible(not fields_supported)

            # print device.speed_spec.min_value
            # print device.speed_spec.max_value

            if self.selected_device in self.device_states:
                state = self.device_states[self.selected_device] # type: glight.GDeviceState

                #for i, color in enumerate(state.colors):
                for i in range(0, len(self.btn_color_field)+1):
                    if len(state.colors) > i:
                        color = state.colors[i]
                    else:
                        color = "ffffff"
                    c = self.get_rgba_from_hex(color)
                    print "[{0}] {1}".format(i, color)

                    if i == 0:
                        self.btn_color_complete.set_rgba(c)
                    else:
                        if len(self.btn_color_field) > i-1:
                            self.btn_color_field[i-1].set_rgba(c)


    def get_rgba_from_hex(self, col_hex):
        """"""
        # rgb = tuple(int(col_hex[i:i + 2], 16) for i in (0, 2, 4))
        # return Gdk.Color(rgb[0], rgb[1], rgb[2])

        rgba = Gdk.RGBA()
        if col_hex is None:
            rgba.parse("#ffffff")
        else:
            rgba.parse("#"+col_hex)
        return rgba

    def get_color_hex_from_button(self, col_btn):
        """"""
        return self.convert_gdk_col_to_string(col_btn.get_rgba())

    def convert_gdk_col_to_string(self, gdk_col):
        """"""
        return "{:02x}{:02x}{:02x}".format(
            int(round(gdk_col.red   * 255)),
            int(round(gdk_col.green * 255)),
            int(round(gdk_col.blue  * 255)))

    def on_window_destroy(self, object, data=None):
        Gtk.main_quit()

    def on_store_settings(self, *args, **kwargs):
        """"""
        self.proxy.save_state()

    def on_restore_settings(self, *args, **kwargs):
        """"""
        state = self.proxy.get_state()
        print state
        self.proxy.load_state()

    def on_device_selected(self, tree_selection):
        """"""
        selection = tree_selection.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            print("You selected '{0}' ({1})".format(model[treeiter][0], model[treeiter][1]))
            self.selected_device = model[treeiter][1]
        else:
            self.selected_device = None

        self.device_states = self.proxy.get_state()

        self.update_ui()

    def on_color_change(self, btn):
        """
        :param btn: Gtk.ColorButton
        :return:
        """
        print btn.get_name()
        print btn.get_color()
        print self.get_color_hex_from_button(btn)

    def on_complete_set(self, *args, **kwargs):
        """"""
        col = self.get_color_hex_from_button(self.btn_color_complete)
        self.proxy.set_colors(self.selected_device, [col])

    def on_fields_set(self, *args, **kwargs):
        """"""
        cols = []
        for btn in self.btn_color_field:
            cols.append(self.get_color_hex_from_button(btn))

        self.proxy.set_colors(self.selected_device, cols)

    def on_breathe_set(self, *args, **kwargs):
        """"""
        col = self.get_color_hex_from_button(self.btn_color_breathe)
        speed = int(self.adj_speed_breathe.get_value())
        brightness = int(self.adj_brightness_breathe.get_value())

        self.proxy.set_breathe(self.selected_device, col, speed, brightness)

    def on_cycle_set(self, *args, **kwargs):
        """"""
        speed = int(self.adj_speed_cycle.get_value())
        brightness = int(self.adj_brightness_cycle.get_value())

        self.proxy.set_cycle(self.selected_device, speed, brightness)


if __name__ == "__main__":
  main = GlightUi()
  Gtk.main()