import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
from keras.applications.vgg16 import VGG16, preprocess_input, decode_predictions
from keras.preprocessing.image import img_to_array
import numpy as np
import os
import random
import subprocess
import threading
import time
from datetime import datetime
import vlc
import platform
from tkinter import Menu
prediction_counts = {}

class AboutDialog(tk.Toplevel):
    def __init__(self, parent, app_name, created_by, creation_date, description, modules_used):
        super().__init__(parent)
        self.title("About")
        self.geometry("600x600")  # Adjusted size
        self.resizable(False, False)

        ttk.Label(self, text=f"{app_name}", font=("Helvetica", 16, "bold")).pack(pady=10)
        ttk.Label(self, text=f"Version 1.0").pack()
        ttk.Label(self, text=f"Created by: {created_by}").pack()
        ttk.Label(self, text=f"Creation Date: {creation_date}").pack()
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(self, text=f"Description:").pack()
        ttk.Label(self, text=f"{description}", wraplength=500).pack()  # Adjusted wraplength
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(self, text=f"Modules Used:").pack()
        ttk.Label(self, text=f"{modules_used}", wraplength=500).pack()  # Adjusted wraplength
        ttk.Button(self, text="OK", command=self.destroy).pack(pady=10)


class DeepDreamGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ArtVisio - Unleash Your Artistic Imagination, Enhanced by AI")
        self.auto_cycle_count = tk.IntVar(value=0)
        self.auto_cycle_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.auto_cycle_elapsed_time = tk.StringVar()
        self.auto_cycle_elapsed_time.set("00:00:00")
        self.rotation_checkbox_var = tk.BooleanVar()
        self.flip_checkbox_var = tk.BooleanVar()
        self.auto_cycle_paused = False
        self.popup_open = True
        self.progress = ttk.Progressbar(self.root, length=200, mode="determinate")

        # Create the menu bar
        menu_bar = Menu(root)
        root.config(menu=menu_bar)
        self.manual_save_clicked = False  # Add this line
        # File menu
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Open Base Image", command=self.browse_base_image)
        file_menu.add_command(label="Save Image", command=self.save_image)
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit menu
        edit_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo_effect)

        # Settings menu
        settings_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_checkbutton(label="Enable Rotation", variable=self.rotation_checkbox_var)
        settings_menu.add_checkbutton(label="Enable Flip", variable=self.flip_checkbox_var)
        settings_menu.add_command(label="About", command=self.show_about_dialog)

        # Create a context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_image)
        self.context_menu.add_command(label="Paste", command=self.paste_image)
        self.context_menu.add_command(label="Save", command=self.save_image)

        # Create result_panel
        self.result_panel = ttk.Label(root, borderwidth=7, relief="solid")
        self.result_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nw")

        # Create the base panel
        self.base_panel = ttk.Label(root, borderwidth=7, relief="solid")
        self.base_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nw")


        # Bind right-click event to show the context menu
        self.base_panel.bind("<Button-3>", self.show_context_menu)
        self.result_panel.bind("<Button-3>", self.show_context_menu)


         # Load your image using PhotoImage
        original_image = tk.PhotoImage(file="background_image.png")  # Replace with your image file path

        # Adjust the size of the image (replace 2 with the desired subsample factor)
        subsample_factor = 15
        resized_image = original_image.subsample(subsample_factor, subsample_factor)

        # Create a Label to display the resized image
        #image_label = ttk.Label(root, image=resized_image)
        #image_label.photo = resized_image  # Keep a reference to the image to prevent it from being garbage collected
        # Create an image label
        image_label = ttk.Label(root, text="Your Image Here")
        image_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")



        
        # Place the Label in the top-left corner
        #image_label.pack(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Add other widgets or functionalities as needed

        # Labels for auto cycle information
        ttk.Label(root, text="Auto Cycle Count:").grid(row=11, column=0, padx=10, pady=10, sticky="e")
        self.auto_cycle_count_label = ttk.Label(root, textvariable=self.auto_cycle_count)
        self.auto_cycle_count_label.grid(row=11, column=1, padx=10, pady=10, sticky="w")

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

        ttk.Label(root, text="Auto Cycle Start Time:").grid(row=12, column=0, padx=10, pady=10, sticky="e")
        self.auto_cycle_start_time_label = ttk.Label(root, text=self.auto_cycle_start_time)
        self.auto_cycle_start_time_label.grid(row=12, column=1, padx=10, pady=10, sticky="w")

        self.auto_cycle_delay = 2000

        ttk.Label(root, text="Auto Cycle Elapsed Time:").grid(row=13, column=0, padx=10, pady=10, sticky="e")
        self.auto_cycle_elapsed_time_label = ttk.Label(root, textvariable=self.auto_cycle_elapsed_time)
        self.auto_cycle_elapsed_time_label.grid(row=13, column=1, padx=10, pady=10, sticky="w")

        # Entry widgets for image paths
        self.base_image_path_entry = ttk.Entry(root, width=40)
        self.base_image_path_entry.grid(row=0, column=1, padx=10, pady=10)

        # Labels for entry widgets
        ttk.Label(root, text="Base Image Path:").grid(row=0, column=0, padx=10, pady=10, sticky="e")

        # Label for real-time clock
        self.real_time_clock_label = ttk.Label(root, text="")
        self.real_time_clock_label.grid(row=14, column=1, pady=10)

        # Buttons for browsing and applying Deep Dream
        ttk.Button(root, text="Browse", command=self.browse_base_image).grid(row=0, column=2, padx=10, pady=10)
        ttk.Button(root, text="Apply Deep Dream", command=self.apply_deep_dream).grid(row=0, column=3, padx=20, pady=40)

        # Resizable canvas for displaying effect image
        self.base_panel = ttk.Label(self.root)
        self.base_panel.grid(row=3, column=0, pady=20)

        self.result_panel = ttk.Label(self.root)
        self.result_panel.grid(row=3, column=1, pady=20)

        # Label for displaying top prediction
        self.top_prediction_label = ttk.Label(root, text="")
        self.top_prediction_label.grid(row=4, column=1, pady=10)

        # Label for displaying top predictions details
        self.top_predictions_label = ttk.Label(root, text="")
        self.top_predictions_label.grid(row=5, column=1, pady=10)
        try:
            with open('last_base_image.txt', 'r') as file:
                last_base_image_path = file.read()
                if last_base_image_path:
                    self.load_last_base_image(last_base_image_path)
        except FileNotFoundError:
            pass  # File not found, continue with a new instance


        # Create a Combobox for selecting effects
        self.effect_var = tk.StringVar()
        self.effect_dropdown = ttk.Combobox(root, textvariable=self.effect_var, values=[
            "Original", "Blur", "Sharpen", "Edge Enhance",
            "Brightness Increase", "Brightness Decrease",
            "Contrast Increase", "Contrast Decrease",
            "Saturation Increase", "Saturation Decrease",
            "Rotate 90 degrees", "Flip Horizontal", "Flip Vertical",
            "Smooth", "Emboss", "Find Edges",
            "Grayscale", "Sepia", "Invert Colors", "Posterize",
            "Negative", "Solarize", "Oil Paint", "Watercolor",
            "Pencil Sketch", "Cartoonize", "Pixelate", "Colorize",
            "Heatmap", "Sobel Edge", "Swirl", "Vignette",
            "Glow", "Comic Book", "Wave", "Raindrops",
            "Mosaic", "Pop Art", "Crosshatch", "Fisheye"
        ])
        self.effect_dropdown.grid(row=1, column=1, columnspan=4, pady=10)
        self.effect_dropdown.set("Original Effect")

        # Checkbox for enabling/disabling rotation effects
        self.rotation_checkbox_var = tk.BooleanVar()
        ttk.Checkbutton(root, text="Enable Rotation", variable=self.rotation_checkbox_var).grid(row=6, column=0, pady=10)

        # Checkbox for enabling/disabling flip effects
        self.flip_checkbox_var = tk.BooleanVar()
        ttk.Checkbutton(root, text="Enable Flip", variable=self.flip_checkbox_var).grid(row=7, column=0, pady=10)

        # Button for random effect
