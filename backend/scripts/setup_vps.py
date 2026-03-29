import os
import secrets
import subprocess
import sys

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_input(prompt, default=""):
    val = input(f"{prompt} [{default}]: ").strip()
    return val if val else default

def run_cmd(cmd, shell=True):
    print(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return False
    return True

def setup():
    clear()
    print("==========================================")
    print("   Miikun Intelligence VPS Setup Wizard   ")
    print("==========================================")
    print("\nThis script will guide you through the setup process.\n")

    # 1. Gather Configuration
    domain = get_input("Enter your domain (e.g., miikun.com)", "localhost")
    shared_secret = get_input("Enter a Shared Secret for Frontend", secrets.token_hex(16))
    master_secret = get_input("Enter a Master Secret for Admin", secrets.token_hex(16))
    webhook_secret = get_input("Enter a Webhook Secret for Deployment", secrets.token_hex(16))
    github_repo = get_input("Enter your GitHub repo (user/repo)", "user/repo")
    github_token = get_input("Enter your GitHub PAT (for Repository Dispatch)", "ghp_xxxx")

    # 2. Generate .env
    env_content = f"""SHARED_SECRET={shared_secret}
ALLOWED_ORIGINS=https://{domain},http://localhost:8080
WEBHOOK_SECRET={webhook_secret}
MASTER_SECRET={master_secret}
GITHUB_REPO={github_repo}
GITHUB_TOKEN={github_token}
VOICEVOX_URL=http://localhost:50021
SPEAKER_ID=13
MODEL_PATH=models/base_model.gguf
LORA_PATH=models/active_lora/
N_GPU_LAYERS=-1
"""
    with open("backend/.env", "w") as f:
        f.write(env_content)
    print("\n[✓] backend/.env generated.")

    # 3. Environment Checks & System Setup
    is_ubuntu = run_cmd("grep -q 'Ubuntu' /etc/os-release")
    if not is_ubuntu:
        print("\n[!] Warning: This script is optimized for Ubuntu 22.04 LTS.")
        cont = get_input("Continue anyway? (y/n)", "n")
        if cont.lower() != 'y': sys.exit(0)

    print("\n--- Installing System Dependencies ---")
    run_cmd("sudo apt update")
    run_cmd("sudo apt install -y nginx docker.io docker-compose python3-venv certbot python3-certbot-nginx")

    # 4. Configure Nginx
    print("\n--- Configuring Nginx ---")
    nginx_conf_path = "backend/infra/nginx.conf"
    if os.path.exists(nginx_conf_path):
        with open(nginx_conf_path, "r") as f:
            conf = f.read().replace("your-domain.com", domain)

        tmp_conf = "/tmp/miikun_nginx.conf"
        with open(tmp_conf, "w") as f:
            f.write(conf)

        run_cmd(f"sudo cp {tmp_conf} /etc/nginx/sites-available/miikun")
        run_cmd("sudo ln -sf /etc/nginx/sites-available/miikun /etc/nginx/sites-enabled/")
        run_cmd("sudo rm /etc/nginx/sites-enabled/default || true")
        run_cmd("sudo nginx -t && sudo systemctl restart nginx")
        print("[✓] Nginx configured.")

    # 5. Setup Systemd Service
    print("\n--- Configuring Systemd ---")
    service_path = "backend/infra/miikun.service"
    if os.path.exists(service_path):
        run_cmd(f"sudo cp {service_path} /etc/systemd/system/miikun.service")
        run_cmd("sudo systemctl daemon-reload")
        run_cmd("sudo systemctl enable miikun")
        print("[✓] Systemd service registered.")

    # 6. Final Steps
    print("\n==========================================")
    print("   Setup Complete! What's next?           ")
    print("==========================================")
    print(f"1. PLACE your VRM model at: assets/miikun.vrm")
    print(f"2. PLACE your GGUF model at: backend/models/base_model.gguf")
    print(f"3. RUN 'sudo systemctl start miikun' to start the backend.")
    print(f"4. RUN 'sudo docker-compose -f backend/infra/docker-compose.yml up -d' for VOICEVOX.")
    print(f"5. SETUP SSL with: sudo certbot --nginx -d {domain}")
    print("\nEnjoy your Miikun Intelligence experience!")

if __name__ == "__main__":
    if os.geteuid() == 0:
        print("Please do not run this script as root directly. It will ask for sudo when needed.")
        sys.exit(1)
    setup()
