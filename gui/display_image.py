import io
import requests
import threading
from PIL import Image, ImageTk
import tkinter as tk

class Display:
    def __init__(self, root):
        self.root = root
        self.label = tk.Label(self.root)
        self.label.pack()
        self.photo = None  # Keep a reference to the PhotoImage

    def show_image(self, image_url):
        # Schedule the _update_image method to be called on the main thread
        self.root.after(0, self._update_image, image_url)

    def _load_image_async(self, image_url):
        def fetch_and_update():
            try:
                response = requests.get(image_url)
                image_data = response.content
                self.root.after(0, lambda: self._update_image(image_data))
            except Exception as e:
                print(f"Error fetching image: {e}")

        threading.Thread(target=fetch_and_update).start()

    def _update_image(self, image_data):
        try:
            image = Image.open(io.BytesIO(image_data))
            self.photo = ImageTk.PhotoImage(image)
            self.label.configure(image=self.photo)
        except Exception as e:
            print(f"Error updating image: {e}")
