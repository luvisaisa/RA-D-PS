# GUI Rendering Pattern - Critical for tkinter

## The Golden Rule

**ALWAYS render the window BEFORE adding dynamic content**

```python
# ❌ WRONG - Text won't show
progress_window = tk.Toplevel()
progress_text = tk.Text(progress_window)
progress_text.pack()
progress_text.insert(tk.END, "Hello")  # ← Window not rendered yet!

# ✅ CORRECT - Text will show
progress_window = tk.Toplevel()
progress_text = tk.Text(progress_window)
progress_text.pack()

# Force rendering BEFORE adding content
progress_window.update_idletasks()  # Calculate sizes
progress_window.update()            # Force display

# NOW add content
progress_text.insert(tk.END, "Hello")
progress_text.update()  # Force text to display
```

## Why This Matters

tkinter uses an event loop that:
1. Queues widget creation commands
2. Batches rendering for performance
3. Only displays when explicitly told or when idle

If you add text before the window renders:
- The text IS added to the widget's internal state
- But the widget hasn't been drawn on screen yet
- So you see an empty/blank widget

## The Fix Pattern

```python
def create_progress_dialog(self):
    # 1. CREATE window and widgets
    dialog = tk.Toplevel(self.master)
    dialog.title("Processing...")
    
    text_widget = tk.Text(dialog)
    text_widget.pack()
    
    # 2. RENDER the window (critical!)
    dialog.update_idletasks()  # Calculate geometry
    dialog.update()             # Force display NOW
    
    # 3. NOW add dynamic content
    def log(msg):
        text_widget.insert(tk.END, f"{msg}\n")
        text_widget.see(tk.END)
        text_widget.update()  # Force each message to show
        dialog.update()
    
    # This will now be visible!
    log("Starting process...")
    log("Loading files...")
```

## Common Mistakes

### Mistake 1: No update before content
```python
# Widget created but not rendered
listbox = tk.Listbox(frame)
listbox.pack()
listbox.insert(tk.END, "Item 1")  # ← Won't show immediately!
```

**Fix:**
```python
listbox = tk.Listbox(frame)
listbox.pack()
listbox.update_idletasks()  # ← Force render
listbox.insert(tk.END, "Item 1")
listbox.update()
```

### Mistake 2: Forgetting to update after each change
```python
for i in range(100):
    progress_text.insert(tk.END, f"Processing {i}\n")
    # ← User sees nothing until loop ends!
```

**Fix:**
```python
for i in range(100):
    progress_text.insert(tk.END, f"Processing {i}\n")
    progress_text.see(tk.END)
    progress_text.update()  # ← Force display each iteration
    window.update()
```

### Mistake 3: Dialog appears blank
```python
def show_dialog():
    dlg = tk.Toplevel()
    text = tk.Text(dlg)
    text.pack()
    # Dialog shows but is blank!
    process_files()  # Long operation
```

**Fix:**
```python
def show_dialog():
    dlg = tk.Toplevel()
    text = tk.Text(dlg)
    text.pack()
    
    dlg.update_idletasks()  # ← Render FIRST
    dlg.update()
    
    process_files()  # Now user sees the dialog
```

## Our Fixes Applied

### Fix 1: Progress Dialog (lines 880-900 in gui.py)
```python
# Progress text area
text_frame = tk.Frame(progress_window, bg="#d7e3fc")
text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

progress_text = tk.Text(text_frame, bg="#f8f9fa", font=("Courier", 10), wrap=tk.WORD)
scrollbar = tk.Scrollbar(text_frame, command=progress_text.yview)
progress_text.config(yscrollcommand=scrollbar.set)
progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# ✅ CRITICAL: Force render BEFORE processing
progress_window.update_idletasks()
progress_window.update()

def log_message(msg):
    progress_text.insert(tk.END, f"{msg}\n")
    progress_text.see(tk.END)
    progress_text.update_idletasks()  # ✅ Force text to show
    progress_window.update()
```

### Fix 2: Main GUI Listbox (line 1478 in gui.py)
```python
for i, path in enumerate(self.files):
    basename = os.path.basename(path)
    self.listbox.insert(tk.END, basename)

# ✅ Force listbox to refresh and show new items
self.listbox.update_idletasks()
self.listbox.update()
```

## Performance Note

Calling `update()` frequently can slow down the UI, especially in tight loops. For better performance:

```python
# ❌ Too many updates
for i in range(10000):
    listbox.insert(tk.END, f"Item {i}")
    listbox.update()  # Called 10,000 times!

# ✅ Batch updates
for i in range(10000):
    listbox.insert(tk.END, f"Item {i}")
    if i % 100 == 0:  # Update every 100 items
        listbox.update()
```

## Summary

**ALWAYS follow this pattern:**
1. Create widgets
2. Pack/grid widgets
3. Call `update_idletasks()` and `update()`
4. THEN add dynamic content
5. Call `update()` after each content change that should be visible

**Remember:** "Render window BEFORE adding text" - this is the golden rule!
