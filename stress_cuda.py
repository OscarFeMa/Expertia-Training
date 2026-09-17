import time, torch
print("cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0))
a = torch.randn(8192, 8192, device="cuda", dtype=torch.float16)
b = torch.randn(8192, 8192, device="cuda", dtype=torch.float16)
print("alloc GB:", torch.cuda.memory_allocated() / 1e9)
t0 = time.time()
i = 0
while time.time() - t0 < 300:
    c = (a @ b).relu()
    torch.cuda.synchronize()
    i += 1
    if i % 50 == 0:
        print("iter %d t=%.0fs" % (i, time.time() - t0), flush=True)
print("SURVIVED 300s, iters=%d" % i)
