from functions import *
from tkinter import *
from tkinter import filedialog

# Open file explorer to choose video file to process
def searchFiles():
  global filename
  filename = filedialog.askopenfilename(initialdir = "/", title = "Select a File")
  labelFile.config(text="Chosen video file path: " + filename)

# Open file explorer to choose directory to save frames
def searchDirectory():
  global directory
  directory = filedialog.askdirectory(initialdir = "/", title = "Select a Directory to save your frames")
  labelDir.config(text="Chosen save directory path: " + directory)

def on_closing():
  if messagebox.askokcancel("Quit", "Do you want to quit?"):
    window.destroy()

# Main function
def run():
  framesExtract(window, filename, directory, stateLabel, entry.get())
  visualizeBool = telemetryExtract(filename)
  stateLabel.config(text='Finished')
  if visualizeBool:
    visualization(filename,directory, entry.get())

## GUI setup
window = Tk()
window.title("Frames extractor")

## Variables

#Choose the video file
button_vid = Button(window, text="Choose video file", command=searchFiles)
button_vid.grid(row=0, column=0, padx=25, pady=10)
labelFile = Label(window, text="Chosen video file path:", fg = "blue")
labelFile.grid(row = 0, column=1)

#Choose the frames save directory
button_saveFile = Button(window, text="Choose frames save directory", command=searchDirectory)
button_saveFile.grid(row=1, column=0, padx=25, pady=10)
labelDir = Label(window, text="Chosen save directory path:", fg = "blue")
labelDir.grid(row=1, column=1, padx=25)

#Choose the saved frame step
Label(window,text="Saved frame step:", font=10).grid(row=2, column=0, padx=25)

entry = Entry(window, font = 20)
entry.grid(row=2,column=1, pady=10)

## State label and buttons

#Saved frame label
stateLabel = Label(window, text="", font=10)
stateLabel.grid(row=3, columnspan=2, pady=20)

#Run the program button
startButton = Button(window, text="Start", width=10, command=run)
startButton.grid(row=4, column=1, pady=10)

#Stop button
stopButton = Button(window, text="Stop", width=10, command=stop)
stopButton.grid(row=4, column=0, pady=10)

#Credentials
Label(window, text="Created by Miłosz Wojciechowski").grid(row=5, column=1)

window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()