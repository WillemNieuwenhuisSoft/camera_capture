# Camera Capture

A Python application to periodically capture images from a set of webcams of the `Aero Club of east Africa`: Kenya webcams (https://webcams.aeroclubea.com/index.html), saving them in a structured folder hierarchy. The configuration is managed via a simple CLI and a config file in your user profile.

---

## Requirements

- Python 3.7+
- Depends on: `requests`, `pandas`, `beautifulsoup4`

## Installing

```
pip install camera-capture
```

> [!CAUTION]
>
> When installing on Windows, preferable make sure Python is installed from https://python.org.
>
> If however, Python is installed from the Microsoft Store, `pip install camera-capture` will properly install, but not fully adjust the `Path` environment variable.
> The installation issues a warning. Consider adding the mentioned directory to `PATH`.

---

## How to use the app

The app provides several commands and subcommands:

### Main Commands

- **run**  
  Capture images from all cameras once.

  ```
  capture run
  ```

  Or, as fallback (see the caution above)

  ```
  python -m camera run
  ```

- **run-repeat**  
  Repeat capturing images at the configured interval for the current day.

  ```
  capture run-repeat
  ```

- **run-repeat-no-limit**  
  Repeat capturing images at the configured interval indefinitely.
  ```
  capture run-repeat-no-limit
  ```

### Config Subcommands

- **config list**  
  List current configuration settings.

  ```
  capture config list
  ```

- **config update <key> <value>**  
  Update a configuration setting.  
  Example: change the image save path
  ```
  capture config update image_save_path D:/CameraImages
  ```
  Example: change the capture interval to 60 minutes
  ```
  capture config update interval 60
  ```
  Example: change the start time to 07:00
  ```
  capture config update start 07:00
  ```
  Example: change the end time to 19:00
  ```
  capture config update end 19:00
  ```

---

## Configuration File

The configuration file (`camera.config`) is stored in your user profile folder (e.g., `C:\Users\<username>\camera.config`).
When the app is first started the configuration file will be created if it does not yet exist.
The config file is stored in JSON format. Below is an example file with all currently accepted keys:

```json
{
  "image_save_path": "D:/CameraImages",
  "start": "06:30",
  "end": "18:30",
  "interval": 30,
  "locations_file":"camera_locations.txt",
  "verbose":False
}
```

Currently these keys are supported:

- image_save_path: The root folder for saving all the captured images.
- start: local time to start the capture (HH:MM)
- end: local time to end the capture (HH:MM)
- interval: time in minutes between captures.
- locations_file: name of the file containing the names of camera locations and their URLs. The file is expected in the current folder.
- verbose: enable verbose output for debugging and information

You can use the CLI to update these values, or manually edit the file.

---

## How the App Works

1. **Configuration**  
   The app uses a configuration file (`camera.config`) in your user profile directory to store settings such as the root folder for saving images, capture interval, and start/end times.

2. **Camera Locations**  
   Camera URLs and location names are loaded from a user provided CSV file (default = `camera_locations.txt`). Each row should have a `url` and a `location` column. The user is free to add/remove locations at will.

3. **Image Capture**  
   For each camera, the app downloads the latest image and saves it in a folder structure:  
   `root_folder/location/YYYY/MM/DD/`
   The root_folder is read from the configuration file when starting the app.

4. **Scheduling**  
   The app can run once, repeat for the current day, or repeat indefinitely, based on your command line options. For all locations the scheduled start and end time per day are equal.

   The capture moments are equally spaced after the `start` time and will stop
   on or before the `end` time, never after.

5. **CLI Configuration**  
   You can list and update configuration settings using the CLI.

---

## Folder Structure

Images are saved in a hierarchy:

```
<image_save_path>/<location>/<year>/<month>/<day>/<location>_<timestamp>.jpg
```

The timestamp is in local time.

---

## Example Usage

- Capture all cameras once:

  ```
  capture run
  ```

- List configuration:

  ```
  capture config list
  ```

- Update interval:
  ```
  capture config update interval 60
  ```

---

## Logging

Logs are written to `camera_capture.log` in the current directory.

---

## Troubleshooting

- Use `capture config list` to check your configuration.
- Use `capture config update <key> <value>` to fix any settings.
- Ensure `camera_locations.txt` exists and has `url` and `location` columns.

Example camera_locations.txt file:

```
url,location
https://webcams.aeroclubea.com/Nairobi/nbo_wilsonE.html,Wilson Airport E
```

---
