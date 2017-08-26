# pvdb - Python visual debugger inspired by Philip Guo's Python Tutor
# Copyright (C) 2017  Stephan Rave
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from idlelib.ColorDelegator import ColorDelegator
from idlelib.Percolator import Percolator
from io import BytesIO
from pdb import Pdb
import sys
import tkinter as tk
from types import FunctionType

from graphviz import Digraph
from PIL import Image
from PIL.ImageTk import PhotoImage

TEXTSIZE = '13'
CLASSSIZE = '9'
ARROWSIZE = '0.7'
FRAMECOLOR = '#ffffb3'
SCALARCOLOR = '#80b1d3'
SIGLETONCOLOR = '#b3de69'
LISTCOLOR = '#fb8072'
TUPLECOLOR = '#fdb462'
DICTCOLOR = '#bebada'
SETCOLOR = '#8dd3c7'


class FrameVisualizer:

    def __init__(self, frames):
        self.frames = frames
        self.graph = Digraph('graph')
        self.seen_objects = set()

    def visualize(self, size=None):
        self._add_frames()
        self._add_objects()

        self.graph.attr(rankdir='LR', dpi='100')
        if size:
            self.graph.attr(size='{},{}'.format(size[0]/100, size[1]/100), ratio='compress')
        # print(self.graph)
        # self.graph.engine = 'neato'
        # print(self.graph.pipe('dot').decode('utf8'))
        out = self.graph.pipe('png')
        stream = BytesIO(out)
        return Image.open(stream)

    def _add_frames(self):
        label = '''<<font point-size="{}"><table cellpadding="0" cellspacing="0" border="0">'''.format(TEXTSIZE)
        for name, entries in self.frames:
            label += '<tr><td align="left"><font point-size="{}">{}</font></td></tr>'.format(CLASSSIZE, name)
            if entries:
                for k in sorted(entries):
                    label += '<tr><td border="1" width="80" bgcolor="{}" port="{}_{}">{}</td></tr>'.format(
                        FRAMECOLOR, name, k, k
                    )
            else:
                label += '<tr><td border="1" width="80" bgcolor="{}">&nbsp;</td></tr>'.format(FRAMECOLOR)
            label += '<tr><td width="80">&nbsp;</td></tr>'
        label += '</table></font>>'
        self.graph.node('frames', label, shape='none')

    def _add_objects(self):
        for name, entries in self.frames:
            for k, v in sorted(entries.items()):
                self._add_object(v)
                self.graph.edge('frames:{}_{}'.format(name, k), 'obj_{}:__INPUT__:w'.format(id(v)), arrowsize=ARROWSIZE)

    def _add_object(self, obj):
        if id(obj) in self.seen_objects:
            return
        label = '<<font point-size="{}"><table cellpadding="0" cellspacing="0" border="0">' \
                '<tr><td align="left"><font point-size="{}">{}</font></td></tr>'.format(TEXTSIZE, CLASSSIZE,
                                                                                        type(obj).__name__)
        label += '<tr><td><table cellpadding="0" cellspacing="0" border="0" port="__INPUT__">'

        if type(obj) in (int, float, str):
            label += '<tr><td border="1" width="10" bgcolor="{}">{}</td></tr>'.format(SCALARCOLOR, obj)
        elif obj in (None, True, False):
            label += '<tr><td border="1" width="10" bgcolor="{}">{}</td></tr>'.format(SIGLETONCOLOR, obj)
        elif type(obj) in (list, tuple):
            label += '<tr>'
            if obj:
                for i, v in enumerate(obj):
                    label += '<td border="1" width="10" port="{}" bgcolor="{}">&nbsp;</td>'.format(
                        i, LISTCOLOR if type(obj) is list else TUPLECOLOR
                    )
            else:
                label += '<td border="1" width="3"></td>'
            label += '</tr>'
        elif type(obj) is dict:
            if obj:
                for k in obj:
                    label += '<tr><td border="1" width="10" port="{}" bgcolor="{}">{}</td></tr>'.format(k, DICTCOLOR, k)
            else:
                label += '<tr><td border="1" width="3"></td></tr>'
        elif type(obj) is set:
            label += '<tr><td border="1" width="10" port="0" bgcolor="{}">{{{}}}</td></tr>'.format(SETCOLOR, len(obj))
        else:
            label += '<tr><td border="1" width="10">&nbsp;</td></tr>'
        label += '</table></td></tr></table></font>>'
        self.graph.node('obj_{}'.format(id(obj)), label, shape='none')

        if type(obj) in (list, tuple):
            for i, v in enumerate(obj):
                self._add_object(v)
                self.graph.edge('obj_{}:{}:s'.format(id(obj), i), 'obj_{}:__INPUT__'.format(id(v)), arrowsize=ARROWSIZE)
        elif type(obj) is dict:
            for k, v in obj.items():
                self._add_object(v)
                self.graph.edge('obj_{}:{}:e'.format(id(obj), k), 'obj_{}:__INPUT__'.format(id(v)), arrowsize=ARROWSIZE)
        elif type(obj) is set:
            for v in obj:
                self._add_object(v)
                self.graph.edge('obj_{}:0'.format(id(obj)), 'obj_{}:__INPUT__'.format(id(v)), arrowsize=ARROWSIZE)


