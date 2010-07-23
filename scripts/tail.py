import sys

def tail_f(file):
  interval = 1.0

  while True:
    where = file.tell()
    line = file.readline()
    if not line:
      time.sleep(interval)
      file.seek(where)
    else:
      yield line

def tail(fn, window=20 ):
    f = open(fn)
    try:
        f.seek( 0, 2 )
        bytes= f.tell()
        size= window
        block= -1
        while size > 0 and bytes+block*1024  > 0:
            f.seek( block*1024, 2 ) # from the end!
            data= f.read( 1024 )
            linesFound= data.count('\n')
            size -= linesFound
            block -= 1
        f.seek( block*1024, 2 )
        f.readline() # find a newline
        lastBlocks= list( f.readlines() )
        lastBlocks = lastBlocks[-window:]
    except:
        f.close()
        f = open(fn)
        lastBlocks = f.readlines()
        lastBlocks = lastBlocks[-window:]
    f.close()
    return lastBlocks


if __name__ == "__main__":
    i = 0
    count = int(sys.argv[2])

    ln = tail(sys.argv[1], count)

    print "".join(ln)