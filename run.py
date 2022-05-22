import os, re, sqlite3, time, logging, argparse, datetime, piexif

logging.basicConfig(filename="logfilename.log", level=logging.INFO)
log = logging.info

con = sqlite3.connect('updates.db')
cur = con.cursor()

TOP_FOLDER = '/Users/Joe/Downloads/lisa/'

def init_db():
    try:
        '''Init Database tables'''
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
    cur.execute("INSERT INTO folders (path,year) VALUES (?,?)",(folder,newyear))

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

        todo = '''for subfolder in year_folders
            if has_year(subfolder)
                new_year = subfolder_year
                prep(subfolder,new_year)'''

    print("Database updated")
    
    con.commit()
    con.close()

def make_updates():
    '''Update files with new modified date & EXIF data'''
    folders = cur.execute("SELECT * FROM folders")
    for folder in folders:
        folder_path = TOP_FOLDER + folder[0] + '/'
        print(folder_path)

        files = next(os.walk(folder_path))[2]
        for filename in files:
            file_path = folder_path + filename
            print(file_path)

            # Prep new dateime based on year
            new_year = int(folder[1])
            naive_dt = datetime.datetime(new_year, 1, 1,12,11,11)
            new_dt = naive_dt.replace(tzinfo=datetime.timezone.utc)
            new_ts = new_dt.timestamp()

            # Update modified date (for all files/media, inc videos)
            os.utime(file_path, (new_ts,)*2)
            log(f"{file_path} Modified date: {new_ts}")

            try:
                # Update Exif metadata (for supported images eg JPEG/WebP)
                exif_dict = piexif.load(file_path)
                exif_date = time.strftime("%Y:%m:%d %H:%M:%S", new_dt)
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
                piexif.insert(piexif.dump(exif_dict), file_path)

            except TypeError: #update error type
                log(f"[{file_path}] Couldn't update EXIF")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Photo year updater')
    parser.add_argument('--index', action='store_true', help='Prep updates in db')
    parser.add_argument('--write', action='store_true', help='Write updates to files')
    args = parser.parse_args()

    if args.index:
        init_db()
        index(TOP_FOLDER)
        
    if args.write:
        make_updates()
