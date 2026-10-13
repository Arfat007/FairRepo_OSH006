from flask import Flask, jsonify, render_template, request
import json
import os
import subprocess

app = Flask(__name__)
ROOT = os.path.dirname(os.path.abspath(__file__))
BINARY = os.path.join(ROOT, "fairrepo")

DEFAULT_SEQUENCE = ["R", "R", "W", "R", "W", "R"]

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "engine": "C + POSIX threads"})

@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    sequence = payload.get("sequence", DEFAULT_SEQUENCE)

    if not isinstance(sequence, list) or not sequence:
        return jsonify({"error": "Provide a non-empty list of R/W requests."}), 400
    if len(sequence) > 40 or any(x not in ("R", "W") for x in sequence):
        return jsonify({"error": "Use at most 40 requests, each exactly R or W."}), 400

    # Compile on demand so a fresh checkout can run with only a C compiler installed.
    compile_result = subprocess.run(
        ["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-pthread",
         os.path.join(ROOT, "fairrepo.c"), "-o", BINARY],
        capture_output=True, text=True
    )
    if compile_result.returncode != 0:
        return jsonify({"error": "C compilation failed", "details": compile_result.stderr}), 500

    sequence_arg = ",".join(sequence)
    run = subprocess.run([BINARY, sequence_arg], capture_output=True, text=True, timeout=20)
    if run.returncode != 0:
        return jsonify({"error": "C simulation failed", "details": run.stderr}), 500
    try:
        result = json.loads(run.stdout)
    except json.JSONDecodeError:
        return jsonify({"error": "C engine returned invalid JSON", "details": run.stdout}), 500
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
