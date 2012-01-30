#!/usr/bin/env python
#Copyright (C) 2011 Emiliano Pastorino <epastorino@plan.ceibal.edu.uy>

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import os
import dbus

import lib.nxt as nxt

from gettext import gettext as _
from dbus.mainloop.glib import DBusGMainLoop


from plugin import Plugin

from TurtleArt.tapalette import make_palette
from TurtleArt.talogo import primitive_dictionary
from TurtleArt.taconstants import BLACK, WHITE, CONSTANTS
from TurtleArt.tautils import debug_output

from dbus.mainloop.glib import DBusGMainLoop
from lib.nxt.locator import BrickNotFoundError
from lib.nxt.motor import PORT_A, PORT_B, PORT_C, Motor, SynchronizedMotors
from lib.nxt.sensor import PORT_1, PORT_2, PORT_3, PORT_4, Touch, Color20, \
     Ultrasonic, Type

NXT_SENSORS = {'nxttouch': 0, 'nxtultrasonic': 1, 'nxtcolor': 2}

class Nxt_plugin(Plugin):

    def __init__(self, parent):
        self.tw = parent
        self.nxtbrick = False

	"""
        The following code will search for a NXT device.
        It is necessary to set the permission for these devices to 0666.
        You can do this by adding a rule to /etc/udev/rules.d

        As root (using sudo or su), copy the following text into a new file in
        /etc/udev/rules.d/99-lego.rules

        BUS=="usb", ATTRS{idVendor}=="0694", ATTRS{idProduct}=="0002", MODE="0666"

        You only have to do this once.
        """

        try:
            self.nxtbrick = nxt.locator.find_one_brick()
            debug_output("NXT found")
            
	except BrickNotFoundError:
            pass


    def setup(self):
        if self.nxtbrick and self.tw:
            palette = make_palette('nxt', ["#A0A0A0", "#606060"],
                        _('Palette of LEGO Mindstorms NXT objects'))

            primitive_dictionary['nxtturnmotor'] = self._prim_nxtturnmotor
            palette.add_block('nxtturnmotor',
                      style='basic-style-3arg',
                      label=[_('turn motor'), _('port'), _('power'),
                             _('rotations')],
                      default=['None', 1, 100],
                      help_string=_('Turn a motor'),
                      prim_name='nxtturnmotor')
            self.tw.lc.def_prim('nxtturnmotor', 3,
                lambda self, x, y, z:
                primitive_dictionary['nxtturnmotor'](x, y, z))

            primitive_dictionary['nxtporta'] = self._prim_nxtporta
            palette.add_block('nxtporta',
                      style='box-style',
                      label=_('PORT A'),
                      help_string=_('Port A'),
                      prim_name='nxtporta')
            self.tw.lc.def_prim('nxtporta', 0,
                lambda self: primitive_dictionary['nxtporta']())

            primitive_dictionary['nxtportb'] = self._prim_nxtportb
            palette.add_block('nxtportb',
                      style='box-style',
                      label=_('PORT B'),
                      help_string=_('Port B'),
                      prim_name='nxtportb')
            self.tw.lc.def_prim('nxtportb', 0,
                lambda self: primitive_dictionary['nxtportb']())

            primitive_dictionary['nxtportc'] = self._prim_nxtportc
            palette.add_block('nxtportc',
                      style='box-style',
                      label=_('PORT C'),
                      help_string=_('Port C'),
                      prim_name='nxtportc')
            self.tw.lc.def_prim('nxtportc', 0,
                lambda self: primitive_dictionary['nxtportc']())

            primitive_dictionary['nxtplaytone'] = self._prim_nxtplaytone
            palette.add_block('nxtplaytone',
                      style='basic-style-2arg',
                      label=[_('play tone'), _('freq'), _('time')],
                      default=[433, 500],
                      help_string=_('Play a tone'),
                      prim_name='nxtplaytone')
            self.tw.lc.def_prim('nxtplaytone', 2,
                lambda self, x, y: primitive_dictionary['nxtplaytone'](x, y))

            primitive_dictionary['nxttouch'] = self._prim_nxttouch
            palette.add_block('nxttouch',
                      style='box-style',
                      label=_('touch'),
                      help_string=_('Touch sensor'),
                      prim_name='nxttouch')
            self.tw.lc.def_prim('nxttouch', 0,
                lambda self: primitive_dictionary['nxttouch']())

            primitive_dictionary['nxtport1'] = self._prim_nxtport1
            palette.add_block('nxtport1',
                      style='box-style',
                      label=_('PORT 1'),
                      help_string=_('Port 1'),
                      prim_name='nxtport1')
            self.tw.lc.def_prim('nxtport1', 0,
                lambda self: primitive_dictionary['nxtport1']())

            primitive_dictionary['nxtport2'] = self._prim_nxtport2
            palette.add_block('nxtport2',
                      style='box-style',
                      label=_('PORT 2'),
                      help_string=_('Port 2'),
                      prim_name='nxtport2')
            self.tw.lc.def_prim('nxtport2', 0,
                lambda self: primitive_dictionary['nxtport2']())

            primitive_dictionary['nxtport3'] = self._prim_nxtport3
            palette.add_block('nxtport3',
                      style='box-style',
                      label=_('PORT 3'),
                      help_string=_('Port 3'),
                      prim_name='nxtport3')
            self.tw.lc.def_prim('nxtport3', 0,
                lambda self: primitive_dictionary['nxtport3']())

            primitive_dictionary['nxtport4'] = self._prim_nxtport4
            palette.add_block('nxtport4',
                      style='box-style',
                      label=_('PORT 4'),
                      help_string=_('Port 4'),
                      prim_name='nxtport4')
            self.tw.lc.def_prim('nxtport4', 0,
                lambda self: primitive_dictionary['nxtport4']())

            primitive_dictionary['nxtultrasonic'] = self._prim_nxtultrasonic
            palette.add_block('nxtultrasonic',
                      style='box-style',
                      label=_('ultrasonic'),
                      help_string=_('Distance sensor'),
                      prim_name='nxtultrasonic')
            self.tw.lc.def_prim('nxtultrasonic', 0,
                lambda self: primitive_dictionary['nxtultrasonic']())

            primitive_dictionary['nxtcolor'] = self._prim_nxtcolor
            palette.add_block('nxtcolor',
                      style='box-style',
                      label=_('color'),
                      help_string=_('Color sensor'),
                      prim_name='nxtcolor')
            self.tw.lc.def_prim('nxtcolor', 0,
                lambda self: primitive_dictionary['nxtcolor']())

            primitive_dictionary['nxtreadsensor'] = self._prim_nxtreadsensor
            palette.add_block('nxtreadsensor',
                      style='number-style-block',
                      label=[_('read'), _('sensor'), _('port')],
                      help_string=_('Read sensor output'),
                      prim_name='nxtreadsensor')
            self.tw.lc.def_prim('nxtreadsensor', 2,
                lambda self, x, y:
                primitive_dictionary['nxtreadsensor'](x, y))

            primitive_dictionary['nxtsyncmotors'] = self._prim_nxtsyncmotors
            palette.add_block('nxtsyncmotors',
                      style='basic-style-3arg',
                      label=[_('sync\nmotors'), _('power'), _('rotations'),
                             _('steering')],
                      default=[100, 0, 1],
                      help_string=_('Synchronize motors'),
                      prim_name='nxtsyncmotors')
            self.tw.lc.def_prim('nxtsyncmotors', 3,
                lambda self, x, y, z:
                primitive_dictionary['nxtsyncmotors'](x, y, z))

            primitive_dictionary['nxtstartmotor'] = self._prim_nxtstartmotor
            palette.add_block('nxtstartmotor',
                      style='basic-style-2arg',
                      label=[_('start motor'), _('port'), _('power')],
                      default=['None', 100],
                      help_string=_('Run motor forever'),
                      prim_name='nxtstartmotor')
            self.tw.lc.def_prim('nxtstartmotor', 2, lambda self, x, y:
                primitive_dictionary['nxtstartmotor'](x, y))

            primitive_dictionary['nxtbrake'] = self._prim_nxtbrake
            palette.add_block('nxtbrake',
                      style='basic-style-1arg',
                      label=_('brake motor'),
                      help_string=_('Brake specified motor'),
                      prim_name='nxtbrake')
            self.tw.lc.def_prim('nxtbrake', 1, lambda self, x:
                primitive_dictionary['nxtbrake'](x))

            primitive_dictionary['nxtsetcolor'] = self._prim_nxtsetcolor
            palette.add_block('nxtsetcolor',
                      style='basic-style-2arg',
                      label=[_('set light'), _('color'), _('port')],
                      help_string=_('Set color sensor light'),
                      prim_name='nxtsetcolor')
            self.tw.lc.def_prim('nxtsetcolor', 2, lambda self, x, y:
                primitive_dictionary['nxtsetcolor'](x, y))

    def start(self):
        # This gets called by the start button
        pass

    def stop(self):
        # This gets called by the stop button
        try:
            self._prim_nxtbrake(PORT_A)
            self._prim_nxtbrake(PORT_B)
            self._prim_nxtbrake(PORT_C)
        except:
            pass


    def goto_background(self):
        # This gets called when your process is sent to the background
        pass

    def return_to_foreground(self):
        # This gets called when your process returns from the background
        pass

    def quit(self):
        # This gets called by the quit button
        pass

    def _prim_nxtturnmotor(self, port, turns, power):
        return Motor(self.nxtbrick, port).turn(power, int(turns*360))

    def _prim_nxtsyncmotors(self, power, steering, turns):
        motorB = Motor(self.nxtbrick, PORT_B)
        motorC = Motor(self.nxtbrick, PORT_C)
        syncmotors = SynchronizedMotors(motorB, motorC, steering)
        return syncmotors.turn(power, int(turns*360))

    def _prim_nxtplaytone(self, freq, time):
        return self.nxtbrick.play_tone(freq, time)

    def _prim_nxttouch(self):
        return NXT_SENSORS['nxttouch']
        
    def _prim_nxtultrasonic(self):
        return NXT_SENSORS['nxtultrasonic']

    def _prim_nxtcolor(self):
        return NXT_SENSORS['nxtcolor']

    def _prim_nxtport1(self):
        return PORT_1

    def _prim_nxtport2(self):
        return PORT_2

    def _prim_nxtport3(self):
        return PORT_3

    def _prim_nxtport4(self):
        return PORT_4

    def _prim_nxtporta(self):
        return PORT_A

    def _prim_nxtportb(self):
        return PORT_B

    def _prim_nxtportc(self):
        return PORT_C

    def _prim_nxtreadsensor(self, sensor, port):
        """ Read sensor at specified port"""
        debug_output("_prim_nxtreadsensor: %s, %s"%(sensor, port))
        colors = [None, BLACK, CONSTANTS['blue'], CONSTANTS['green'],
                  CONSTANTS['yellow'], CONSTANTS['red'], WHITE]
        if sensor == NXT_SENSORS['nxtcolor']:
            return colors[Color20(self.nxtbrick, port).get_sample()]
        elif sensor == NXT_SENSORS['nxtultrasonic']:
            return Ultrasonic(self.nxtbrick, port).get_sample()
        elif sensor == NXT_SENSORS['nxttouch']:
            return Touch(self.nxtbrick, port).get_sample()
        else:
            return None

    def _prim_nxtstartmotor(self, port, power):
        return Motor(self.nxtbrick, port).weak_turn(power, 0)

    def _prim_nxtbrake(self, port):
        return Motor(self.nxtbrick, port).brake()

    def _prim_nxtsetcolor(self, color, port):
        if color == WHITE:
            color = Type.COLORFULL
        elif color == CONSTANTS['red']:
            color = Type.COLORRED
        elif color == CONSTANTS['green']:
            color = Type.COLORGREEN
        elif color == CONSTANTS['blue']:
            color = Type.COLORBLUE
        else:
            color = Type.COLORNONE
        Color20(self.nxtbrick, port).set_light_color(color)
