import gzip
import os

def hamming(a, b):
    if len(a) != len(b):
        return 100000
    return sum([a[x] != b[x] for x in range(len(a))])

def correct_barcodes(barcodes, whitelist):
    # uniquify and remove spurious entries
    whitelist = list(set([x for x in whitelist if not 'N' in x]))
    corrected = dict.fromkeys(barcodes)
    for bc in corrected.keys():
        if corrected[bc] is None:
            # avoid recompute
            H = [hamming(bc, x) for x in whitelist]
            m = min(H)
            if m < 2:
                corrected[bc] = [wl[x] for x in range(len(whitelist)) if H[x] == m][0]
            else:
                # no bc in whitelist, keep this
                corrected[bc] = bc
    return [corrected[bc] for bc in barcodes]

def addbarcodes(cb_position, fq1, fq2, fq3=None, prefix="", suffix="", wl=None):
    """Add cell barcode to read names

    Parameters
    ----------
    cb_position : int
        Base positions containing cell barcode information
    fq1 : str
        Fastq file containing cell barcode sequences
    fq2 : str
        Fastq file to add cell barcodes to
    fq3 : str
        Fastq file to add cell barcodes to (optional)
    prefix : str
        Prefix to append to cell barcodes
    suffix : str
        Suffix to append to cell barcodes
    """
    barcodes, whitelist = get_barcodes(f=fq1, bases=cb_position, prefix=prefix, suffix=suffix, wl=None)
    if len(whitelist) > 0:
        barcodes = correct_barcodes(barcodes, whitelist)
    add_barcodes(f=fq2, cb=barcodes)
    if fq3 is not None:
        add_barcodes(f=fq3, cb=barcodes)


def get_barcodes(f, bases=12, prefix="", suffix="", wl=None):
    f_open = open_fastq(f)
    whitelist = []
    if f.endswith(".gz"):
        gz = True
    else:
        gz = False
    x = 0
    cb = []
    for i in f_open:
        if (x % 4 == 1):
            if gz:
                cb.append(prefix + i.decode("utf-8")[:bases] + suffix)
            else:
                cb.append(prefix + i[:bases] + suffix)
        x += 1
    f_open.close()
    if wl is not None:
        for line in open(wl):
            fields = line.split()
            whitelist.append(fields[0])
    return(cb, whitelist)

def add_barcodes(f, cb):
    f_open = open_fastq(f)
    if f.endswith(".gz"):
        gz = True
        o = f.replace(".fastq.gz", "").replace(".fq.gz", "") + ".barcoded.fastq.gz"
        outfile = gzip.GzipFile(o, mode = "wb")
    else:
        gz = False
        o = f.replace(".fastq", "").replace(".fq", "") + ".barcoded.fastq"
        outfile = open(o, "w+")
    x = 0
    y = 0
    for i in f_open:
        if (x % 4 ==0):
            if gz:
                rdname = i.decode("utf-8")
            else:
                rdname = i
            rdname = "@" + cb[y] + ":" + rdname[1:]
            if gz:
                outfile.write(rdname.encode("utf-8"))
            else:
                outfile.write(rdname)
            y += 1
        else:
            outfile.write(i)
        x += 1
    f_open.close()
    outfile.close()


def open_fastq(f):
    if os.path.isfile(f):
        if f.endswith(".gz"):
            f_open = gzip.open(f, "rb")
        else:
            f_open = open(f, "r")
        return(f_open)
    else:
        raise Exception("File not found")
