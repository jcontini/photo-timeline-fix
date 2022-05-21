import os, re, sqlite3, time, logging, argparse, datetime, piexif

logging.basicConfig(filename="logfilename.log", level=logging.INFO)
log = logging.info

con = sqlite3.connect('updates.db')
cur = con.cursor()

TOP_FOLDER = '/Users/Joe/Downloads/lisa'

def init_db():
    '''Init Database tables'''
    cur.execute('''
    CREATE TABLE folders (
        path TEXT PRIMARY KEY, 
        year INT
    )''')
    con.close()

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

def make_updates():
    '''Update files with new modified date & EXIF data'''
    folders = cur.execute("SELECT * FROM folders")
    for folder in folders:
        print(folder[0])

        for file in folder:
            # Prep new dateime based on year
            new_year = int(folder[1])
            print(new_year)
            new_dt = datetime.datetime(new_year, 1, 1)

            # Update modified date (for all files/media, inc videos)
            ## TODO change to integer
            os.utime(file, (new_dt,)*2)
            log("[%s] Modified date: %s" % (file, new_dt))

            try:
                # Update Exif metadata (for supported images)
                exif_dict = piexif.load(file)
                if piexif.ExifIFD.DateTimeOriginal not in exif_dict['Exif']:
                    exif_date = time.strftime("%Y:%m:%d %H:%M:%S", time.localtime(new_dt))
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
                    piexif.insert(piexif.dump(exif_dict), file)

            except:
                log("[%s] Couldn't update EXIF" % file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Photo year updater')
    parser.add_argument('--init', action='store_true', help='Initialize DB')
    parser.add_argument('--index', action='store_true', help='Prep updates in db')
    parser.add_argument('--write', action='store_true', help='Write updates to files')
    args = parser.parse_args()

    if args.init:
        init_db()

    if args.index:
        index(TOP_FOLDER)
        con.commit()
        con.close()

    if args.write:
        make_updates()