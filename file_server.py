import socket, threading, os, sys, json, pickle,hashlib,gzip
from cryptography.fernet import Fernet


server = socket.socket()
server.bind(("localhost", 9999))

print("[+] waiting for connections...\n")

def log():
    pass


def FunHandle(conn, addr):
    server_path = f"D:/Varun/Networks_Lab/networks_pkg/logic/serverfiles/"
    name_command = conn.recv(1024).decode()
    conn.send("RandomBuff".encode())
    command, username, password = name_command.split()
    if command == "ADD":
        with open(r"D:/Networks_Lab/usersDB.json") as usr_file:
            data = json.load(usr_file)
        
        if username not in data.keys():
            data[username] = hashlib.sha256(password.encode('utf-8')).hexdigest()
            with open('D://Networks_Lab//usersDB.json', 'w') as outfile:
                json.dump(data, outfile, indent=4)
            os.mkdir(f"D://Networks_Lab//serverfiles/{username}")
            print(f"{username} connected succesfully")
            conn.send(f"{username} connected succesfully".encode())

        else:
            conn.send(f"Username {username} already exists".encode())
    
    elif command == "USER":
        
        with open("D://Networks_Lab//usersDB.json") as usr_file:
            data = json.load(usr_file)
    
        if username not in data.keys():
            conn.send(f"{username} is an invalid username".encode())
        else:
            if data[username] != hashlib.sha256(password.encode('utf-8')).hexdigest():
                conn.send(f"Password is incorrect".encode())
            else:
                print("Error : Invalid Password .")
                conn.send("Error : Invalid Password .".encode())
                
    
    elif "DWLD" == command:
        try:
            file_name = conn.recv(1024).decode()
            file_size = os.path.getsize(file_name)
            print(file_size)
            key = Fernet.generate_key()
            f = Fernet(key)
            conn.send(f"{file_size}".encode())
            sample = conn.recv(1024)
            with open(file_name, 'rb') as f_in:
                compressed_data = gzip.compress(f_in.read())
            # Encrypt the compressed data
            encrypted_data = f.encrypt(compressed_data)
            # Send the key and encrypted data to the server
            data = pickle.dumps((f, encrypted_data))
            conn.sendall(data)
            print("File Sent Successfully .")
        except Exception as e:
            conn.sendall(b"Couldn't download file.")
    
    elif "UPLD" == command:
        try:
            filename = conn.recv(1024).decode()
            
            exactfile = filename.split("/")[-1]
            
            exactfile = "D:Networks_Lab/server_files"+"//"+username+"//"+exactfile
            
            conn.send("RandomBuff".encode())
            
            file_size = int(conn.recv(1024).decode())
            
            print(file_size)
            
            conn.send("RandomBuff".encode())
            
            data = b''
            while True:
                packet = conn.recv(file_size)
                if not packet:
                    break
                data += packet
            f, encrypted_data = pickle.loads(data)
            # Decrypt the encrypted data
            compressed_data = f.decrypt(encrypted_data)
            # Decompress the compressed data using gzip
            decompressed_data = gzip.decompress(compressed_data)
            
            
            with open(exactfile, "wb") as write_file:
                write_file.write(decompressed_data)
            print("data read")
     
        
     
        
     
        
     
        
def start():        
    server.listen(2)
    while True:
            conn, addr = server.accept()
            thread = threading.Thread(target = FunHandle, args = (conn, addr))
            thread.start()
start()
