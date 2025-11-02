from customtkinter import *
from PIL import Image
import base64, io, os, threading
from socket import socket, AF_INET, SOCK_STREAM
from tkinter import filedialog


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x400")
        self.title("LogiTalk")
        self.configure(fg_color="#2B2B2B")
        self.is_menu_shown = False
        self.username = "Ім'я"

        # --- UI элементы ---
        self.menu_frame = CTkFrame(self, width=40, height=400, fg_color="indigo", corner_radius=0)
        self.menu_frame.place(x=0, y=0)

        self.menu_btn = CTkButton(self, width=30, text="⚙", command=self.toggle_menu)
        self.menu_btn.place(x=0, y=0)

        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=40, y=0)

        self.msg_entry = CTkEntry(self, height=40, placeholder_text="Введіть повідомлення 💬")
        self.msg_entry.place(x=40, y=360)

        self.open_img_btn = CTkButton(self, width=50, height=40, text="📂", command=self.open_img)
        self.open_img_btn.place(x=440, y=360)

        self.send_btn = CTkButton(self, width=50, height=40, text="➡", command=self.send_msg)
        self.send_btn.place(x=500, y=360)

        self.add_msg(f"{self.username}: test")
        self.adaptive_ui()

        # --- Сеть ---
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("localhost", 8080))
            hello = f"TEXT@{self.username}@[System] {self.username} приєднався до чату!\n"
            self.sock.send(hello.encode("utf-8"))
            threading.Thread(target=self.recv_msg, daemon=True).start()
        except Exception as e:
            self.add_msg(f"Не вдалося підключитися до сервера: {e}")

    # -------- Меню --------
    def toggle_menu(self):
        if not self.is_menu_shown:
            self.is_menu_shown = True
            self.menu_frame.configure(width=200)
            self.show_menu_widgets()
        else:
            self.is_menu_shown = False
            for widget in self.menu_frame.winfo_children():
                widget.destroy()
            self.menu_frame.configure(width=40)

    def show_menu_widgets(self):
        CTkLabel(self.menu_frame, text="Ім'я").pack(pady=10)
        self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік")
        self.entry.insert(0, self.username)
        self.entry.pack(pady=(0, 10))
        CTkButton(self.menu_frame, text="Зберегти", command=self.save_name).pack()

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_msg(f"Ваш новий нік: {self.username}")

    # -------- UI адаптация --------
    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.configure(width=self.winfo_width() - self.menu_frame.winfo_width() - 10,
                                  height=self.winfo_height() - 50)
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)

        self.msg_entry.configure(width=self.winfo_width() - self.menu_frame.winfo_width() - 120)
        self.msg_entry.place(x=self.menu_frame.winfo_width(), y=self.winfo_height() - 40)

        self.open_img_btn.place(x=self.winfo_width() - 110, y=self.winfo_height() - 40)
        self.send_btn.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.after(100, self.adaptive_ui)

    # -------- Сообщения --------
    def add_msg(self, msg, img=None):
        msg_frame = CTkFrame(self.chat_field, fg_color="gray30", corner_radius=8)
        msg_frame.pack(pady=5, anchor="w", padx=10)
        wrap_size = max(300, self.chat_field.winfo_width() - 100)
        if img:
            CTkLabel(msg_frame, text=msg, wraplength=wrap_size, text_color="white",
                     image=img, compound="top", justify="left").pack(padx=10, pady=5)
        else:
            CTkLabel(msg_frame, text=msg, wraplength=wrap_size,
                     text_color="white", justify="left").pack(padx=10, pady=5)

    def send_msg(self):
        msg = self.msg_entry.get()
        if msg:
            self.add_msg(f"{self.username}: {msg}")
            data = f"TEXT@{self.username}@{msg}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
            self.msg_entry.delete(0, END)

    def recv_msg(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT" and len(parts) >= 3:
            author, msg = parts[1], parts[2]
            self.add_msg(f"{author}: {msg}")

        elif msg_type == "IMAGE" and len(parts) >= 4:
            author, filename, b64_img = parts[1], parts[2], parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                ctk_img = CTkImage(pil_img, size=(300, 300))
                self.add_msg(f"{author} надіслав зображення: {filename}", img=ctk_img)
            except Exception as e:
                self.add_msg(f"Помилка відображення зображення: {e}")
        else:
            self.add_msg(line)

    def open_img(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            self.add_msg("", CTkImage(light_image=Image.open(file_name), size=(300, 300)))
        except Exception as e:
            self.add_msg(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()
