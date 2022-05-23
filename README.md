# Why

Media timeline apps (iPhoto, Google Photos, Synology Photos, etc) sort photo/videos by date of
1. Photo Exif DateTimeOriginal metadata (if available - eg JPEG, WebP)
1. File modified date (all file types, inc videos)

My mom scanned a bunch of physical photographs/negatives going back decades, and organized most of them into folder names with a year. I wanted to be able to browse these photos in a timeline view.

However, since photos from 1950 were scanned in 2020, both the Exif & file date data showed 2020. This makes the 1950's photos show up for 2020.

# What it does
This script accepts a folder path, and then:
- Look for all subfolders (1 level) with a year anywhere in the name (eg `1950 *`,`*1950*`)
- Associate each of those folders with the 1st year in the name
- For each subfolder (eg 1950), determine an `upper date` of Dec 30, Year+1 (eg Dec 30, 1951)
  - Determine a `new date` of Dec 30 of the folder year (eg Dec 30,1950)
  - Find files where `modified date` > `upper date` (eg Dec 1950 - Dec 1951)
    - If that file has Exif DateTimeOriginal metadata (`exif date`)
      - If `exif date` > `upper date` 
        - Update Exif & file modified date to the `new date`
      - Else (if date is not sketchy)
        - Update the file modified date to the `exif date` (to help preserve it)
    - Else (if it doesn't have Exif date)
      - Update Exif & file modified date to the `new date`

The result should be: 
- Your media (photos/videos etc) in the folders with years should now show up properly in your timeline app.
- Updated files will have timestamps of Dec 30, (folder year) at 12:00 UTC+0

# How to use it

First: *Make a backup!!* The script overwrites metadata in each of the affected files.

Clone the repo, cd into it, then run
1. `pipenv shell`
2. `python run.py {top_folder_path}

It'll run through subfolders & files and make changes per above.
Changes are logged in repo folder as `log.log`

You may need to have the app re-index the folder/library so it can refresh the timeline.