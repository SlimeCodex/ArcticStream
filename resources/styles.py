# Desc: Styles for the GUI
# This file is part of ArcticTerminal Library.

dark_theme_app = """
	QMainWindow {
		background-color: #1e1e1e;
        border: 2px solid #333333;
	}
	QMainWindow::title {
		background-color: #1e1e1e;
		color: #dcdcdc;
	}
	QListWidget {
		background-color: #1e1e1e;
		color: #dcdcdc;
		padding: 8px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
	QLabel {
		color: #dcdcdc;
	}
	QPushButton {
		background-color: #333333;
		color: #ffffff;
		border-radius: 4px;
		padding: 4px;
        height: 16px;
	}
	QPushButton:hover {
		background-color: #3d3d3d;
	}
	QPushButton:pressed {
		background-color: #292929;
	}
"""

close_button_style = """
	QPushButton {
		background-color: #333333;
		color: #ffffff;
		border-radius: 0px;
		padding: 4px;
        height: 16px;
	}
	QPushButton:hover {
		background-color: red;
	}
	QPushButton:pressed {
		background-color: darkred;
	}
"""

dark_theme_qle_debugf = """
	QLineEdit {
		background-color: #2b2b2b;
		color: #dcdcdc;
        
		margin: 0px;
		padding: 0px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 10px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_qpb_title = """
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

dark_theme_qte_printf = """
	QTextEdit {
		background-color: #1e1e1e;
		color: #dcdcdc;
		padding-top: 8px;
		padding-bottom: 8px;
		padding-left: 8px;
		padding-right: 8px;
		margin: 0px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_qle_singlef = """
	QLineEdit {
		background-color: #1e1e1e;
		color: #dcdcdc;
		padding: 4px;
		margin: 0px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_qle_send_data = """
	QLineEdit {
		background-color: #555555;
		color: #ffffff;
		padding: 4px;
		margin: 0px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: 1px solid #292929;
		border-radius: 4px;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_tab = """
	QTabWidget::pane {
		border-top: 2px solid #2b2b2b;
		background-color: #2b2b2b;
        
		margin: 0px;
		padding: 0px;
        
		border-bottom-right-radius: 2px;
		border-bottom-left-radius: 2px;
	}

	QTabBar::tab {
		background: #333333;
		color: #dcdcdc;
		padding: 6px;
		margin-right: 2px;
		border: 1px solid #292929;
		border-bottom-color: #2b2b2b;
		border-top-left-radius: 4px;
		border-top-right-radius: 4px;
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

dark_theme_scroll = """
	QScrollBar:vertical {
		border: none;
		background-color: #2b2b2b;
		width: 8px;
	}
	QScrollBar::handle:vertical {
		background-color: #555555;
		min-height: 20px;
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
		border: none;
		background-color: #2b2b2b;
		height: 8px;
		margin-bottom: 8px;
	}
	QScrollBar::handle:horizontal {
		background-color: #555555;
		min-height: 20px;
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

dark_theme_qte_ota_highlight = """
	QTextEdit {
		background-color: rgba(150, 150, 150, 0.5);
		color: #dcdcdc;
		padding-top: 8px;
		padding-bottom: 8px;
		padding-left: 8px;
		padding-right: 8px;
		margin: 0px;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_qle_ota_placeholder = """
	QLineEdit {
        background: transparent;
		color: gray;
		padding: 4px;
		margin: 0px;
        font-style: italic;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
		border: none;
        
		border-top-left-radius: 2px;
		border-top-right-radius: 2px;
		border-bottom-left-radius: 2px;
		border-bottom-right-radius: 2px;
	}
"""

dark_theme_qpb_load_bar = """
	QProgressBar {
		background-color: #555555;
		color: #ffffff;
        
		height: 26px;
		padding: 0px;
		border-radius: 2px;
        
		text-align: center;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
	}
	QProgressBar::chunk {
		background-color: darkgreen;
		border-radius: 2px;
    }
"""

dark_theme_qpb_load_bar_fail = """
	QProgressBar {
		background-color: #555555;
		color: #ffffff;
        
		height: 26px;
		padding: 0px;
		border-radius: 2px;
        
		text-align: center;
		font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
		font-size: 12px;
	}
	QProgressBar::chunk {
		background-color: darkred;
		border-radius: 2px;
    }
"""