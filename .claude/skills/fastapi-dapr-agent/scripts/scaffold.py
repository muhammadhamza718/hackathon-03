#!/usr/bin/env python3
import sys
import os

def scaffold_service(name):
    os.makedirs(name, exist_ok=True)
    with open(os.path.join(name, "main.py"), "w") as f:
        f.write(f"""from fastapi import FastAPI
app = FastAPI(title="{name}")

@app.get("/")
def read_root():
    return {{"Hello": "from {name}"}}
""")
    with open(os.path.join(name, "requirements.txt"), "w") as f:
        f.write("fastapi\nuvicorn\ndapr-ext-fastapi\n")
    print(f"✓ Scaffolded FastAPI service: {name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scaffold.py <service_name>")
        sys.exit(1)
    scaffold_service(sys.argv[1])
