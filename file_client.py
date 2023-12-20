from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import SlideTransition


from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.toast import toast

from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.filemanager import MDFileManager

import socket
import json
import os
import hashlib
from cryptography.fernet import Fernet


class ListItem(OneLineAvatarIconListItem):
    text = StringProperty()
    icon_left = StringProperty()
    icon_right = StringProperty()
            

class Content_New_Dir(MDBoxLayout):
    pass

class Content_Upload_File(MDBoxLayout):
    pass

class app(MDApp):
    
    def build(self):
        self.screen_manager = MDScreenManager(transition = SlideTransition())
        self.theme_cls.theme_style = "Dark"
        self.LoginScreen = Builder.load_file("screens\\LoginScreen.kv")
        self.SignupScreen = Builder.load_file("screens\\SignupScreen.kv")
        self.MainScreen = Builder.load_file("screens\\MainScreen.kv")
        self.screen_manager.add_widget(self.LoginScreen)
        self.screen_manager.add_widget(self.SignupScreen)
        self.screen_manager.add_widget(self.MainScreen)
        self.file_manager = MDFileManager(
            exit_manager = self.exit_manager,
            select_path = self.select_path,
            selector = "file"
        )
        return self.screen_manager
    
    def on_start(self):
        pass
    
    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''

        self.exit_manager()
        self.upload_dialog.content_cls.ids.upload_file_path.text = path
        self.file_manager_path = path
        toast(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()
    
    def login(self, username, password):
        self.client = socket.socket()
        self.client.connect(("192.168.29.72", 9999))
        password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        self.client.send(f"USER {username} {password}".encode())
        login_response = self.client.recv(1024).decode()
        toast(login_response)
        if login_response == f"{username} connected succesfully":
            self.username = username
            self.MainScreen.ids.path.text = f"{self.username}"
            self.data = json.loads(self.client.recv(1024).decode())
            self.key = self.data["key"].encode()
            print(self.key)
            self.crypto = Fernet(self.key)
            self.screen_manager.current = "MainScreen"
            self.LoginScreen.ids.usn.text, self.LoginScreen.ids.pwd.text = "", ""
        elif login_response == f"{username} is an invalid username":
            self.LoginScreen.ids.usn.text, self.LoginScreen.ids.pwd.text = "", ""
        elif login_response == f"Password is incorrect":
            self.LoginScreen.ids.pwd.text = ""
    
    def signup(self, username, password):
        self.client = socket.socket()
        self.client.connect(("192.168.29.72", 9999))
        self.client.send(f"ADD {username} {password}".encode())
        self.client.recv(1024)
        key = Fernet.generate_key()
        self.client.send(key)
        signup_response = self.client.recv(1024).decode()
        toast(signup_response)
        if signup_response == f"{username} connected succesfully":
            self.key = key
            print(self.key)
            self.crypto = Fernet(self.key)
            self.username = username
            self.MainScreen.ids.path.text = f"{self.username}"
            self.data = {"dirs": [], "files": []}
            self.screen_manager.current = "MainScreen"
            self.SignupScreen.ids.usn.text, self.SignupScreen.ids.pwd.text = "", ""
        elif signup_response == f"Username {username} already exists":
            self.SignupScreen.ids.usn.text, self.SignupScreen.ids.pwd.text = "", ""
    
    def verify_username(self, tb, text):
        for i in text:
            if not i.isalnum():
                text = text.replace(i, "")
        tb.text = text
    
    def enter_main(self):
        self.MainScreen.ids.files_list.clear_widgets()
        if self.MainScreen.ids.path.text != f"{self.username}":
            self.MainScreen.ids.files_list.add_widget(ListItem(text = f"..", icon_left = "folder", icon_right = ""))            
        for i in self.data["dirs"]:
            self.MainScreen.ids.files_list.add_widget(ListItem(text = f"{i}", icon_left = "folder", icon_right = ""))
        for i in self.data["files"]:
            self.MainScreen.ids.files_list.add_widget(ListItem(text = f"{i}", icon_left = "file-document", icon_right = "download"))
        
    def on_press(self, icon_left, text):
        if icon_left == "folder":
            self.client.send(f"CD {text}".encode())
            self.data = json.loads(self.client.recv(1024).decode())
            self.MainScreen.ids.path.text = self.data["cwd"]
            self.enter_main()
    
    def on_download_press(self, filename):
        file_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        self.client.send(f"DWLD {filename}".encode())
        file_size = int(self.client.recv(1024).decode())
        print("request sent")
        file_data = self.client.recv(file_size)
        print(file_data)
        print(self.crypto.decrypt(file_data))
        print("data received")
        if file_data == "Couldn't download file.":
            toast(file_data)
        else:
            with open(file_path, 'wb') as new_file:
                new_file.write(self.crypto.decrypt(file_data))
            toast("File has been downloaded successfully!")
    
    def open_mkdir_dialog(self):
        self.new_dir_dialog = MDDialog(
                title="CREATE A NEW FOLDER",
                type="custom",
                content_cls=Content_New_Dir(),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_press=self.close_new_dir_dialog
                    ),
                    MDRaisedButton(
                        text="CREATE FOLDER",
                        on_press=self.create_folder
                    ),
                ],
            )
        self.new_dir_dialog.open()

    def close_new_dir_dialog(self, t1):
        if self.new_dir_dialog:
            self.new_dir_dialog.content_cls.ids.folder_name.text = ""
            self.new_dir_dialog.dismiss()

    def create_folder(self, t1):
        folder_name = self.new_dir_dialog.content_cls.ids.folder_name.text
        if " " in folder_name:
            toast("Enter folder without spaces")
            self.new_dir_dialog.content_cls.ids.folder_name.text = ""
        else:
            self.client.send(f"MKDIR {folder_name}".encode())
            self.data = json.loads(self.client.recv(1024).decode())
            self.close_new_dir_dialog('hi')
            self.enter_main()
    
    def open_upload_dialog(self):
        self.upload_dialog = MDDialog(
                title="UPLOAD A FILE",
                type="custom",
                content_cls=Content_Upload_File(),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_press=self.close_upload_dialog
                    ),
                    MDRaisedButton(
                        text="UPLOAD",
                        on_press=self.upload_folder
                    ),
                ],
            )
        self.upload_dialog.content_cls.ids.upload_file_path.text = ""
        self.file_manager_path = None
        self.upload_dialog.open()
    
    def open_file_manager(self):
        self.file_manager.show_disks()
    
    def close_upload_dialog(self, t1):
        self.file_manager_path = None
        if self.upload_dialog:
            self.upload_dialog.content_cls.ids.upload_file_path.text = ""
            self.upload_dialog.dismiss()
    
    def upload_folder(self, rand):
        print(self.file_manager_path)
        with open(self.file_manager_path, "rb") as upload_file:
            file_name = self.file_manager_path.split("\\")[-1]
            data = upload_file.read()
        file_data = self.crypto.encrypt(data)
        upload_file_size = len(file_data)
        self.client.send(f"UPLD {file_name}".encode())
        self.client.send(f"{upload_file_size}".encode())
        buffRes = self.client.recv(1024)
        self.client.send(file_data)
        response = self.client.recv(1024).decode()
        if response == "Upload Successful.":
            toast("File upload successful!")
            self.close_upload_dialog("hi")
            self.data = json.loads(self.client.recv(1024).decode())
            self.MainScreen.ids.path.text = self.data["cwd"]
            self.enter_main()
        elif response == "Couldn't upload file.":
            toast("Couldn't upload file")
        

app().run()