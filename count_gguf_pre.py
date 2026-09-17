import sys
path = sys.argv[1]
print("phi-3=%d gpt-2=%d" % (
    sum(ch.count(b"phi-3") for ch in open(path, "rb").read().split(b"")) if False else open(path, "rb").read().count(b"phi-3"),
    open(path, "rb").read().count(b"gpt-2")))
