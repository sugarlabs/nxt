#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Emiliano Pastorino <epastorino@plan.ceibal.edu.uy>
# Copyright (C) 2011, 2012 Butiá Team butia@fing.edu.uy 
# Butia is a free open plataform for robotics projects
# www.fing.edu.uy/inco/proyectos/butia
# Universidad de la República del Uruguay
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
import time

from gettext import gettext as _

from plugins.plugin import Plugin

from TurtleArt.tapalette import make_palette
from TurtleArt.tapalette import palette_name_to_index
from TurtleArt.tapalette import special_block_colors
from TurtleArt.tapalette import palette_blocks
from TurtleArt.talogo import primitive_dictionary
from TurtleArt.taconstants import BLACK, WHITE, CONSTANTS, BOX_COLORS
from TurtleArt.tautils import debug_output


sys.path.insert(0, os.path.abspath('./plugins/nxt_plugin'))
import usb
import nxt
from nxt.locator import find_one_brick
from nxt.motor import PORT_A, PORT_B, PORT_C, Motor, SynchronizedMotors
from nxt.sensor import PORT_1, PORT_2, PORT_3, PORT_4, Touch, Color20, \
     Ultrasonic, Type, Sound

NXT_SENSORS = {_('touch'): 0, _('ultrasonic'): 1, _('color'): 2, _('light'): 3, _('sound'): 4}
NXT_MOTOR_PORTS = {_('PORT A'): PORT_A, _('PORT B'): PORT_B, _('PORT C'): PORT_C}
NXT_SENSOR_PORTS = {_('PORT 1'): PORT_1, _('PORT 2'): PORT_2, _('PORT 3'): PORT_3, _('PORT 4'): PORT_4}

colors = [None, BLACK, CONSTANTS['blue'], CONSTANTS['green'], CONSTANTS['yellow'], CONSTANTS['red'], WHITE]

COLOR_NOTPRESENT = ["#A0A0A0","#808080"]
COLOR_PRESENT = ["#00FF00","#008000"]

ERROR_BRICK = _('Please check the connection with the brick.')
ERROR_PORT = _('Please check the port.')
ERROR_POWER = _('The value of power must be between -127 to 127.')
ERROR = _('An error has occurred: check all connections and try to reconnect.')

MINIMO_INTERVALO = 0.2

