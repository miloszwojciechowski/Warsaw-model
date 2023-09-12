const fs = require('fs');
const path = require('path');
const gpmfExtract = require('./gpmf-extract');
const goproTelemetry = require('./gopro-telemetry');

// Path to video file is received from the first argument of the program
const videoFilePath = process.argv[2];
const teleFileSaveLoc = process.argv[3];

// Function to extract filename from a path
function getFilename(filePath) {
	filePath = filePath.replace(/^.*[\\\/]/, '')
	filePath = filePath.replace(/\.[^/.]+$/, "")
	return filePath
}

// Function to process video and generate csv file with telemetry data
async function processVideoFile() {
  try {
    // Read a video file
    const video = fs.readFileSync(videoFilePath);

    // Get GPMF data from video file
    const gpmfData = await gpmfExtract(video);
    console.log('Length of data received:', gpmfData.rawData.length);
    console.log('Framerate of data received:', 1 / gpmfData.timing.frameDuration);

    // Get GPS data from telemetry
    const telemetryData = await goproTelemetry(gpmfData);
	const gpsStream = telemetryData['1'].streams.GPS5;

	// Read values: date, timestamp, latitude, longitude and altitude
	const dates = gpsStream.samples.map((sample) => sample.date.toISOString());
	const time = gpsStream.samples.map((sample) => sample.cts);
	const latitude = gpsStream.samples.map((sample) => sample.value[0]);
	const longitude = gpsStream.samples.map((sample) => sample.value[1]);
	const altitude = gpsStream.samples.map((sample) => sample.value[2]);
	
    // Prepare data
	const csvData = time.map((t, index) => [dates[index], t, latitude[index], longitude[index], altitude[index]]);
	const csvRows = csvData.map((row) => row.join(','));

	// Generate CSV contents
	const csvContent = 'date,timestamp,latitude,longitude,altitude\n' + csvRows.join('\n');

	// Save data to CSV file named after video name
	if (teleFileSaveLoc){
		var csvFilePath = path.join(teleFileSaveLoc, getFilename(videoFilePath) + '_telemetry.csv');
	}
	else{
		var csvFilePath = path.join(__dirname, getFilename(videoFilePath) + '_telemetry.csv');
	}
	fs.writeFileSync(csvFilePath, csvContent);
	console.log('Telemetry exported to CSV:', csvFilePath);

  } catch (error) {
    console.error('Error:', error);
  }
}

// Run the main function
processVideoFile();
