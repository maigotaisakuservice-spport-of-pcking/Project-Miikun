import os
import secrets
import subprocess
import sys
import getpass

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

    # 1. Gather System Information
    install_dir = os.getcwd()
    current_user = getpass.getuser()

    install_dir = get_input("Installation Directory", install_dir)
    user_name = get_input("Linux User Name (for Systemd)", current_user)
    domain = get_input("Domain Name (e.g., miikun.com)", "localhost")

    print("\n--- API & Security ---")
    shared_secret = get_input("Shared Secret for Frontend Handshake", secrets.token_hex(16))
    master_secret = get_input("Master Secret for Admin Access", secrets.token_hex(16))
    webhook_secret = get_input("Webhook Secret for Deployment", secrets.token_hex(16))

    print("\n--- GitHub Integration ---")
    gh_repo = get_input("GitHub Repo (user/repo)", "user/repo")
    gh_pat = get_input("GitHub Personal Access Token", "ghp_xxxx")

    print("\n--- Voice Settings ---")
    print("Common VOICEVOX Speaker IDs:")
    print("  13: 栗田まろん (Recommended: Young Boy)")
    print("  8: 春日部つむぎ (Girl)")
    speaker_id = get_input("VOICEVOX Speaker ID", "13")

    # 2. Generate .env
    env_content = f"""SHARED_SECRET={shared_secret}
ALLOWED_ORIGINS=https://{domain},http://localhost:8080,http://{domain}
WEBHOOK_SECRET={webhook_secret}
MASTER_SECRET={master_secret}
GH_REPO={gh_repo}
GH_PAT={gh_pat}
VOICEVOX_URL=http://localhost:50021
SPEAKER_ID={speaker_id}
MODEL_PATH=models/base_model.gguf
LORA_PATH=models/active_lora/
N_GPU_LAYERS=-1
"""
    with open("backend/.env", "w") as f:
        f.write(env_content)
    print("\n[✓] backend/.env generated.")

    # 3. System Dependencies
    print("\n--- Installing System Dependencies ---")
    run_cmd("sudo apt update")
    run_cmd("sudo apt install -y nginx docker.io docker-compose python3-venv certbot python3-certbot-nginx")

    # 4. Python Environment
    print("\n--- Setting up Python Virtual Environment ---")
    if not os.path.exists("venv"):
        run_cmd("python3 -m venv venv")
    run_cmd(f"{install_dir}/venv/bin/pip install -r backend/requirements.txt")

    # 5. Configure Nginx
    print("\n--- Configuring Nginx ---")
    nginx_template = "backend/infra/nginx.conf"
    if os.path.exists(nginx_template):
        with open(nginx_template, "r") as f:
            conf = f.read()
            conf = conf.replace("{{DOMAIN}}", domain)
            conf = conf.replace("{{INSTALL_DIR}}", install_dir)

        tmp_conf = "/tmp/miikun_nginx.conf"
        with open(tmp_conf, "w") as f:
            f.write(conf)

        run_cmd(f"sudo cp {tmp_conf} /etc/nginx/sites-available/miikun")
        run_cmd("sudo ln -sf /etc/nginx/sites-available/miikun /etc/nginx/sites-enabled/")
        run_cmd("sudo rm /etc/nginx/sites-enabled/default || true")
        run_cmd("sudo nginx -t && sudo systemctl restart nginx")
        print("[✓] Nginx configured.")

    # 6. Setup Systemd Service & Timers
    print("\n--- Configuring Systemd & Weekly Cron ---")
    service_template = "backend/infra/miikun.service"
    if os.path.exists(service_template):
        with open(service_template, "r") as f:
            service = f.read()
            service = service.replace("{{USER}}", user_name)
            service = service.replace("{{INSTALL_DIR}}", install_dir)

        tmp_service = "/tmp/miikun.service"
        with open(tmp_service, "w") as f:
            f.write(service)

        run_cmd(f"sudo cp {tmp_service} /etc/systemd/system/miikun.service")
        run_cmd("sudo systemctl daemon-reload")
        run_cmd("sudo systemctl enable miikun")
        print("[✓] Systemd service registered.")

    # 7. Setup Weekly Training Cron Task (Sunday AM3:00)
    cron_job = f"0 3 * * 0 {install_dir}/venv/bin/python {install_dir}/backend/scripts/weekly_train_local.py >> {install_dir}/backend/data/weekly_train.log 2>&1"
    run_cmd(f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -')
    print("[✓] Weekly Training Cron Task scheduled (Sundays AM3:00).")

    # 7. Final Steps
    print("\n==========================================")
    print("   Setup Complete! FINAL STEPS:           ")
    print("==========================================")
    print(f"1. PLACE your VRM model at: {install_dir}/assets/miikun.vrm")
    print(f"2. PLACE your GGUF model at: {install_dir}/models/base_model.gguf")
    print(f"3. START Backend: sudo systemctl start miikun")
    print(f"4. START VOICEVOX: sudo docker-compose -f backend/infra/docker-compose.yml up -d")
    if domain != "localhost":
        print(f"5. SETUP SSL: sudo certbot --nginx -d {domain}")

    print("\n--- CRITICAL: GitHub Secrets ---")
    print("Copy the following WEBHOOK_SECRET to your GitHub Repo Secrets as WEBHOOK_SECRET:")
    print(f"WEBHOOK_SECRET: {webhook_secret}")

    print("\nWelcome to the future of learning with Miikun!")

if __name__ == "__main__":
    if os.geteuid() == 0:
        print("Please do not run this script as root directly. It will ask for sudo when needed.")
        sys.exit(1)
    setup()
