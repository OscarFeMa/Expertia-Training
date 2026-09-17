import sys
path = sys.argv[1]
old, new = b"phi-3", b"gpt-2"
count = 0
tmp = path + ".tmp-gpt2"
with open(path, "rb") as f, open(tmp, "wb") as o:
    carry = b""
    while True:
        ch = f.read(67108864)
        eof = len(ch) == 0
        data = carry + ch
        if not eof:
            proc, carry = data[:-4], data[-4:]
        else:
            proc, carry = data, b""
        if not proc and eof:
            break
        c = proc.count(old)
        if c:
            proc = proc.replace(old, new)
            count += c
        o.write(proc)
        if eof:
            break
print("replacements: %d" % count)
