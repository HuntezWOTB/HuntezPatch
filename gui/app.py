"""Main window: unified Blitz Mods Utility (HiddenTanks + AutoRanksOFF).

Layout: header bar | left settings column | right mods + actions + log | status bar.
Long operations run in a background thread; the UI stays responsive.
"""
import os
import queue
import sys
import threading
import tkinter as tk
import traceback
from tkinter import ttk, filedialog, messagebox

from core.config import load_config, save_config
from core.localization import load_locales, get_localized_string
from core.dlc_utils import get_dlc_root, open_folder_in_explorer
from core import orchestrator
from gui.widgets import (
    LogWidget, DlcFolderPopup, OptionsPopup, ChoicePopup, place_popup,
    fit_popup_to_button,
    ModTile, SegmentedControl, FileTree, ModFileView, ScrollableFrame,
    BarWithText, show_help_dialog,
)
from core.moddetect import get_modified_files

if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

VERSION = "v1.02"


class App:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.locales = load_locales()
        if not self.locales:
            messagebox.showerror("Error", "locales/ not found")
            raise SystemExit(1)

        self.available_langs = sorted(self.locales.keys())
        lang = self.config.get('language', 'ru')
        self.current_lang = lang if lang in self.locales else 'en'
        self.current_theme = self.config.get('theme', 'dark')

        self.game_path_var = tk.StringVar(value=self.config.get('game_path', ''))
        self.project_var = tk.StringVar(value=self.config.get('project', 'wargaming'))
        self.dvpl_var = tk.StringVar(value=self.config.get('dvpl_mode', 'DVPL'))
        self.operation_var = tk.StringVar(value=self.config.get('operation', 'generate'))
        self.dlc_var = tk.BooleanVar(value=self.config.get('use_dlc', False))
        mods = self.config.get('mods', ['hidden_tanks'])
        self.mod_hidden_var = tk.BooleanVar(value='hidden_tanks' in mods)
        self.mod_autoranks_var = tk.BooleanVar(value='autoranks' in mods)
        self.mod_randomtank_var = tk.BooleanVar(value='random_tank' in mods)

        self._dlc_popup = None
        self._dlc_outside_binding = None
        self._run_popup = None
        self._run_outside_binding = None
        self._lang_popup = None
        self._lang_outside_binding = None
        self._queue = queue.Queue()
        self._busy = False
        self._status_kind = 'ready'
        self._help_colors = None
        try:
            self.root.bind('<Deactivate>', lambda e: self._close_all_popups(), add='+')
        except Exception:
            pass

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, minsize=300)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        try:
            # popups hide on move/resize/hide; any wheel scroll dismisses them
            self.root.bind('<Configure>', self._track_popups, add='+')
            self.root.bind('<Unmap>', lambda e: self._close_all_popups(), add='+')
            self.root.bind('<MouseWheel>', self._wheel_closes_popups, add='+')
            self.root.bind('<Button-4>', self._wheel_closes_popups, add='+')
            self.root.bind('<Button-5>', self._wheel_closes_popups, add='+')
        except Exception:
            pass

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self.create_widgets()
        self.update_theme()
        self.update_texts()
        self.refresh_path_status()
        self.refresh_dlc_hint()
        self.refresh_explorers()
        self.set_status('ready')

    # ---------- helpers ----------
    def loc(self, key, **kwargs):
        return get_localized_string(self.locales, self.current_lang, key, **kwargs)

    def selected_mods(self):
        mods = []
        if self.mod_hidden_var.get():
            mods.append('hidden_tanks')
        if self.mod_autoranks_var.get():
            mods.append('autoranks')
        if self.mod_randomtank_var.get():
            mods.append('random_tank')
        return mods

    def save_state(self):
        self.config.update({
            'language': self.current_lang,
            'theme': self.current_theme,
            'dvpl_mode': self.dvpl_var.get(),
            'operation': self.operation_var.get(),
            'game_path': self.game_path_var.get(),
            'use_dlc': self.dlc_var.get(),
            'project': self.project_var.get(),
            'mods': self.selected_mods(),
        })
        save_config(self.config)

    # ---------- layout ----------
    def create_widgets(self):
        # Header: title left, language/theme right
        self.header = ttk.Frame(self.main_frame)
        self.header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        self.title_label = ttk.Label(self.header, font=('', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT)
        self.theme_btn = ttk.Button(self.header, width=4, command=self.cycle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=(4, 0))
        self.lang_btn = ttk.Button(self.header, width=5, command=self.toggle_lang_popup)
        self.lang_btn.pack(side=tk.RIGHT)

        # Path: full window width on top, browse button at the right edge
        self.game_group = ttk.LabelFrame(self.main_frame, padding="6")
        self.game_group.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        self.game_group.columnconfigure(2, weight=1)
        self.path_label = ttk.Label(self.game_group)
        self.path_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.path_dot = tk.Label(self.game_group, text="●", font=('', 11))
        self.path_dot.grid(row=0, column=1, sticky=tk.W, padx=(0, 4))
        self.path_entry = ttk.Entry(self.game_group, textvariable=self.game_path_var)
        self.path_entry.grid(row=0, column=2, sticky=(tk.W, tk.E))
        self.path_entry.bind('<KeyRelease>', lambda e: (self.refresh_path_status(), self.save_state()))
        self.path_entry.bind('<Return>', lambda e: self._commit_path())
        self.path_entry.bind('<FocusOut>', lambda e: self._commit_path())
        self.btn_browse = ttk.Button(self.game_group, command=self.browse_folder, width=14)
        self.btn_browse.grid(row=0, column=3, sticky=tk.E, padx=(8, 0))

        # Left: scrollable column (mods, project, DVPL, DLC, actions) —
        # nothing gets pushed out of reach when the window is small
        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        self.left_panel.columnconfigure(0, weight=1)
        self.left_panel.rowconfigure(0, weight=1)
        self.left_scroll = ScrollableFrame(self.left_panel)
        self.left_scroll.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        lp = self.left_scroll.inner

        self.mods_label = ttk.Label(lp)
        self.mods_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 2))
        self.ht_tile = ModTile(lp, variable=self.mod_hidden_var,
                               on_toggle=self.on_mods_change,
                               on_help=self.show_hidden_help)
        self.ht_tile.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        self.ar_tile = ModTile(lp, variable=self.mod_autoranks_var,
                               on_toggle=self.on_mods_change,
                               on_help=self.show_autoranks_help)
        self.ar_tile.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        self.rt_tile = ModTile(lp, variable=self.mod_randomtank_var,
                               on_toggle=self.on_mods_change,
                               on_help=self.show_randomtank_help)
        self.rt_tile.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        self.project_label = ttk.Label(lp)
        self.project_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 2))
        self.seg_project = SegmentedControl(
            lp, values=('wargaming', 'lesta'),
            variable=self.project_var, command=self.on_project_seg, width=13)
        self.seg_project.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        self.dvpl_label = ttk.Label(lp)
        self.dvpl_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 2))
        self.seg_dvpl = SegmentedControl(
            lp, values=('DVPL', 'NON-DVPL'),
            variable=self.dvpl_var, command=self.on_dvpl_seg, width=13)
        self.seg_dvpl.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=(0, 8))

        self.dlc_frame = ttk.LabelFrame(lp, padding="6")
        self.dlc_frame.grid(row=8, column=0, sticky=(tk.W, tk.E))
        self.dlc_frame.columnconfigure(0, weight=1)
        self.dlc_check = ttk.Checkbutton(self.dlc_frame, variable=self.dlc_var,
                                         command=self.on_dlc_change)
        self.dlc_check.grid(row=0, column=0, sticky=tk.W)
        self.dlc_hint = ttk.Label(self.dlc_frame, wraplength=250, justify=tk.LEFT)
        self.dlc_hint.grid(row=1, column=0, sticky=tk.W, pady=(4, 6))
        self.btn_dlc_folder = ttk.Button(self.dlc_frame, command=self.toggle_dlc_popup)
        self.btn_dlc_folder.grid(row=2, column=0, sticky=(tk.W, tk.E))

        actions = ttk.Frame(lp)
        actions.grid(row=10, column=0, sticky=(tk.W, tk.E, tk.S), pady=(8, 0))
        actions.columnconfigure(0, weight=1)
        self.btn_run = ttk.Button(actions, command=self.toggle_run_popup)
        self.btn_run.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        self.btn_restore = ttk.Button(actions, command=self.restore_operation)
        self.btn_restore.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 4))
        self.btn_stats = ttk.Button(actions, command=self.stats_operation)
        self.btn_stats.grid(row=2, column=0, sticky=(tk.W, tk.E))

        # spacer pushes actions to the bottom so fullscreen has no dead zone
        self.left_spacer = ttk.Frame(lp)
        self.left_spacer.grid(row=9, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        lp.rowconfigure(9, weight=1)

        # Right: big notebook fills all remaining space
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab 1: log
        self.log_tab = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.log_tab, text='...')
        log_controls = ttk.Frame(self.log_tab)
        log_controls.pack(fill=tk.X, pady=(0, 4))
        self.btn_copy_log = ttk.Button(log_controls, command=self.copy_log)
        self.btn_copy_log.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_clear_log = ttk.Button(log_controls, command=self.clear_log)
        self.btn_clear_log.pack(side=tk.LEFT)
        self.log_hint_label = ttk.Label(log_controls)
        self.log_hint_label.pack(side=tk.RIGHT)
        self.log_widget = LogWidget(self.log_tab)
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        # Tab 2: game files, Tab 3: DLC files
        self.game_tab = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.game_tab, text='...')
        self.exp_game = self._build_explorer_tab(self.game_tab, which='game')
        self.dlc_tab = ttk.Frame(self.notebook, padding="6")
        self.notebook.add(self.dlc_tab, text='...')
        self.exp_dlc = self._build_explorer_tab(self.dlc_tab, which='dlc')

        # Status bar
        self.status_bar = ttk.Frame(self.main_frame)
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(8, 0))
        self.status_dot = tk.Label(self.status_bar, text="●", font=('', 11))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 6))
        self.status_text = ttk.Label(self.status_bar)
        self.status_text.pack(side=tk.LEFT)
        self.version_label = ttk.Label(self.status_bar, font=('', 9))
        self.version_label.pack(side=tk.RIGHT, padx=(8, 0))
        self.bar = BarWithText(self.status_bar, height=22)
        self.bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    # ---------- embedded file explorer ----------
    def _build_explorer_tab(self, parent, which):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 4))
        refresh_btn = ttk.Button(toolbar, command=lambda: self.refresh_explorers())
        refresh_btn.pack(side=tk.LEFT, padx=(0, 6))
        reveal_btn = ttk.Button(toolbar, command=lambda: self.reveal_selected(which))
        reveal_btn.pack(side=tk.LEFT, padx=(0, 6))
        mod_var = tk.BooleanVar(value=False)
        mod_check = ttk.Checkbutton(toolbar, variable=mod_var,
                                    command=lambda: self._toggle_modview(which))
        mod_check.pack(side=tk.LEFT)
        body = ttk.Frame(parent)
        body.pack(fill=tk.BOTH, expand=True)
        tree = FileTree(body, on_open=self.reveal_in_explorer)
        tree.pack(fill=tk.BOTH, expand=True)
        modview = ModFileView(body)
        return {'refresh': refresh_btn, 'reveal': reveal_btn, 'check': mod_check,
                'mod_var': mod_var, 'body': body, 'tree': tree, 'modview': modview,
                'which': which}

    def _toggle_modview(self, which):
        exp = self.exp_game if which == 'game' else self.exp_dlc
        if exp['mod_var'].get():
            exp['tree'].pack_forget()
            exp['modview'].pack(fill=tk.BOTH, expand=True)
        else:
            exp['modview'].pack_forget()
            exp['tree'].pack(fill=tk.BOTH, expand=True)

    def _expected_paths(self):
        """(game_files, dlc_files): full paths of mod files for highlight."""
        from core import orchestrator as _orc
        game_set, dlc_set = set(), set()
        game_path = self.game_path_var.get().strip()
        dlc_root = get_dlc_root(self.project_var.get())
        for mid in self.selected_mods():
            for rel in _orc.mod_rel_paths(mid):
                game_set.add(os.path.join(game_path, "Data", rel))
                game_set.add(os.path.join(game_path, "Data", rel) + ".dvpl")
                if dlc_root:
                    dlc_set.add(os.path.join(dlc_root, rel) + ".dvpl")
        return game_set, dlc_set

    def _mod_sections(self):
        from core import orchestrator as _orc
        from gui.widgets import _fmt_size as _fmt
        game_path = self.game_path_var.get().strip()
        dlc_root = get_dlc_root(self.project_var.get())
        sections = []
        mod_titles = {'hidden_tanks': self.loc('mod_hidden_tanks'),
                      'autoranks': self.loc('mod_autoranks'),
                      'random_tank': self.loc('mod_random_tank')}
        for mid in self.selected_mods():
            title = mod_titles.get(mid, mid)
            rows = []
            for rel in _orc.mod_rel_paths(mid):
                plain = os.path.join(game_path, "Data", rel)
                dvpl = plain + ".dvpl"
                parts = []
                size_text = "—"
                for cand in (plain, dvpl):
                    if os.path.exists(cand):
                        parts.append("✓" if cand == plain else "✓ .dvpl")
                        if size_text == "—":
                            try:
                                size_text = _fmt(os.path.getsize(cand))
                            except OSError:
                                pass
                game_state = " / ".join(parts) if parts else "—"
                dlc_file = os.path.join(dlc_root, rel) + ".dvpl" if dlc_root else None
                if dlc_file and os.path.exists(dlc_file):
                    dlc_state = "✓ .dvpl"
                    if size_text == "—":
                        try:
                            size_text = _fmt(os.path.getsize(dlc_file))
                        except OSError:
                            pass
                else:
                    dlc_state = "—"
                rows.append((rel, size_text, game_state, dlc_state))
            sections.append((title, rows))
        return sections

    def _rebuild_modviews(self):
        sections = self._mod_sections()
        for exp in (self.exp_game, self.exp_dlc):
            exp['modview'].set_headings(self.loc('col_name'), self.loc('col_size'),
                                        self.loc('mv_game'), self.loc('mv_dlc'))
            exp['modview'].rebuild(sections)

    def _current_modified(self):
        return get_modified_files(self.game_path_var.get().strip(),
                                  self.selected_mods(),
                                  get_dlc_root(self.project_var.get()))

    def refresh_explorers(self):
        game_set, dlc_set = self._expected_paths()
        modset = self._current_modified()
        mod_label = self.loc('st_modified')
        game_path = self.game_path_var.get().strip()
        if game_path and os.path.isdir(game_path):
            placeholder = None
        elif game_path:
            placeholder = self.loc('tree_no_folder')
        else:
            placeholder = self.loc('tree_no_path')
        self.exp_game['tree'].set_highlight(game_set)
        self.exp_game['tree'].set_modified(modset, mod_label)
        self.exp_game['tree'].set_root(game_path if game_path else None, placeholder)
        dlc_root = get_dlc_root(self.project_var.get())
        self.exp_dlc['tree'].set_highlight(dlc_set)
        self.exp_dlc['tree'].set_modified(modset, mod_label)
        self.exp_dlc['tree'].set_root(dlc_root, self.loc('tree_no_folder'))
        self._rebuild_modviews()

    def update_explorer_texts(self):
        self.notebook.tab(self.log_tab, text=self.loc('frame_log'))
        self.notebook.tab(self.game_tab, text=self.loc('tab_game'))
        self.notebook.tab(self.dlc_tab, text=self.loc('tab_dlc'))
        modset = self._current_modified()
        mod_label = self.loc('st_modified')
        for exp in (self.exp_game, self.exp_dlc):
            exp['refresh'].config(text=self.loc('btn_refresh'))
            exp['reveal'].config(text=self.loc('btn_reveal'))
            exp['check'].config(text=self.loc('mod_only'))
            exp['tree'].set_headings(self.loc('col_name'), self.loc('col_size'),
                                     self.loc('col_status'))
            exp['tree'].set_modified(modset, mod_label)
        self._rebuild_modviews()

    def reveal_in_explorer(self, path):
        target = path if os.path.isdir(path) else os.path.dirname(path)
        ok, err = open_folder_in_explorer(target)
        if not ok:
            self._close_all_popups()
            messagebox.showerror(self.loc('msg_error_title'), f"{target}\n{err}")

    def reveal_selected(self, which):
        exp = self.exp_game if which == 'game' else self.exp_dlc
        path = exp['tree'].selected_path()
        if not path:
            path = (self.game_path_var.get().strip() if which == 'game'
                    else get_dlc_root(self.project_var.get()))
        if path:
            self.reveal_in_explorer(path)

    # ---------- header buttons ----------
    def toggle_lang_popup(self):
        if self._busy:
            return
        if self._lang_popup is not None:
            try:
                self._lang_popup.close()
            except Exception:
                pass
            self._lang_popup = None
            return
        self._close_all_popups()
        try:
            x = self.lang_btn.winfo_rootx()
            y = self.lang_btn.winfo_rooty() + self.lang_btn.winfo_height() + 2
        except Exception:
            x, y = 200, 200
        options = [(code, self.locales[code].get('lang_code', code.upper()))
                   for code in self.available_langs]
        popup = ChoicePopup(self.root, x, y, options, on_pick=self._lang_picked)
        self._lang_popup = popup
        fit_popup_to_button(self.root, popup, self.lang_btn)

        def on_destroy(_e=None):
            self._lang_popup = None
            try:
                if getattr(self, '_lang_outside_binding', None):
                    self.root.unbind('<Button-1>', self._lang_outside_binding)
                    self._lang_outside_binding = None
            except Exception:
                pass
        popup.bind('<Destroy>', on_destroy)
        self._lang_outside_binding = self.root.bind(
            '<Button-1>', self._close_lang_popup_on_outside_click, add='+')

    def _close_lang_popup_on_outside_click(self, event):
        popup = self._lang_popup
        if popup is None:
            return
        try:
            widget = event.widget
            wname = str(widget)
        except Exception:
            return
        try:
            if wname.startswith(str(popup)):
                return
            if widget is self.lang_btn:
                return
        except Exception:
            pass
        try:
            popup.close()
        except Exception:
            pass
        finally:
            self._lang_popup = None
            try:
                if getattr(self, '_lang_outside_binding', None):
                    self.root.unbind('<Button-1>', self._lang_outside_binding)
                    self._lang_outside_binding = None
            except Exception:
                pass

    def _lang_picked(self, code):
        if code in self.locales:
            self.current_lang = code
        self.save_state()
        self.update_texts()
        self.refresh_dlc_hint()
        self.refresh_explorers()

    def _track_popups(self, event=None):
        # <Configure> bubbles up from children — react to the root only.
        # Popups hide (not follow) on any window move/resize.
        try:
            if event is not None and event.widget is not self.root:
                return
        except Exception:
            pass
        self._close_all_popups()

    def _wheel_closes_popups(self, event=None):
        if (self._dlc_popup is not None or self._run_popup is not None or
                self._lang_popup is not None):
            self._close_all_popups()

    def _close_all_popups(self):
        for attr in ('_dlc_popup', '_run_popup', '_lang_popup'):
            popup = getattr(self, attr, None)
            if popup is not None:
                try:
                    popup.close()
                except Exception:
                    pass
                try:
                    setattr(self, attr, None)
                except Exception:
                    pass
        for binding_attr in ('_dlc_outside_binding', '_run_outside_binding',
                             '_lang_outside_binding'):
            try:
                binding = getattr(self, binding_attr, None)
                if binding:
                    self.root.unbind('<Button-1>', binding)
                setattr(self, binding_attr, None)
            except Exception:
                pass

    def cycle_theme(self):
        if self._busy:
            return
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.save_state()
        self.update_theme()
        self.update_texts()

    # ---------- events ----------
    def _commit_path(self):
        self.save_state()
        self.refresh_path_status()
        self.refresh_explorers()

    def browse_folder(self):
        if self._busy:
            return
        folder = filedialog.askdirectory()
        if folder:
            self.game_path_var.set(folder)
            self.save_state()
            self.refresh_path_status()
            self.refresh_dlc_hint()
            self.refresh_explorers()

    def on_project_seg(self, value):
        self.project_var.set(value)
        self.save_state()
        self.refresh_dlc_hint()
        self.refresh_explorers()

    def on_dvpl_seg(self, value):
        self.dvpl_var.set(value)
        self.save_state()
        self.refresh_explorers()

    def on_dlc_change(self):
        if self._busy:
            return
        self.save_state()
        self.refresh_dlc_hint()

    def on_mods_change(self):
        if self._busy:
            return
        self.save_state()
        self.refresh_dlc_hint()
        self.refresh_explorers()

    # ---------- status / validation ----------
    def set_status(self, kind):
        self._status_kind = kind
        colors = {'ready': '#888888', 'busy': '#e0a030',
                  'done': '#3fa34d', 'error': '#d64545'}
        try:
            self.status_dot.config(fg=colors.get(kind, '#888888'))
            self.status_text.config(text=self.loc(f'status_{kind}'))
        except Exception:
            pass

    def refresh_path_status(self):
        path = self.game_path_var.get().strip()
        ok = bool(path) and os.path.isdir(os.path.join(path, "Data"))
        try:
            self.path_dot.config(fg='#3fa34d' if ok else ('#888888' if not path else '#d64545'))
        except Exception:
            pass
        return ok

    def refresh_dlc_hint(self):
        try:
            mods = self.selected_mods()
            dlc_root = get_dlc_root(self.project_var.get())
            presence = orchestrator.check_dlc_presence(dlc_root, mods) if mods else {}
            total = sum(len(v) for v in presence.values())
            if total > 0:
                self.dlc_hint.config(text=self.loc('dlc_hint_found', count=total))
            else:
                self.dlc_hint.config(text=self.loc('dlc_hint_none'))
        except Exception:
            pass

    # ---------- DLC folder popup ----------
    def toggle_dlc_popup(self):
        if self._busy:
            return
        if self._dlc_popup is not None:
            try:
                self._dlc_popup.close()
            except Exception:
                pass
            self._dlc_popup = None
            return
        self._close_all_popups()
        try:
            x = self.btn_dlc_folder.winfo_rootx()
            y = self.btn_dlc_folder.winfo_rooty() + self.btn_dlc_folder.winfo_height() + 2
        except Exception:
            x, y = 200, 200
        popup = DlcFolderPopup(self.root, x, y, on_pick=self.open_dlc_project_folder)
        popup.set_labels(self.loc('dlc_popup_wg'), self.loc('dlc_popup_lesta'))
        fit_popup_to_button(self.root, popup, self.btn_dlc_folder)
        self._dlc_popup = popup

        def on_destroy(_e=None):
            self._dlc_popup = None
            try:
                if getattr(self, '_dlc_outside_binding', None):
                    self.root.unbind('<Button-1>', self._dlc_outside_binding)
                    self._dlc_outside_binding = None
            except Exception:
                pass
        popup.bind('<Destroy>', on_destroy)
        self._dlc_outside_binding = self.root.bind(
            '<Button-1>', self._close_dlc_popup_on_outside_click, add='+')

    def _close_dlc_popup_on_outside_click(self, event):
        popup = self._dlc_popup
        if popup is None:
            return
        try:
            widget = event.widget
            wname = str(widget)
        except Exception:
            return
        try:
            if wname.startswith(str(popup)):
                return
            if widget is self.btn_dlc_folder:
                return
        except Exception:
            pass
        try:
            popup.close()
        except Exception:
            pass
        finally:
            self._dlc_popup = None
            try:
                if getattr(self, '_dlc_outside_binding', None):
                    self.root.unbind('<Button-1>', self._dlc_outside_binding)
                    self._dlc_outside_binding = None
            except Exception:
                pass

    def open_dlc_project_folder(self, project):
        path = get_dlc_root(project)
        ok, err = open_folder_in_explorer(path)
        if not ok:
            self._close_all_popups()
            messagebox.showerror(self.loc('msg_error_title'), f"{path}\n{err}")

    # ---------- Run popup (like DLC-folder button) ----------
    def toggle_run_popup(self):
        if self._busy:
            return
        if self._run_popup is not None:
            try:
                self._run_popup.close()
            except Exception:
                pass
            self._run_popup = None
            return
        self._close_all_popups()
        try:
            x = self.btn_run.winfo_rootx()
            y = self.btn_run.winfo_rooty() + self.btn_run.winfo_height() + 2
        except Exception:
            x, y = 200, 200
        popup = OptionsPopup(self.root, x, y, on_pick=self._run_picked,
                             value_top='generate', value_bottom='export')
        popup.set_labels(self.loc('run_opt_replace'), self.loc('run_opt_export'))
        fit_popup_to_button(self.root, popup, self.btn_run)
        self._run_popup = popup

        def on_destroy(_e=None):
            self._run_popup = None
            try:
                if getattr(self, '_run_outside_binding', None):
                    self.root.unbind('<Button-1>', self._run_outside_binding)
                    self._run_outside_binding = None
            except Exception:
                pass
        popup.bind('<Destroy>', on_destroy)
        self._run_outside_binding = self.root.bind(
            '<Button-1>', self._close_run_popup_on_outside_click, add='+')

    def _close_run_popup_on_outside_click(self, event):
        popup = self._run_popup
        if popup is None:
            return
        try:
            widget = event.widget
            wname = str(widget)
        except Exception:
            return
        try:
            if wname.startswith(str(popup)):
                return
            if widget is self.btn_run:
                return
        except Exception:
            pass
        try:
            popup.close()
        except Exception:
            pass
        finally:
            self._run_popup = None
            try:
                if getattr(self, '_run_outside_binding', None):
                    self.root.unbind('<Button-1>', self._run_outside_binding)
                    self._run_outside_binding = None
            except Exception:
                pass

    def _run_picked(self, mode):
        self.operation_var.set(mode)
        self.save_state()
        self.run_operation(mode=mode)

    # ---------- help ----------
    def show_hidden_help(self):
        self._close_all_popups()
        show_help_dialog(self.root, self.loc('help_hidden_title'),
                         self.loc('help_hidden_body'), colors=self._help_colors)

    def show_autoranks_help(self):
        self._close_all_popups()
        show_help_dialog(self.root, self.loc('help_autoranks_title'),
                         self.loc('help_autoranks_body'), colors=self._help_colors)

    def show_randomtank_help(self):
        self._close_all_popups()
        show_help_dialog(self.root, self.loc('help_random_tank_title'),
                         self.loc('help_random_tank_body'), colors=self._help_colors)

    # ---------- log helpers ----------
    def log(self, message):
        self.log_widget.log(message)

    def copy_log(self):
        self.log_widget.copy_selection()

    def clear_log(self):
        self.log_widget.clear()

    # ---------- texts / theme ----------
    def update_texts(self):
        self.root.title(self.loc('app_title'))
        self.title_label.config(text=self.loc('app_short'))
        self.lang_btn.config(
            text=self.locales.get(self.current_lang, {}).get('lang_code', self.current_lang.upper()))
        self.theme_btn.config(text="☀" if self.current_theme == 'dark' else "☾")
        self.game_group.config(text=self.loc('frame_game_path'))
        self.path_label.config(text=self.loc('label_game_path'))
        self.btn_browse.config(text=self.loc('btn_browse'))
        self.project_label.config(text=self.loc('label_project'))
        self.seg_project.set_labels([self.loc('project_wargaming'), self.loc('project_lesta')])
        self.dvpl_label.config(text=self.loc('label_dvpl'))
        self.seg_dvpl.set_labels([self.loc('dvpl_mode_dvpl'), self.loc('dvpl_mode_nondvpl')])
        self.dlc_frame.config(text=self.loc('frame_dlc'))
        self.dlc_check.config(text=self.loc('dlc_check'))
        self.btn_dlc_folder.config(text=self.loc('btn_dlc_folder'))
        self.mods_label.config(text=self.loc('frame_mods'))
        self.ht_tile.set_texts(self.loc('mod_hidden_tanks'), self.loc('mod_hidden_desc'),
                               self.loc('tile_ht_meta'))
        self.ar_tile.set_texts(self.loc('mod_autoranks'), self.loc('mod_autoranks_desc'),
                               self.loc('tile_ar_meta'))
        self.rt_tile.set_texts(self.loc('mod_random_tank'), self.loc('mod_random_tank_desc'),
                               self.loc('tile_rt_meta'))
        self.btn_run.config(text=self.loc('btn_run'))
        self.btn_restore.config(text=self.loc('btn_restore'))
        self.btn_stats.config(text=self.loc('btn_stats'))
        self.btn_copy_log.config(text=self.loc('btn_copy_log'))
        self.btn_clear_log.config(text=self.loc('btn_clear_log'))
        self.log_hint_label.config(text=self.loc('hint_copy'))
        self.log_widget.set_menu_labels(self.loc('menu_copy'), self.loc('menu_select_all'),
                                        self.loc('menu_clear'))
        self.update_explorer_texts()
        self.version_label.config(text=VERSION)
        try:
            if not self._busy:
                self.bar.set_idle(self.loc('progress_idle'))
        except Exception:
            pass
        self.set_status(self._status_kind)

    def update_theme(self):
        dark = self.current_theme == 'dark'
        if dark:
            bg, fg, entry_bg = '#1e1e1e', '#ffffff', '#2d2d2d'
            select_bg, trough, scroll, active = '#3a5f7a', '#2d2d2d', '#4a4a4a', '#5a5a5a'
            light, darkc, frame_bg = '#3a3a3a', '#1a1a1a', '#2d2d2d'
            label_bg, button_bg, combo_bg, arrow = '#1e1e1e', '#2d2d2d', '#2d2d2d', '#ffffff'
            tile_bg, tile_sel_bg = '#242424', '#2f3f4a'
            tile_border, tile_sel_border = '#3a3a3a', '#3a5f7a'
            meta_fg = '#aaaaaa'
        else:
            bg, fg, entry_bg = '#f0f0f0', '#000000', '#ffffff'
            select_bg, trough, scroll, active = '#cce8ff', '#e0e0e0', '#d0d0d0', '#b0b0b0'
            light, darkc, frame_bg = '#e8e8e8', '#c0c0c0', '#f0f0f0'
            label_bg, button_bg, combo_bg, arrow = '#f0f0f0', '#e0e0e0', '#ffffff', '#000000'
            tile_bg, tile_sel_bg = '#f7f7f7', '#e2eef7'
            tile_border, tile_sel_border = '#c0c0c0', '#7fb8dd'
            meta_fg = '#555555'

        self.root.configure(bg=bg)
        disabled_fg = '#888888'
        self._help_colors = (entry_bg, fg, select_bg)
        self.style.configure('.', background=bg, foreground=fg, fieldbackground=entry_bg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabelframe', background=frame_bg, foreground=fg,
                             bordercolor=light, lightcolor=light, darkcolor=darkc)
        self.style.configure('TLabelframe.Label', background=frame_bg, foreground=fg)
        self.style.configure('TLabel', background=label_bg, foreground=fg)
        self.style.configure('TButton', background=button_bg, foreground=fg, padding=6,
                             focuscolor=active)
        self.style.map('TButton',
                       foreground=[('disabled', disabled_fg),
                                   ('pressed', fg),
                                   ('active', fg),
                                   ('focus', fg)],
                       background=[('disabled', button_bg),
                                   ('pressed', select_bg),
                                   ('active', active),
                                   ('focus', button_bg)],
                       focuscolor=[('focus', active)],
                       bordercolor=[('focus', active),
                                    ('active', light)])
        self.style.map('TCheckbutton',
                       foreground=[('disabled', disabled_fg),
                                   ('active', fg)],
                       background=[('disabled', bg),
                                   ('active', bg),
                                   ('pressed', bg),
                                   ('focus', bg)])
        self.style.map('TRadiobutton',
                       foreground=[('disabled', disabled_fg),
                                   ('active', fg)],
                       background=[('disabled', bg),
                                   ('active', bg),
                                   ('pressed', bg),
                                   ('focus', bg)])
        self.style.configure('TEntry', fieldbackground=entry_bg, foreground=fg,
                             selectbackground=select_bg, selectforeground=fg)
        self.style.configure('TCombobox', fieldbackground=entry_bg, background=combo_bg,
                             foreground=fg, arrowcolor=arrow)
        self.style.map('TCombobox',
                       fieldbackground=[('disabled', trough),
                                        ('readonly', entry_bg),
                                        ('focus', entry_bg)],
                       foreground=[('disabled', disabled_fg)],
                       background=[('disabled', button_bg),
                                   ('readonly', combo_bg),
                                   ('pressed', active),
                                   ('active', active)],
                       selectbackground=[('readonly', select_bg)],
                       selectforeground=[('readonly', fg)])
        self.root.option_add('*TCombobox*Listbox.background', entry_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', fg)
        self.root.option_add('*TCombobox*Listbox.selectBackground', select_bg)
        self.root.option_add('*TCombobox*Listbox.selectForeground', fg)
        # Tiles
        self.style.configure('Tile.TFrame', background=tile_bg, bordercolor=tile_border)
        self.style.configure('Tile.TLabel', background=tile_bg, foreground=fg)
        self.style.configure('Tile.Selected.TFrame', background=tile_sel_bg,
                             bordercolor=tile_sel_border)
        self.style.configure('Tile.Selected.TLabel', background=tile_sel_bg, foreground=fg)
        self.style.configure('TileMeta.TLabel', background=tile_bg, foreground=meta_fg)
        # Segmented
        self.style.configure('Seg.TButton', background=button_bg, foreground=fg, padding=6,
                             focuscolor=active)
        self.style.map('Seg.TButton',
                       foreground=[('disabled', disabled_fg), ('active', fg)],
                       background=[('disabled', button_bg), ('pressed', select_bg),
                                   ('active', active)])
        self.style.configure('Seg.Selected.TButton', background=select_bg, foreground=fg,
                             padding=6, focuscolor=active)
        self.style.map('Seg.Selected.TButton',
                       foreground=[('disabled', disabled_fg)],
                       background=[('disabled', button_bg)])
        self.style.configure('Vertical.TScrollbar', background=scroll, troughcolor=trough,
                             arrowcolor=arrow, bordercolor=bg)
        try:
            self.bar.set_colors(fill=select_bg, trough=trough, fg=fg, border=light)
        except Exception:
            pass
        # Notebook + trees
        self.style.configure('TNotebook', background=bg, bordercolor=bg)
        self.style.configure('TNotebook.Tab', background=button_bg, foreground=fg,
                             padding=(12, 4), focuscolor=active)
        self.style.map('TNotebook.Tab',
                       foreground=[('disabled', disabled_fg), ('selected', fg)],
                       background=[('disabled', button_bg), ('selected', frame_bg),
                                   ('active', active)])
        self.style.configure('Treeview', background=entry_bg, foreground=fg,
                             fieldbackground=entry_bg, bordercolor=bg)
        self.style.map('Treeview',
                       background=[('selected', select_bg)],
                       foreground=[('selected', fg)])
        self.style.configure('Treeview.Heading', background=button_bg, foreground=fg)
        self.style.map('Treeview.Heading',
                       background=[('active', active)])
        mod_accent = '#8fc3ea' if dark else '#0b5fa5'
        for _tree in (self.exp_game['tree'].tree, self.exp_dlc['tree'].tree):
            try:
                _tree.tag_configure('mod', foreground=mod_accent,
                                    font=('', 9, 'bold'))
            except Exception:
                pass
        try:
            self.status_bar.configure(style='TFrame')
            self.status_dot.config(bg=bg)
            self.path_dot.config(bg=frame_bg)
            self.left_scroll.set_bg(bg)
            self.log_widget.text.configure(bg=entry_bg, fg=fg, insertbackground=fg,
                                           selectbackground=select_bg, selectforeground=fg,
                                           relief='flat')
        except Exception:
            pass
        try:
            self.ht_tile.refresh()
            self.ar_tile.refresh()
            self.rt_tile.refresh()
            self.seg_project.refresh()
            self.seg_dvpl.refresh()
        except Exception:
            pass

    # ---------- validation ----------
    def validated_context(self):
        game_path = self.game_path_var.get().strip()
        if not game_path or not os.path.isdir(os.path.join(game_path, "Data")):
            self._close_all_popups()
            messagebox.showerror(self.loc('msg_error_title'), self.loc('error_invalid_path'))
            return None
        mods = self.selected_mods()
        if not mods:
            self._close_all_popups()
            messagebox.showerror(self.loc('msg_error_title'), self.loc('error_no_mod'))
            return None
        self.save_state()
        return {
            'game_path': game_path,
            'mod_ids': mods,
            'dvpl_mode': self.dvpl_var.get(),
            'use_dlc': self.dlc_var.get(),
            'dlc_root': get_dlc_root(self.project_var.get()),
        }

    # ---------- background operations ----------
    def _controls(self):
        return [self.btn_run, self.btn_restore, self.btn_stats, self.btn_browse,
                self.path_entry, self.dlc_check, self.btn_dlc_folder,
                self.lang_btn, self.theme_btn,
                *self.seg_project.buttons, *self.seg_dvpl.buttons,
                self.btn_copy_log, self.btn_clear_log,
                self.exp_game['refresh'], self.exp_game['reveal'], self.exp_game['check'],
                self.exp_dlc['refresh'], self.exp_dlc['reveal'], self.exp_dlc['check']]

    def _progress_text(self, done, total):
        try:
            pct = 100 if total <= 0 else min(100, round(100 * done / total))
        except Exception:
            pct = 0
        return self.loc('progress_text', pct=pct, done=done, total=total)

    def _set_busy(self, busy):
        self._busy = busy
        for w in self._controls():
            try:
                w.state(['disabled' if busy else '!disabled'])
            except Exception:
                pass
        self.ht_tile._locked = busy
        self.ar_tile._locked = busy
        self.rt_tile._locked = busy
        try:
            if busy:
                self.bar.set_values(0, 0, self._progress_text(0, 0))
            else:
                self.bar.set_idle(self.loc('progress_idle'))
        except Exception:
            pass

    def _launch(self, worker, on_done=None):
        if self._busy:
            return
        ctx = self.validated_context()
        if not ctx:
            return
        self.set_status('busy')
        self._set_busy(True)
        tr = lambda k, **kw: self.loc(k, **kw)

        def boot():
            try:
                pg = lambda d, t: self._queue.put(('progress', (d, t)))
                result = worker(ctx, lambda m: self._queue.put(('log', m)), tr, pg)
                self._queue.put(('done', (result, on_done)))
            except Exception:
                self._queue.put(('error', traceback.format_exc()))
        threading.Thread(target=boot, daemon=True).start()
        self.root.after(120, self._poll)

    def _poll(self):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == 'log':
                    self.log(payload)
                elif kind == 'progress':
                    try:
                        done, total = payload
                        self.bar.set_values(done, total,
                                            self._progress_text(done, total))
                    except Exception:
                        pass
                elif kind == 'done':
                    result, on_done = payload
                    self._set_busy(False)
                    self.set_status('done')
                    self.log(self.loc('log_done'))
                    self.refresh_explorers()
                    self._close_all_popups()
                    messagebox.showinfo(self.loc('msg_done_title'), self.loc('msg_done_body'))
                    if on_done is not None:
                        try:
                            on_done(result)
                        except Exception as e:
                            self.log(self.loc('log_error', error=str(e)))
                    return
                elif kind == 'error':
                    self._set_busy(False)
                    self.set_status('error')
                    self.log(self.loc('log_error', error=payload))
                    self._close_all_popups()
                    messagebox.showerror(self.loc('msg_error_title'), payload[-500:])
                    return
        except queue.Empty:
            pass
        if self._busy:
            self.root.after(120, self._poll)

    # ---------- operations ----------
    def run_operation(self, mode=None):
        mode = mode or self.operation_var.get()
        self.operation_var.set(mode)
        if mode == 'export':
            def worker(ctx, tl, tr, pg):
                self._queue.put(('log', self.loc(
                    'log_start_export', mods="+".join(ctx['mod_ids']),
                    mode=ctx['dvpl_mode'], dlc=ctx['use_dlc'])))
                return orchestrator.export_mods(log=tl, tr=tr, progress_cb=pg, **ctx)
            self._launch(worker, on_done=self._offer_open_folder)
        else:
            def worker(ctx, tl, tr, pg):
                self._queue.put(('log', self.loc(
                    'log_start_generate', mods="+".join(ctx['mod_ids']),
                    mode=ctx['dvpl_mode'], dlc=ctx['use_dlc'])))
                return orchestrator.generate_mods(log=tl, tr=tr, progress_cb=pg, **ctx)
            self._launch(worker)

    def _offer_open_folder(self, path):
        try:
            self._close_all_popups()
            if messagebox.askyesno(self.loc('msg_open_result_title'),
                                   self.loc('msg_open_result_body')):
                open_folder_in_explorer(path)
        except Exception:
            pass

    def restore_operation(self):
        def worker(ctx, tl, tr, pg):
            self._queue.put(('log', self.loc('log_restore_start')))
            return orchestrator.restore_mods(ctx['game_path'], ctx['mod_ids'],
                                             ctx['dlc_root'], log=tl, tr=tr,
                                             progress_cb=pg)
        self._launch(worker)

    def stats_operation(self):
        def worker(ctx, tl, tr, pg):
            self._queue.put(('log', self.loc('log_stats_start')))
            return orchestrator.collect_stats(log=tl, tr=tr, progress_cb=pg, **ctx)
        self._launch(worker, on_done=self.display_stats)

    def display_stats(self, stats):
        if "hidden_tanks" in stats:
            nations = stats["hidden_tanks"]
            self.log(f"\n{self.loc('statistics_title')}:\n" + "=" * 30)
            names = {'CN': 'China', 'EU': 'Europe', 'FR': 'France', 'DE': 'Germany',
                     'JP': 'Japan', 'HN': 'Other', 'UK': 'UK', 'US': 'USA', 'SU': 'USSR'}
            tv = th = 0
            for code, st in nations.items():
                self.log(f"{names.get(code, code)}: {self.loc('stat_visible')}={st['visible']}, "
                         f"{self.loc('stat_hidden_ordinary')}={st['hidden_ordinary']}, "
                         f"{self.loc('stat_hidden_collectible')}={st['hidden_collectible']}, "
                         f"{self.loc('stat_hidden_premium')}={st['hidden_premium']}")
                tv += st['visible']
                th += st['hidden_ordinary'] + st['hidden_collectible'] + st['hidden_premium']
            self.log(f"{self.loc('stat_total_visible')}: {tv}")
            self.log(f"{self.loc('stat_total_hidden')}: {th}")
            self.log(f"{self.loc('stat_grand_total')}: {tv + th}")
        if "autoranks" in stats:
            self.log(f"\n{self.loc('stats_autoranks_title')}:")
            for d in stats["autoranks"]:
                if not d.get('found'):
                    self.log(f"  ✗ {d['rel']}")
                else:
                    where = "DLC" if d.get('is_dlc') else "Game"
                    self.log(f"  {d['rel']} [{where}]: {d['would_change']} edit(s)")
        if "random_tank" in stats:
            self.log(f"\n{self.loc('stats_randomtank_title')}:")
            for d in stats["random_tank"]:
                if not d.get('found'):
                    self.log(f"  ✗ {d['rel']}")
                else:
                    where = "DLC" if d.get('is_dlc') else "Game"
                    self.log(f"  {d['rel']} [{where}]: {d['would_change']} edit(s)")


def main():
    root = tk.Tk()
    root.title("Blitz Mods Utility")
    root.minsize(920, 660)
    try:
        cfg = load_config()
        root.geometry(cfg.get('geometry', '1000x760'))
    except Exception:
        pass
    app = App(root)

    def on_close():
        try:
            app.save_state()
            app.config['geometry'] = root.geometry()
            save_config(app.config)
        except Exception:
            pass
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