#        ttk.Button(root, text="Random Effect", command=self.apply_random_effect, style='Random.TButton').grid(row=1, column=1, pady=10)

#        random_effect_button.grid(row=0, column=0, pady=10)

        # Stop button for auto cycle
        ttk.Button(root, text="■ Stop", command=self.auto_cycle_effects).grid(row=2, column=0, columnspan=2, pady=10)

        # Play button for auto cycle
        ttk.Button(root, text="▶ Play", command=self.pause_auto_cycle).grid(row=2, column=1, pady=10)

        # Fast forward button for auto cycle
        ttk.Button(root, text=">> Fast forward", command=self.auto_cycle_fastfoward).grid(row=2, column=1, columnspan=3, pady=10)

        # Button to auto cycle random effects
        ttk.Button(root, text="Apply", command=self.apply_deep_dream).grid(row=1, column=2, columnspan=3, pady=10)

        # Button to undo the last effect
        ttk.Button(root, text="Undo", command=self.undo_effect).grid(row=2, column=2, columnspan=3, pady=5)

        # Button to save the image
        ttk.Button(root, text="Save Image", command=self.save_image2).grid(row=1, column=1, pady=10)


        # Store the list of applied effects
        self.applied_effects = []
        self.vgg16_model = VGG16(weights='imagenet')
        self.auto_cycle_thread = None
        self.auto_cycle_interval = 15

        # Configure style for the random effect button
        root.tk_setPalette(background='#ececec')
        root.style = ttk.Style()
        root.style.configure('Random.TButton', font=('Helvetica', 14), foreground='green', padding=10, relief='flat')

        # vlc ------------------------------------------------------------------------
        #self.vlc_frame = ttk.Frame(root)
        #self.vlc_frame.grid(row=15, column=0, columnspan=3, pady=20)

        # VLC player instance and media
        #self.instance = vlc.Instance("--no-xlib")
        #self.player = self.instance.media_player_new()
        #self.media = self.instance.media_new('rtsp://Steadyforge190:Bodam1420@192.168.0.113:554/live0')
        #self.player.set_media(self.media)

        # Canvas for displaying VLC stream
        #self.vlc_canvas = tk.Canvas(self.vlc_frame, width=640, height=480, bg='black')
        #self.vlc_canvas.pack()

        # Set the window ID for VLC video output
        #if platform.system() == "Windows":
        #    self.player.set_hwnd(self.vlc_canvas.winfo_id())
        #elif platform.system() == "Linux":
        #    self.player.set_xwindow(int(self.vlc_canvas.winfo_id()))

        # Start playing the VLC stream
        #self.player.play()

        # Schedule the next update
        #self.root.after(10, self.update_vlc_canvas)

        # Schedule the first update of the VLC canvas
        #self.root.after(10, self.update_vlc_canvas)
    def copy_image(self):
        # Get the currently displayed image
        current_image = self.applied_effects[-1][1]

        # Convert the image to a format that can be copied to the clipboard
        current_image = current_image.convert("RGB")
        image_data = np.array(current_image)
        image_data = Image.fromarray(image_data)

        # Copy the image to the clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(image_data)
        self.root.update()

    def paste_image(self):
        # Get the image data from the clipboard
        clipboard_data = self.root.clipboard_get()

        if clipboard_data:
            try:
                # Open the image from clipboard data
                pasted_image = Image.open(io.BytesIO(clipboard_data.encode("utf-8")))
                
                # Optionally, you can display the pasted image in the GUI
                # self.display_result_image(pasted_image)
                
                # Update the applied effects with the pasted image
                self.applied_effects.append(("Pasted Image", pasted_image))
                
                # Notify the user
                messagebox.showinfo("Image Pasted", "Image pasted successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to paste image: {str(e)}")

    def save_image(self):
        # Get the currently displayed image
        current_image = self.applied_effects[-1][1]

        # Ask user for the output image path
        output_image_path = filedialog.asksaveasfilename(title="Save Image", defaultextension=".png")

        if not output_image_path:
            # User canceled the save operation
            return

        # Save the image to the specified path
        current_image.save(output_image_path)

        # Open the folder where the file is saved and select the file
        subprocess.Popen(['explorer', '/select,', os.path.abspath(output_image_path)])

        # Display a popup message
        messagebox.showinfo("Image Saved", "Image saved successfully!")
    def show_context_menu(self, event):
        # Display the context menu at the current mouse position
        self.context_menu.post(event.x_root, event.y_root)
        self.current_widget = event.widget

        
    def show_about_dialog(self):
        app_name = "ArtVisio"
        created_by = "Steadyforge LLC"
        creation_date = "January 18, 2024"
        description = (
    "ArtVisio is a powerful image processing application that empowers you to explore "
    "and enhance your artistic imagination using cutting-edge AI techniques. Transform "
    "your images with a wide range of effects, including blur, sharpening, edge enhancement, "
    "color adjustments, artistic filters, and more. Unleash your creativity and discover "
    "unique visual styles for your photos.\n\n"
    "Key Features:\n"
    "- Apply various artistic effects to your images, such as blur, sharpen, and edge enhance.\n"
    "- Adjust brightness, contrast, and saturation to create striking visual compositions.\n"
    "- Explore unique styles with rotation and flip effects, providing a new perspective.\n"
    "- Access real-time predictions using a pre-trained VGG16 model for object recognition.\n"
    "- Auto-cycle through effects to discover surprising combinations and enhance creativity.\n"
    "- Save your transformed images to share with others or use in creative projects.\n\n"
    "ArtVisio is more than just an image editor; it's a tool for unlocking your artistic potential. "
    "Experiment with different effects, get insights from AI predictions, and turn ordinary images "
    "into extraordinary works of art. Let ArtVisio be your companion in the journey of visual exploration."
)
        modules_used = "Tkinter, PIL, Keras, NumPy"

        about_dialog = AboutDialog(self.root, app_name, created_by, creation_date, description, modules_used)
        self.root.wait_window(about_dialog)
        
    def auto_cycle_fastfoward(self):
        # Increase the auto_cycle_delay to make the prediction steps go faster
        self.auto_cycle_delay = max(100, self.auto_cycle_delay - 100)
    def pause_auto_cycle(self):
        # Toggle the auto_cycle_paused flag
        self.auto_cycle_paused = not self.auto_cycle_paused
    def load_last_base_image(self, last_base_image_path):
        self.last_base_image = last_base_image_path
        self.base_image_path_entry.delete(0, tk.END)
        self.base_image_path_entry.insert(0, last_base_image_path)
        img = Image.open(last_base_image_path)
        self.applied_effects = [(None, img)]
        self.display_base_image(img)
    def apply_effect(self):
        # Get the selected effect from the Combobox
        selected_effect = self.effect_var.get()

    def load_config(self):
        config_path = filedialog.asksaveasfilename(title="Save Config", defaultextension=".config", filetypes=[("Config files", "*.config")])
        if config_path:
            # Check if the selected file is a new config file
            is_new_config = not os.path.isfile(config_path)

            # Logic to load the configuration from the file or add default settings to a new config file
            if is_new_config:
                self.add_default_settings(config_path)
                messagebox.showinfo("Info", f"New configuration file created at {config_path} with default settings")
            else:
                # Logic to load the existing configuration
                messagebox.showinfo("Info", f"Configuration loaded from {config_path}")

    def add_default_settings(self, config_path):
        # Logic to add default settings to a new config file
        # You can customize this based on your configuration structure
        # For example, you might write default values for various settings to the file
        with open(config_path, 'w') as config_file:
            config_file.write("# Default Configuration\n")
            config_file.write("setting1 = value1\n")
            config_file.write("setting2 = value2\n")
            # Add more settings as needed
    #def update_vlc_canvas(self):
        # ... (implementation of the method)
        # Schedule the next update
    #    self.root.after(10, self.update_vlc_canvas)

    def on_closing(self):
        if self.auto_cycle_thread and self.auto_cycle_thread.is_alive():
            self.auto_cycle_thread.join()
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def auto_cycle_effects(self):
        if self.auto_cycle_thread is None or not self.auto_cycle_thread.is_alive():
            self.manual_save_clicked = False  # Reset the flag
            self.auto_cycle_paused = True  # Reset the paused flag
            self.auto_cycle_thread = threading.Thread(target=self._auto_cycle_effects_thread)
            self.auto_cycle_thread.start()
        else:
            # If the thread is running, stop the auto cycle
            self.stop_auto_cycle()

    def _auto_cycle_effects_thread(self):
        if self.auto_cycle_paused or (self.auto_cycle_stopped if hasattr(self, 'auto_cycle_stopped') else False):
            return  # Exit if auto cycle is paused or stopped

        self.auto_cycle_count.set(self.auto_cycle_count.get() + 1)

        if self.auto_cycle_count.get() == 1:
            self.auto_cycle_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        elapsed_time = datetime.now() - datetime.strptime(self.auto_cycle_start_time, '%Y-%m-%d %H:%M:%S')
        self.auto_cycle_elapsed_time.set(str(elapsed_time).split(".")[0])
        if self.applied_effects:
            self.apply_random_effect()

        self.update_auto_cycle_info()
        self.update_real_time_clock()

        self.root.after(self.auto_cycle_delay, self._auto_cycle_effects_thread)


    def stop_auto_cycle(self):
        if self.auto_cycle_thread and self.auto_cycle_thread.is_alive():
            self.auto_cycle_paused = False  # Reset the flag
            self.auto_cycle_thread.join()
            self.auto_cycle_count.set(0)
            self.auto_cycle_elapsed_time.set("00:00:00")
            self.update_auto_cycle_info()
            self.update_real_time_clock()
            self.auto_cycle_stopped = True
            self.auto_cycle_thread = None  # Reset the thread
            
    def pause_auto_cycle(self):
        self.auto_cycle_paused = not self.auto_cycle_paused

            

        if not hasattr(self, 'auto_cycle_stopped'):
            # Initialize the auto_cycle_stopped attribute
            self.auto_cycle_stopped = False

        if not self.auto_cycle_paused and not self.auto_cycle_stopped:
            self.auto_cycle_count.set(self.auto_cycle_count.get() + 1)

            if self.auto_cycle_count.get() == 1:
                self.auto_cycle_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            elapsed_time = datetime.now() - datetime.strptime(self.auto_cycle_start_time, '%Y-%m-%d %H:%M:%S')
            self.auto_cycle_elapsed_time.set(str(elapsed_time).split(".")[0])
            if self.applied_effects:
                self.apply_random_effect()

            self.update_auto_cycle_info()
            self.update_real_time_clock()

            self.root.after(self.auto_cycle_delay, self._auto_cycle_effects_thread)
        elif self.auto_cycle_stopped:
            # Reset the auto cycle count and elapsed time
            self.auto_cycle_count.set(0)
            self.auto_cycle_elapsed_time.set("00:00:00")
            self.update_auto_cycle_info()
            self.update_real_time_clock()
            self.auto_cycle_stopped = False  # Reset the flag            
    def update_real_time_clock(self):
        current_time = time.strftime('%H:%M:%S')
        self.real_time_clock_label.config(text=f"Current Time: {current_time}")

    def update_auto_cycle_info(self):
        self.auto_cycle_count_label.config(text=f"Auto Cycle Count: {self.auto_cycle_count.get()}")
        self.auto_cycle_start_time_label.config(text=f"Auto Cycle Start Time: {self.auto_cycle_start_time}")
        self.auto_cycle_elapsed_time_label.config(text=f"Auto Cycle Elapsed Time: {self.auto_cycle_elapsed_time.get()}")
    def browse_base_image(self, initial_path=None):
        base_image_path = filedialog.askopenfilename(title="Select Base Image", initialdir=initial_path)
        if base_image_path:
            # Save the selected base image path to a file
            with open('last_base_image.txt', 'w') as file:
                file.write(base_image_path)

            self.last_base_image = base_image_path
            self.base_image_path_entry.delete(0, tk.END)
            self.base_image_path_entry.insert(0, base_image_path)
            img = Image.open(base_image_path)
            self.applied_effects = [(None, img)]
            self.display_base_image(img)

    def browse_output_path(self):
        output_image_path = filedialog.asksaveasfilename(title="Select Output Image Path", defaultextension=".png")
        self.output_image_path_entry.delete(0, tk.END)
        self.output_image_path_entry.insert(0, output_image_path)

    def display_base_image(self, img):
        img.thumbnail((300, 300))
        img = ImageTk.PhotoImage(img)

        self.base_panel.config(image=img)
        self.base_panel.image = img

    def display_result_image(self, img):
        img = ImageTk.PhotoImage(img)
        self.result_panel.config(image=img)
        self.result_panel.image = img

    def display_effect_image(self, img):
        img.thumbnail((300, 300))
        img = ImageTk.PhotoImage(img)

        # Code to display effect image in a new window
        effect_window = tk.Toplevel(self.root)
        effect_window.title("Effect Image")
        effect_panel = ttk.Label(effect_window,borderwidth=7,relief="solid", image=img)
        effect_panel.image = img
        effect_panel.pack()

    def apply_deep_dream(self):
        base_image_path = self.base_image_path_entry.get()
        output_image_path = "output_image.png"

        if not base_image_path or not output_image_path:
            messagebox.showwarning("Warning", "Please fill in all the required fields.")
            return

        base_img = self.applied_effects[-1][1]
        base_img = base_img.resize((224, 224), Image.ANTIALIAS)
        img_array = preprocess_input(np.expand_dims(img_to_array(base_img), axis=0))

        predictions = self.vgg16_model.predict(img_array)
        top_prediction = decode_predictions(predictions)[0][0]

        self.top_prediction_label.config(text=f"Top Prediction: {top_prediction[1]} ({top_prediction[2]:.2%})")

        top_predictions = decode_predictions(predictions)[0][:3]
        top_predictions_text = "\n".join([f"{word}: {probability:.2%}" for _, word, probability in top_predictions])
        self.top_predictions_label.config(text=f"Top Predictions:\n{top_predictions_text}")

        selected_effect = self.effect_var.get()
        result_image = self.apply_effect(base_img, selected_effect)
        self.display_result_image(result_image)
