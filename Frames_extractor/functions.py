import cv2
import folium
from folium.plugins import *
from natsort import natsorted
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import subprocess
from tkinter import messagebox
import threading
import webbrowser
import http.server
import socketserver

# Global flag to manage frames extraction loop
running = True

## Class and function to run local server on which extracted frames will be hosted,
## since many browsers no longer allow access to local files

# Define the request handler
class PhotoRequestHandler(http.server.SimpleHTTPRequestHandler):
  def __init__(self, *args, directory=None, **kwargs):
    self.directory = directory
    super().__init__(*args, directory=directory, **kwargs)

# Function to run server
def start_server(port, directory):
  with socketserver.ThreadingTCPServer(("", port), lambda *args, **kwargs: PhotoRequestHandler(*args, directory=directory,
                                                                                      **kwargs)) as httpd:
    print(f"Serving at port {port}")
    httpd.serve_forever()

# Function to stop frames extracting process
def stop():
  global running
  running = False

# Function to get file name without extension from the path
def getFilename(path):
  return os.path.splitext(os.path.basename(path))[0]

# Function to extract frames from a video file:
## window - required to display processing on app's window
## file - path to video file
## dir - path to frames save directory
## processLabel - label that is being updated on main window
## frameStep - retrieved from user inpput, step for extracting frames
def framesExtract(appWindow, vidFile, dir, processLabel, frameStep):
  global running
  running = True

  if (len(frameStep) == 0):
    messagebox.showerror(title='ERROR', message='Fill all needed data fields')
    return

  try:
    # read the video file from the path
    vidcap = cv2.VideoCapture(vidFile)

    # frame
    currentframe = 0

    while (running):
      # reading from frame
      ret, frame = vidcap.read()

      if ret:
        # if video is still left continue creating images
        # save frame
        try:
          name = dir + '/frame' + str(currentframe) + '.jpg'

          processLabel.config(text='Creating...' + name)

          # writing the extracted images
          cv2.imwrite(name, frame)

          # increasing counter so that it will
          # show how many frames are created
          currentframe += int(frameStep)  # i.e. at 30 fps, frameStep=30 advances one second
        except NameError:
          messagebox.showerror(title='ERROR', message='Fill all needed data fields')
          break

        vidcap.set(1, currentframe)
        appWindow.update()
      else:
        break

    # Release all space and windows once done
    vidcap.release()

  except NameError:
    messagebox.showerror(title='ERROR', message='Fill all needed data fields')

  cv2.destroyAllWindows()


# Function that runs extractor.js program, if it is not present in the same directory as this program, error window pops out:
## file - path to video file
def telemetryExtract(vidFile):
  if os.path.isfile('extractor.js'):
    completed_process = subprocess.run(['node', 'extractor.js'] + [vidFile], capture_output=True, text=True)
    if completed_process.stderr:
      messagebox.showwarning(title='WARNING', message='Couldn\'t extract telemetry data.')
      return False
    else:
      return True
  else:
    messagebox.showerror(title='ERROR',
                         message='extractor.js not found. \n Telemetry extraction process couldn\'t be executed.')
    return False

