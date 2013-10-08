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

from gettext import gettext as _

from plugins.plugin import Plugin

from TurtleArt.tapalette import make_palette
from TurtleArt.tapalette import palette_name_to_index
from TurtleArt.tapalette import special_block_colors
from TurtleArt.tapalette import palette_blocks
from TurtleArt.talogo import primitive_dictionary, logoerror
from TurtleArt.taconstants import BLACK, WHITE, CONSTANTS
from TurtleArt.tautils import debug_output

sys.path.insert(0, os.path.abspath('./plugins/nxt_plugin'))
import usb
from nxt.motor import PORT_A, PORT_B, PORT_C, Motor, SynchronizedMotors
from nxt.sensor import PORT_1, PORT_2, PORT_3, PORT_4, Touch, Color20, Ultrasonic, Type, Sound, Light
from nxt.usbsock import USBSock, ID_VENDOR_LEGO, ID_PRODUCT_NXT

NXT_SENSORS = {_('touch'): 0, _('ultrasonic'): 1, _('color'): 2, _('light'): 3, _('sound'): 4, _('gray'): 5}
NXT_MOTOR_PORTS = {'A': PORT_A, 'B': PORT_B, 'C': PORT_C}
NXT_SENSOR_PORTS = {'1': PORT_1, '2': PORT_2, '3': PORT_3, '4': PORT_4}

colors = [None, BLACK, CONSTANTS['blue'], CONSTANTS['green'], CONSTANTS['yellow'], CONSTANTS['red'], WHITE]

COLOR_NOTPRESENT = ["#A0A0A0","#808080"]
COLOR_PRESENT = ["#00FF00","#008000"]


ERROR_BRICK = _('Please check the connection with the brick')
ERROR_PORT_M = _("Invalid port '%s'. Port must be: PORT A, B or C")
ERROR_PORT_S = _("Invalid port '%s'. Port must be: PORT 1, 2, 3 or 4")
ERROR_POWER = _('The value of power must be between -127 to 127')
ERROR_NO_NUMBER = _("The parameter must be a integer, not '%s'")
ERROR = _('An error has occurred: check all connections and try to reconnect')

BRICK_FOUND = _('NXT found %s bricks')
BRICK_NOT_FOUND = _('NXT not found')
BRICK_INDEX_NOT_FOUND = _('Brick number %s was not found')


