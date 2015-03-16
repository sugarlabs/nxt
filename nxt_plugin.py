#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Emiliano Pastorino <epastorino@plan.ceibal.edu.uy>
# Copyright (C) 2011, 2015 Butia Team butia@fing.edu.uy
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

from gettext import gettext as _

from plugins.plugin import Plugin

from TurtleArt.tapalette import make_palette
from TurtleArt.tapalette import palette_name_to_index
from TurtleArt.tapalette import special_block_colors
from TurtleArt.tapalette import palette_blocks
from TurtleArt.talogo import logoerror
from TurtleArt.taconstants import BLACK, WHITE, CONSTANTS, MACROS
from TurtleArt.taprimitive import Primitive, ArgSlot, ConstantArg
from TurtleArt.tatype import TYPE_INT, TYPE_STRING, TYPE_NUMBER

sys.path.insert(0, os.path.abspath('./plugins/nxt_plugin'))
import usb
from nxt.motor import PORT_A, PORT_B, PORT_C, Motor, SynchronizedMotors
from nxt.sensor import PORT_1, PORT_2, PORT_3, PORT_4, Touch, Color20, Ultrasonic, Type, Sound, Light
from nxt.usbsock import USBSock, ID_VENDOR_LEGO, ID_PRODUCT_NXT
from nxt.bluesock import BlueSock
try:
    import bluetooth
except:
    bluetooth = None

NXT_MOTOR_PORTS = {'A': PORT_A, 'B': PORT_B, 'C': PORT_C}
NXT_SENSOR_PORTS = {1: PORT_1, 2: PORT_2, 3: PORT_3, 4: PORT_4}
NXT_SENSORS = [_('button'), _('distance'), _('color'), _('light'), _('sound'), _('gray')]

colors = [None, BLACK, CONSTANTS['blue'], CONSTANTS['green'], CONSTANTS['yellow'], CONSTANTS['red'], WHITE]

COLOR_NOTPRESENT = ["#A0A0A0","#808080"]
COLOR_PRESENT = ["#00FF00","#008000"]

ERROR_BRICK = _('Please check the connection with the brick')
ERROR_PORT_M = _("Invalid port '%s'. Port must be: PORT A, B or C")
ERROR_PORT_S = _("Invalid port '%s'. Port must be: PORT 1, 2, 3 or 4")
ERROR_POWER = _('The value of power must be between -127 to 127')
ERROR_NO_NUMBER = _("The parameter must be a integer, not '%s'")
ERROR_UNKNOW_SENSOR = ("Unknow '%s' sensor")
ERROR_GENERIC = _('An error has occurred: check all connections and try to reconnect')
ERROR = -1
BRICK_FOUND = _('NXT found %s bricks')
BRICK_NOT_FOUND = _('NXT not found')
BRICK_INDEX_NOT_FOUND = _('Brick number %s was not found')
SYNC_STRING1 = '   \n'
SYNC_STRING2 = '         \n'