def getFPS(videoFile):
  videocap = cv2.VideoCapture(videoFile)

  # Find OpenCV version
  (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')

  if int(major_ver) < 3:
    fps = videocap.get(cv2.cv.CV_CAP_PROP_FPS)
  else:
    fps = videocap.get(cv2.CAP_PROP_FPS)

  return fps

#function to open map
def open_map(path, f_map):
  html_page = f'{path}'
  f_map.save(html_page)
  # open in browser.
  new = 2
  webbrowser.open(html_page, new=new)

# Definition of folium popup that displays telemetry data of the point
def coord_popup(dataframe, title, row_index):
  img_src = dataframe.iloc[row_index,5]

  table_html = f"<h3 style='text-align:center'>{title}</h3><table style='width:100%'>"
  table_html += dataframe.iloc[row_index,:5].to_frame().to_html(header=False, justify='center')
  table_html += "</table>"
  if img_src != '':
    table_html += f"<br><a href='{img_src}' target='_blank'>" \
                  f"<img src='{img_src}' width='100%' />" \
                  "</a>"

  return table_html

def visualization(videoFile,framesDir, frameStep):
  PORT = 7777
  server_thread = threading.Thread(target=start_server, args=(PORT, framesDir))
  server_thread.daemon = True  # Thread will end as soon as we close the program
  server_thread.start()

  # Create pandas dataframe from telemetry file
  csv = getFilename(videoFile) + '_telemetry.csv'

  telemetry = pd.read_csv(csv)
  # Format date
  telemetry['date'] = pd.to_datetime(telemetry['date']).dt.strftime('%d-%m-%Y %H:%m:%S %Z')

  # Add column for video frames files
  telemetry['images'] = ''

  # Create a list of frames' paths
  videoFrames = natsorted([join(f'http://localhost:{PORT}', f) for f in listdir(framesDir) if isfile(join(framesDir, f))])

  # Get time period between extracted frames (in milliseconds since that's the unit of timestamp in GoPro camera)
  fps = getFPS(videoFile)
  tmPeriod = (int(frameStep)/fps) * 1000 #multiplied by 1000 to receive milliseconds

  # Divide telemetry dataframe into fragments, to search closest point for each extracted frame
  rows_per_fragment = len(telemetry) // len(videoFrames)
  fragments = [telemetry.iloc[i:i + rows_per_fragment] for i in range(0, len(telemetry), rows_per_fragment)]

  frameRows = [] # list to keep row numbers of those that have frame path
  millisecond = 0
  for i in range(len(videoFrames)):
    fragment = fragments[i]
    closestPoint = (fragment['timestamp']-millisecond).abs().idxmin() # in each fragment find closest point to each frame
                                                                        # by comparing timestamp and time of frame
    fragment.at[closestPoint, 'images'] = videoFrames[i] # add frame path to column 'images' for chosen row
    frameRows.append(closestPoint) # add row index of row that has image path
    millisecond += tmPeriod # increase by period between each frame

  # Tuple with x, y coordinates
  points = tuple(zip(telemetry["latitude"].values, telemetry["longitude"].values))

  # Define map and add layers
  mymap = folium.Map(location=[telemetry.latitude.mean(), telemetry.longitude.mean()], zoom_start=13, max_zoom = 30, tiles=None )
  folium.TileLayer('openstreetmap', name ='OpenStreetMap').add_to(mymap)
  folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                   attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(mymap)
  folium.TileLayer('http://tile.stamen.com/terrain/{z}/{x}/{y}.jpg', attr="terrain-bcg", name='Terrain Map').add_to(mymap)
  folium.LayerControl().add_to(mymap)

  ## Add features

  #Minimap
  minimap = folium.plugins.MiniMap(width=270, height=270, zoom_level_offset=-6, toggle_display=True)
  mymap.add_child(minimap)

  # Map cursor coordinates
  folium.plugins.MousePosition(position='topright').add_to(mymap)


  ## Route - start,end,frame points and route line

  # Create route line
  folium.PolyLine(points, color='red', weight=4.5, opacity=1).add_to(mymap)

  # Create start marker and its popup
  startIFrame = folium.IFrame(html=coord_popup(telemetry, 'Start point', 0), width=400, height=410)
  startPopup = folium.Popup(startIFrame, max_width=500)
  folium.Marker(location=points[0], popup=startPopup, tooltip='Star point',
                        icon=folium.Icon(icon='circle-play', prefix='fa')).add_to(mymap)

  # Create end marker and its popup
  endIFrame = folium.IFrame(html= coord_popup(telemetry, 'End point', -1), width=300, height=220)
  endPopup = folium.Popup(endIFrame, max_width=400)
  folium.Marker(location=points[-1], popup=endPopup, tooltip='End point',
                      icon=folium.Icon(icon='flag-checkered', prefix='fa')).add_to(mymap)

  # Create points containing frames
  for i in range(1, len(videoFrames)):
    iframe = folium.IFrame(html=coord_popup(telemetry, f'Frame{i}', frameRows[i]), width=400, height=410)
    popup = folium.Popup(iframe, max_width=500)
    folium.Circle(location=points[frameRows[i]], radius=3, fill_color='#F58A1F', fill_opacity=0.8, color="black", weight=1, tooltip=f'Frame{i}',
                  popup=popup).add_to(mymap)

  open_map('map.html', mymap)