#        self.display_effect_image(result_image)

        self.applied_effects.append((selected_effect, result_image))
        #self.save_image(result_image, output_image_path)
    def save_image2(self, result_image=None, output_image_path=None):
        if result_image is None:
            # If result_image is not provided, use the last applied effect
            result_image = self.applied_effects[-1][1]
        if len(self.applied_effects) > 1:
            self.applied_effects.pop()
            _, prev_image = self.applied_effects[-1]
            self.display_result_image(prev_image)
            self.display_effect_image(prev_image)
            # Save and update the undone effect
            self.save_image(prev_image)
        random_number = random.randint(1, 1000)
        output_image_path = f"output_image_{random_number}.png"
        desired_width = 800
        desired_height = 600
        result_image_resized = result_image.resize((desired_width, desired_height))
        result_image_resized.save(output_image_path)

        # Open the folder where the file is saved and select the file
        subprocess.Popen(['explorer', '/select,', os.path.abspath(output_image_path)])

        # Display a popup message only when the button is clicked manually
        if self.manual_save_clicked:
            messagebox.showinfo("Image Saved", "Image saved successfully!")
            self.manual_save_clicked = False  # Reset the flag
            
    def save_image(self, result_image=None, output_image_path=None):
        if result_image is None:
            # If result_image is not provided, use the last applied effect
            result_image = self.applied_effects[-1][1]

        output_image_path = "output_image.png"
        desired_width = 800
        desired_height = 600
        result_image_resized = result_image.resize((desired_width, desired_height))
        result_image_resized.save(output_image_path)

        # Open the folder where the file is saved
        # subprocess.Popen(['explorer', '/select,', os.path.normpath(output_image_path)])

        # Display a popup message only when the button is clicked manually
        if self.manual_save_clicked:
            messagebox.showinfo("Image Saved", "Image saved successfully!")
            self.manual_save_clicked = False  # Reset the flag
    def apply_random_effect(self):
        all_effects = [
            "Original", "Blur", "Sharpen", "Edge Enhance",
            "Brightness Increase", "Brightness Decrease",
            "Contrast Increase", "Contrast Decrease",
            "Saturation Increase", "Saturation Decrease",
            "Rotate 90 degrees", "Flip Horizontal", "Flip Vertical",
            "Smooth", "Emboss", "Find Edges",
            "Grayscale", "Sepia", "Invert Colors", "Posterize",
            "Negative", "Solarize", "Oil Paint", "Watercolor",
            "Pencil Sketch", "Cartoonize", "Pixelate", "Colorize",
            "Heatmap", "Sobel Edge", "Swirl", "Vignette",
            "Glow", "Comic Book", "Wave", "Raindrops",
            "Mosaic", "Pop Art", "Crosshatch", "Fisheye"
            "Blur", "Sharpen", "Edge Enhance",
            "Brightness Increase", "Brightness Decrease",
            "Contrast Increase", "Contrast Decrease",
            "Saturation Increase", "Saturation Decrease",
            "Rotate 90 degrees", "Flip Horizontal", "Flip Vertical",
            "Smooth", "Emboss", "Find Edges",
            "Grayscale", "Sepia", "Invert Colors", "Posterize"
        ]
        random_effect = random.choice(all_effects)
        self.effect_var.set(random_effect)

        _, last_applied_image = self.applied_effects[-1]

        if last_applied_image.mode != 'RGB':
            last_applied_image = last_applied_image.convert('RGB')

        base_img = last_applied_image.resize((224, 224), Image.ANTIALIAS)

        img_array = preprocess_input(np.expand_dims(img_to_array(base_img), axis=0))

        predictions = self.vgg16_model.predict(img_array)
        top_prediction = decode_predictions(predictions)[0][0]

        self.top_prediction_label.config(text=f"Top Prediction: {top_prediction[1]} ({top_prediction[2]:.2%})")

        top_predictions = decode_predictions(predictions)[0][:3]
        top_predictions_text = "\n".join([f"{word}: {probability:.2%}" for _, word, probability in top_predictions])
        self.top_predictions_label.config(text=f"Top Predictions:\n{top_predictions_text}")

        result_image = self.apply_effect(base_img, random_effect)

        # Update the displayed image in the result_panel
        self.display_result_image(result_image)

        self.applied_effects.append((random_effect, result_image))
        self.save_image(result_image)

        self.root.after(0, lambda: self.top_prediction_label.config(
            text=f"Top Prediction: {top_prediction[1]} ({top_prediction[2]:.2%})"
        ))
         # Display the progress bar
        self.progress.grid(row=1, column=0, pady=10)
        self.progress["value"] = 0
        self.root.update_idletasks()
        # Start the process in a separate thread
        threading.Thread(target=self.execute_long_running_process).start()

        total_steps = 100  # Adjust based on the total steps of your process

        for i in range(total_steps):
            # Simulate your process step
            time.sleep(0.01)

            # Update progress bar
            self.progress["value"] = (i + 1) * (100 / total_steps)
            self.root.update_idletasks()

        # Hide the progress bar after completion
        self.progress.grid_forget()
    def execute_long_running_process(self):
        total_steps = 100  # Adjust based on the total steps of your process

        for i in range(total_steps):
            # Simulate your process step
            time.sleep(0.1)

            # Update progress bar on the main thread
            self.root.after(0, self.update_progress, (i + 1) * (100 / total_steps))

        # Hide the progress bar after completion
        self.root.after(0, self.hide_progress)
    def update_progress(self, value):
        # Update progress bar
        self.progress["value"] = value

    def hide_progress(self):
        # Hide the progress bar
        self.progress.grid_forget()
        
    def undo_effect(self):
        # Undo the last applied effect
        if len(self.applied_effects) > 1:
            self.applied_effects.pop()
            _, prev_image = self.applied_effects[-1]
            self.display_result_image(prev_image)
