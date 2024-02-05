import tkinter as tk
from tkinter import filedialog
from os.path import basename, dirname

def select_and_concatenate_files():
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Open file dialog to select multiple text files
    file_paths = filedialog.askopenfilenames(filetypes=[("Text files", "*.txt")])
    
    if not file_paths:
        return  # No files were selected

    # Concatenate the contents of the files
    concatenated_content = ""
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().replace("[Musique]", "")
            file_desc = "Sujet: " + basename(file_path).split(".")[0]  # Add "Vidéo: " and exclude file extension
            concatenated_content += f"{file_desc}\n{content}\n\n"

    # Default save file name suggestion
    default_file_name = "Concatenated_" + basename(dirname(file_paths[0])) + ".txt"

    # Ask for a file name to save the concatenated content
    save_path = filedialog.asksaveasfilename(initialdir=dirname(file_paths[0]),
                                             initialfile=default_file_name,
                                             filetypes=[("Text files", "*.txt")])
    if save_path:
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(concatenated_content)

# Run the function
select_and_concatenate_files()