class Nxt_plugin(Plugin):

    def __init__(self, parent):
        self.tw = parent
        self.nxtbrick = None

        """
        Adding a rule to /etc/udev/rules.d call: /etc/udev/rules.d/99-lego.rules
        with:

        BUS=="usb", ATTRS{idVendor}=="0694", ATTRS{idProduct}=="0002", MODE="0666"
        """

        self.nxtbrick = nxt.locator.find_one_brick()

        if self.nxtbrick:
            debug_output(_('NXT found'))
        else:
            debug_output(_('NXT not found'))

        self.anterior = time.time()

        self.res = -1

        self.motor_pos = 0

    def setup(self):

        # Palette of Motors
        palette_motors = make_palette('nxt-motors', ["#00FF00","#008000"],
                    _('Palette of LEGO NXT blocks of motors'))

        primitive_dictionary['nxtrefresh'] = self._prim_nxtrefresh
        palette_motors.add_block('nxtrefresh',
                     style='basic-style',
                     label=_('refresh NXT'),
                     prim_name='nxtrefresh',
                     help_string=_('Search for a connected NXT brick.'))
        self.tw.lc.def_prim('nxtrefresh', 0, lambda self :
            primitive_dictionary['nxtrefresh']())

        primitive_dictionary['nxtplaytone'] = self._prim_nxtplaytone
        palette_motors.add_block('nxtplaytone',
                  style='basic-style-2arg',
                  label=[_('play tone'), _('freq'), _('time')],
                  default=[433, 500],
                  help_string=_('Play a tone at freq for time.'),
                  prim_name='nxtplaytone')
        self.tw.lc.def_prim('nxtplaytone', 2,
            lambda self, x, y: primitive_dictionary['nxtplaytone'](x, y))

        primitive_dictionary['nxtturnmotor'] = self._prim_nxtturnmotor
        palette_motors.add_block('nxtturnmotor',
                  style='basic-style-3arg',
                  label=[_('turn motor\nrotations'), _('port'), _('power')],
                  default=['None', 1, 100],
                  help_string=_('turn a motor'),
                  prim_name='nxtturnmotor')
        self.tw.lc.def_prim('nxtturnmotor', 3,
            lambda self, x, y, z:
            primitive_dictionary['nxtturnmotor'](x, y, z))

        primitive_dictionary['nxtsyncmotors'] = self._prim_nxtsyncmotors
        palette_motors.add_block('nxtsyncmotors',
                  style='basic-style-3arg',
                  label=[_('sync motors\nsteering'), _('power'), _('rotations')],
                  default=[100, 0, 1],
                  help_string=_('synchronize two motors'),
                  prim_name='nxtsyncmotors')
        self.tw.lc.def_prim('nxtsyncmotors', 3,
            lambda self, x, y, z:
            primitive_dictionary['nxtsyncmotors'](x, y, z))

        primitive_dictionary['nxtporta'] = self._prim_nxtporta
        palette_motors.add_block('nxtporta',
                  style='box-style',
                  label=_('PORT A'),
                  help_string=_('PORT A of the brick'),
                  prim_name='nxtporta')
        self.tw.lc.def_prim('nxtporta', 0,
            lambda self: primitive_dictionary['nxtporta']())

        primitive_dictionary['nxtportb'] = self._prim_nxtportb
        palette_motors.add_block('nxtportb',
                  style='box-style',
                  label=_('PORT B'),
                  help_string=_('PORT B of the brick'),
                  prim_name='nxtportb')
        self.tw.lc.def_prim('nxtportb', 0,
            lambda self: primitive_dictionary['nxtportb']())

        primitive_dictionary['nxtportc'] = self._prim_nxtportc
        palette_motors.add_block('nxtportc',
                  style='box-style',
                  label=_('PORT C'),
                  help_string=_('PORT C of the brick'),
                  prim_name='nxtportc')
        self.tw.lc.def_prim('nxtportc', 0,
            lambda self: primitive_dictionary['nxtportc']())

        primitive_dictionary['nxtstartmotor'] = self._prim_nxtstartmotor
        palette_motors.add_block('nxtstartmotor',
                  style='basic-style-2arg',
                  label=[_('start motor'), _('port'), _('power')],
                  default=['None', 100],
                  help_string=_('Run a motor forever.'),
                  prim_name='nxtstartmotor')
        self.tw.lc.def_prim('nxtstartmotor', 2, lambda self, x, y:
            primitive_dictionary['nxtstartmotor'](x, y))

        primitive_dictionary['nxtbrake'] = self._prim_nxtbrake
        palette_motors.add_block('nxtbrake',
                  style='basic-style-1arg',
                  label=_('brake motor'),
                  default=['None'],
                  help_string=_('Stop a specified motor.'),
                  prim_name='nxtbrake')
        self.tw.lc.def_prim('nxtbrake', 1, lambda self, x:
            primitive_dictionary['nxtbrake'](x))

        primitive_dictionary['nxtmotorreset'] = self._prim_nxtmotorreset
        palette_motors.add_block('nxtmotorreset',
                  style='basic-style-1arg',
                  label=_('reset motor'),
                  default=['None'],
                  help_string=_('Reset the motor counter.'),
                  prim_name='nxtmotorreset')
        self.tw.lc.def_prim('nxtmotorreset', 1, lambda self, x:
            primitive_dictionary['nxtmotorreset'](x))

        primitive_dictionary['nxtmotorposition'] = self._prim_nxtmotorposition
        palette_motors.add_block('nxtmotorposition',
                  style='number-style-1arg',
                  label=_('motor position'),
                  default=['None'],
                  help_string=_('Get the motor position.'),
                  prim_name='nxtmotorposition')
        self.tw.lc.def_prim('nxtmotorposition', 1, lambda self, x:
            primitive_dictionary['nxtmotorposition'](x))

        # Palette of Sensors
        palette_sensors = make_palette('nxt-sensors', ["#00FF00","#008000"],
                    _('Palette of LEGO NXT blocks of sensors'))

        primitive_dictionary['nxtport1'] = self._prim_nxtport1
        palette_sensors.add_block('nxtport1',
                  style='box-style',
                  label=_('PORT 1'),
                  help_string=_('PORT 1 of the brick'),
                  prim_name='nxtport1')
        self.tw.lc.def_prim('nxtport1', 0,
            lambda self: primitive_dictionary['nxtport1']())

        primitive_dictionary['nxtreadsensor'] = self._prim_nxtreadsensor
        palette_sensors.add_block('nxtreadsensor',
                  style='number-style-block',
                  label=[_('read'), _('sensor'), _('port')],
                  help_string=_('Read sensor output.'),
                  prim_name='nxtreadsensor')
        self.tw.lc.def_prim('nxtreadsensor', 2,
            lambda self, x, y:
            primitive_dictionary['nxtreadsensor'](x, y))

        primitive_dictionary['nxtport2'] = self._prim_nxtport2
        palette_sensors.add_block('nxtport2',
                  style='box-style',
                  label=_('PORT 2'),
                  help_string=_('PORT 2 of the brick'),
                  prim_name='nxtport2')
        self.tw.lc.def_prim('nxtport2', 0,
            lambda self: primitive_dictionary['nxtport2']())

        primitive_dictionary['nxtcolor'] = self._prim_nxtcolor
        palette_sensors.add_block('nxtcolor',
                  style='box-style',
                  label=_('color'),
                  help_string=_('color sensor'),
                  prim_name='nxtcolor')
        self.tw.lc.def_prim('nxtcolor', 0,
            lambda self: primitive_dictionary['nxtcolor']())

        primitive_dictionary['nxtlight'] = self._prim_nxtlight
        palette_sensors.add_block('nxtlight',
                  style='box-style',
                  label=_('light'),
                  help_string=_('light sensor'),
                  prim_name='nxtlight')
        self.tw.lc.def_prim('nxtlight', 0,
            lambda self: primitive_dictionary['nxtlight']())

        primitive_dictionary['nxtport3'] = self._prim_nxtport3
        palette_sensors.add_block('nxtport3',
                  style='box-style',
                  label=_('PORT 3'),
                  help_string=_('PORT 3 of the brick'),
                  prim_name='nxtport3')
        self.tw.lc.def_prim('nxtport3', 0,
            lambda self: primitive_dictionary['nxtport3']())

        primitive_dictionary['nxttouch'] = self._prim_nxttouch
        palette_sensors.add_block('nxttouch',
                  style='box-style',
                  label=_('touch'),
                  help_string=_('touch sensor'),
                  prim_name='nxttouch')
        self.tw.lc.def_prim('nxttouch', 0,
            lambda self: primitive_dictionary['nxttouch']())

        primitive_dictionary['nxtultrasonic'] = self._prim_nxtultrasonic
        palette_sensors.add_block('nxtultrasonic',
                  style='box-style',
                  label=_('ultrasonic'),
                  help_string=_('distance sensor'),
                  prim_name='nxtultrasonic')
        self.tw.lc.def_prim('nxtultrasonic', 0,
            lambda self: primitive_dictionary['nxtultrasonic']())

        primitive_dictionary['nxtport4'] = self._prim_nxtport4
        palette_sensors.add_block('nxtport4',
                  style='box-style',
                  label=_('PORT 4'),
                  help_string=_('PORT 4 of the brick'),
                  prim_name='nxtport4')
        self.tw.lc.def_prim('nxtport4', 0,
            lambda self: primitive_dictionary['nxtport4']())

        primitive_dictionary['nxtsound'] = self._prim_nxtsound
        palette_sensors.add_block('nxtsound',
                  style='box-style',
                  label=_('sound'),
                  help_string=_('sound sensor'),
                  prim_name='nxtsound')
        self.tw.lc.def_prim('nxtsound', 0,
            lambda self: primitive_dictionary['nxtsound']())

        primitive_dictionary['nxtsetcolor'] = self._prim_nxtsetcolor
        palette_sensors.add_block('nxtsetcolor',
                  style='basic-style-2arg',
                  label=[_('set light'), _('color'), _('port')],
                  help_string=_('Set color sensor light.'),
                  prim_name='nxtsetcolor')
        self.tw.lc.def_prim('nxtsetcolor', 2, lambda self, x, y:
            primitive_dictionary['nxtsetcolor'](x, y))

        self.change_color_blocks()


    def start(self):
        # This gets called by the start button
        pass

    def stop(self):
        # This gets called by the stop button
        if self.nxtbrick:
            try:
                Motor(self.nxtbrick, PORT_A).idle()
                Motor(self.nxtbrick, PORT_B).idle()
                Motor(self.nxtbrick, PORT_C).idle()
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
        if self.nxtbrick:
            if (port in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port]
                if not((power < -127) or (power > 127)):
                    try:
                        m = Motor(self.nxtbrick, port)
                        m.turn(power, int(turns*360), brake=True)
                        m.brake()
                    except:
                        return ERROR
                else:
                    return ERROR_POWER
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtsyncmotors(self, power, steering, turns):
        if self.nxtbrick:
            if not((power < -127) or (power > 127)):
                try:
                    motorB = Motor(self.nxtbrick, PORT_B)
                    motorC = Motor(self.nxtbrick, PORT_C)
                    syncmotors = SynchronizedMotors(motorB, motorC, steering)
                    syncmotors.turn(power, int(turns*360))
                except:
                    return ERROR
            else:
                return ERROR_POWER
        else:
            return ERROR_BRICK

    def _prim_nxtplaytone(self, freq, time):
        if self.nxtbrick:
            try:
                self.nxtbrick.play_tone(freq, time)
            except:
                return ERROR
        else:
            return ERROR_BRICK

    def _prim_nxttouch(self):
        return _('touch')

    def _prim_nxtultrasonic(self):
        return _('ultrasonic')

    def _prim_nxtcolor(self):
        return _('color')

    def _prim_nxtlight(self):
        return _('light')

    def _prim_nxtsound(self):
        return _('sound')

    def _prim_nxtport1(self):
        return _('PORT 1')

    def _prim_nxtport2(self):
        return _('PORT 2')

    def _prim_nxtport3(self):
        return _('PORT 3')

    def _prim_nxtport4(self):
        return _('PORT 4')

    def _prim_nxtporta(self):
        return _('PORT A')

    def _prim_nxtportb(self):
        return _('PORT B')

    def _prim_nxtportc(self):
        return _('PORT C')

    def _prim_nxtreadsensor(self, sensor, port):
        """ Read sensor at specified port"""
        if (port in NXT_SENSOR_PORTS):
            actual = time.time()
            if ((actual - self.anterior) > MINIMO_INTERVALO) and (self.nxtbrick):
                self.anterior = actual
                port = NXT_SENSOR_PORTS[port]
                try:
                    if sensor == _('color'):
                        self.res = colors[Color20(self.nxtbrick, port).get_sample()]
                    elif sensor == _('light'):
                        self.res = int(Color20(self.nxtbrick, port).get_light())
                    elif sensor == _('ultrasonic'):
                        self.res = Ultrasonic(self.nxtbrick, port).get_sample()
                    elif sensor == _('touch'):
                        self.res = Touch(self.nxtbrick, port).get_sample()
                    elif sensor == _('sound'):
                        self.res = Sound(self.nxtbrick, port).get_sample()
                except:
                    pass
            return self.res
        else:
            return ERROR_PORT

    def _prim_nxtstartmotor(self, port, power):
        if self.nxtbrick:
            if (port in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port]
                if not((power < -127) or (power > 127)):
                    try:
                        m = Motor(self.nxtbrick, port)
                        m.weak_turn(power, 0)
                    except:
                        return ERROR
                else:
                    return ERROR_POWER
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtbrake(self, port):
        if self.nxtbrick:
            if (port in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port]
                try:
                    m = Motor(self.nxtbrick, port)
                    m.brake()
                except:
                    return ERROR
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtsetcolor(self, color, port):
        if self.nxtbrick:
            if (port in NXT_SENSOR_PORTS):
                port = NXT_SENSOR_PORTS[port]
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
                try:
                    Color20(self.nxtbrick, port).set_light_color(color)
                except:
                    return ERROR
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtmotorreset(self, port):
        if self.nxtbrick:
            if (port in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port]
                try:
                    m = Motor(self.nxtbrick, port)
                    t = m.get_tacho()
                    self.motor_pos = t.tacho_count
                    m.idle()
                except:
                    return ERROR
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtmotorposition(self, port):
        if self.nxtbrick:
            if (port in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port]
                try:
                    m = Motor(self.nxtbrick, port)
                    t = m.get_tacho()
                    d = t.tacho_count - self.motor_pos
                    return d
                except:
                    return ERROR
            else:
                return ERROR_PORT
        else:
            return ERROR_BRICK

    def _prim_nxtrefresh(self):

        try:
            self.nxtbrick.get_device_info()
        except:
            self.nxtbrick = nxt.locator.find_one_brick()

        self.change_color_blocks()

        self.tw.show_toolbar_palette(palette_name_to_index('nxt-motors'), regenerate=True, show=False)
        self.tw.show_toolbar_palette(palette_name_to_index('nxt-sensors'), regenerate=True, show=False)

    def change_color_blocks(self):
        motors_blocks = palette_blocks[palette_name_to_index('nxt-motors')]
        sensors_blocks = palette_blocks[palette_name_to_index('nxt-sensors')]
        nxt_palette_blocks = motors_blocks + sensors_blocks

        for block in self.tw.block_list.list:
            if block.type in ['proto', 'block']:
                if block.name in nxt_palette_blocks:
                    if (self.nxtbrick) or (block.name == 'nxtrefresh'):
                        BOX_COLORS[block.name] = COLOR_PRESENT[:]
                    else:
                        BOX_COLORS[block.name] = COLOR_NOTPRESENT[:]
                    block.refresh()

