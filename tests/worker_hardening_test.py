import subprocess, os

# Runs the Worker hardening checks (admin CORS, constant-time token compare,
# /program rate limit) in plain node against a mocked D1 - see
# worker/test/hardening.mjs. No network, no wrangler.
here = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(here, "..", "worker", "test", "hardening.mjs")
r = subprocess.run(["node", script], capture_output=True, text=True, timeout=60)
print(r.stdout.strip())
if r.returncode != 0:
    print("worker script ran: False")
    print("Error:", r.stderr.strip())
