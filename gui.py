import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys
from masses import *
import pandas as pd
import webbrowser

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update()

    def flush(self):
        pass  # Needed for compatibility with Python's built-in print function

def select_file(entry,output_text, mod=False):
    file_path = filedialog.askopenfilename()
    entry.delete(0, tk.END)
    entry.insert(0, file_path)
    mess = verify_mods(file_path) if mod else verify_masses(file_path)
    if mess:
        entry.delete(0,tk.END)
    else: 
        mess = 'Loaded ' + file_path
    mess += '\n' 
    output_text.insert(tk.END, mess)
    output_text.see(tk.END)
    output_text.update()
   
def verify_mods(path):
    if not path.lower().endswith("_modifications.csv"):
        return "Invalid file name - make sure the file ends in \"_modifications.csv\""
    mods = pd.read_csv(path)
    req_cols = ["Name", "ShortName", "Experiment", "Mass", "To"]
    for col in req_cols:
        if col not in mods.columns: 
            return f"Invalid column names - missing Col \"{col}\" - Please see ReadME for input specification"
    return "" 

def verify_masses(path):
    if not path.lower().endswith("_observed_masses.csv"):
        return "Invalid file name - make sure the file ends in \"_observed_masses.csv\""
    return ""

def open_readme():
    PATH = r'./ReadME.pdf'
    webbrowser.open_new(PATH)

def run_command(mod, masses, error, run_button, output_text):
    run_button.config(state=tk.DISABLED)
    mod_path = mod.get()
    masses_path = masses.get()
    eps = error.get()

    if not mod_path or not masses_path:
        output_text.insert(tk.END, "Please select both input files.\n")
        return
    else: 
        output_text.insert(tk.END, f"Files successfully loaded\nCalculating Combinations with error of {eps} daltons\n")
    # Redirect stdout to the text widget
    old_stdout = sys.stdout
    sys.stdout = StdoutRedirector(output_text)

    try:
        main(mod_path, masses_path, int(eps))
    except Exception as e:
        print(f"Error: {e}")

    # Restore original stdout
    sys.stdout = old_stdout
    run_button.config(state=tk.NORMAL)

def create_gui():
    root = tk.Tk()
    root.title("Intact Mass Analysis")
    root.geometry("600x500")
    root.configure(bg='grey')

    # Title
    title = tk.Label(root, text="Intact Mass Assignments", bg='grey', font=("Helvetica", 16, "bold"))
    title.pack(pady=10)

    # Subheader
    subheader_frame = tk.Frame(root, bg='grey')
    subheader_frame.pack(pady=5)
    subheader_text = tk.Label(subheader_frame, text="Make sure your files are in the correct format specified in the", bg='grey')
    subheader_text.pack(side=tk.LEFT)
    readme_link = tk.Label(subheader_frame, text="ReadME", fg="blue", cursor="hand2", bg="grey")
    readme_link.pack(side=tk.LEFT)
    readme_link.bind("<Button-1>", lambda e: open_readme())

    # File input section
    file_frame = tk.Frame(root, bg='grey')
    file_frame.pack(pady=20)

    tk.Label(file_frame, text="Modification File:", bg='grey').grid(row=0, column=0, padx=10, pady=10)
    file1_entry = tk.Entry(file_frame, width=50)
    file1_entry.grid(row=0, column=1, padx=10, pady=10)
    tk.Button(file_frame, text="Browse", command=lambda: select_file(file1_entry,output_text, mod=True)).grid(row=0, column=2, padx=10, pady=10)

    tk.Label(file_frame, text="Masses File:", bg='grey').grid(row=1, column=0, padx=10, pady=10)
    file2_entry = tk.Entry(file_frame, width=50)
    file2_entry.grid(row=1, column=1, padx=10, pady=10)
    tk.Button(file_frame, text="Browse", command=lambda: select_file(file2_entry,output_text)).grid(row=1, column=2, padx=10, pady=10)
    
    #Error Input
    tk.Label(file_frame, text="Error range:", bg='grey').grid(row=2, column=0, padx=10, pady=10)
    integer_spinbox = tk.Spinbox(file_frame, from_=0, to=100, width=10)
    integer_spinbox.grid(row=2, column=1, padx=10, pady=10, sticky='w')


    # Run button
    run_button = tk.Button(root, text="Run", command=lambda: run_command(file1_entry, file2_entry,integer_spinbox, run_button, output_text))
    run_button.pack(pady=20)

    # Output display
    output_text = scrolledtext.ScrolledText(root, width=70, height=15)
    output_text.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
