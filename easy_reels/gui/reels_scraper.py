import customtkinter as ctk
from tkinter import messagebox, simpledialog
import threading
import time
import os
import random
from queue import Queue
import json
import datetime

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# --- MODIFICATION: Inherit from CTkToplevel to act as a popup window ---
class ReelScraperApp(ctk.CTkToplevel):
    def __init__(self, parent): # --- MODIFICATION: Accept a parent window ---
        super().__init__(parent)

        self.title("Instagram Reels Scraper")
        self.geometry("850x550")
        self.minsize(750, 450)

        # --- MODIFICATION: Make it a modal window that stays on top ---
        self.transient(parent)
        self.grab_set()

        # --- App State ---
        self.scraper_thread = None
        self.stop_event = None
        self.log_queue = Queue()

        # --- Account Management ---
        self.accounts_file = "config/scraper_accounts.json"
        self.accounts = {}
        self.load_accounts()

        # --- UI Setup ---
        self.create_widgets()
        self.after(100, self.process_log_queue)
        
        # --- MODIFICATION: Handle window closing ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window closing gracefully."""
        if self.scraper_thread and self.scraper_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", "Scraping is in progress. Are you sure you want to close? This will stop the current process."):
                self.stop_scraping()
                self.destroy()
        else:
            self.destroy()

    def create_widgets(self):
        """Creates and configures the GUI elements."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Frame (Controls) ---
        controls_frame = ctk.CTkFrame(self, width=300)
        controls_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ns")

        ctk.CTkLabel(controls_frame, text="Reels Scraper", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 20))

        # --- Account Frame ---
        account_frame = ctk.CTkFrame(controls_frame)
        account_frame.pack(pady=10, padx=10, fill="x", expand=False)
        ctk.CTkLabel(account_frame, text="Account Management").pack(pady=(5,0))

        # Account Dropdown
        self.account_selector = ctk.CTkComboBox(account_frame, values=list(self.accounts.keys()) or ["No accounts saved"], command=self.on_account_select)
        self.account_selector.pack(pady=10, padx=10, fill="x")

        self.username_entry = ctk.CTkEntry(account_frame, placeholder_text="Username")
        self.username_entry.pack(pady=5, padx=10, fill="x")
        self.password_entry = ctk.CTkEntry(account_frame, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=5, padx=10, fill="x")

        account_button_frame = ctk.CTkFrame(account_frame, fg_color="transparent")
        account_button_frame.pack(pady=5, padx=10, fill="x")
        account_button_frame.grid_columnconfigure((0, 1), weight=1)

        self.save_account_button = ctk.CTkButton(account_button_frame, text="Save", command=self.add_or_update_account)
        self.save_account_button.grid(row=0, column=0, padx=(0,5), sticky="ew")
        self.delete_account_button = ctk.CTkButton(account_button_frame, text="Delete", command=self.delete_selected_account, fg_color="#D32F2F", hover_color="#C62828")
        self.delete_account_button.grid(row=0, column=1, padx=(5,0), sticky="ew")

        # --- Scraping Frame ---
        scraping_frame = ctk.CTkFrame(controls_frame)
        scraping_frame.pack(pady=10, padx=10, fill="x", expand=False)
        ctk.CTkLabel(scraping_frame, text="Scraping Settings").pack()
        self.limit_entry = ctk.CTkEntry(scraping_frame, placeholder_text="Number of Reels (e.g., 50)")
        self.limit_entry.pack(pady=5, padx=10, fill="x")

        # --- Main Buttons ---
        self.start_button = ctk.CTkButton(controls_frame, text="Start Scraping", command=self.start_scraping, height=40)
        self.start_button.pack(pady=(20, 5), padx=20, fill="x")
        self.stop_button = ctk.CTkButton(controls_frame, text="Stop Scraping", command=self.stop_scraping, fg_color="red", hover_color="darkred", state="disabled")
        self.stop_button.pack(pady=5, padx=20, fill="x")

        # --- Right Frame (Logs) ---
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", font=("Consolas", 12))
        self.log_textbox.grid(row=0, column=0, sticky="nsew")
        
        # --- Initialize dropdown ---
        self.update_account_dropdown()

    # --- Account Management Methods ---
    def load_accounts(self):
        """Loads accounts from the JSON file."""
        try:
            os.makedirs(os.path.dirname(self.accounts_file), exist_ok=True)
            with open(self.accounts_file, "r") as f:
                self.accounts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.accounts = {}

    def save_accounts(self):
        """Saves the current accounts to the JSON file."""
        with open(self.accounts_file, "w") as f:
            json.dump(self.accounts, f, indent=4)

    def update_account_dropdown(self):
        """Updates the dropdown with current account usernames."""
        usernames = list(self.accounts.keys())
        if not usernames:
            self.account_selector.configure(values=["No accounts saved"])
            self.account_selector.set("No accounts saved")
        else:
            self.account_selector.configure(values=usernames)

    def on_account_select(self, selected_username):
        """Fills credentials when an account is selected from the dropdown."""
        if selected_username in self.accounts:
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, selected_username)
            self.password_entry.delete(0, "end")
            self.password_entry.insert(0, self.accounts[selected_username])

    def add_or_update_account(self):
        """Saves or updates an account based on the entry fields."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Missing Info", "Please enter both a username and password to save.")
            return
        self.accounts[username] = password
        self.save_accounts()
        self.update_account_dropdown()
        self.account_selector.set(username)
        messagebox.showinfo("Success", f"Account '{username}' has been saved.")

    def delete_selected_account(self):
        """Deletes the account currently selected in the dropdown."""
        selected_username = self.account_selector.get()
        if selected_username not in self.accounts:
            messagebox.showwarning("No Account Selected", "Please select a valid account to delete.")
            return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the account '{selected_username}'?"):
            del self.accounts[selected_username]
            self.save_accounts()
            self.update_account_dropdown()
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
            messagebox.showinfo("Success", f"Account '{selected_username}' has been deleted.")

    # --- Logging Methods ---
    def log(self, message):
        """Adds a message to the log queue to be displayed in the textbox."""
        timestamp = time.strftime('%H:%M:%S')
        self.log_queue.put(f"[{timestamp}] {message}\n")

    def process_log_queue(self):
        """Updates the log textbox from the queue in a thread-safe way."""
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message)
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")
        self.after(100, self.process_log_queue)

    # --- Scraping Control Methods ---
    def start_scraping(self):
        """Validates inputs and starts the scraping process in a new thread."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            reel_limit = int(self.limit_entry.get())
            if reel_limit <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a positive whole number for the reel limit.")
            return

        if not all([username, password]):
            messagebox.showwarning("Missing Information", "Please select or enter a username and password.")
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        self.stop_event = threading.Event()
        self.scraper_thread = threading.Thread(
            target=self.run_scraper_thread,
            args=(username, password, reel_limit),
            daemon=True
        )
        self.scraper_thread.start()

    def stop_scraping(self):
        """Signals the scraper thread to stop."""
        if self.stop_event:
            self.log("🛑 Stop signal sent. Finishing current action...")
            self.stop_event.set()
            self.stop_button.configure(state="disabled")

    def on_scraping_complete(self):
        """Resets the UI after the scraper thread has finished."""
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.scraper_thread = None
        self.stop_event = None

    # --- File Handling ---
    def get_output_filename(self):
        """Generates a unique filename in the format MM-DD-N.txt."""
        today = datetime.datetime.now().strftime("%m-%d")
        i = 1
        while True:
            filename = f"scraped_links_{today}-{i}.txt"
            if not os.path.exists(filename):
                return filename
            i += 1
            
    def save_links_to_file(self, links_set, filename):
        """Saves the current set of links to the specified file."""
        self.log(f"💾 Saving {len(links_set)} links to {filename}...")
        with open(filename, "w") as f:
            for link in sorted(list(links_set)):
                f.write(f"{link}\n")

    # --- Core Scraper Logic ---
    def run_scraper_thread(self, username, password, reel_limit):
        """The main scraper logic that runs in the background thread."""
        driver = None
        try:
            self.log("🚀 Starting the Instagram Reels scraper...")
            chrome_options = Options()
            chrome_options.add_argument("--log-level=3") # Suppress console logs
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            driver = webdriver.Chrome(options=chrome_options)

            driver.get("https://www.instagram.com/accounts/login/")
            self.log("😴 Waiting for the login page to load...")
            time.sleep(random.uniform(2, 4))

            self.log(f"👤 Logging in as {username}...")
            driver.find_element(By.NAME, "username").send_keys(username)
            driver.find_element(By.NAME, "password").send_keys(password)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            self.log("⏳ Waiting for login...")
            time.sleep(random.uniform(5, 8))

            # --- MODIFICATION: Manual confirmation instead of automatic check ---
            self.log("⏸️ Please complete the login manually if needed (2FA, alerts, etc.)")
            self.log("⏸️ The scraper is waiting for you to proceed...")

            # Wait for user confirmation in main thread
            confirmation_needed = threading.Event()
            user_confirmed = [False]  # Mutable container for thread-safe communication

            def ask_confirmation():
                result = messagebox.askyesno(
                    "Login Confirmation",
                    "Have you completed the login process?\n\n"
                    "Click YES if you're logged in and ready to continue.\n"
                    "Click NO to cancel scraping."
                )
                user_confirmed[0] = result
                confirmation_needed.set()

            # Schedule confirmation dialog in main thread
            self.after(0, ask_confirmation)
            confirmation_needed.wait()  # Wait for user response

            if not user_confirmed[0]:
                self.log("❌ Scraping canceled by user.")
                return

            self.log("✅ Login confirmed! Continuing...")

            self.log("🎬 Navigating to the Reels feed...")
            driver.get("https://www.instagram.com/reels/")
            time.sleep(random.uniform(4, 6))

            reel_links = set()
            filename = self.get_output_filename()
            self.log(f"✍️ Output will be saved to: {filename}")
            self.log(f"🕵️‍♂️ Starting to scrape for {reel_limit} reel links...")

            while len(reel_links) < reel_limit:
                if self.stop_event.is_set():
                    self.log("🛑 Process stopped by user.")
                    break

                ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
                time.sleep(random.uniform(1.5, 2.5))

                current_url = driver.current_url
                
                # A simple check to ensure it's a valid reel URL
                if "/reels/" in current_url and len(current_url.split('/')) >= 5:
                    initial_count = len(reel_links)
                    reel_links.add(current_url)
                    
                    if len(reel_links) > initial_count:
                        self.log(f"✅ Link #{len(reel_links)} found: ...{current_url.split('/')[-2][-15:]}")
                        watch_time = random.uniform(3, 7)
                        self.log(f"👀 Watching reel for {watch_time:.2f} seconds...")
                        time.sleep(watch_time)

                        # Save a backup every 10 links
                        if len(reel_links) % 10 == 0:
                            self.save_links_to_file(reel_links, filename)

            self.log(f"\n✅ Scraping complete! Found {len(reel_links)} unique links.")
            self.save_links_to_file(reel_links, filename)

        except Exception as e:
            self.log(f"❌ An error occurred: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        finally:
            if driver:
                driver.quit()
            self.log("🎉 All done!")
            self.after(0, self.on_scraping_complete) # Safely schedule UI update