# Warsaw model

## Project contains and describes programs and resources used in building a model of part of the city of Warsaw

This project serves as a test and an example of using modern 3D LiDAR data recorder - Mandeye (https://github.com/JanuszBedkowski/mandeye_controller/tree/main) with its documentation available at https://github.com/JanuszBedkowski/mandeye_controller/tree/main/doc/manual/manual_v0_2. Project involved a few tasks:
- planning scans of parts of Warsaw and their execution using Mandeye scanner
- extracting telemetry data from the GoPro MAX camera
- extracting equirectangular images along with their coordinates from the GoPro MAX camera

### Repository contents

Contents of the repository are as follows:
- **Warsaw_scanning_updates** - it is the core file of the project, as it serves as a report of the whole scanning process. It contains project file structure, telemetry files atttribute description, maps of all scanning routes, scans schedule and descriptions of all of the scans. Should you need any information about Warsaw scanning process this is the file you should be looking for.
- **Manuals** - it contains full manuals describing how to prepare, install and use GoPro telemetry extractor and GoPro MAX video parser as well as providing some hints about GoPro MAX usage.
- **GoPro telemetry extractor** - JavaScript console program based on [JuanIrache gopro-telemetry](https://github.com/JuanIrache/gopro-telemetry/tree/9c44de1e7e7fe0fd6bc0da211b5c2bae65d19924) which parser telemetry data extracted by his [gpmf-extract](https://github.com/JuanIrache/gpmf-extract/tree/a0bdd225f64c4ecda53bc0797f586ffe8b53e039) module. The application requires GoPro video file to parse and produce csv spreadsheet containing video telemetry data registrated by a camera. Full manual describing how to use the program available in the [Manuals section](https://github.com/miloszwojciechowski/Warsaw-model/tree/v1.0/Manuals/Telemetry_extractor)
- **GoPro MAX video parser** - python window application basicly responsible for extracting equirectangular frames from GoPro MAX videos. It uses external multimedia framework - [FFMPEG](https://ffmpeg.org) - to extract frames using either seconds or frame number interval. The program may integrate the functionality of Telemetry extractor thus giving as an output video telemetry data, extracted frames, spreadshit containing frames GPS data and map visualization of traveled route. Full manual describing all options of program usage available in the [Manuals section](https://github.com/miloszwojciechowski/Warsaw-model/tree/v1.0/Manuals/GoPro_MAX_video_parser).
![](https://github.com/miloszwojciechowski/Warsaw-model/blob/v1.0/Manuals/GoPro_MAX_video_parser/images/window1.png)

- **HEVC_video_extension** - a plugin required to run GoPro Player application on Windows. The application is necessary to parse GoPro MAX video files and in turn receive equirectangular videos. To do so follow these steps:<br />


![](https://github.com/miloszwojciechowski/Warsaw-model/blob/main/Manuals/GoPro-app-images/1.png)
Open .360 file in the GoPro application, then in the left upper corner open File.

![](https://github.com/miloszwojciechowski/Warsaw-model/blob/main/Manuals/GoPro-app-images/2.png)
Choose Export as -> 5.6K for the highest resolution.

![](https://github.com/miloszwojciechowski/Warsaw-model/blob/main/Manuals/GoPro-app-images/3.png) <br />
Choose options for exported video (recommended are sufficient except for World Lock which I recommend turning off), then choose where an equirectangular file should be saved and confirm.