class Nxt_plugin(Plugin):

    def __init__(self, parent):
        self.tw = parent

        """
        Adding a rule to /etc/udev/rules.d call: /etc/udev/rules.d/99-lego.rules
        with:

        SUBSYSTEM=="usb", ATTRS{idVendor}=="0694", ATTRS{idProduct}=="0002", MODE="0666"
        """
        self.nxtbricks = []

        self.active_nxt = 0

        #self.nxt_find()

    def setup(self):

        # Palette of Motors
        debug_output('creating %s palette' % _('nxt-motors'), self.tw.running_sugar)
        palette_motors = make_palette('nxt-motors', COLOR_NOTPRESENT,
                                    _('Palette of LEGO NXT blocks of motors'))

        primitive_dictionary['nxtrefresh'] = self._prim_nxtrefresh
        palette_motors.add_block('nxtrefresh',
                     style='basic-style',
                     label=_('refresh NXT'),
                     prim_name='nxtrefresh',
                     help_string=_('Search for a connected NXT brick.'))
        self.tw.lc.def_prim('nxtrefresh', 0, lambda self :
            primitive_dictionary['nxtrefresh']())
        special_block_colors['nxtrefresh'] = COLOR_PRESENT[:]

        primitive_dictionary['nxtselect'] = self._prim_nxtselect
        palette_motors.add_block('nxtselect',
                          style='basic-style-1arg',
                          default = 1,
                          label=_('NXT'),
                          help_string=_('set current NXT device'),
                          prim_name = 'nxtselect')
        self.tw.lc.def_prim('nxtselect', 1, lambda self, n: 
            primitive_dictionary['nxtselect'](n))

        primitive_dictionary['nxtcount'] = self._prim_nxtcount
        palette_motors.add_block('nxtcount',
                          style='box-style',
                          label=_('number of NXTs'),
                          help_string=_('number of NXT devices'),
                          prim_name = 'nxtcount')
        self.tw.lc.def_prim('nxtcount', 0, lambda self:
            primitive_dictionary['nxtcount']())

        primitive_dictionary['nxtbrickname'] = self._prim_nxtbrickname
        palette_motors.add_block('nxtbrickname',
                  style='number-style-1arg',
                  label=_('brick name'),
                  default=[1],
                  help_string=_('Get the name of a brick.'),
                  prim_name='nxtbrickname')
        self.tw.lc.def_prim('nxtbrickname', 1, lambda self, x:
            primitive_dictionary['nxtbrickname'](x))

        primitive_dictionary['nxtplaytone'] = self._prim_nxtplaytone
        palette_motors.add_block('nxtplaytone',
                  style='basic-style-2arg',
                  label=[_('play tone'), _('frequency'), _('time')],
                  default=[433, 500],
                  help_string=_('Play a tone at frequency for time.'),
                  prim_name='nxtplaytone')
        self.tw.lc.def_prim('nxtplaytone', 2, lambda self, x, y:
            primitive_dictionary['nxtplaytone'](x, y))

        primitive_dictionary['nxtturnmotor'] = self._prim_nxtturnmotor
        palette_motors.add_block('nxtturnmotor',
                  style='basic-style-3arg',
                  label=[_('turn motor\n\n'), _('port'), _('rotations'), _('power')],
                  default=['None', 1, 100],
                  help_string=_('turn a motor'),
                  prim_name='nxtturnmotor')
        self.tw.lc.def_prim('nxtturnmotor', 3, lambda self, x, y, z:
            primitive_dictionary['nxtturnmotor'](x, y, z))

        primitive_dictionary['nxtsyncmotors'] = self._prim_nxtsyncmotors
        palette_motors.add_block('nxtsyncmotors',
                  style='basic-style-3arg',
                  label=[_('synchronize\n\nmotors'), _('power'), _('rotations'), _('steering')],
                  default=[100, 0, 1],
                  help_string=_('synchronize two motors connected in PORT B and PORT C'),
                  prim_name='nxtsyncmotors')
        self.tw.lc.def_prim('nxtsyncmotors', 3, lambda self, x, y, z:
            primitive_dictionary['nxtsyncmotors'](x, y, z))

        primitive_dictionary['nxtporta'] = self._prim_nxtporta
        palette_motors.add_block('nxtporta',
                  style='box-style',
                  label=_('PORT A'),
                  help_string=_('PORT A of the brick'),
                  prim_name='nxtporta')
        self.tw.lc.def_prim('nxtporta', 0, lambda self:
            primitive_dictionary['nxtporta']())

        primitive_dictionary['nxtportb'] = self._prim_nxtportb
        palette_motors.add_block('nxtportb',
                  style='box-style',
                  label=_('PORT B'),
                  help_string=_('PORT B of the brick'),
                  prim_name='nxtportb')
        self.tw.lc.def_prim('nxtportb', 0, lambda self:
            primitive_dictionary['nxtportb']())

        primitive_dictionary['nxtportc'] = self._prim_nxtportc
        palette_motors.add_block('nxtportc',
                  style='box-style',
                  label=_('PORT C'),
                  help_string=_('PORT C of the brick'),
                  prim_name='nxtportc')
        self.tw.lc.def_prim('nxtportc', 0, lambda self:
            primitive_dictionary['nxtportc']())

        primitive_dictionary['nxtsyncmotorsforever'] = self._prim_nxtsyncmotorsforever
        palette_motors.add_block('nxtsyncmotorsforever',
                  style='basic-style-2arg',
                  label=[_('synchronize\nmotors'), _('power'), _('steering')],
                  default=[100, 0],
                  help_string=_('synchronize two motors connected in PORT B and PORT C'),
                  prim_name='nxtsyncmotorsforever')
        self.tw.lc.def_prim('nxtsyncmotorsforever', 2, lambda self, x, y:
            primitive_dictionary['nxtsyncmotorsforever'](x, y))

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
        debug_output('creating %s palette' % _('nxt-sensors'), self.tw.running_sugar)
        palette_sensors = make_palette('nxt-sensors', COLOR_NOTPRESENT,
                    _('Palette of LEGO NXT blocks of sensors'))

        primitive_dictionary['nxtport1'] = self._prim_nxtport1
        palette_sensors.add_block('nxtport1',
                  style='box-style',
                  label=_('PORT 1'),
                  help_string=_('PORT 1 of the brick'),
                  prim_name='nxtport1')
        self.tw.lc.def_prim('nxtport1', 0, lambda self:
            primitive_dictionary['nxtport1']())

        primitive_dictionary['nxtreadsensor'] = self._prim_nxtreadsensor
        palette_sensors.add_block('nxtreadsensor',
                  style='number-style-block',
                  label=[_('read'), _('port'), _('sensor')],
                  help_string=_('Read sensor output.'),
                  prim_name='nxtreadsensor')
        self.tw.lc.def_prim('nxtreadsensor', 2, lambda self, x, y:
            primitive_dictionary['nxtreadsensor'](x, y))

        primitive_dictionary['nxtport2'] = self._prim_nxtport2
        palette_sensors.add_block('nxtport2',
                  style='box-style',
                  label=_('PORT 2'),
                  help_string=_('PORT 2 of the brick'),
                  prim_name='nxtport2')
        self.tw.lc.def_prim('nxtport2', 0, lambda self:
            primitive_dictionary['nxtport2']())

        primitive_dictionary['nxtlight'] = self._prim_nxtlight
        palette_sensors.add_block('nxtlight',
                  style='box-style',
                  label=_('light'),
                  help_string=_('light sensor'),
                  prim_name='nxtlight')
        self.tw.lc.def_prim('nxtlight', 0, lambda self:
            primitive_dictionary['nxtlight']())

        primitive_dictionary['nxtgray'] = self._prim_nxtgray
        palette_sensors.add_block('nxtgray',
                  style='box-style',
                  label=_('gray'),
                  help_string=_('gray sensor'),
                  prim_name='nxtgray')
        self.tw.lc.def_prim('nxtgray', 0, lambda self:
            primitive_dictionary['nxtgray']())

        primitive_dictionary['nxtport3'] = self._prim_nxtport3
        palette_sensors.add_block('nxtport3',
                  style='box-style',
                  label=_('PORT 3'),
                  help_string=_('PORT 3 of the brick'),
                  prim_name='nxtport3')
        self.tw.lc.def_prim('nxtport3', 0, lambda self:
            primitive_dictionary['nxtport3']())

        primitive_dictionary['nxttouch'] = self._prim_nxttouch
        palette_sensors.add_block('nxttouch',
                  style='box-style',
                  label=_('touch'),
                  help_string=_('touch sensor'),
                  prim_name='nxttouch')
        self.tw.lc.def_prim('nxttouch', 0, lambda self:
            primitive_dictionary['nxttouch']())

        primitive_dictionary['nxtultrasonic'] = self._prim_nxtultrasonic
        palette_sensors.add_block('nxtultrasonic',
                  style='box-style',
                  label=_('ultrasonic'),
                  help_string=_('distance sensor'),
                  prim_name='nxtultrasonic')
        self.tw.lc.def_prim('nxtultrasonic', 0, lambda self:
            primitive_dictionary['nxtultrasonic']())

        primitive_dictionary['nxtport4'] = self._prim_nxtport4
        palette_sensors.add_block('nxtport4',
                  style='box-style',
                  label=_('PORT 4'),
                  help_string=_('PORT 4 of the brick'),
                  prim_name='nxtport4')
        self.tw.lc.def_prim('nxtport4', 0, lambda self:
            primitive_dictionary['nxtport4']())

        primitive_dictionary['nxtsound'] = self._prim_nxtsound
        palette_sensors.add_block('nxtsound',
                  style='box-style',
                  label=_('sound'),
                  help_string=_('sound sensor'),
                  prim_name='nxtsound')
        self.tw.lc.def_prim('nxtsound', 0, lambda self:
            primitive_dictionary['nxtsound']())

        primitive_dictionary['nxtcolor'] = self._prim_nxtcolor
        palette_sensors.add_block('nxtcolor',
                  style='box-style',
                  label=_('color'),
                  help_string=_('color sensor'),
                  prim_name='nxtcolor')
        self.tw.lc.def_prim('nxtcolor', 0, lambda self:
            primitive_dictionary['nxtcolor']())

        primitive_dictionary['nxtsetcolor'] = self._prim_nxtsetcolor
        palette_sensors.add_block('nxtsetcolor',
                  style='basic-style-2arg',
                  label=[_('set light'), _('port'), _('color')],
                  help_string=_('Set color sensor light.'),
                  prim_name='nxtsetcolor')
        self.tw.lc.def_prim('nxtsetcolor', 2, lambda self, x, y:
            primitive_dictionary['nxtsetcolor'](x, y))

        primitive_dictionary['nxtbattery'] = self._prim_nxtbattery
        palette_sensors.add_block('nxtbattery',
                  style='box-style',
                  label=_('battery level'),
                  help_string=_('Get the battery level of the brick in millivolts'),
                  prim_name='nxtbattery')
        self.tw.lc.def_prim('nxtbattery', 0, lambda self:
            primitive_dictionary['nxtbattery']())

    ############################### Turtle signals ############################

    def start(self):
        # This gets called by the start button
        pass

    def stop(self):
        # This gets called by the stop button
        for i in range(len(self.nxtbricks)):
            try:
                Motor(self.nxtbricks[i], PORT_A).idle()
                Motor(self.nxtbricks[i], PORT_B).idle()
                Motor(self.nxtbricks[i], PORT_C).idle()
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
        for i in range(len(self.nxtbricks)):
            try:
                Motor(self.nxtbricks[i], PORT_A).idle()
                Motor(self.nxtbricks[i], PORT_B).idle()
                Motor(self.nxtbricks[i], PORT_C).idle()
                self.nxtbricks[i].close_brick()
            except:
                pass

    ################################# Primitives ##############################

    def _prim_nxtturnmotor(self, port, turns, power):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                if not((power < -127) or (power > 127)):
                    if turns < 0:
                        turns = abs(turns)
                        power = -1 * power
                    try:
                        m = Motor(self.nxtbricks[self.active_nxt], port)
                        m.turn(power, int(turns*360), brake=True)
                        m.brake()
                    except:
                        raise logoerror(ERROR)
                else:
                    raise logoerror(ERROR_POWER)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtsyncmotors(self, power, steering, turns):
        if self.nxtbricks:
            if not((power < -127) or (power > 127)):
                if turns < 0:
                    turns = abs(turns)
                    power = -1 * power
                try:
                    motorB = Motor(self.nxtbricks[self.active_nxt], PORT_B)
                    motorC = Motor(self.nxtbricks[self.active_nxt], PORT_C)
                    syncmotors = SynchronizedMotors(motorB, motorC, steering)
                    syncmotors.turn(power, int(turns*360))
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_POWER)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtsyncmotorsforever(self, power, steering):
        if self.nxtbricks:
            if not((power < -127) or (power > 127)):
                try:
                    motorB = Motor(self.nxtbricks[self.active_nxt], PORT_B)
                    motorC = Motor(self.nxtbricks[self.active_nxt], PORT_C)
                    syncmotors = SynchronizedMotors(motorB, motorC, steering)
                    syncmotors.run(power)
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_POWER)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtplaytone(self, freq, time):
        if self.nxtbricks:
            try:
                self.nxtbricks[self.active_nxt].play_tone(freq, time)
            except:
                raise logoerror(ERROR)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxttouch(self):
        return _('touch')

    def _prim_nxtultrasonic(self):
        return _('ultrasonic')

    def _prim_nxtcolor(self):
        return _('color')

    def _prim_nxtlight(self):
        return _('light')

    def _prim_nxtgray(self):
        return _('gray')

    def _prim_nxtsound(self):
        return _('sound')

    def _prim_nxtport1(self):
        return '1'

    def _prim_nxtport2(self):
        return '2'

    def _prim_nxtport3(self):
        return '3'

    def _prim_nxtport4(self):
        return '4'

    def _prim_nxtporta(self):
        return 'A'

    def _prim_nxtportb(self):
        return 'B'

    def _prim_nxtportc(self):
        return 'C'

    def _prim_nxtreadsensor(self, port, sensor):
        """ Read sensor at specified port"""
        port = str(port)
        port_up = port.upper()
        if (port_up in NXT_SENSOR_PORTS):
            if self.nxtbricks:
                port_aux = NXT_SENSOR_PORTS[port_up]
                return self._aux_read_sensor(port_aux, sensor)
            else:
                return -1
        else:
            raise logoerror(ERROR_PORT_S % port)

    def _aux_read_sensor(self, port, sensor):
        res = -1
        try:
            if sensor == _('color'):
                res = colors[Color20(self.nxtbricks[self.active_nxt], port).get_sample()]
            elif sensor == _('light'):
                light_sensor = Light(self.nxtbricks[self.active_nxt], port)
                light_sensor.set_illuminated(False)
                res = light_sensor.get_lightness()
            elif sensor == _('ultrasonic'):
                res = Ultrasonic(self.nxtbricks[self.active_nxt], port).get_sample()
            elif sensor == _('touch'):
                res = Touch(self.nxtbricks[self.active_nxt], port).get_sample()
            elif sensor == _('sound'):
                res = Sound(self.nxtbricks[self.active_nxt], port).get_sample()
            elif sensor == _('gray'):
                gray_sensor = Light(self.nxtbricks[self.active_nxt], port)
                gray_sensor.set_illuminated(True)
                res = gray_sensor.get_lightness()
        except:
            pass
        return res

    def _prim_nxtstartmotor(self, port, power):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                if not((power < -127) or (power > 127)):
                    try:
                        m = Motor(self.nxtbricks[self.active_nxt], port)
                        m.weak_turn(power, 0)
                    except:
                        raise logoerror(ERROR)
                else:
                    raise logoerror(ERROR_POWER)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtbrake(self, port):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self.nxtbricks[self.active_nxt], port)
                    m.brake()
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtsetcolor(self, port, color):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_SENSOR_PORTS):
                port = NXT_SENSOR_PORTS[port_up]
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
                    Color20(self.nxtbricks[self.active_nxt], port).set_light_color(color)
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_PORT_S % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtmotorreset(self, port):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self.nxtbricks[self.active_nxt], port)
                    t = m.get_tacho()
                    if port == PORT_A:
                        self.motor_pos_A[self.active_nxt] = t.tacho_count
                    elif port == PORT_B:
                        self.motor_pos_B[self.active_nxt] = t.tacho_count
                    elif port == PORT_C:
                        self.motor_pos_C[self.active_nxt] = t.tacho_count
                    m.idle()
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtmotorposition(self, port):
        if self.nxtbricks:
            port = str(port)
            port_up = port.upper()
            if (port_up in NXT_MOTOR_PORTS):
                port = NXT_MOTOR_PORTS[port_up]
                try:
                    m = Motor(self.nxtbricks[self.active_nxt], port)
                    t = m.get_tacho()
                    if port == PORT_A:
                        previous = self.motor_pos_A[self.active_nxt]
                    elif port == PORT_B:
                        previous = self.motor_pos_B[self.active_nxt]
                    elif port == PORT_C:
                        previous = self.motor_pos_C[self.active_nxt]
                    return (t.tacho_count - previous)
                except:
                    raise logoerror(ERROR)
            else:
                raise logoerror(ERROR_PORT_M % port)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtbattery(self):
        if self.nxtbricks:
            try:
                return self.nxtbricks[self.active_nxt].get_battery_level()
            except:
                raise logoerror(ERROR)
        else:
            raise logoerror(ERROR_BRICK)

    def _prim_nxtrefresh(self):
        self.nxt_find()
        #self.nxtbrick.get_device_info()

        self.change_color_blocks()

        self.tw.show_toolbar_palette(palette_name_to_index('nxt-motors'), regenerate=True, show=False)
        self.tw.show_toolbar_palette(palette_name_to_index('nxt-sensors'), regenerate=True, show=False)

        if self.nxtbricks:
            n = len(self.nxtbricks)
            self.tw.showlabel('print', BRICK_FOUND % int(n))
        else:
            self.tw.showlabel('print', BRICK_NOT_FOUND)

    def _prim_nxtselect(self, i):
        n = len(self.nxtbricks)
        # The list index begin in 0
        try:
            i = int(i - 1)
        except:
            raise logoerror(ERROR_NO_NUMBER % str(i))
        if (i < n) and (i >= 0):
            self.active_nxt = i
        else:
            raise logoerror(BRICK_INDEX_NOT_FOUND % int(i + 1))

    def _prim_nxtcount(self):
        return len(self.nxtbricks)

    def _prim_nxtbrickname(self, i):
        n = len(self.nxtbricks)
        # The list index begin in 0
        try:
            i = int(i - 1)
        except:
            raise logoerror(ERROR_NO_NUMBER % str(i))
        if (i < n) and (i >= 0):
            try:
                info = self.nxtbricks[i].get_device_info()
                name = info[0]
                name = name.replace('\x00', '')
                return name
            except:
                raise logoerror(ERROR)
        else:
            raise logoerror(BRICK_INDEX_NOT_FOUND % int(i + 1))

    ############################### Useful functions ##########################

    def change_color_blocks(self):
        motors_blocks = palette_blocks[palette_name_to_index('nxt-motors')]
        sensors_blocks = palette_blocks[palette_name_to_index('nxt-sensors')]
        nxt_palette_blocks = motors_blocks + sensors_blocks

        for block in self.tw.block_list.list:
            if block.type in ['proto', 'block']:
                if block.name in nxt_palette_blocks:
                    if (self.nxtbricks) or (block.name == 'nxtrefresh'):
                        special_block_colors[block.name] = COLOR_PRESENT[:]
                    else:
                        special_block_colors[block.name] = COLOR_NOTPRESENT[:]
                    block.refresh()

    def nxt_find(self):

        for b in self.nxtbricks:
            try:
                b.close()
            except:
                pass
            try:
                b.__del__()
            except:
                pass
        self.nxtbricks = []

        for d in usb.core.find(find_all=True, idVendor=ID_VENDOR_LEGO, idProduct=ID_PRODUCT_NXT):
            try:
                dev = USBSock(d)
                b = dev.connect()
                self.nxtbricks.append(b)
            except:
                pass

        self.motor_pos_A = []
        self.motor_pos_B = []
        self.motor_pos_C = []
        for i in range(len(self.nxtbricks)):
            self.motor_pos_A.append(0)
            self.motor_pos_B.append(0)
            self.motor_pos_C.append(0)

