#! /usr/bin/python2

import socket
import json
import sys
from sys import exit
import matplotlib
matplotlib.use("GTK")
import matplotlib.pyplot as plt
import time

UDP_PORT = 5000

config = None
variables = {}
plots = []

class Plot():
    def __init__(self):
        self.figure = None
        self.subplots = []

    def configure(self, cfg):
        self.figure, axes = plt.subplots(len(cfg['subplots']))
        print("create subplots")
        self.figure.suptitle(str(cfg['title']))

        if len(cfg['subplots']) == 1:
            axes = [axes]

        for subplot_cfg, axis in zip(cfg['subplots'], axes):
            subplot_obj = Subplot()
            subplot_obj.axis = axis
            subplot_obj.variables = subplot_cfg['variables']
            subplot_obj.range_x = subplot_cfg['xrange']
            subplot_obj.range_y = subplot_cfg['yrange']
            subplot_obj.plot_type = subplot_cfg['type']
            subplot_obj.axis.set_title(str(subplot_cfg['title']))
            subplot_obj.setup()
            self.subplots.append(subplot_obj)
            for variable in subplot_cfg['variables']:
                variables[variable] = []

    def plot(self):
        for subplot in self.subplots:
            subplot.plot()
        self.figure.canvas.draw()
        print("draw figure")

    def show(self):
        self.figure.show()

    def close(self):
        plt.close(self.figure)

class Subplot():
    def __init__(self):
        self.axis = None
        self.lines = []
        self.variables = []
        self.range_x = []
        self.range_y = []
        self.plot_type = None

    def setup(self):
        if len(self.range_x) == 2:
            self.axis.set_xlim(self.range_x)
        if len(self.range_y) == 2:
            self.axis.set_ylim(self.range_y)

        if self.plot_type == 'plot':
            for variable in self.variables:
                new_line = self.axis.plot(0, label = variable)
                print("new line")
                self.lines.append(new_line[0])

    def plot(self):
        if self.plot_type == 'plot':
            delta_x_range = self.range_x[1] - self.range_x[0]

            x_max = max([len(variables[var]) for var in self.variables])
            if x_max > delta_x_range:
                self.axis.set_xlim([x_max - delta_x_range, x_max])
                print("x_min: " + str(x_max - delta_x_range))
                print("x_max: " + str(x_max))
                for var in self.variables:
                    print(variables[var])

            for variable, line in zip(self.variables, self.lines):
                if len(variables[variable]) < delta_x_range:
                    line.set_data(range(0, len(variables[variable])),
                                  variables[variable])
                    print("set data")
                else:
                    line.set_data(range(x_max - delta_x_range, x_max),
                                  variables[variable][-delta_x_range:])
                    print("set data " + str(delta_x_range))



            if self.range_y == 'auto':
                try:
                    y_max = max([max(variables[var][-delta_x_range:]) for var in self.variables])
                    y_min = min([min(variables[var][-delta_x_range:]) for var in self.variables])
                    self.axis.set_ylim([y_min, y_max])
                    print("y_min: " + str(y_min))
                    print("y_max: " + str(y_max))
                except:
                    # no fucks given when list is empty
                    pass





def load_config(path=None):
    global config
    if path is None:
        config = json.load(open(sys.argv[1]))
    else:
        config = json.load(open(path))

    if 'default' in config:
        if not 'title' in config['default']:
            exit('error: no default title specified')
        if not 'xrange' in config['default']:
            exit('error: no default xrange specified')
        if not 'yrange' in config['default']:
            exit('error: no default yrange specified')
        if not 'type' in config['default']:
            exit('error: no default type specified')
    else:
        exit('error: no default values specified')

    if not 'frequency' in config:
        exit('error: no frequency specified')
    if not 'ip' in config:
        exit('error: no ip specified')
    if not 'port' in config:
        exit('error: no port specified')

    if 'plots' in config:
        for plot, i in zip(config['plots'], range(0, len(config['plots']))):
            if not 'title' in plot:
                plot['title'] = config['default']['title'] + str(i)
            if not 'xrange' in plot:
                plot['xrange'] = config['default']['xrange']
            if not 'yrange' in plot:
                plot['yrange'] = config['default']['yrange']
            if not 'type' in plot:
                plot['type'] = config['default']['type']
            if not 'subplots' in plot:
                new_subplots = []
                new_subplot = {}
                new_subplot['title'] = plot['title']
                new_subplot['xrange'] = plot['xrange']
                new_subplot['yrange'] = plot['yrange']
                new_subplot['type'] = plot['type']
                if 'variables' in plot:
                    new_subplot['variables'] = plot['variables']
                else:
                    exit('error: no variables for ' + str(plot['title']))
                new_subplots.append(new_subplot)
                plot['subplots'] = new_subplots

            for subplot, j in zip(plot['subplots'], range(0, len(plot['subplots']))):
                if not 'title' in subplot:
                    subplot['title'] = plot['title'] + '_' + str(j)
                if not 'xrange' in subplot:
                    subplot['xrange'] = plot['xrange']
                if not 'yrange' in subplot:
                    subplot['yrange'] = plot['yrange']
                if not 'type' in subplot:
                    subplot['type'] = plot['type']
                if not 'variables' in subplot:
                    exit('error: no variables for ' + str(subplot['title']))
    print(config)


def create_plot_objects():
    for plot_cfg in config['plots']:
        new_plot = Plot()
        new_plot.configure(plot_cfg)
        plots.append(new_plot)

def show_plots():
    for plot in plots:
        plot.show()

def plot_all():
    for plot in plots:
        plot.plot()

def connect():
    print("Connecting to " + config['ip'] + ":" + str(config['port']))
    s = socket.socket()
    s.connect((config['ip'], config['port']))
    for var in variables:
        print(var)
        s.sendall(var.encode('ascii') + b'\n')
    s.sendall(str(config['frequency']).encode('ascii') + b'\n')
    s.close()
    print("Config sent to server.")

def update_variables(data):
    data = data.decode('ascii')
    incoming = data.split('\n')
    incoming_split = []
    for line in incoming:
        incoming_split.append(line.split(' '))
    for variable_hash in incoming_split:
        if variable_hash[0] in variables and len(variable_hash) > 1:
            variables[variable_hash[0]] = variable_hash[1]


def main():
    # load configuration from .json
    load_config()
    create_plot_objects()
    # connect via TCP and send config
    connect()

    show_plots()

    # listen on UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', config['port']))

    # main loop
    while True:
        data, addr = sock.recvfrom(4096)
        update_variables(data)
        plot_all()


if __name__ == "__main__":
    main()
