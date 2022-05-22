import os, re, sqlite3, time, logging, datetime, piexif

logging.basicConfig(filename="logfilename.log", level=logging.INFO)
log = logging.info

con = sqlite3.connect('updates.db')
cur = con.cursor()

TOP_FOLDER = '/Users/Joe/Downloads/lisa/'

def init_db():
    '''Init Database tables'''
    try:
        cur.execute('''
        CREATE TABLE folders (
            path TEXT PRIMARY KEY, 
            year INT
        )''')
        print("Database initilized")
    except sqlite3.OperationalError:
        print("Database already initialized")

def prep(folder,newyear):
    '''Add folder & year to folders table'''
    cur.execute("INSERT OR IGNORE INTO folders (path,year) VALUES (?,?)",(folder,newyear))

def get_year(folder):
    '''Determine year from folder name'''
    pattern = r"[1-2][0-9]{3}"
    result = re.findall(pattern, folder)
    if len(result) > 0:
        return int(result[0])
    else:
        return 0

def index(folder):
    '''List all folders'''
    root_folders = next(os.walk(folder))[1]

    year_folders = []
    for folder in root_folders:
        year = get_year(folder)
        if year > 0:
            prep(folder,year)
            year_folders.append(folder)

    print("Database updated")
    con.commit()

def update_mtime(file_path,new_ts):
    '''Update file modified date'''
    os.utime(file_path, (new_ts,)*2)
    log(f"[{file_path}] Modified date: {new_ts}")

def update_exif(file_path,exif_dict,new_exif_date):
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_exif_date
    piexif.insert(piexif.dump(exif_dict), file_path)
    log(f"[{file_path}] Updated Exif: {new_exif_date}")


def make_updates():
    '''Update files with new modified date & EXIF data'''
    folders = cur.execute("SELECT * FROM folders")
    for folder in folders:
        folder_path = TOP_FOLDER + folder[0] + '/'
        print(folder_path)

        # Prep new timestamp based on year
        new_year = int(folder[1])
        naive_dt = datetime.datetime(new_year,6,1,12,00,00)
        new_dt = naive_dt.replace(tzinfo=datetime.timezone.utc)

        new_ts = new_dt.timestamp()
        new_exif_date = time.strftime("%Y:%m:%d %H:%M:%S", new_dt.timetuple())

        dt_upper = new_dt + datetime.timedelta(days = 365)
        ts_upper = dt_upper.timestamp()
        
        files = next(os.walk(folder_path))[2]
        for filename in files:
            file_path = folder_path + filename
            print(file_path)

            mdate_file = os.stat(file_path).st_mtime
            if (mdate_file > ts_upper):
                try:
                    # Update Exif metadata (for supported images eg JPEG/WebP)
                    exif_dict = piexif.load(file_path)
                    
                    if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                        exif_date = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode()
                        exif_ts = datetime.datetime.strptime(exif_date,"%Y:%m:%d %H:%M:%S").timestamp()

                        if (exif_ts > ts_upper):
                            update_exif(file_path,exif_dict,new_exif_date)
                            update_mtime(file_path,new_ts)

                        else:
                            update_mtime(file_path,exif_ts)

                    else:
                        update_exif(file_path,exif_dict,new_exif_date)
                        update_mtime(file_path,new_ts)

                except piexif._exceptions.InvalidImageDataError:
                    log(f"[{file_path}] Unable to update Exif (not supported)")

init_db()
index(TOP_FOLDER)
make_updates()
con.close()
