# rm ~/gitlogs.txt; for f in ~/CartridgeOCR ~/t4t-annotation-UI/ ~/CartridgeOCR/src/t4t-annotation-UI/; do cd $f; git log  --reverse --all --date=format:'%Y-%m-%d %H:%M:%S' >> ~/gitlogs.txt; done; cd ~
from time import strptime, mktime
timestamps = {}

with open('/home/simra/gitlogs.txt', 'r') as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith('commit'):
            commit = l.split(' ')[-1].strip()
        elif l.startswith('Author'):
            author = l.split('Author:')[1].strip()
        elif l.startswith('Date'):
            date = l.split('Date:')[1].strip()                   
            #print(f"{author}\t{date}\t{commit}")
            date = strptime(date, '%Y-%m-%d %H') #:%M:%S')
            if date.tm_year<2022 or date.tm_year==2022 and date.tm_mon<7:
                continue
            if author not in timestamps:
                timestamps[author] = set()
            timestamps[author].add(date)

for a in timestamps:
    print(f"{a}|{len(timestamps[a])}")

exit()
for a in timestamps:
    timestamps[a].sort()
    # drop timestamps within 1 hour of each other
    for i in range(len(timestamps[a])-1, 0, -1):
        if mktime(timestamps[a][i]) - mktime(timestamps[a][i-1]) < 3600:
            timestamps[a].pop(i)
    print(f"{a}|{len(timestamps[a])}") 