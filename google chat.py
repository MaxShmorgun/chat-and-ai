import google.generativeai as genai
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter
import os

API_KEY = "AIzaSyCSZUahYGRBh5MZPEDEXM5fvls7npWK_4o"
genai.configure(api_key=API_KEY)

model = None
chat = None
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat()
except Exception as e:
    print(f"Помилка ініціалізації моделі Gemini: {e}")

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class ChatApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Штучний інтелект (AI)")
        self.geometry("800x700")
        self.minsize(600, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_columnconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled',
                                                      font=("Arial", 10),
                                                      bg=customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"][0],
                                                      fg=customtkinter.ThemeManager.theme["CTkLabel"]["text_color"][0])
        self.chat_display.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.image_label = customtkinter.CTkLabel(self, text="")
        self.image_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.current_image = None
        self.current_image_path = None

        self.msg_input = customtkinter.CTkEntry(self, placeholder_text="Введіть запит або шлях до зображення...", width=400)
        self.msg_input.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.msg_input.bind("<Return>", self.send_message_enter)

        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.attach_button = customtkinter.CTkButton(self.button_frame, text="Додати зображення", command=self.attach_image)
        self.attach_button.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        self.send_button = customtkinter.CTkButton(self.button_frame, text="Надіслати", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")

        self.control_frame = customtkinter.CTkFrame(self)
        self.control_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.control_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.clear_history_button = customtkinter.CTkButton(self.control_frame, text="Очистити історію", command=self.clear_chat_history)
        self.clear_history_button.grid(row=0, column=0, padx=5, pady=0, sticky="ew")

        self.settings_button = customtkinter.CTkButton(self.control_frame, text="Налаштування", command=self.open_settings)
        self.settings_button.grid(row=0, column=1, padx=5, pady=0, sticky="ew")

        self.stop_button = customtkinter.CTkButton(self.control_frame, text="Зупинити", command=self.stop_generation, state='disabled', fg_color="red")
        self.stop_button.grid(row=0, column=2, padx=5, pady=0, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Готово", text_color="grey")
        self.status_label.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.create_context_menus()

        self.stop_event = threading.Event()

        self.image_refs = []

        self.current_font_size = 10
        self.update_font_size(self.current_font_size, label_widget=None)

        self._update_widget_colors()


    def create_context_menus(self):
        self.chat_display_menu = tk.Menu(self, tearoff=0)
        self.chat_display_menu.add_command(label="Копіювати", command=self.copy_from_chat_display)
        self.chat_display.bind("<Button-3>", lambda event: self.chat_display_menu.post(event.x_root, event.y_root))

        self.msg_input_menu = tk.Menu(self, tearoff=0)
        self.msg_input_menu.add_command(label="Вирізати", command=lambda: self.focus_get().event_generate("<<Cut>>"))
        self.msg_input_menu.add_command(label="Копіювати", command=lambda: self.focus_get().event_generate("<<Copy>>"))
        self.msg_input_menu.add_command(label="Вставити", command=lambda: self.focus_get().event_generate("<<Paste>>"))
        self.msg_input.bind("<Button-3>", lambda event: self.msg_input_menu.post(event.x_root, event.y_root))

    def attach_image(self):
        file_path = filedialog.askopenfilename(
            title="Виберіть зображення",
            filetypes=[("Зображення", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            try:
                img = Image.open(file_path)
                img.thumbnail((250, 250))
                self.current_image = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.current_image)
                self.current_image_path = file_path
            except Exception as e:
                self.display_message("Помилка", f"Не вдалося відкрити або відобразити зображення: {e}")
                messagebox.showerror("Помилка зображення", f"Не вдалося відкрити або відобразити зображення: {e}")

    def copy_from_chat_display(self):
        try:
            selected_text = self.chat_display.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.clipboard_clear()
                self.clipboard_append(selected_text)
        except tk.TclError:
            pass
        except Exception as e:
            print(f"Помилка копіювання: {e}")
            messagebox.showerror("Помилка", f"Не вдалося скопіювати текст: {e}")

    def display_message(self, sender, message):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def display_image(self, sender, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((250, 250))
            photo = ImageTk.PhotoImage(img)
            self.chat_display.configure(state='normal')
            self.chat_display.image_create(tk.END, image=photo, padx=5, pady=5)
            self.chat_display.insert(tk.END, f"  ({sender} надіслав зображення)\n\n")
            self.chat_display.configure(state='disabled')
            self.chat_display.see(tk.END)
            self.image_refs.append(photo)
        except Exception as e:
            self.display_message("Помилка", f"Не вдалося відобразити зображення в чаті: {e}")
            messagebox.showerror("Помилка зображення", f"Не вдалося відобразити зображення в чаті: {e}")

    def send_message_enter(self, event=None):
        self.send_message()

    def send_message(self):
        user_message = self.msg_input.get()
        image_path = self.current_image_path
        parts = []

        if user_message.strip():
            parts.append(user_message)
            self.display_message("Я", user_message)

        if image_path:
            try:
                img = Image.open(image_path)
                parts.append(img)
                self.display_image("Я", image_path)
            except Exception as e:
                self.display_message("Помилка", f"Не вдалося відкрити зображення для надсилання: {e}")
                messagebox.showerror("Помилка надсилання", f"Не вдалося відкрити зображення для надсилання: {e}")
                return
            finally:
                self.current_image = None
                self.current_image_path = None
                self.image_label.configure(image=None)

        if not parts:
            messagebox.showwarning("Порожній запит", "Будь ласка, введіть текст або додайте зображення.")
            return

        self.msg_input.delete(0, tk.END)
        self.send_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.status_label.configure(text="AI пише...", text_color="orange")

        self.stop_event.clear()

        if model and chat:
            threading.Thread(target=self.get_gemini_response, args=(parts,)).start()
        else:
            self.display_message("Помилка", "AI не ініціалізовано. Перевірте API ключ та модель.")
            self.send_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            self.status_label.configure(text="Помилка", text_color="red")
            messagebox.showerror("Помилка AI", "AI не ініціалізовано. Перевірте API ключ та модель.")


    def get_gemini_response(self, parts):
        try:
            response_chunks = chat.send_message(content=parts, stream=True)
            self.display_message("Ai", "")

            for chunk in response_chunks:
                if self.stop_event.is_set():
                    self.display_message("Система", "Генерування зупинено користувачем.")
                    break
                
                if hasattr(chunk, 'text') and chunk.text is not None:
                    self.after(0, self._update_chat_display_streaming, chunk.text)
                
        except Exception as e:
            self.display_message("Помилка", f"Не вдалося отримати відповідь від AI: {e}")
            self.status_label.configure(text="Помилка зв'язку з AI", text_color="red")
            messagebox.showerror("Помилка AI", f"Не вдалося отримати відповідь від AI: {e}")
        finally:
            self.send_button.configure(state='normal')
            self.stop_button.configure(state='disabled')
            self.status_label.configure(text="Готово", text_color="grey")
            self.stop_event.clear()

    def _update_chat_display_streaming(self, text_chunk):
        self.chat_display.configure(state='normal')
        current_content = self.chat_display.get("1.0", tk.END)
        last_ai_tag_start = current_content.rfind("Ai: ")
        
        if last_ai_tag_start != -1 and last_ai_tag_start > current_content.rfind("Я: "):
            start_index = self.chat_display.search("Ai: ", "end-2c", backwards=True, nocase=True, stopindex="1.0")
            if start_index:
                end_index = self.chat_display.index(tk.END + "-1c")
                self.chat_display.insert(end_index, text_chunk)
            else:
                self.chat_display.insert(tk.END, text_chunk)
        else:
             self.chat_display.insert(tk.END, text_chunk)
        
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def stop_generation(self):
        self.stop_event.set()
        self.status_label.configure(text="Зупиняю генерування...", text_color="red")
        self.stop_button.configure(state='disabled')

    def clear_chat_history(self):
        if messagebox.askyesno("Очистити історію", "Ви впевнені, що хочете очистити всю історію чату?"):
            self.chat_display.configure(state='normal')
            self.chat_display.delete('1.0', tk.END)
            self.chat_display.configure(state='disabled')
            self.image_label.configure(image=None)
            self.current_image = None
            self.current_image_path = None
            self.image_refs = []
            messagebox.showinfo("Історія очищена", "Історію чату було успішно очищено.")

    def open_settings(self):
        settings_window = customtkinter.CTkToplevel(self)
        settings_window.title("Налаштування")
        settings_window.geometry("300x200") # Зменшено висоту
        settings_window.resizable(False, False)
        settings_window.transient(self)

        appearance_label = customtkinter.CTkLabel(settings_window, text="Режим вигляду:")
        appearance_label.pack(pady=10)
        appearance_options = ["Світлий", "Темний"]
        self.appearance_menu = customtkinter.CTkOptionMenu(settings_window, values=appearance_options,
                                                           command=self.change_appearance_mode)
        current_mode = customtkinter.get_appearance_mode()
        if current_mode == "Light" or current_mode == "System":
            self.appearance_menu.set("Світлий")
        elif current_mode == "Dark":
            self.appearance_menu.set("Темний")
        self.appearance_menu.pack(pady=5)

        # Видалено секцію "Кольорова тема"

        font_size_label = customtkinter.CTkLabel(settings_window, text="Розмір шрифту чату:")
        font_size_label.pack(pady=10)
        font_size_value_label = customtkinter.CTkLabel(settings_window, text=str(int(self.current_font_size)))
        self.font_size_slider = customtkinter.CTkSlider(settings_window, from_=8, to=20, number_of_steps=12,
                                                        command=lambda value, label=font_size_value_label: self.update_font_size(value, label))
        self.font_size_slider.set(self.current_font_size)
        self.font_size_slider.pack(pady=5)
        font_size_value_label.pack()

    def _update_widget_colors(self):
        current_mode = customtkinter.get_appearance_mode()

        # CTkFrame fg_color (фон чату)
        chat_bg_color = customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"][0] if current_mode == "Light" or current_mode == "System" else customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"][1]

        # CTkLabel text_color (колір тексту)
        text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"][0] if current_mode == "Light" or current_mode == "System" else customtkinter.ThemeManager.theme["CTkLabel"]["text_color"][1]

        self.chat_display.configure(bg=chat_bg_color, fg=text_color)
        self.msg_input.configure(text_color=text_color)

    def change_appearance_mode(self, new_appearance_mode: str):
        if new_appearance_mode == "Світлий":
            customtkinter.set_appearance_mode("Light")
        elif new_appearance_mode == "Темний":
            customtkinter.set_appearance_mode("Dark")
        else:
            customtkinter.set_appearance_mode(new_appearance_mode)
        
        self._update_widget_colors()

    # Метод change_color_theme більше не потрібен, оскільки вибір теми видалено
    # Однак, якщо ви хочете, щоб зміна кольору тексту все ще відбувалася при інших оновленнях,
    # переконайтеся, що _update_widget_colors() викликається в потрібних місцях.

    def update_font_size(self, new_font_size_value, label_widget=None):
        self.current_font_size = int(new_font_size_value)
        if label_widget:
            label_widget.configure(text=str(self.current_font_size))
        self.chat_display.configure(font=("Arial", self.current_font_size))
        self.msg_input.configure(font=("Arial", self.current_font_size))


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