#            self.display_effect_image(prev_image)
            # Save and update the undone effect
            self.save_image(prev_image)

            # Check if the popup is not already open
            if not self.popup_open:
                # Open the popup only when it's not already open
                self.open_popup()
    def open_popup(self):
        # Your existing code to open the popup

        # Set the flag to indicate that the popup is open
        self.popup_open = True

    def close_popup(self):
        # Your existing code to close the popup

        # Set the flag to indicate that the popup is closed
        self.popup_open = False
                
    def apply_effect(self, img, effect):
        if effect is None:
            return img

        if effect == "Blur":
            return img.filter(ImageFilter.BLUR)
        elif effect == "Sharpen":
            return img.filter(ImageFilter.SHARPEN)
        elif effect == "Edge Enhance":
            return img.filter(ImageFilter.EDGE_ENHANCE)
        elif effect == "Brightness Increase":
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(1.5)
        elif effect == "Brightness Decrease":
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(0.5)
        elif effect == "Contrast Increase":
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(1.5)
        elif effect == "Contrast Decrease":
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(0.5)
        elif effect == "Saturation Increase":
            enhancer = ImageEnhance.Color(img)
            return enhancer.enhance(1.5)
        elif effect == "Saturation Decrease":
            enhancer = ImageEnhance.Color(img)
            return enhancer.enhance(0.5)
        elif effect == "Rotate 90 degrees" and self.rotation_checkbox_var.get():
            return img.rotate(90)
        elif effect == "Flip Horizontal" and self.flip_checkbox_var.get():
            return img.transpose(Image.FLIP_LEFT_RIGHT)
        elif effect == "Flip Vertical" and self.flip_checkbox_var.get():
            return img.transpose(Image.FLIP_TOP_BOTTOM)
        elif effect == "Smooth":
            return img.filter(ImageFilter.SMOOTH)
        elif effect == "Emboss":
            return img.filter(ImageFilter.EMBOSS)
        elif effect == "Find Edges":
            return img.filter(ImageFilter.FIND_EDGES)
        elif effect == "Grayscale":
            return ImageOps.grayscale(img)
        elif effect == "Sepia":
            return self.apply_sepia(img)
        elif effect == "Invert Colors":
            return ImageOps.invert(img)
        elif effect == "Posterize":
            return ImageOps.posterize(img, 3)  # 3 levels of posterization
        # resized_img = img.resize((500, 500), Image.ANTIALIAS)
        # Add more effects as needed
        return img

    def apply_sepia(self, image):
        # Apply a simpler sepia filter
        sepia_filter = ImageEnhance.Color(image).enhance(0.7)
        sepia_image = ImageEnhance.Contrast(sepia_filter).enhance(1.2)
        sepia_image = ImageEnhance.Brightness(sepia_image).enhance(0.8)
        return sepia_image


if __name__ == "__main__":
    root = tk.Tk()
    app = DeepDreamGUI(root)
    root.mainloop()        