class Nxt_plugin(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self)
        self.tw = parent
        self._bricks = []
        self.active_nxt = 0
        self._motor_pos = {}

    def setup(self):

        # Palette of Motors
        palette_motors = make_palette('nxt-motors', COLOR_NOTPRESENT,
                                    _('Palette of LEGO NXT blocks of motors'),
                                    translation=_('nxt-motors'))

        palette_motors.add_block('nxtrefresh',
                     style='basic-style',
                     label=_('refresh NXT'),
                     prim_name='nxtrefresh',
                     help_string=_('Search for a connected NXT brick.'))
        self.tw.lc.def_prim('nxtrefresh', 0,
            Primitive(self.refresh))
        special_block_colors['nxtrefresh'] = COLOR_PRESENT[:]

        palette_motors.add_block('nxtselect',
                          style='basic-style-1arg',
                          default = 1,
                          label=_('NXT'),
                          help_string=_('set current NXT device'),
                          prim_name = 'nxtselect')
        self.tw.lc.def_prim('nxtselect', 1,
            Primitive(self.select, arg_descs=[ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtcount',
                          style='box-style',
                          label=_('number of NXTs'),
                          help_string=_('number of NXT devices'),
                          prim_name = 'nxtcount')
        self.tw.lc.def_prim('nxtcount', 0,
            Primitive(self.count, TYPE_INT))

        palette_motors.add_block('nxtbrickname',
                  style='number-style-1arg',
                  label=_('brick name'),
                  default=[1],
                  help_string=_('Get the name of a brick.'),
                  prim_name='nxtbrickname')
        self.tw.lc.def_prim('nxtbrickname', 1,
            Primitive(self.brickname, TYPE_STRING, [ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtplaytone',
                  style='basic-style-2arg',
                  label=[_('play tone'), _('frequency'), _('time')],
                  default=[433, 500],
                  help_string=_('Play a tone at frequency for time.'),
                  prim_name='nxtplaytone')
        self.tw.lc.def_prim('nxtplaytone', 2,
            Primitive(self.playtone, arg_descs=[ArgSlot(TYPE_NUMBER), ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtsyncmotors',
                  style='basic-style-2arg',
                  label=[_('synchronize %s motors') % SYNC_STRING1, _('power'), _('rotations')],
                  default=[100, 1],
                  help_string=_('synchronize two motors connected in PORT B and PORT C'),
                  prim_name='nxtsyncmotors')
        self.tw.lc.def_prim('nxtsyncmotors', 2,
            Primitive(self.syncmotors, arg_descs=[ArgSlot(TYPE_NUMBER), ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtsyncmotorsforever',
                  style='basic-style-1arg',
                  label=[_('synchronize %s motors') % SYNC_STRING2, _('power')],
                  default=[100],
                  help_string=_('synchronize two motors connected in PORT B and PORT C'),
                  prim_name='nxtsyncmotorsforever')
        self.tw.lc.def_prim('nxtsyncmotorsforever', 1,
            Primitive(self.syncmotorsforever, arg_descs=[ArgSlot(TYPE_NUMBER)]))

        global CONSTANTS
        CONSTANTS['PORT A'] = 'A'
        palette_motors.add_block('nxtporta',
                  style='box-style',
                  label=_('PORT %s') % 'A',
                  help_string=_('PORT %s of the brick') % 'A',
                  prim_name='nxtporta')
        self.tw.lc.def_prim('nxtporta', 0,
            Primitive(CONSTANTS.get, TYPE_STRING, [ConstantArg('PORT A')]))

        CONSTANTS['PORT B'] = 'B'
        palette_motors.add_block('nxtportb',
                  style='box-style',
                  label=_('PORT %s') % 'B',
                  help_string=_('PORT %s of the brick') % 'B',
                  prim_name='nxtportb')
        self.tw.lc.def_prim('nxtportb', 0,
            Primitive(CONSTANTS.get, TYPE_STRING, [ConstantArg('PORT B')]))

        CONSTANTS['PORT C'] = 'C'
        palette_motors.add_block('nxtportc',
                  style='box-style',
                  label=_('PORT %s') % 'C',
                  help_string=_('PORT %s of the brick') % 'C',
                  prim_name='nxtportc')
        self.tw.lc.def_prim('nxtportc', 0,
            Primitive(CONSTANTS.get, TYPE_STRING, [ConstantArg('PORT C')]))

        palette_motors.add_block('nxtstartmotor',
                  style='basic-style-2arg',
                  label=[_('start motor'), _('port'), _('power')],
                  default=['A', 100],
                  help_string=_('Run a motor forever.'),
                  prim_name='nxtstartmotor')
        self.tw.lc.def_prim('nxtstartmotor', 2,
            Primitive(self.startmotor, arg_descs=[ArgSlot(TYPE_STRING), ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtbrake',
                  style='basic-style-1arg',
                  label=_('brake motor'),
                  default=['A'],
                  help_string=_('Stop a specified motor.'),
                  prim_name='nxtbrake')
        self.tw.lc.def_prim('nxtbrake', 1,
            Primitive(self.brake, arg_descs=[ArgSlot(TYPE_STRING)]))

        palette_motors.add_block('nxtturnmotor',
                  style='basic-style-3arg',
                  hidden=True,
                  label=[_('turn motor %s') % '\n\n', _('port'), _('rotations'), _('power')],
                  default=['A', 1, 100],
                  help_string=_('turn a motor'),
                  prim_name='nxtturnmotor')
        self.tw.lc.def_prim('nxtturnmotor', 3,
            Primitive(self.turnmotor, arg_descs=[ArgSlot(TYPE_STRING), ArgSlot(TYPE_NUMBER), ArgSlot(TYPE_NUMBER)]))

        palette_motors.add_block('nxtturnmotorMacro',
                          style='basic-style-extended-vertical',
                          label= _('turn motor %s') % '',
                          help_string=_('turn a motor'))

        global MACROS
        MACROS['nxtturnmotorMacro'] = [[0, 'nxtturnmotor', 0, 0, [None, 1, 2, 3, None]],
                                          [1, ['string', 'A'], 0, 0, [0, None]],
                                          [2, ['number', 1], 0, 0, [0, None]],
                                          [3, ['number', 100], 0, 0, [0, None]]
                                         ]

        palette_motors.add_block('nxtmotorreset',
                  style='basic-style-1arg',
                  label=_('reset motor'),
                  default=['A'],
                  help_string=_('Reset the motor counter.'),
                  prim_name='nxtmotorreset')
        self.tw.lc.def_prim('nxtmotorreset', 1,
            Primitive(self.motorreset, arg_descs=[ArgSlot(TYPE_STRING)]))

        palette_motors.add_block('nxtmotorposition',
                  style='number-style-1arg',
                  label=_('motor position'),
                  default=['A'],
                  help_string=_('Get the motor position.'),
                  prim_name='nxtmotorposition')
        self.tw.lc.def_prim('nxtmotorposition', 1,
            Primitive(self.motorposition, TYPE_INT, arg_descs=[ArgSlot(TYPE_STRING)]))

        ######################### Palette of Sensors ###########################

        palette_sensors = make_palette('nxt-sensors', COLOR_NOTPRESENT,
                                    _('Palette of LEGO NXT blocks of sensors'),
                                    translation=_('nxt-sensors'))

        palette_sensors.add_block('nxtlight',
                  style='number-style-1arg',
                  label=_('light'),
                  default=[1],
                  help_string=_('light sensor'),
                  prim_name='nxtlight')
        self.tw.lc.def_prim('nxtlight', 1,
            Primitive(self.getLight, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtgray',
                  style='number-style-1arg',
                  label=_('gray'),
                  default=[1],
                  help_string=_('gray sensor'),
                  prim_name='nxtgray')
        self.tw.lc.def_prim('nxtgray', 1,
            Primitive(self.getGray, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtbutton',
                  style='number-style-1arg',
                  label=_('button'),
                  default=[1],
                  help_string=_('button sensor'),
                  prim_name='nxtbutton')
        self.tw.lc.def_prim('nxtbutton', 1,
            Primitive(self.getButton, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtdistance',
                  style='number-style-1arg',
                  label=_('distance'),
                  default=[1],
                  help_string=_('distance sensor'),
                  prim_name='nxtdistance')
        self.tw.lc.def_prim('nxtdistance', 1,
            Primitive(self.getDistance, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtsound',
                  style='number-style-1arg',
                  label=_('sound'),
                  default=[1],
                  help_string=_('sound sensor'),
                  prim_name='nxtsound')
        self.tw.lc.def_prim('nxtsound', 1,
            Primitive(self.getSound, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtcolor',
                  style='number-style-1arg',
                  label=_('color'),
                  default=[1],
                  help_string=_('color sensor'),
                  prim_name='nxtcolor')
        self.tw.lc.def_prim('nxtcolor', 1,
            Primitive(self.getColor, TYPE_INT, [ArgSlot(TYPE_INT)]))

        CONSTANTS['PORT 1'] = 1
        palette_sensors.add_block('nxtport1',
                  style='box-style',
                  label=_('PORT %s') % 1,
                  help_string=_('PORT %s of the brick') % 1,
                  prim_name='nxtport1')
        self.tw.lc.def_prim('nxtport1', 0,
            Primitive(CONSTANTS.get, TYPE_INT, [ConstantArg('PORT 1')]))

        CONSTANTS['PORT 2'] = 2
        palette_sensors.add_block('nxtport2',
                  style='box-style',
                  label=_('PORT %s') % 2,
                  help_string=_('PORT %s of the brick') % 2,
                  prim_name='nxtport2')
        self.tw.lc.def_prim('nxtport2', 0,
            Primitive(CONSTANTS.get, TYPE_INT, [ConstantArg('PORT 2')]))

        CONSTANTS['PORT 3'] = 3
        palette_sensors.add_block('nxtport3',
                  style='box-style',
                  label=_('PORT %s') % 3,
                  help_string=_('PORT %s of the brick') % 3,
                  prim_name='nxtport3')
        self.tw.lc.def_prim('nxtport3', 0,
            Primitive(CONSTANTS.get, TYPE_INT, [ConstantArg('PORT 3')]))

        CONSTANTS['PORT 4'] = 4
        palette_sensors.add_block('nxtport4',
                  style='box-style',
                  label=_('PORT %s') % 4,
                  help_string=_('PORT %s of the brick') % 4,
                  prim_name='nxtport4')
        self.tw.lc.def_prim('nxtport4', 0,
            Primitive(CONSTANTS.get, TYPE_INT, [ConstantArg('PORT 4')]))

        palette_sensors.add_block('nxtbattery',
                  style='box-style',
                  label=_('battery level'),
                  help_string=_('Get the battery level of the brick in millivolts'),
                  prim_name='nxtbattery')
        self.tw.lc.def_prim('nxtbattery', 0,
            Primitive(self.battery, TYPE_INT))

        palette_sensors.add_block('nxtlightcolor',
                  style='number-style-1arg',
                  label=_('color as light'),
                  default=[1],
                  help_string=_('use color sensor as light sensor'),
                  prim_name='nxtlightcolor')
        self.tw.lc.def_prim('nxtlightcolor', 1,
            Primitive(self.getLightColor, TYPE_INT, [ArgSlot(TYPE_INT)]))

        palette_sensors.add_block('nxtsetcolor',
                  style='basic-style-2arg',
                  label=[_('set light'), _('port'), _('color')],
                  default=[1],
                  help_string=_('Set color sensor light.'),
                  prim_name='nxtsetcolor')
        self.tw.lc.def_prim('nxtsetcolor', 2,
            Primitive(self.setcolor, arg_descs=[ArgSlot(TYPE_INT), ArgSlot(TYPE_INT)]))

    ############################### Turtle signals ############################

    def stop(self):
        self._idle_motors()

    def quit(self):
        self._idle_motors()
        self._close_bricks()

    ################################# Primitives ##############################

    def turnmotor(self, port, turns, power):
        if self._bricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                if not((power < -127) or (power > 127)):
                    if turns < 0:
                        turns = abs(turns)
                        power = -1 * power
                    try:
                        m = Motor(self._bricks[self.active_nxt], port)
                        m.turn(power, int(turns*360), brake=True)
                        m.brake()
                    except:
                        raise logoerror(ERROR_GENERIC)
                else:
                    raise logoerror(ERROR_POWER)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def syncmotors(self, power, turns):
        if self._bricks:
            if not((power < -127) or (power > 127)):
                if turns < 0:
                    turns = abs(turns)
                    power = -1 * power
                try:
                    motorB = Motor(self._bricks[self.active_nxt], PORT_B)
                    motorC = Motor(self._bricks[self.active_nxt], PORT_C)
                    syncmotors = SynchronizedMotors(motorB, motorC, 0)
                    syncmotors.turn(power, int(turns*360))
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_POWER)
        else:
            raise logoerror(ERROR_BRICK)

    def syncmotorsforever(self, power):
        if self._bricks:
            if not((power < -127) or (power > 127)):
                try:
                    motorB = Motor(self._bricks[self.active_nxt], PORT_B)
                    motorC = Motor(self._bricks[self.active_nxt], PORT_C)
                    syncmotors = SynchronizedMotors(motorB, motorC, 0)
                    syncmotors.run(power)
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_POWER)
        else:
            raise logoerror(ERROR_BRICK)

    def playtone(self, freq, time):
        if self._bricks:
            try:
                self._bricks[self.active_nxt].play_tone(freq, time)
            except:
                raise logoerror(ERROR_GENERIC)
        else:
            raise logoerror(ERROR_BRICK)

    def getLight(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Light(self._bricks[self.active_nxt], port_aux)
                    sensor.set_illuminated(False)
                    res = sensor.get_lightness()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getLightColor(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Light(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_lightness()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getGray(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Light(self._bricks[self.active_nxt], port_aux)
                    sensor.set_illuminated(True)
                    res = sensor.get_lightness()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getButton(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Touch(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_sample()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getDistance(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Ultrasonic(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_sample()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getColor(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Color20(self._bricks[self.active_nxt], port_aux)
                    res = colors[sensor.get_sample()]
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def getSound(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Sound(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_sample()
                except:
                    pass
                return res
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def startmotor(self, port, power):
        if self._bricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                if not((power < -127) or (power > 127)):
                    try:
                        m = Motor(self._bricks[self.active_nxt], port)
                        m.weak_turn(power, 0)
                    except:
                        raise logoerror(ERROR_GENERIC)
                else:
                    raise logoerror(ERROR_POWER)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def brake(self, port):
        if self._bricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self._bricks[self.active_nxt], port)
                    m.brake()
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def setcolor(self, port, color):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                port_aux = NXT_SENSOR_PORTS[port]
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
                    Color20(self._bricks[self.active_nxt], port_aux).set_light_color(color)
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def motorreset(self, port):
        if self._bricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self._bricks[self.active_nxt], port)
                    t = m.get_tacho()
                    self._motor_pos[port_up][self.active_nxt] = t.tacho_count
                    m.idle()
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def motorposition(self, port):
        if self._bricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self._bricks[self.active_nxt], port)
                    t = m.get_tacho()
                    previous = self._motor_pos[port_up][self.active_nxt]
                    return (t.tacho_count - previous)
                except:
                    raise logoerror(ERROR_GENERIC)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def battery(self):
        if self._bricks:
            try:
                return self._bricks[self.active_nxt].get_battery_level()
            except:
                raise logoerror(ERROR_GENERIC)
        else:
            raise logoerror(ERROR_BRICK)

    def refresh(self):
        self.nxt_find()
        self.change_color_blocks()
        self._reset_motors_pos()
        if self._bricks:
            n = len(self._bricks)
            self.tw.showlabel('print', BRICK_FOUND % int(n))
        else:
            self.tw.showlabel('print', BRICK_NOT_FOUND)

    def select(self, i):
        # The list index begin in 0
        try:
            i = int(i)
            i = i - 1
        except:
            raise logoerror(ERROR_NO_NUMBER % str(i))
        if (i < len(self._bricks)) and (i >= 0):
            self.active_nxt = i
        else:
            raise logoerror(BRICK_INDEX_NOT_FOUND % int(i + 1))

    def count(self):
        return len(self._bricks)

    def brickname(self, i):
        # The list index begin in 0
        try:
            i = int(i)
            i = i - 1
        except:
            raise logoerror(ERROR_NO_NUMBER % str(i))
        if (i < len(self._bricks)) and (i >= 0):
            try:
                info = self._bricks[i].get_device_info()
                name = info[0]
                name = name.replace('\x00', '')
                return name
            except:
                raise logoerror(ERROR_GENERIC)
        else:
            raise logoerror(BRICK_INDEX_NOT_FOUND % int(i + 1))

    ############################### Useful functions ##########################

    def change_color_blocks(self):
        index1 = palette_name_to_index('nxt-motors')
        index2 = palette_name_to_index('nxt-sensors')
        if (index1 is not None) and (index2 is not None):
            nxt_palette_blocks = palette_blocks[index1] + palette_blocks[index2]
            for block in self.tw.block_list.list:
                if block.type in ['proto', 'block']:
                    if block.name in nxt_palette_blocks:
                        if (self._bricks) or (block.name == 'nxtrefresh'):
                            special_block_colors[block.name] = COLOR_PRESENT[:]
                        else:
                            special_block_colors[block.name] = COLOR_NOTPRESENT[:]
                        block.refresh()
            self.tw.regenerate_palette(index1)
            self.tw.regenerate_palette(index2)

    def _close_bricks(self):
        for b in self._bricks:
            try:
                b.__del__()
            except:
                pass
        self._bricks = []
        self.active_nxt = 0

    def _idle_motors(self):
        for b in self._bricks:
            try:
                Motor(b, PORT_A).idle()
                Motor(b, PORT_B).idle()
                Motor(b, PORT_C).idle()
            except:
                pass

    def _reset_motors_pos(self):
        self._motor_pos['A'] = []
        self._motor_pos['B'] = []
        self._motor_pos['C'] = []
        for i in range(len(self._bricks)):
            self._motor_pos['A'].append(0)
            self._motor_pos['B'].append(0)
            self._motor_pos['C'].append(0)

    def _nxt_search(self):
        ret = []
        devices = []
        try:
            devices = usb.core.find(find_all=True, idVendor=ID_VENDOR_LEGO, idProduct=ID_PRODUCT_NXT)
        except:
            pass
        for dev in devices:
            ret.append(USBSock(dev))
        devices = []
        try:
            devices = bluetooth.discover_devices()
        except:
            pass
        for dev in devices:
            ret.append(BlueSock(dev))
        return ret

    def nxt_find(self):
        self._close_bricks()
        for dev in self._nxt_search():
            try:
                b = dev.connect()
                self._bricks.append(b)
            except:
                pass

