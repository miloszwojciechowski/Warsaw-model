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
# running = True
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
    httpd.daemon_threads = True
    httpd.serve_forever()

# Function to get file name with path without extension
def stripExtension(path):
  return os.path.splitext(path)[0]

# Function to extract frames from a video file:
## window - required to display processing on app's window
## vidFile - path to video file
## dir - path to frames save directory
## intervalSeconds - bool variable defining whether the step between frames is measured in seconds (True) or frames (False)
## interval - retrieved from user inpput, step for extracting frames
def framesExtract(vidFile, dir, intervalSeconds, interval):
  if intervalSeconds:
    command = f'ffmpeg -y -i {vidFile} -vf \"select=bitor(gte(t-prev_selected_t\\,{interval})\\,isnan(prev_selected_t))\" -fps_mode vfr {dir}/frame%d.jpg'
  else:
    command = f'ffmpeg -y -i {vidFile} -vf \"select=not(mod(n\\,{interval}))\" -q:v 1 -qmin 1 -fps_mode vfr {dir}/frame%d.jpg'

  os.system(f"start /wait cmd /c {command}")

# Function that runs extractor.js program:
## vidFile - path to video file
## extractorDir - extractor.js from gopro telemetry extractor directory
def telemetryExtract(vidFile, extractorDir):
  vidFile = vidFile[:-3]+'LRV'

  completed_process = subprocess.run(['node', extractorDir] + [vidFile] + [os.path.dirname(vidFile)], capture_output=True, text=True)
  if completed_process.stderr:
    messagebox.showwarning(title='WARNING', message='Couldn\'t extract telemetry data.')

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

# Main function that creates the map and gives location to frames:
# videoFile - file containing a video
# framesDir - folder directory to save frames
# intervalSeconds - variable to recognize if program is run using number of frames as measurement between extracted, True is for seconds, False is for frames
# frameStep - frames or seconds between extracted frames
# timeLapseInterval - variable to tell if program is working on normal video or on timeLapse, default value is normal video
def visualization(videoFile, framesDir, intervalSeconds, frameStep, timeLapseInterval=1):
  PORT = 7777
  server_thread = threading.Thread(target=start_server, args=(PORT, framesDir))
  server_thread.daemon = True  # Thread will end as soon as we close the program
  server_thread.start()

  # Create pandas dataframe from telemetry file
  csv = stripExtension(videoFile) + '_telemetry.csv'
  telemetry = pd.read_csv(csv)

  # Format date
  telemetry['date'] = pd.to_datetime(telemetry['date']).dt.strftime('%d-%m-%Y %H:%m:%S %Z')

  # Add column for video frames files
  telemetry['images'] = ''

  # Create a list of frames' paths
  videoFramesFilePaths = natsorted([join(framesDir, f) for f in listdir(framesDir) if isfile(join(framesDir, f))])
  videoFrames = natsorted([join(f'http://localhost:{PORT}', f) for f in listdir(framesDir) if isfile(join(framesDir, f))])

  # Get time period between extracted frames (in milliseconds since that's the unit of timestamp in GoPro camera)
  if timeLapseInterval == 1:
    if intervalSeconds:
      tmPeriod = frameStep * 1000 #multiplied by 1000 to receive milliseconds
    else:
      fps = getFPS(videoFile)
      tmPeriod = (frameStep/fps) * 1000 #multiplied by 1000 to receive milliseconds
  else:
    tmPeriod = timeLapseInterval * frameStep * 1000

  frameRows = [] # list to keep row numbers of those that have frame path
  millisecond = 0

  # First loop is to export frames file paths to csv, second is to replace them with local server ones and project to map
  for i in range(len(videoFrames)):
    closestPointRow = (telemetry['timestamp'] - millisecond).abs().idxmin() # each iteration find the closest point to each frame
                                                                         # by comparing timestamp and time of frame
    telemetry.at[closestPointRow, 'images'] = videoFramesFilePaths[i] # add frame path to column 'images' for chosen row

    frameRows.append(closestPointRow) # add row index of row that has image path
    millisecond += tmPeriod # increase by period between each frame

  telemetry.to_csv(f'{stripExtension(videoFile)}_GPS_{frameStep}.csv')

  # Replace file path for the local server ones
  imageCounter = 0

  for i in range(len(telemetry)):
    if len(telemetry.iloc[i, -1]) != 0:
      telemetry.iloc[i, -1] = videoFrames[imageCounter]
      imageCounter += 1

  # Tuple with x, y coordinates
  points = tuple(zip(telemetry["latitude"].values, telemetry["longitude"].values))

  # Define map and add layers
  mymap = folium.Map(location=[telemetry.latitude.mean(), telemetry.longitude.mean()], zoom_start=13, max_zoom = 19, tiles=None )
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

  open_map(f'map_{stripExtension(os.path.basename(videoFile))}.html', mymap)