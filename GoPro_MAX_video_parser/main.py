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

# Open file explorer to find exctractor.js file
def findExtractor():
  global extractor
  extractor = filedialog.askopenfilename(initialdir = "/", title = "Provide extractor.js file")
  labelExtractor.config(text="Extractor.js location:" + extractor)

def on_closing():
  if messagebox.askokcancel("Quit", "Do you want to quit?"):
    window.destroy()
    exit()

# Main function activated by pushing Start button
lock = threading.Lock()
def run():
  if (len(entry.get()) == 0 or 'filename' not in globals() or 'directory' not in globals()):
    messagebox.showerror(title='ERROR', message='Fill all needed data fields')
    return

  # By default visualization is off
  visualizeBool = False

  if 'extractor' not in globals():
    if messagebox.askokcancel("Run without telemetry extractor", "Do you want to run the program without extraction telemetry and thus without visualization?"):
      pass
    else:
      return
  else:
    telemetryExtract(filename, extractor)
    visualizeBool = True # Turn on visualization if extractor.js is detected

# Function to run extracting frames as separate thread
  def run_ffmpeg():
    stateLabel.config(text='Extracting frames.')

    framesExtract(filename, directory, stepVar.get(), int(entry.get()))
    stateLabel.config(text='Frames extracted')
    lock.release()

# Run a thread for frames extracting using ffmpeg script
  t = threading.Thread(target=run_ffmpeg)
  t.daemon = True
  t.start()

# Following code runs only when extractor.js is provided
  if visualizeBool:
    lock.acquire()

# Function to call for visualization as separate thread
    def run_visualization():
      # Wait for unlocking lock after run_ffmpeg ends
      lock.acquire()
      visualization(filename, directory, stepVar.get(), int(entry.get()))
      stateLabel.config(text='Map generated')
      lock.release()

    # Run visualization in separate thread
    visThread = threading.Thread(target=run_visualization)
    visThread.daemon = True
    visThread.start()

## GUI setup
window = Tk()
window.resizable(width=False, height=False)
window.title("GoPro MAX video parser")

## Variables
stepVar = BooleanVar(window, True) #Defines whether the step between frames is in seconds or in frames

#Choose the video file
button_vid = Button(window, text="Choose video file", command=searchFiles)
button_vid.grid(row=0, column=0, padx=25, pady=10)
labelFile = Label(window, text="Chosen video file path:", fg = "blue")
labelFile.grid(row=0, column=1, columnspan=2, sticky=W)

#Choose the frames save directory
button_saveFile = Button(window, text="Choose frames save directory", command=searchDirectory)
button_saveFile.grid(row=1, column=0, padx=25, pady=10)
labelDir = Label(window, text="Chosen save directory path:", fg = "blue")
labelDir.grid(row=1, column=1, columnspan=2, sticky=W)

#Choose the step between frames - in seconds or in frames
secRbutton = Radiobutton(window, text="Seconds", variable=stepVar, value=True)
secRbutton.grid(row=2, column=1, sticky=W)

frameRButton = Radiobutton(window, text="Frames", variable=stepVar, value=False)
frameRButton.grid(row=3, column=1, sticky=W)

Label(window, text="Saved frame step:", font=10).grid(row=2, column=0, rowspan=2, padx=25)

entry = Entry(window, font = 20)
entry.grid(row=2,column=2, rowspan=2, padx=10, sticky=W)

#Choose extractor.js location
button_extractor = Button(window, text="Pass the extractor.js localization", command=findExtractor)
button_extractor.grid(row=4, column=0, padx=25, pady=10)
labelExtractor = Label(window,text="Extractor.js location:", fg = "blue")
labelExtractor.grid(row=4, column=1, columnspan=2, sticky=W)

## State label and buttons

#Process state label
stateLabel = Label(window, text="", font=10)
stateLabel.grid(row=5, columnspan=3, pady=20)

#Run the program button
startButton = Button(window, text="Start", width=10, command=run)
startButton.grid(row=6, column=0, columnspan=3, pady=10)

#Credentials
Label(window, text="Created by Miłosz Wojciechowski").grid(row=7, column=2)

window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()