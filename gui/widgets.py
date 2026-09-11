"""Reusable widgets: copy-friendly log, DLC folder popup, help dialog."""
import os
import tkinter as tk
from tkinter import ttk


class LogWidget(tk.Frame):
    """Read-only log with selection, Ctrl+C / Ctrl+A and right-click menu."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.text = tk.Text(
            self, height=12, wrap=tk.WORD, borderwidth=0, highlightthickness=0,
            font=('Consolas', 9), state='disabled', undo=False,
        )
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Select-all / copy in BOTH layouts: on RU layout Ctrl+A/C come
        # through as Cyrillic_ef / Cyrillic_es keysyms, not latin ones.
        for seq in ('<Control-a>', '<Control-A>',
                    '<Control-Cyrillic_ef>', '<Control-Cyrillic_EF>'):
            self.text.bind(seq, self.select_all)
        for seq in ('<Control-c>', '<Control-C>',
                    '<Control-Cyrillic_es>', '<Control-Cyrillic_ES>'):
            self.text.bind(seq, self.copy_selection)
        self.text.bind('<Button-3>', self._show_menu)
        self.text.bind('<Button-1>', lambda e: self.text.focus_set())

        self.menu = tk.Menu(self.text, tearoff=0)
        self.menu.add_command(label="Copy", command=self.copy_selection)
        self.menu.add_separator()
        self.menu.add_command(label="Select All", command=self.select_all)
        self.menu.add_command(label="Clear", command=self.clear)

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def log(self, message):
        self.text.config(state='normal')
        self.text.insert(tk.END, str(message) + "\n")
        self.text.see(tk.END)
        self.text.config(state='disabled')
        self.update_idletasks()

    def copy_selection(self, event=None):
        try:
            selected = self.text.selection_get()
        except tk.TclError:
            return "break"
        if selected:
            try:
                self.clipboard_clear()
                self.clipboard_append(selected)
                self.update()
            except tk.TclError:
                pass
        return "break"

    def select_all(self, event=None):
        self.text.focus_set()
        self.text.tag_add('sel', '1.0', 'end')
        return "break"

    def clear(self, event=None):
        self.text.config(state='normal')
        self.text.delete('1.0', tk.END)
        self.text.config(state='disabled')

    def set_menu_labels(self, copy_label, select_all_label, clear_label):
        self.menu.entryconfig(0, label=copy_label)
        self.menu.entryconfig(2, label=select_all_label)
        self.menu.entryconfig(3, label=clear_label)


def place_popup(root, popup, button):
    """Position an overrideredirect popup under a button, clamped inside
    the app window (flips above the button if it does not fit below),
    then clamped to the screen. Call after content/labels are set."""
    try:
        popup.update_idletasks()
        pw, ph = popup.winfo_reqwidth(), popup.winfo_reqheight()
    except Exception:
        pw, ph = 220, 90
    try:
        bx = button.winfo_rootx()
        by = button.winfo_rooty()
        bh = button.winfo_height()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        rw = root.winfo_width()
        rh = root.winfo_height()
    except Exception:
        return
    x = bx
    y = by + bh + 2
    if rw > 0:
        x = max(rx, min(x, rx + rw - pw))
    if rh > 0 and y + ph > ry + rh:
        y = by - ph - 2  # flip above the button
    try:
        sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
        x = max(0, min(x, sw - pw))
        y = max(0, min(y, sh - ph))
    except Exception:
        pass
    try:
        popup.geometry(f"+{x}+{y}")
    except Exception:
        pass


def fit_popup_to_button(root, popup, button):
    """Size a popup to its button width (never narrower than content),
    then clamp it inside the app window. Option buttons fill the whole
    width, so the mouse path from button to option never leaves the popup.
    """
    try:
        popup.update_idletasks()
        bw = button.winfo_width()
        req_w = popup.winfo_reqwidth()
        req_h = popup.winfo_reqheight()
        if bw > 0:
            popup.geometry(f"{max(bw, req_w)}x{req_h}")
            popup.update_idletasks()
    except Exception:
        pass
    place_popup(root, popup, button)


class ChoicePopup(tk.Toplevel):
    """Generic N-option popup under a button.

    Same guarded auto-hide as DlcFolderPopup/OptionsPopup: selection,
    Escape, deactivation, guarded FocusOut, plus caller-side outside-click
    handling. Final position via place_popup() so it never leaves the app.
    """

    def __init__(self, parent, x, y, options, on_pick):
        super().__init__(parent)
        self.overrideredirect(True)
        # NOTE: no '-topmost' on purpose: a topmost popup floats above ALL
        # system windows. As a child of root it already stacks above the app.
        self._on_pick = on_pick
        self._closed = False

        frame = ttk.Frame(self, padding=4, relief='raised', borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True)
        self.buttons = []
        for value, label in options:
            btn = ttk.Button(frame, text=label,
                             command=lambda v=value: self._pick(v))
            btn.pack(fill=tk.X, pady=2)
            self.buttons.append(btn)

        self.geometry(f"+{x}+{y}")
        self.bind('<Deactivate>', lambda e: self.close())
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Escape>', lambda e: self.close())
        watch_proximity(self)

    def _is_focus_inside(self):
        try:
            focused = self.focus_get()
        except Exception:
            return False
        if focused is None:
            return False
        try:
            return str(focused).startswith(str(self))
        except Exception:
            return False

    def _on_focus_out(self, event=None):
        self.after(150, self._close_if_outside)

    def _close_if_outside(self):
        if self._closed:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if not self._is_focus_inside():
            self.close()

    def set_options_labels(self, labels):
        for btn, text in zip(self.buttons, labels):
            btn.config(text=text)

    def _pick(self, value):
        if not self._closed:
            self._closed = True
            try:
                self._on_pick(value)
            finally:
                self.destroy()

    def close(self):
        if not self._closed:
            self._closed = True
            self.destroy()


def watch_proximity(popup, margin=50, interval=120):
    """Auto-hide a popup once the mouse leaves its area + margin.

    Covers app switching, window moves and stray popups without relying
    on focus events. Stops itself once the popup is closed/destroyed.
    """
    def check():
        try:
            if getattr(popup, '_closed', False) or not popup.winfo_exists():
                return
        except Exception:
            return
        try:
            mx, my = popup.winfo_pointerx(), popup.winfo_pointery()
            x, y = popup.winfo_rootx(), popup.winfo_rooty()
            w, h = popup.winfo_width(), popup.winfo_height()
            inside = (x - margin <= mx <= x + w + margin and
                      y - margin <= my <= y + h + margin)
        except Exception:
            try:
                popup.after(interval, check)
            except Exception:
                pass
            return
        if not inside:
            try:
                popup.close()
            except Exception:
                pass
            return
        try:
            popup.after(interval, check)
        except Exception:
            pass
    try:
        popup.after(interval, check)
    except Exception:
        pass


class DlcFolderPopup(tk.Toplevel):
    """Small popup under the DLC-folder button with 2 project buttons.

    Auto-hides on selection or when focus is lost (click elsewhere).
    """

    def __init__(self, parent, x, y, on_pick):
        super().__init__(parent)
        self.overrideredirect(True)
        # NOTE: no '-topmost': child of root already stacks above the app,
        # topmost would float it above all other system windows.
        self._on_pick = on_pick
        self._closed = False

        frame = ttk.Frame(self, padding=4, relief='raised', borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True)
        self.btn_wg = ttk.Button(frame, command=lambda: self._pick('wargaming'))
        self.btn_lesta = ttk.Button(frame, command=lambda: self._pick('lesta'))
        self.btn_wg.pack(fill=tk.X, pady=2)
        self.btn_lesta.pack(fill=tk.X, pady=2)

        self.geometry(f"+{x}+{y}")
        # NOTE: plain <FocusOut> on the Toplevel fires as soon as focus moves
        # to a child button -> popup would close instantly. Use guarded handlers.
        self.bind('<Deactivate>', lambda e: self.close())
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Escape>', lambda e: self.close())
        watch_proximity(self)

    def _is_focus_inside(self):
        try:
            focused = self.focus_get()
        except Exception:
            return False
        if focused is None:
            return False
        try:
            return str(focused).startswith(str(self))
        except Exception:
            return False

    def _on_focus_out(self, event=None):
        # Focus moved somewhere; close only if it really left the popup.
        # Delayed check lets button clicks fire first.
        self.after(150, self._close_if_outside)

    def _close_if_outside(self):
        if self._closed:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if not self._is_focus_inside():
            self.close()

    def set_labels(self, wg_label, lesta_label):
        self.btn_wg.config(text=wg_label)
        self.btn_lesta.config(text=lesta_label)

    def _pick(self, project):
        if not self._closed:
            self._closed = True
            try:
                self._on_pick(project)
            finally:
                self.destroy()

    def close(self):
        if not self._closed:
            self._closed = True
            self.destroy()


class OptionsPopup(tk.Toplevel):
    """Generic 2-option popup below a button (same behaviour as DlcFolderPopup).

    Auto-hides on selection, Escape, deactivation or outside click (handled
    by the caller via root binding). Guarded against instant FocusOut close.
    """

    def __init__(self, parent, x, y, on_pick, value_top='generate', value_bottom='export'):
        super().__init__(parent)
        self.overrideredirect(True)
        # NOTE: no '-topmost': child of root already stacks above the app,
        # topmost would float it above all other system windows.
        self._on_pick = on_pick
        self._value_top = value_top
        self._value_bottom = value_bottom
        self._closed = False

        frame = ttk.Frame(self, padding=4, relief='raised', borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True)
        self.btn_top = ttk.Button(frame, command=lambda: self._pick(self._value_top))
        self.btn_bottom = ttk.Button(frame, command=lambda: self._pick(self._value_bottom))
        self.btn_top.pack(fill=tk.X, pady=2)
        self.btn_bottom.pack(fill=tk.X, pady=2)

        self.geometry(f"+{x}+{y}")
        self.bind('<Deactivate>', lambda e: self.close())
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Escape>', lambda e: self.close())
        watch_proximity(self)

    def _is_focus_inside(self):
        try:
            focused = self.focus_get()
        except Exception:
            return False
        if focused is None:
            return False
        try:
            return str(focused).startswith(str(self))
        except Exception:
            return False

    def _on_focus_out(self, event=None):
        self.after(150, self._close_if_outside)

    def _close_if_outside(self):
        if self._closed:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if not self._is_focus_inside():
            self.close()

    def set_labels(self, top_label, bottom_label):
        self.btn_top.config(text=top_label)
        self.btn_bottom.config(text=bottom_label)

    def _pick(self, value):
        if not self._closed:
            self._closed = True
            try:
                self._on_pick(value)
            finally:
                self.destroy()

    def close(self):
        if not self._closed:
            self._closed = True
            self.destroy()


class ModTile(ttk.Frame):
    """Big clickable mod card. Whole tile toggles; ☑/☐ prefix shows state."""

    def __init__(self, parent, variable, on_toggle, on_help):
        super().__init__(parent, padding=10, relief='groove', borderwidth=2,
                         style='Tile.TFrame')
        self.variable = variable
        self._on_toggle = on_toggle
        self._base_title = ""
        self.columnconfigure(0, weight=1)

        top = ttk.Frame(self, style='Tile.TFrame')
        top.grid(row=0, column=0, sticky=(tk.W, tk.E))
        top.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(top, font=('', 11, 'bold'), style='Tile.TLabel')
        self.title_label.grid(row=0, column=0, sticky=tk.W)
        self.help_btn = ttk.Button(top, text="?", width=3, command=on_help)
        self.help_btn.grid(row=0, column=1, sticky=tk.E, padx=(8, 0))

        self.desc_label = ttk.Label(self, wraplength=260, justify=tk.LEFT,
                                    style='Tile.TLabel')
        self.desc_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(4, 0))
        self.meta_label = ttk.Label(self, justify=tk.LEFT, font=('', 9),
                                    style='TileMeta.TLabel')
        self.meta_label.grid(row=2, column=0, sticky=tk.W, pady=(6, 0))

        self._inner = (top, self.title_label, self.desc_label, self.meta_label)
        self._locked = False
        for w in (self,) + self._inner:
            w.bind('<Button-1>', self._click)
        self.refresh()

    def _click(self, event=None):
        self.toggle()

    def toggle(self):
        if getattr(self, '_locked', False):
            return
        self.variable.set(not self.variable.get())
        self.refresh()
        self._on_toggle()

    def set_texts(self, title, desc, meta):
        self._base_title = title
        self.desc_label.config(text=desc)
        self.meta_label.config(text=meta)
        self.refresh()

    def refresh(self):
        mark = "☑" if self.variable.get() else "☐"
        self.title_label.config(text=f"{mark}  {self._base_title}")
        frame_style = 'Tile.Selected.TFrame' if self.variable.get() else 'Tile.TFrame'
        label_style = 'Tile.Selected.TLabel' if self.variable.get() else 'Tile.TLabel'
        self.config(style=frame_style)
        for w in self._inner:
            try:
                if isinstance(w, ttk.Label):
                    if w is self.meta_label:
                        continue
                    w.config(style=label_style)
                else:
                    w.config(style=frame_style)
            except Exception:
                pass


class SegmentedControl(ttk.Frame):
    """Two-button segmented switch (same popup-free behaviour as radio)."""

    def __init__(self, parent, values, variable, command, width=12):
        super().__init__(parent)
        self.values = list(values)
        self.variable = variable
        self._command = command
        self.buttons = []
        for i, value in enumerate(self.values):
            btn = ttk.Button(self, width=width,
                             command=lambda v=value: self._pick(v))
            btn.pack(side=tk.LEFT, padx=(0, 0) if i == len(self.values) - 1 else (0, 4))
            self.buttons.append(btn)
        self.refresh()

    def _pick(self, value):
        self.variable.set(value)
        self.refresh()
        self._command(value)

    def set_labels(self, labels):
        for btn, text in zip(self.buttons, labels):
            btn.config(text=text)

    def refresh(self):
        current = self.variable.get()
        for btn, value in zip(self.buttons, self.values):
            btn.config(style='Seg.Selected.TButton' if value == current else 'Seg.TButton')


class ScrollableFrame(ttk.Frame):
    """Vertically scrollable container: content never gets pushed out of reach.

    The scrollbar appears only when content is taller than the viewport.
    Mouse wheel works while the pointer is over the panel (temporarily
    takes over <MouseWheel> on Enter, releases on Leave).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.vsb = ttk.Scrollbar(self, orient='vertical',
                                 command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.columnconfigure(0, weight=1)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor='nw')
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.inner.bind('<Configure>', lambda e: self._sync(), add='+')
        self.canvas.bind('<Configure>', lambda e: self._sync(), add='+')
        self.bind('<Enter>', lambda e: self.canvas.bind_all(
            '<MouseWheel>', self._wheel, add='+'))
        self.bind('<Leave>', lambda e: self.canvas.unbind_all('<MouseWheel>'))
        self._sync()

    def set_bg(self, color):
        try:
            self.canvas.configure(bg=color)
        except Exception:
            pass

    def _on_scroll(self, first, last):
        try:
            self.vsb.set(first, last)
        except Exception:
            pass
        try:
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.vsb.grid_remove()
            else:
                self.vsb.grid()
        except Exception:
            pass

    def _sync(self):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        except Exception:
            pass
        try:
            # stretch short content to the viewport so bottom-anchored
            # widgets (actions) sit at the window bottom in fullscreen
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            reqh = self.inner.winfo_reqheight()
            self.canvas.itemconfig(self._win, width=cw,
                                   height=max(reqh, ch))
        except Exception:
            pass
        try:
            self._on_scroll(*self.canvas.yview())
        except Exception:
            pass

    def _wheel(self, event):
        # NOTE: no "break" — the root-level handler also closes popups.
        try:
            steps = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(steps, 'units')
        except Exception:
            pass


