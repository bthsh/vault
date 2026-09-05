# SETUP.md — Environment Setup (Ubuntu)

Run this BEFORE starting any build phase in `BUILD_PLAN.md`. This file
gives exact commands — if a step fails, fix it before continuing; do not
let the agent proceed on a broken environment.

## 1. System Requirements

- Ubuntu 20.04+ (or WSL2 with Ubuntu, though native dual-boot is
  preferred — see project notes)
- At least 8GB RAM (16GB more comfortable for running the model +
  Docker + IDE simultaneously)
- At least 10GB free disk space (model file + Docker images + dependencies)
- `sudo` access confirmed and password remembered

## 2. System Package Updates

```bash
sudo apt update && sudo apt upgrade -y
```

## 3. Python Environment

Check Python version (need 3.10+):
```bash
python3 --version
```

If missing or too old:
```bash
sudo apt install -y python3 python3-pip python3-venv
```

Create and activate a virtual environment inside the project folder:
```bash
cd vaultllm
python3 -m venv venv
source venv/bin/activate
```

**Note for the agent:** always activate `venv` before installing packages
or running any Python file in this project. Do not install dependencies
globally.

## 4. Python Dependencies

Create `requirements.txt` in the project root with:
```
fastapi
uvicorn
llama-cpp-python
cryptography
requests
python-multipart
```

Install:
```bash
pip install -r requirements.txt
```

**If `llama-cpp-python` fails to build:** it needs a C++ compiler. Install
build tools first:
```bash
sudo apt install -y build-essential cmake
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

## 5. Docker Installation

```bash
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

**Important:** after running `usermod`, log out and back in (or reboot)
for the group change to take effect — otherwise you'll need `sudo` before
every `docker` command, which is fine but must be consistent throughout
testing.

Verify:
```bash
docker --version
docker run hello-world
```

## 6. Download the LLM Model (do this manually, on your own machine)

This cannot be automated by the agent inside most sandboxed build
environments — download it yourself ahead of time.

1. Go to Hugging Face and search for a small quantized GGUF model. Recommended:
   - `Phi-3-mini-4k-instruct-q4.gguf` (~2.3GB), or
   - `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (~2GB)
2. Download the `.gguf` file directly
3. Place it inside the project folder, e.g.:
   ```
   vaultllm/models/model.gguf
   ```
4. Set the path as an environment variable so both servers can find it:
   ```bash
   export MODEL_PATH="$(pwd)/models/model.gguf"
   ```
   Add this line to your `~/.bashrc` (or a project `.env` file) so it
   persists across terminal sessions.

## 7. Verify the Model Loads

```bash
python3 -c "
from llama_cpp import Llama
llm = Llama(model_path='models/model.gguf', n_ctx=2048)
output = llm('Hello, how are you?', max_tokens=30)
print(output['choices'][0]['text'])
"
```

If this prints a coherent response, the model and runtime are working —
proceed to `BUILD_PLAN.md` Phase 2.

## 8. Generate the Shared Encryption Key

Run once, before building Track 2:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save the output string somewhere safe (e.g. a local `.env` file, NOT
committed to git). Both Track 2's server and client need this exact same
key.

Create `.env` in the project root:
```
FERNET_KEY=<paste the generated key here>
```

Add `.env` to `.gitignore` immediately:
```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "models/" >> .gitignore
```
(Model files are large — don't commit them to git either; document the
download step in README instead.)

## 9. GitHub Repository Setup

Per hackathon rules, you must push to an organizer-provided GitHub repo
at least once per hour during the finale.

```bash
git init
git remote add origin <organizer-provided-repo-url>
git add .
git commit -m "Initial project setup"
git push -u origin main
```

Confirm this works BEFORE the hackathon starts — test the push once now,
not for the first time during the actual event.

## 10. Final Verification Checklist

- [ ] `python3 --version` shows 3.10+
- [ ] `source venv/bin/activate` works, `(venv)` shows in your prompt
- [ ] `pip list` shows fastapi, uvicorn, llama-cpp-python, cryptography
- [ ] `docker run hello-world` succeeds without needing `sudo`
- [ ] Model file exists at the path in `MODEL_PATH`
- [ ] The verification script in Step 7 prints a real response
- [ ] The Fernet key is generated and saved in `.env`
- [ ] `.env`, `venv/`, and `models/` are in `.gitignore`
- [ ] A test `git push` to the organizer's repo succeeds

Once every box here is checked, tell your AI agent (Antigravity) to begin
`BUILD_PLAN.md` Phase 1.
