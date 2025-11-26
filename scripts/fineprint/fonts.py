import os
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

def list_fonts(font_dir):
    """Recursively list all font files in the directory."""
    font_files = []
    for root, _, files in os.walk(font_dir):
        for file in files:
            if file.lower().endswith((".ttf", ".otf")):
                font_files.append(os.path.join(root, file))
    return font_files

def show_font(font_path, sample_text="The quick brown fox jumps over the lazy dog"):
    print(f"Selected font: {font_path}")  # Print the full path to the command line
    font_prop = FontProperties(fname=font_path)
    plt.figure(figsize=(10, 2))
    plt.text(0.01, 0.5, sample_text, fontproperties=font_prop, fontsize=24)
    plt.title(os.path.basename(font_path), fontsize=10)
    plt.axis('off')
    plt.show()

def gui_font_browser(font_dir):
    import tkinter as tk
    from tkinter import ttk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    font_files = list_fonts(font_dir)
    if not font_files:
        print("No fonts found.")
        return
    root = tk.Tk()
    root.title("Font Browser")
    root.geometry("900x300")
    # Frame for filter and listbox
    frame = ttk.Frame(root)
    frame.pack(side=tk.LEFT, fill=tk.Y)
    # Filter input
    filter_var = tk.StringVar()
    filter_entry = ttk.Entry(frame, textvariable=filter_var, foreground="#228B22")  # Middle green
    filter_entry.pack(side=tk.TOP, fill=tk.X)
    filter_entry.insert(0, "Filter fonts...")
    # Listbox for font names
    listbox = tk.Listbox(frame, width=50, height=20)
    listbox.pack(side=tk.LEFT, fill=tk.Y)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    # Store filtered font files
    filtered_fonts = font_files.copy()
    def update_listbox():
        nonlocal filtered_fonts
        filter_text = filter_var.get().strip().lower()
        listbox.delete(0, tk.END)
        if filter_text == '' or filter_text == 'filter fonts...':
            filtered_fonts = font_files.copy()
        else:
            filtered_fonts = [f for f in font_files if filter_text in os.path.basename(f).lower()]
        for font_path in filtered_fonts:
            listbox.insert(tk.END, os.path.basename(font_path))
        # Select first font if available
        if filtered_fonts:
            listbox.selection_set(0)
            listbox.event_generate('<<ListboxSelect>>')
    # Matplotlib figure
    fig, ax = plt.subplots(figsize=(7, 2))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
    sample_text = "The quick brown fox jumps over the lazy dog [ěščřžýáíé]"
    def update_plot(event):
        selection = listbox.curselection()
        if not selection:
            ax.clear()
            ax.text(0.01, 0.5, "No font selected", fontsize=12, color='gray')
            ax.axis('off')
            canvas.draw()
            return
        idx = selection[0]
        if idx >= len(filtered_fonts):
            return
        font_path = filtered_fonts[idx]
        print(f"Selected font: {font_path}")  # Print the full path to the command line
        ax.clear()
        try:
            font_prop = FontProperties(fname=font_path)
            ax.text(0.01, 0.5, sample_text, fontproperties=font_prop, fontsize=24, va='center')
            ax.set_title(os.path.basename(font_path), fontsize=10)
            ax.axis('off')
        except Exception as e:
            ax.text(0.01, 0.5, f"Error rendering font:\n{e}", fontsize=12, color='red')
            ax.axis('off')
        canvas.draw()
    listbox.bind('<<ListboxSelect>>', update_plot)
    # Filter callback
    def on_filter_change(*args):
        update_listbox()
    filter_var.trace_add('write', on_filter_change)
    # Remove placeholder text on focus
    def clear_placeholder(event):
        if filter_entry.get() == 'Filter fonts...':
            filter_entry.delete(0, tk.END)
    filter_entry.bind('<FocusIn>', clear_placeholder)
    # Populate listbox initially
    update_listbox()
    root.mainloop()

def interactive_font_browser(font_dir):
    font_files = list_fonts(font_dir)
    if not font_files:
        print("No fonts found.")
        return
    while True:
        try:
            idx = input(f"Enter font index (0-{len(font_files)-1}) to preview, or 'q' to quit: ")
            if idx.lower() == 'q':
                break
            idx = int(idx)
            if 0 <= idx < len(font_files):
                show_font(font_files[idx])
            else:
                print("Invalid index.")
        except Exception as e:
            print(f"Error: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Font browser and visualizer.")
    parser.add_argument('font_dir', nargs='?', default=None, help="Directory to search for fonts.")
    parser.add_argument('--list', action='store_true', help="List fonts only.")
    parser.add_argument('--gui', action='store_true', help="Use GUI font browser.")
    args = parser.parse_args()
    if args.font_dir is None:
        print("Warning: No font directory specified. Using default: /usr/share/fonts")
        args.font_dir = "/usr/share/fonts"
    if args.list:
        for idx, font_path in enumerate(list_fonts(args.font_dir)):
            print(f"{idx}: {font_path}")
    elif args.gui:
        gui_font_browser(args.font_dir)
    else:
        interactive_font_browser(args.font_dir)

if __name__ == "__main__":
    main()