def _fmt_size(num):
    try:
        num = int(num)
    except (TypeError, ValueError):
        return ""
    if num < 1024:
        return f"{num} B"
    if num < 1024 * 1024:
        return f"{num / 1024:.1f} KB"
    return f"{num / (1024 * 1024):.1f} MB"


class FileTree(ttk.Frame):
    """Lazy directory tree: [+] expands on demand, children load on open.

    Columns: name | size | status. Status marks files — and, deeply,
    folders containing them — listed in the modification registry.
    Column separators are locked so the layout cannot break.
    """

    def __init__(self, parent, on_open=None):
        super().__init__(parent)
        self._on_open = on_open
        self._root_path = None
        self._highlight = set()
        self._modified = set()
        self._status_text = "MODIFIED"
        self.tree = ttk.Treeview(self, columns=('size', 'status'),
                                 show='tree headings')
        self.tree.heading('#0', text='...')
        self.tree.heading('size', text='...')
        self.tree.heading('status', text='...')
        self.tree.column('#0', stretch=True)
        self.tree.column('size', width=90, minwidth=90, stretch=False, anchor='e')
        self.tree.column('status', width=130, minwidth=130, stretch=False, anchor='w')
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree.bind('<<TreeviewOpen>>', self._on_open_node)
        self.tree.bind('<Double-Button-1>', self._on_activate)
        self.tree.bind('<Return>', self._on_activate)
        self.tree.bind('<ButtonPress-1>', self._block_separator, add='+')

    def _block_separator(self, event):
        try:
            if self.tree.identify_region(event.x, event.y) == 'separator':
                return 'break'
        except Exception:
            pass

    def set_headings(self, name, size, status):
        self.tree.heading('#0', text=name)
        self.tree.heading('size', text=size)
        self.tree.heading('status', text=status)

    def set_highlight(self, paths):
        self._highlight = set(paths or [])

    def set_modified(self, norm_paths, label="MODIFIED"):
        self._modified = set(norm_paths or [])
        self._status_text = label

    def _norm(self, path):
        try:
            return os.path.normcase(os.path.abspath(path))
        except Exception:
            return path

    def _file_mark(self, full):
        return self._status_text if self._norm(full) in self._modified else ""

    def _dir_mark(self, full):
        prefix = self._norm(full) + os.sep
        for m in self._modified:
            if m.startswith(prefix):
                return self._status_text
        return ""

    def set_root(self, path, placeholder=None):
        self._root_path = path
        self.tree.delete(*self.tree.get_children())
        if not path or not os.path.isdir(path):
            if placeholder:
                self.tree.insert('', 'end', text=placeholder, values=('', ''))
            return
        node = self.tree.insert('', 'end', iid=path,
                                text=os.path.basename(path) or path,
                                values=('', self._dir_mark(path)), open=True)
        self._populate(node)

    def refresh(self, placeholder=None):
        self.set_root(self._root_path, placeholder)

    def selected_path(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _on_open_node(self, event=None):
        for node in self.tree.selection() or ():
            kids = self.tree.get_children(node)
            if len(kids) == 1 and self.tree.item(kids[0], 'text') == '…':
                self.tree.delete(kids[0])
                self._populate(node)

    def _populate(self, node):
        try:
            entries = sorted(os.scandir(node),
                             key=lambda e: (not e.is_dir(follow_symlinks=False),
                                            e.name.lower()))
        except OSError:
            return
        for entry in entries:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            full = entry.path
            if is_dir:
                child = self.tree.insert(node, 'end', iid=full, text=entry.name,
                                         values=('', self._dir_mark(full)))
                self.tree.insert(child, 'end', text='…', values=('', ''))
            else:
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                tags = ('mod',) if full in self._highlight else ()
                self.tree.insert(node, 'end', iid=full, text=entry.name,
                                 values=(_fmt_size(size), self._file_mark(full)),
                                 tags=tags)

    def _on_activate(self, event=None):
        path = self.selected_path()
        if path and self._on_open is not None:
            self._on_open(path)
        return 'break'


class ModFileView(ttk.Frame):
    """Mod files as a folder hierarchy (same look as the full tree):
    mod title | folders | files with size and game/DLC state.
    Column separators are locked so the layout cannot break.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=('size', 'game', 'dlc'),
                                 show='tree headings')
        self.tree.heading('#0', text='...')
        self.tree.heading('size', text='...')
        self.tree.heading('game', text='...')
        self.tree.heading('dlc', text='...')
        self.tree.column('#0', stretch=True)
        self.tree.column('size', width=90, minwidth=90, stretch=False, anchor='e')
        self.tree.column('game', width=110, minwidth=110, stretch=False)
        self.tree.column('dlc', width=110, minwidth=110, stretch=False)
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.tree.bind('<ButtonPress-1>', self._block_separator, add='+')

    def _block_separator(self, event):
        try:
            if self.tree.identify_region(event.x, event.y) == 'separator':
                return 'break'
        except Exception:
            pass

    def set_headings(self, name, size, game, dlc):
        self.tree.heading('#0', text=name)
        self.tree.heading('size', text=size)
        self.tree.heading('game', text=game)
        self.tree.heading('dlc', text=dlc)

    def rebuild(self, sections):
        """sections: [(mod_title, [(rel, size_text, game_state, dlc_state)] )]."""
        self.tree.delete(*self.tree.get_children())
        for title, rows in sections:
            parent = self.tree.insert('', 'end', text=title,
                                      values=('', '', ''), open=True)
            folders = {(): parent}
            for rel, size_text, game_state, dlc_state in rows:
                parts = rel.replace("\\", "/").split("/")
                node = parent
                for part in parts[:-1]:
                    node = self._subfolder(node, part)
                self.tree.insert(node, 'end', text=parts[-1],
                                 values=(size_text, game_state, dlc_state))

    def _subfolder(self, parent, part):
        for child in self.tree.get_children(parent):
            if self.tree.item(child, 'text') == part:
                return child
        return self.tree.insert(parent, 'end', text=part, values=('', '', ''))


def show_help_dialog(parent, title, body, colors=None):
    """Modal help window, centered inside the parent window and themed.

    No flicker: built hidden (withdraw), shown (deiconify) only when ready.
    colors: optional (entry_bg, fg, select_bg) tuple for dark/light support.
    """
    win = tk.Toplevel(parent)
    try:
        win.withdraw()
    except Exception:
        pass
    win.title(title)
    width, height = 560, 440
    entry_bg, fg, select_bg = colors if colors else (None, None, None)
    if entry_bg is not None:
        # preset background BEFORE showing: no bright flash on open
        try:
            win.configure(bg=entry_bg)
        except Exception:
            pass
    try:
        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        if pw > 0 and ph > 0:
            x = max(0, min(px + (pw - width) // 2, sw - width))
            y = max(0, min(py + (ph - height) // 2, sh - height))
            win.geometry(f"{width}x{height}+{x}+{y}")
        else:
            win.geometry(f"{width}x{height}")
    except Exception:
        try:
            win.geometry(f"{width}x{height}")
        except Exception:
            pass
    win.minsize(420, 300)
    text = tk.Text(win, wrap=tk.WORD, font=('Segoe UI', 10), padx=12, pady=12)
    scroll = ttk.Scrollbar(win, orient=tk.VERTICAL, command=text.yview,
                           style='Help.Vertical.TScrollbar')
    try:
        _help_scroll_style = ttk.Style()
        _help_scroll_style.configure('Help.Vertical.TScrollbar', width=18)
    except Exception:
        pass
    text.configure(yscrollcommand=scroll.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    text.insert('1.0', body)
    text.config(state='disabled')
    if entry_bg is not None:
        try:
            text.configure(bg=entry_bg, fg=fg, insertbackground=fg,
                           selectbackground=select_bg, selectforeground=fg,
                           relief='flat')
        except Exception:
            pass
    _sel_all = lambda e: (text.focus_set(), text.tag_add('sel', '1.0', 'end'), "break")[2]
    for _seq in ('<Control-a>', '<Control-A>',
                 '<Control-Cyrillic_ef>', '<Control-Cyrillic_EF>'):
        text.bind(_seq, _sel_all)
    # mouse wheel scrolling (all platforms)
    text.bind('<MouseWheel>',
              lambda e: (text.yview_scroll(-1 if e.delta > 0 else 1, 'units'), "break")[1])
    text.bind('<Button-4>', lambda e: (text.yview_scroll(-1, 'units'), "break")[1])
    text.bind('<Button-5>', lambda e: (text.yview_scroll(1, 'units'), "break")[1])
    btn_frame = ttk.Frame(win, padding=8)
    btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
    ttk.Button(btn_frame, text="OK", command=win.destroy).pack(side=tk.RIGHT)
    try:
        # appear already themed: invisible -> positioned -> visible
        win.attributes('-alpha', 0.0)
    except Exception:
        pass
    try:
        win.update_idletasks()
        win.deiconify()
    except Exception:
        pass
    try:
        win.transient(parent)
        win.grab_set()
    except Exception:
        pass
    try:
        win.attributes('-alpha', 1.0)
    except Exception:
        pass
    win.focus_set()


class BarWithText(tk.Canvas):
    """Determinate progress bar with centered text, drawn on a canvas.

    Single text color stays readable on both the filled and empty parts
    in either theme (colors supplied via set_colors).
    """

    def __init__(self, parent, height=22):
        super().__init__(parent, height=height, highlightthickness=1,
                         borderwidth=0)
        self._done = 0
        self._total = 0
        self._text = ""
        self._fill = '#3a5f7a'
        self._trough = '#2d2d2d'
        self._fg = '#ffffff'
        self._border = '#1a1a1a'
        self.bind('<Configure>', lambda e: self._draw(), add='+')

    def set_colors(self, fill, trough, fg, border):
        self._fill = fill
        self._trough = trough
        self._fg = fg
        self._border = border
        try:
            self.configure(highlightbackground=border, bg=trough)
        except Exception:
            pass
        self._draw()

    def set_values(self, done, total, text):
        try:
            done = max(0, int(done))
        except (TypeError, ValueError):
            done = 0
        try:
            total = max(0, int(total))
        except (TypeError, ValueError):
            total = 0
        if total > 0:
            done = min(done, total)
        self._done = done
        self._total = total
        self._text = text or ""
        self._draw()

    def set_idle(self, text):
        self.set_values(1, 1, text)

    def _frac(self):
        if self._total <= 0:
            return 0.0
        return min(1.0, max(0.0, self._done / self._total))

    def _draw(self):
        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except Exception:
            return
        if w < 4 or h < 4:
            return
        try:
            self.delete('all')
            self.create_rectangle(1, 1, w - 1, h - 1, fill=self._trough,
                                  outline=self._border)
            fw = int(w * self._frac())
            if fw > 2:
                self.create_rectangle(1, 1, fw, h - 1, fill=self._fill,
                                      outline='')
            self.create_text(w // 2, h // 2, text=self._text,
                             fill=self._fg, font=('', 9))
        except Exception:
            pass
