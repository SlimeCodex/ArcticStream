# Desc: Styles for the GUI
# This file is part of ArcticStream Library.

default_app = """
    QMainWindow {
        background-color: #1e1e1e;
    }
    QListWidget {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        margin: 0px;
        padding: 8px;
        
        border: none;
        border-radius: 4px;
    }
    QLabel {
        color: #dcdcdc;
        font-size: 13px;
    }
"""

# QToolTip ----------------------------

default_tooltip = """
    QToolTip {
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #292929;
        padding: 5px;
        border-radius: 4px;
        font-size: 12px;
        font-family: "Inconsolata";
    }
"""
    
# QWidgets --------------------------------

custom_bar_widget = """
    QWidget {
        background-color: #333333;
    }
"""

# Push buttons ----------------------------

default_button = """
    QPushButton {
        background-color: #333333;
        color: #ffffff;
        font-size: 12px;
        
        height: 30px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #292929;
    }
"""

custom_bar_button = """
    QPushButton {
        background-color: #333333;
        color: #ffffff;
        border-radius: 0px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #292929;
    }
"""

custom_bar_close_button = """
    QPushButton {
        background-color: #333333;
        color: #ffffff;
        border-radius: 0px;
    }
    QPushButton:hover {
        background-color: red;
    }
    QPushButton:pressed {
        background-color: darkred;
    }
"""

connectors_button = """
    QPushButton {
        background-color: #333333;
        color: #ffffff;
        
        height: 3000px;
        border-top-left-radius: 30px;
        border-top-right-radius: 30px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #292929;
    }
"""

connectors_desc_button = """
    QPushButton {
        background-color: #333333;
        color: #ffffff;
        
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
        border-bottom-left-radius: 30px;
        border-bottom-right-radius: 30px;
    }
    QPushButton:hover {
        background-color: #3d3d3d;
    }
    QPushButton:pressed {
        background-color: #292929;
    }
"""

# QLineEdit ----------------------------

default_line_edit = """
    QLineEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        margin: 0px;
        padding: 4px;
        
        border: none;
        border-radius: 4px;
    }
"""

console_send_line_edit = """
    QLineEdit {
        background-color: #555555;
        color: #ffffff;
        font-size: 12px;
    }
"""

console_status_line_edit = """
    QLineEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        border: none;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }
"""

updater_placeholder_line_edit = """
    QLineEdit {
        background: transparent;
        color: gray;
        
        font-size: 12px;
    }
"""

debug_bar_line_edit = """
    QLineEdit {
        background-color: #2b2b2b;
        color: #dcdcdc;
        font-size: 10px;
    }
"""

# QTextEdit ----------------------------

default_text_edit = """
    QTextEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        padding: 8px;
        margin: 0px;
        
        border: none;
        border-radius: 4px;
    }
"""

default_ptext_edit = """
    QPlainTextEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        padding-left: 8px;
        padding-right: 0px;
        padding-top: 8px;
        padding-bottom: 0px;
        margin: 0px;
        
        border: none;
        border-radius: 4px;
    }
"""

timestamp_ptext_edit = """
    QPlainTextEdit {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-size: 12px;
        
        padding: 8px;
        margin: 0px;
        
        border: none;
        border-radius: 4px;
    }
"""

updater_highligh_ptext_edit = """
    QPlainTextEdit {
        background-color: rgba(150, 150, 150, 0.5);
    }
"""

# QTabWidget ----------------------------

default_tab = """
    QTabWidget::pane {
        background-color: #2b2b2b;
        
        margin: 0px;
        padding: 0px;
        
        border-bottom-right-radius: 4px;
        border-bottom-left-radius: 4px;
    }
    QTabBar::tab {
        background: #333333;
        color: #dcdcdc;
        font-size: 12px;
        
        padding: 4px;
        margin-right: 4px;
        
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabWidget::tab-bar {
        alignment: left;
    }
    QTabBar::tab:hover {
        background: #3d3d3d;
    }
    QTabBar::tab:selected {
        background: #2b2b2b;
        border-bottom-color: #2b2b2b;
    }
    QTabBar::tab:!selected {
        margin-top: 2px;
    }
    QTabBar::scroller {
        width: 20px;
    }
    QTabBar QToolButton {
        background: #333333;
        border: 1px solid #292929;
        border-radius: 4px;
    }
    QTabBar QToolButton:hover {
        background: #3d3d3d;
    }
"""

# Scroll bars ----------------------------

scroll_bar_hide = """
    QScrollBar:vertical {
        width: 0px;
    }
    QScrollBar:horizontal {
        height: 0px;
    }
"""

default_scroll = """
    QScrollBar:vertical {
        border: 8px solid #1e1e1e;
        background-color: #2b2b2b;
        width: 24px;
        border-radius: 12px;
    }
    QScrollBar::handle:vertical {
        background-color: #555555;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #3d3d3d;
    }
    QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        border: 8px solid #1e1e1e;
        background-color: #2b2b2b;
        height: 24px;
        border-radius: 12px;
    }
    QScrollBar::handle:horizontal {
        background-color: #555555;
        min-width: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #3d3d3d;
    }
    QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
        border: none;
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }
"""

# Loading bar ----------------------------

default_loading_bar = """
    QProgressBar {
        background-color: #555555;
        color: #ffffff;
        font-size: 12px;
        
        height: 26px;
        padding: 0px;
        border-radius: 4px;
        
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: rgba(0, 100, 0, 128);
        border-radius: 4px;
    }
"""

uploader_loading_bar_fail = """
    QProgressBar {
        background-color: #555555;
        color: #ffffff;
        font-size: 12px;
        
        height: 26px;
        padding: 0px;
        border-radius: 4px;
        
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: rgba(139, 0, 0, 128);
        border-radius: 4px;
    }
"""

# QSplitters ----------------------------

default_splitter = """
    QSplitter::handle {
        background-color: #2b2b2b;
        border: none;
    }
    QSplitter::handle:hover {
        background-color: #3d3d3d;
    }
"""
