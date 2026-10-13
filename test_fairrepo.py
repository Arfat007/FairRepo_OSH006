import json, subprocess, tempfile, os, re

def main():
    with tempfile.TemporaryDirectory() as d:
        binary = os.path.join(d, "fairrepo")
        compile_cmd = ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-pthread",
                       os.path.join(os.path.dirname(__file__), "fairrepo.c"), "-o", binary]
        c = subprocess.run(compile_cmd, capture_output=True, text=True)
        assert c.returncode == 0, c.stderr
        p = subprocess.run([binary, "R,R,W,R,W,R"], capture_output=True, text=True, timeout=10)
        assert p.returncode == 0, p.stderr
        data = json.loads(p.stdout)
        assert data["completed"] == 6, data
        assert data["sequence"] == "R,R,W,R,W,R", data
        events = data["events"]
        entered = [e for e in events if "entered repository" in e]
        # Admission order must preserve FIFO order.
        labels = [re.match(r"([RW]\d+)", e).group(1) for e in entered]
        assert labels == ["R1", "R2", "W3", "R4", "W5", "R6"], labels
        print("PASS: compiles, completes all requests, and preserves FIFO admission.")
        print("Max wait:", data["max_wait_ms"], "ms | Average wait:", data["average_wait_ms"], "ms")

if __name__ == "__main__":
    main()
