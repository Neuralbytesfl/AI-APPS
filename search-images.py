import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 6.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

class ImageSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Search Browser")
        self.geometry("500x600")
        self.resizable(False, False)  # Fixed window size
        self.configure(bg='#1c1c1c')

        # Search box
        self.search_entry = tk.Entry(self, width=40, font=("Arial", 14), bg='#2c2c2c', fg='white')
        self.search_entry.pack(pady=10)

        # ComboBox for number of images
        self.num_images_label = tk.Label(self, text="Number of images:", bg='#1c1c1c', fg='white')
        self.num_images_label.pack()
        self.num_images_var = tk.StringVar(value="5")
        self.num_images_combo = ttk.Combobox(self, textvariable=self.num_images_var, values=[str(i) for i in range(1, 21)], state="readonly", width=5)
        self.num_images_combo.pack(pady=10)

        # Download button at the top
        self.download_button = tk.Button(self, text="Download All Images", command=self.download_all_images, font=("Arial", 12), bg='#4c4c4c', fg='white')
        self.download_button.pack(pady=10)

        # Search button
        self.search_button = tk.Button(self, text="Search", command=self.start_search_thread, font=("Arial", 12), bg='#3c3c3c', fg='white')
        self.search_button.pack(pady=10)

        # Image display area
        self.image_frame = tk.Frame(self, bg='#1c1c1c')
        self.image_frame.pack(expand=True, fill=tk.BOTH)
        self.image_label = tk.Label(self.image_frame, bg='#1c1c1c')
        self.image_label.pack(expand=True)

        # Navigation buttons
        self.prev_button = tk.Button(self, text="<<", command=self.show_prev_image, font=("Arial", 12), bg='#3c3c3c', fg='white')
        self.prev_button.place(relx=0.1, rely=0.9, anchor='center')  # Fixed position

        self.next_button = tk.Button(self, text=">>", command=self.show_next_image, font=("Arial", 12), bg='#3c3c3c', fg='white')
        self.next_button.place(relx=0.9, rely=0.9, anchor='center')  # Fixed position

        # Variables to hold image data and current index
        self.image_urls = []
        self.current_index = 0
        self.current_img_data = None

    def start_search_thread(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a search query.")
            return

        thread = threading.Thread(target=self.search_images, args=(query,))
        thread.start()

    def search_images(self, query):
        self.image_urls.clear()
        self.current_index = 0

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--log-level=3")
        options.add_argument("start-minimized")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            # DuckDuckGo search with SafeSearch off (kp=-2)
            search_url = f"https://duckduckgo.com/?q={query}&iar=images&iax=images&ia=images&kp=-2"
            driver.get(search_url)
            time.sleep(3)  # Wait for the page to load

            thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.tile--img__img")

            if not thumbnails:
                messagebox.showerror("Error", "No images found.")
                return

            num_images = int(self.num_images_var.get())
            for i, thumbnail in enumerate(thumbnails[:num_images]):  # Limit to selected number of images
                try:
                    thumbnail.click()
                    time.sleep(1)

                    images = driver.find_elements(By.CSS_SELECTOR, "img.tile--img__img")
                    if len(images) > i:
                        src_url = images[i].get_attribute("src")
                        if "http" in src_url and not src_url.startswith("data:image"):
                            self.image_urls.append(src_url)
                            print(f"Debug: Image URL added to list: {src_url}")  # Debug output

                except Exception as e:
                    print(f"Error clicking thumbnail: {e}")

            if self.image_urls:
                self.show_image(0)
            else:
                print("Debug: No image URLs were added to the list.")  # Debug output

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

        finally:
            driver.quit()

    def show_image(self, index):
        if not self.image_urls or index < 0 or index >= len(self.image_urls):
            return

        img_url = self.image_urls[index]
        print(f"Debug: Displaying image from URL: {img_url}")  # Debug output
        try:
            response = requests.get(img_url)
            img_data = response.content
            self.current_img_data = img_data  # Save the current image data

            img = Image.open(BytesIO(img_data))
            img.thumbnail((450, 450))
            img_tk = ImageTk.PhotoImage(img)

            self.image_label.configure(image=img_tk)
            self.image_label.image = img_tk

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def show_prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.current_index)

    def show_next_image(self):
        if self.current_index < len(self.image_urls) - 1:
            self.current_index += 1
            self.show_image(self.current_index)

    def download_all_images(self):
        if not self.image_urls:
            messagebox.showerror("Error", "No images to download.")
            return

        directory = filedialog.askdirectory()
        if not directory:
            return

        for i, img_url in enumerate(self.image_urls):
            try:
                response = requests.get(img_url)
                img_data = response.content

                file_path = os.path.join(directory, f"image_{i+1}.jpg")

                # Ensure no file overwrite
                count = 1
                while os.path.exists(file_path):
                    file_name, file_extension = os.path.splitext(file_path)
                    file_path = f"{file_name}_{count}{file_extension}"
                    count += 1

                with open(file_path, 'wb') as f:
                    f.write(img_data)

                print(f"Debug: Image {i+1} downloaded to {file_path}")

            except Exception as e:
                print(f"Error downloading image {i+1}: {e}")

        messagebox.showinfo("Success", "All images downloaded successfully.")

if __name__ == "__main__":
    app = ImageSearchApp()
    app.mainloop()
