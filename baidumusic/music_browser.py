#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import webkit
import javascriptcore as jscore

from widget.ui import NetworkConnectFailed, LoadingBox
from deepin_utils.net import is_network_connected
from widget.ui_utils import switch_tab

from music_player import MusicPlayer, PlayerInterface, TTPDownload

class MusicBrowser(gtk.VBox):
    
    def __init__(self):
        super(MusicBrowser, self).__init__()
        
        # check network status
        self.progress_value = 0
        self.is_reload_flag = False        
        self.network_connected_flag = False
        self.update_progress_flag = True
        self.prompt_text = "正在加载数据(%d%%)，如果长时间没有响应，点击此处刷新"
        
        self._player = MusicPlayer()
        self._player_interface = PlayerInterface()
        self._ttp_download = TTPDownload()
        
        self.loading_box = LoadingBox(self.prompt_text % self.progress_value, "此处", self.reload_browser)
        self.network_failed_box = NetworkConnectFailed(self.check_network_connection)
        self.check_network_connection(auto=True)

        self.webview = webkit.WebView()
        self.webview.set_transparent(True)
        
        settings = self.webview.get_settings()
        settings.set_property('enable-plugins', False)
        self.webview.set_settings(settings)
        
        self.webview.load_uri("http://musicmini.baidu.com/static/recommend/recommend.html")
        self.js_context = jscore.JSContext(self.webview.get_main_frame().get_global_context()).globalObject                        
        self.webview.connect("load-finished", self.on_webview_load_finished)

        self.webview.connect("load-progress-changed", self.on_webview_progress_changed)
        
        # message status
        self.webview.connect("script-alert", self.on_webview_script_alert)        
        self.webview.connect("console-message", self.on_webview_console_message)
        
        # resource load
        self.webview.connect("resource-load-failed", self.on_webview_resource_request)
        # self.webview.connect("resource-request-starting", self.on_webview_resource_request)
        # self.webview.connect("resource-load-finished", self.on_webview_resource_request)
        
        
    def on_webview_script_alert(self, widget, frame, message):    
        self.injection_object()
        self._player.alert(message)
        
        # reject alert dialog.
        return True
    
    def on_webview_console_message(self, widget, message, line, source_id):
        return True
    
    def on_webview_resource_request(self, *args):    
        self.injection_object()
            
    def on_webview_progress_changed(self, widget, value):    
        if self.update_progress_flag:
            if self.is_reload_flag:
                self.progress_value = (100 + value ) / 200.0
            else:    
                self.progress_value = value / 200.0            
                
            self.loading_box.update_prompt_text(self.prompt_text % int(self.progress_value * 100))    
        
    def check_network_connection(self, auto=False):    
        if is_network_connected():
            self.network_connected_flag = True
            switch_tab(self, self.loading_box)
            if not auto:
                self.reload_browser()
        else:    
            self.network_connected_flag = False
            switch_tab(self, self.network_failed_box)
            
    def reload_browser(self):        
        self.is_reload_flag = False
        self.update_progress_flag = True
        self.progress_value = 0
        self.webview.reload()
            
    def injection_object(self):
        self.js_context.player = self._player
        self.js_context.window.top.ttp_download = self._ttp_download
        self.js_context.window.top.playerInterface = self._player_interface
        self.js_context.link_support = True
        self.js_context.alert = self._player.alert
        
    def injection_js(self):    
        js_e = self.js_context.document.createElement("script")
        js_e.src = "http://musicmini.baidu.com/resources/js/jquery.js"
        self.js_context.document.appendChild(js_e)
        
    def on_webview_load_finished(self, *args):    
        if not self.is_reload_flag:
            self.webview.reload()
            self.is_reload_flag = True
        elif self.is_reload_flag and self.update_progress_flag:    
            self.update_progress_flag = False
            if self.network_connected_flag:
                switch_tab(self, self.webview)
            
        # inject object.    
        self.injection_object()            