def get_frame_data(frame):
    filename = frame.f_code.co_filename
    frames = []
    while True:
        frames.insert(0, (frame.f_code.co_name,
                          {k: v for k, v in frame.f_locals.items()
                           if not (k.startswith('__') or
                                   isinstance(v, type) or
                                   isinstance(v, FunctionType))}))
        frame = frame.f_back
        if not frame:
            break
        if frame.f_code.co_filename != filename:
            break
    frames[0] = ('global', frames[0][1])
    return frames


def visualize_frame(frame, filename=None, show=True, size=None):
    if filename:
        raise NotImplementedError
    frames = get_frame_data(frame)
    pil_image = FrameVisualizer(frames).visualize(size=size)
    if show:
        root = tk.Tk()
        text = tk.Text(root)
        text.grid(row=0, column=0)
        canvas = tk.Canvas(root, width=pil_image.width, height=pil_image.height)
        canvas.grid(row=0, column=1)
        image = PhotoImage(pil_image)
        canvas.create_image((0, 0), image=image, anchor='nw')
        root.mainloop()
    else:
        return pil_image


def visualize_state(pop=1):
    frame = sys._getframe()
    for _ in range(pop):
        frame = frame.f_back
    visualize_frame(frame)


class TkTextStream:

    def __init__(self, text):
        self.text = text

    def write(self, data):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, data)
        self.text.config(state=tk.DISABLED)

    def flush(self):
        pass


class Stepper(Pdb):
    def __init__(self, filename):
        super().__init__()
        self.set_step()
        self.filename = self.canonic(filename)
        with open(self.filename, 'rt') as f:
            self.source = f.readlines()

    def user_line(self, frame):
        if self.canonic(frame.f_code.co_filename) != self.filename:
            return
        self.visualize(frame, 'line')

    def user_return(self, frame, return_value):
        if self.canonic(frame.f_code.co_filename) != self.filename:
            return
        frame.f_locals['~retval~'] = return_value
        self.visualize(frame, 'return')

    def start(self):
        self.setup_gui()
        self._runscript(self.filename)

    def setup_gui(self):
        self.root = root = tk.Tk()

        main_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, showhandle=True)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_frame = tk.Frame(main_pane)
        main_pane.add(left_frame)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_rowconfigure(2, weight=0)
        self.text = text = tk.Text(left_frame)
        text.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        for l in self.source:
            text.insert(tk.END, '  ')
            text.insert(tk.END, l)
        text.config(state=tk.DISABLED)
        Percolator(self.text).insertfilter(ColorDelegator())
        self.canvas = canvas = tk.Canvas(main_pane, bg='white')
        main_pane.add(canvas)

        stdout_text = tk.Text(left_frame)
        stdout_text.grid(row=1, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        stdout_text.config(state=tk.DISABLED)
        sys.stdout = TkTextStream(stdout_text)
        button = tk.Button(left_frame, text="Step", command=root.quit)
        button.grid(row=2, column=0)
        root.bind("<KeyPress>", self._keydown)
        self.image = None
        self.last_line = None

    def visualize(self, frame, mode):
        self.text.config(state=tk.NORMAL)
        if self.last_line:
            self.text.delete("{}.0".format(self.last_line), "{}.1".format(self.last_line))
            self.text.insert("{}.0".format(self.last_line), ' ')
        self.text.delete("{}.0".format(frame.f_lineno), "{}.1".format(frame.f_lineno))
        self.text.insert("{}.0".format(frame.f_lineno), '>' if mode == 'line' else 'R')
        self.text.config(state=tk.DISABLED)
        self.last_line = frame.f_lineno

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        pil_image = visualize_frame(frame, show=False, size=(w, h))
        iw, ih = pil_image.width, pil_image.height
        self.image = image = PhotoImage(pil_image)
        self.canvas.create_image(((w - iw) // 2, (h - ih) // 2), image=image, anchor='nw')
        self.root.mainloop()

    def _keydown(self, e):
        if e.char == ' ':
            self.root.quit()


def main():
    import sys
    import pvdb
    pvdb.Stepper(sys.argv[1]).start()


if __name__ == '__main__':
    main()
