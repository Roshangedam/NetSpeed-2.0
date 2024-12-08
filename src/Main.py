import random
import psutil
import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import tkinter.font as tkFont
import json
import os
import sys
import pystray
from PIL import Image
import threading
import win32security
import ntsecuritycon as con

class DigitalNetworkMonitor:
    def __init__(self):
        self.app_icon_path=self.get_file_path("assets","app_icon.ico")
        self.settings_file = self.get_file_path("config","settings.json")
        self.load_settings()  # Load saved settings if available
        self.old_data = psutil.net_io_counters(pernic=True)
        self.root = tk.Tk()
        
        # Frameless and transparent window
        self.root.overrideredirect(True)  # Remove the title bar
        self.root.attributes('-topmost', True)  # Keep the window on top
        self.root.attributes('-transparentcolor', 'black')  # Set transparency
        self.root.configure(bg='black')  # Match the transparent color
        self.root.iconbitmap(self.app_icon_path)
        # Initialize font after root window is created
        self.font = tkFont.Font(family=self.font_family, size=self.font_size)

        # Speed display with the font size and buttons for adjusting it
        self.speed_label = tk.StringVar()
        self.label = tk.Label(
            self.root,
            textvariable=self.speed_label,
            font=self.font,  # Use loaded font
            fg=self.text_color,  # Use saved text color
            bg="black",
            anchor="center"  # Center-align text
        )
        self.label.pack()

        # Right-click context menu
        self.create_context_menu()

        # Enable dragging of the frameless window
        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        
        self.create_tray_icon()        
        
        #for position in right center
        set_window_position(self)
        # Update speeds periodically
        self.update_data()  # Start updating the network stats
        self.root.mainloop()

    def start_move(self, event):
        """Store the initial position when the mouse is pressed."""
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        """Move the window when the mouse is dragged."""
        delta_x = event.x_root - self.x
        delta_y = event.y_root - self.y
        self.root.geometry(f"+{event.x_root - self.x}+{event.y_root - self.y}")

    def create_context_menu(self):
        """Create and style the right-click context menu with extra options."""
        if hasattr(self, "context_menu"):
            return  # Prevent duplicate creation
        
        self.context_menu = tk.Menu(self.root, tearoff=0, bg='white', fg='black', bd=2, relief="solid")
        
        # Standard options
        self.context_menu.add_command(label="Choose Font", command=self.show_font_select)
        self.context_menu.add_command(label="Change Color", command=self.change_color)
        self.context_menu.add_command(label="Reset to Default", command=self.reset_to_default)
        self.context_menu.add_command(label="Exit", command=self.exit_app)
        self.context_menu.add_separator()

        # Font size control (as buttons in the context menu)
        # self.font_size_menu = tk.Menu(self.context_menu, tearoff=0)
        # self.font_size_menu.add_command(label="+", command=self.increase_font_size)
        # self.font_size_menu.add_command(label="-", command=self.decrease_font_size)
        # self.context_menu.add_cascade(label="Font Size", menu=self.font_size_menu)
        self.context_menu.add_command(label="Font Size", command=lambda: self.show_font_size_dialog)

        # Extra menu options
        self.context_menu.add_command(label="Save Settings", command=self.save_settings)
        self.context_menu.add_command(label="Toggle Transparency", command=self.toggle_transparency)
        # self.context_menu.add_command(label="Change Background Color", command=self.change_background_color)

        # Bind right-click to show the context menu
        self.root.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu on right-click."""
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu.entryconfig("Choose Font", command=lambda: self.show_font_select(event))  # Pass event
        self.context_menu.entryconfig("Font Size", command=lambda: self.show_font_size_dialog(event))  # Pass event        

    def show_tray_context_menu(self):
        """Show context menu triggered by tray icon."""
        self.root.deiconify()  # Make the root visible
        # self.root.geometry("300x200")  # Example position/size for the root window
        self.create_context_menu()
        # Show context menu near the application window (top-left corner as an example)
        self.context_menu.post(self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50)

    def create_tray_icon(self):
        """Create system tray icon."""
        def on_quit(icon, item):
            self.root.quit()
            icon.stop()

        def on_show(icon, item):
            # Restore the window to the right-center position
            self.root.deiconify()
            self.set_window_position_right_center()

        icon_image = Image.open(self.app_icon_path)
        
        self.icon = pystray.Icon("test_icon", icon_image, "NetSpeed 2.0", menu=pystray.Menu(
            pystray.MenuItem("Show", on_show),
            pystray.MenuItem("Options", self.show_tray_context_menu),
            pystray.MenuItem("Exit", on_quit)
        ))
        
        # Start the tray icon in a separate thread
        tray_thread = threading.Thread(target=self.icon.run)
        tray_thread.daemon = True
        tray_thread.start()

        # Hide the main window on start
        # self.root.withdraw()

    def set_window_position_right_center(self):
        """Position the window at the right-center of the screen."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Calculate right-center position
        x = screen_width - window_width - 50  # 50 pixels offset from right edge
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")

    def show_font_select(self, event=None):
        """Display a list of system fonts in a drop-down to select a font at the mouse click position."""
        # Create the Toplevel window for font selection
        font_select_window = tk.Toplevel(self.root)
        font_select_window.title("Select Font")
        font_select_window.iconbitmap(self.app_icon_path)
        # Position the dialog at the mouse click position
        if event:
            font_select_window.geometry(f"+{event.x_root}+{event.y_root}")
        else:
            # Fallback to default position if event is not passed
            font_select_window.geometry("+100+100")

        # Get the list of system fonts
        available_fonts = sorted(tkFont.families())  # Sorted for easier navigation

        # Create a combobox to list available fonts
        font_combobox = ttk.Combobox(font_select_window, values=available_fonts, state="readonly")
        font_combobox.set(self.font_family)  # Set current font family as default
        font_combobox.pack(padx=20, pady=10)

        # Function to update the font of the apply button dynamically
        def update_apply_button_font(event=None):
            """Update the font of the apply button dynamically as the font changes in combobox."""
            selected_font = font_combobox.get()        
            if selected_font:               
                apply_button.config(text=self.get_random_message(),font=(selected_font, 12))  # Update font of the button

        # Bind combobox selection event to update apply button font
        font_combobox.bind("<<ComboboxSelected>>", update_apply_button_font)

        # Add a button to apply selected font
        def apply_font():
            selected_font = font_combobox.get()
            if selected_font:
                self.font_family = selected_font
                self.font.config(family=self.font_family)
                self.label.config(font=self.font)
                self.user_settings['font'] = self.font_family  # Save font to user settings
                self.save_settings()  # Save user settings
            font_select_window.destroy()
        apply_button = tk.Button(font_select_window, text='Select', command=apply_font)
        apply_button.pack(padx=20, pady=10)
        
        # Initially set the font of the apply button
        #update_apply_button_font()


    def show_font_size_dialog(self, event=None):
        """Create a dialog for adjusting font size with + and - buttons."""
        # Create a new window (Toplevel) for font size control
        font_size_dialog = tk.Toplevel(self.root)
        font_size_dialog.title("Adjust Font Size")
        font_size_dialog.iconbitmap(self.app_icon_path)
        

        # Position the dialog near the main window (at the mouse click position)
        if event:
            font_size_dialog.geometry(f"+{event.x_root}+{event.y_root}")
        else:
            font_size_dialog.geometry("+300+300")  # Default position

        # Create buttons to increase and decrease font size
        button_frame = tk.Frame(font_size_dialog)
        button_frame.pack(pady=20)

        increase_button = tk.Button(button_frame, text="+", width=5, command=self.increase_font_size_dialog)
        increase_button.pack(side=tk.LEFT, padx=5)

        decrease_button = tk.Button(button_frame, text="-", width=5, command=self.decrease_font_size_dialog)
        decrease_button.pack(side=tk.LEFT, padx=5)

        # Create an OK button to apply the changes
        ok_button = tk.Button(font_size_dialog, text="OK", command=lambda: self.apply_font_save(font_size_dialog))
        ok_button.pack(pady=10)

    def increase_font_size_dialog(self):
        """Increase the font size in the font size dialog."""
        self.font_size += 2  # Increase by 2 points
        self.apply_font_size()  # Update font in main window immediately

    def decrease_font_size_dialog(self):
        """Decrease the font size in the font size dialog."""
        if self.font_size > 2:  # Prevent font size from going below 2
            self.font_size -= 2
            self.apply_font_size()  # Update font in main window immediately

    def apply_font_save(self, font_size_dialog):
        """Apply the font size changes to the main window and close the font size dialog."""
        self.font.config(size=self.font_size)  # Update the main font
        self.label.config(font=self.font)  # Update the label font
        self.user_settings['font_size'] = self.font_size  # Save the font size to settings
        self.save_settings()  # Save user settings
        font_size_dialog.destroy()  # Close the dialog window

    def apply_font_size(self):
        """Apply the font size changes to the main window immediately."""
        self.font.config(size=self.font_size)  # Update the main font
        self.label.config(font=self.font)  # Update the label font


    

    def change_color(self):
        """Open color chooser to change the font color."""
        color = colorchooser.askcolor()[1]  # Get the color in hex format
        if color:
            self.text_color = color
            self.label.config(fg=self.text_color)
            self.user_settings['color'] = color  # Save color to user settings
            self.save_settings()  # Save user settings

    def reset_font_size(self):
        """Reset font size to default value."""
        self.font_size = 10  # Default font size
        self.font.config(size=self.font_size)
        self.label.config(font=self.font)
        self.user_settings['font_size'] = self.font_size  # Save font size to user settings
        self.save_settings()  # Save user settings

    def save_settings(self):
        """Save current settings (both user and default) to file."""
        settings = {
            'user': self.user_settings,
            'default': self.default_settings
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

    def toggle_transparency(self):
        """Toggle transparency of the window."""
        current_transparency = self.root.attributes('-transparentcolor')
        if current_transparency == 'black':
            self.root.attributes('-transparentcolor', '')  # Disable transparency
        else:
            self.root.attributes('-transparentcolor', 'black')  # Enable transparency

    def change_background_color(self):
        """Allow the user to change the background color of the window."""
        color = colorchooser.askcolor()[1]  # Get the color in hex format
        if color:
            self.root.configure(bg=color)  # Set the background color of the window
            self.user_settings['bg_color'] = color  # Save background color to user settings
            self.save_settings()  # Save user settings

    def reset_to_default(self):
        """Reset settings to default values."""
        self.font = tkFont.Font(family=self.default_settings['font'], size=self.default_settings['font_size'])
        self.text_color = self.default_settings['color']
        self.bg_color = self.default_settings.get('bg_color', 'black')  # Ensure bg_color exists in default
        self.label.config(font=self.font, fg=self.text_color, bg=self.bg_color)
        self.user_settings = self.default_settings.copy()  # Reset user settings
        self.save_settings()  # Save default settings to user settings

    def exit_app(self):
        """Exit the application."""
        self.root.quit()

    def load_settings(self):
        """Load settings from file (if available)."""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                self.user_settings = settings.get('user', {})
                self.default_settings = settings.get('default', {})
                
                # Apply user settings or fallback to defaults
                self.font_family = self.user_settings.get('font', "DS-Digital")  # Default font
                self.font_size = self.user_settings.get('font_size', 12)  # Default font size
                self.text_color = self.user_settings.get('color', "#76c7c0")  # Default color
                self.bg_color = self.user_settings.get('bg_color', "black")  # Default background color
                # Load messages list or fallback to default messages
                self.messages = settings.get('messages', [
                    "Good choice!",
                    "That will be great!",
                    "Nice pick!",
                    "Excellent selection!",
                    "Looking good!",
                    "That's a perfect match!",
                    "Great idea!",
                    "Wonderful choice!"
                ])
                
        else:
            # Default settings if no saved settings
            self.default_settings = {
                'font': "DS-Digital",
                'font_size': 12,
                'color': "#76c7c0",
                'bg_color': "black",
                "font_family": ""  # Ensure bg_color exists in default settings
            }
            self.user_settings = self.default_settings.copy()
            self.messages = [
                "Good choice!",
                "That will be great!",
                "Nice pick!",
                "Excellent selection!",
                "Looking good!",
                "That's a perfect match!",
                "Great idea!",
                "Wonderful choice!"
            ]

    def update_data(self):
        """Update network statistics periodically."""
        sent_bytes = 0
        recv_bytes = 0

        # Get network stats
        new_data = psutil.net_io_counters(pernic=True)

        for interface, stats in new_data.items():
            if stats.bytes_sent > 0 or stats.bytes_recv > 0:
                sent_diff = stats.bytes_sent - self.old_data[interface].bytes_sent
                recv_diff = stats.bytes_recv - self.old_data[interface].bytes_recv

                sent_bytes += sent_diff
                recv_bytes += recv_diff

        # Convert bytes to bits per second
        upload_speed_bps = sent_bytes * 8
        download_speed_bps = recv_bytes * 8

        # Format the speeds
        self.speed_label.set(
            f"{self.format_speed(download_speed_bps)}  ↓  {self.format_speed(upload_speed_bps)} ↑"
        )

        # Update the old data and schedule the next update
        self.old_data = new_data
        self.root.after(1000, self.update_data)  # Update every second

    def format_speed(self, bits_per_sec):
        """Convert bits per second to an appropriate unit with a label, remove decimals."""
        if bits_per_sec < 1024:
            value = f"{int(bits_per_sec)} bps"
        elif bits_per_sec < 1024 ** 2:
            value = f"{int(bits_per_sec / 1024)} kbps"
        elif bits_per_sec < 1024 ** 3:
            value = f"{int(bits_per_sec / (1024 ** 2))} Mbps"
        else:
            value = f"{int(bits_per_sec / (1024 ** 3))} Gbps"
        return value.ljust(10)
   
    def get_file_path(self,path,file):
        """Get the correct path to settings.json based on the application's structure."""
        if getattr(sys, 'frozen', False):  # Check if running as a bundled app
         
            if file.lower().endswith('.ico'):
                return os.path.join(sys._MEIPASS,path, file)
            
            appdata_path = os.path.join(os.getenv('APPDATA'), 'NetSpeed 2.0')
            if not os.path.exists(appdata_path):                
                os.makedirs(appdata_path)
            set_permissions(appdata_path)
            file_path = os.path.join(appdata_path, file)

            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    # Write default content to the settings file if needed
                    default_settings = {
                        "user": {
                            "font": "DS-Digital",
                            "font_size": 14,
                            "color": "#76c7c0",
                            "font_family": ""
                        },
                        "default": {
                            "font": "DS-Digital",
                            "font_size": 14,
                            "color": "#76c7c0",
                            "font_family": ""
                        },
                        "messages": [
                            "Good choice!",
                            "That will be great!",
                            "Nice pick!",
                            "Excellent selection!",
                            "Looking good!",
                            "That's a perfect match!",
                            "Great idea!",
                            "Wonderful choice!"
                        ]
                    }
                    json.dump(default_settings, f, indent=4)
                    
                
            return file_path
        # Check if running in a bundled executable
        else:
            # Running as a script, locate settings.json relative to the script
            base_path = os.path.dirname(os.path.abspath(__file__))  # Get the current script directory
            return os.path.join(base_path, path, file)
   
    def get_random_message(self):
        """Retrieve a random message from the messages list, or default to 'Apply'."""
        if isinstance(self.messages, list) and self.messages:
            return random.choice(self.messages)
        return "Apply"

        
def set_window_position(self):
        """Set the window's position to the right-center of the screen."""
        screen_width = self.root.winfo_screenwidth()  # Get screen width
        screen_height = self.root.winfo_screenheight()  # Get screen height
        window_width = self.root.winfo_reqwidth()  # Get window width
        window_height = self.root.winfo_reqheight()  # Get window height

        # Calculate position: right-center
        x = screen_width - window_width - 10  # 10 pixels from the right edge
        y = (screen_height - window_height) // 2  # Center vertically

        # Set the geometry (position) of the window
        self.root.geometry(f"+{x}+{y}")

def set_permissions(directory_path):
    """Sets permissions to allow full access for the current user."""
    try:
        # Get the current user's SID
        user_name = os.getlogin()  # Get the username of the current user
        user_sid, _, _ = win32security.LookupAccountName(None, user_name)
        
        # Get the current DACL (Discretionary Access Control List) for the folder
        security_descriptor = win32security.GetFileSecurity(directory_path, win32security.DACL_SECURITY_INFORMATION)
        dacl = security_descriptor.GetSecurityDescriptorDacl()
        
        # Add full access rights for the current user
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user_sid)
        
        # Apply the updated DACL back to the directory
        win32security.SetFileSecurity(directory_path, win32security.DACL_SECURITY_INFORMATION, security_descriptor)
        
        print(f"Permissions set to full control for {user_name} on {directory_path}")
        return True
    except Exception as e:
        print(f"Error setting permissions: {e}")
        return False
        
# Run the application
if __name__ == "__main__":
    DigitalNetworkMonitor()


# pyinstaller --onefile --windowed --name "NetSpeed 2.0" --icon=src/assets/app_icon.ico --add-data "src/assets/app_icon.ico;assets"  --add-data "src/config/settings.json;config"  --version-file version_info.txt src/Main.py



