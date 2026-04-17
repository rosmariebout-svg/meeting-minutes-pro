import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import openai
import sounddevice as sd
import soundfile as sf
import tempfile
import threading
import numpy as np
import queue
import pyperclip
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

openai.api_key = ""

recording = False
audio_queue = queue.Queue()
frames = []

def set_api_key():
    openai.api_key = api_entry.get()
    status_label.config(text="API Key Set ✅")

def start_recording():
    global recording, frames
    frames = []
    recording = True
    status_label.config(text="Recording... 🎤")

    def callback(indata, frames_count, time, status):
        if recording:
            audio_queue.put(indata.copy())

    def record():
        with sd.InputStream(samplerate=44100, channels=1, callback=callback):
            while recording:
                while not audio_queue.empty():
                    frames.append(audio_queue.get())

    threading.Thread(target=record).start()

def stop_recording():
    global recording
    recording = False
    status_label.config(text="Processing audio... ⏳")

    audio_data = np.concatenate(frames, axis=0)

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    sf.write(file.name, audio_data, 44100)

    process_audio(file.name)

def upload_audio():
    file_path = filedialog.askopenfilename()
    if file_path:
        process_audio(file_path)

def process_audio(file_path):
    output.delete("1.0", tk.END)
    output.insert(tk.END, "Transcribing...\n")

    def run():
        try:
            with open(file_path, "rb") as audio:
                transcript = openai.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=audio
                )

            text = transcript.text

            output.delete("1.0", tk.END)
            output.insert(tk.END, "Generating meeting minutes...\n")

            summary = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Create professional meeting minutes with:

Meeting Title
Date
Attendees
Key Discussion Points
Decisions Made
Action Items

Keep it clean, structured, and concise."""
                    },
                    {"role": "user", "content": text}
                ]
            )

            result = summary.choices[0].message.content

            output.delete("1.0", tk.END)
            output.insert(tk.END, result)

            status_label.config(text="Done ✅")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="Error ❌")

    threading.Thread(target=run).start()

def save_txt():
    content = output.get("1.0", tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        with open(file_path, "w") as f:
            f.write(content)
        status_label.config(text="Saved TXT ✅")

def export_pdf():
    content = output.get("1.0", tk.END)
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf")

    if file_path:
        c = canvas.Canvas(file_path)
        y = 800
        for line in content.split("\n"):
            c.drawString(40, y, line[:90])
            y -= 15
            if y < 40:
                c.showPage()
                y = 800
        c.save()
        status_label.config(text="PDF Exported ✅")

def copy_text():
    pyperclip.copy(output.get("1.0", tk.END))
    status_label.config(text="Copied 📋")

root = tk.Tk()
root.title("Meeting Minutes Pro")
root.geometry("800x650")

tk.Label(root, text="Meeting Minutes Pro", font=("Arial", 18, "bold")).pack(pady=10)

api_frame = tk.Frame(root)
api_frame.pack()

tk.Label(api_frame, text="API Key:").pack(side=tk.LEFT)
api_entry = tk.Entry(api_frame, width=55)
api_entry.pack(side=tk.LEFT)
tk.Button(api_frame, text="Set", command=set_api_key).pack(side=tk.LEFT)

controls = tk.Frame(root)
controls.pack(pady=10)

tk.Button(controls, text="Start Recording 🎤", command=start_recording).grid(row=0, column=0, padx=5)
tk.Button(controls, text="Stop Recording ⏹", command=stop_recording).grid(row=0, column=1, padx=5)
tk.Button(controls, text="Upload Audio 📁", command=upload_audio).grid(row=0, column=2, padx=5)

output = scrolledtext.ScrolledText(root, width=95, height=28)
output.pack(pady=10)

actions = tk.Frame(root)
actions.pack()

tk.Button(actions, text="Save TXT 💾", command=save_txt).grid(row=0, column=0, padx=5)
tk.Button(actions, text="Export PDF 📄", command=export_pdf).grid(row=0, column=1, padx=5)
tk.Button(actions, text="Copy 📋", command=copy_text).grid(row=0, column=2, padx=5)

status_label = tk.Label(root, text="Ready", fg="green")
status_label.pack(pady=5)

root.mainloop()
