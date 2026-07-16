#!/data/data/com.termux/files/usr/bin/bash

echo "===================================="
echo "      YasinCoder Installer"
echo "===================================="

chmod +x run.sh 2>/dev/null

mkdir -p logs
mkdir -p cache
mkdir -p backups
mkdir -p prompts
mkdir -p providers
mkdir -p commands
mkdir -p core

touch logs/.keep
touch cache/.keep
touch backups/.keep

echo
echo "[1/7] Checking Python..."

python --version

echo
echo "[2/7] Checking Project..."

if [ -d "/data/data/com.termux/files/home/YasinPress-AI-Engine" ]; then

    echo "Project Found"

else

    echo "WARNING: Project not found"

fi

echo
echo "[3/7] Running Doctor..."

python doctor.py

echo
echo "[4/7] Running Tests..."

python test.py

echo
echo "[5/7] Saving Configuration..."

cat > config.json << CONF
{
    "provider":"cloudflare",
    "model":"auto",
    "temperature":0.2,
    "project":"/data/data/com.termux/files/home/YasinPress-AI-Engine"
}
CONF

echo
echo "[6/7] Creating Workspace..."

mkdir -p workspace

echo
echo "[7/7] Done."

echo
echo "===================================="
echo "YasinCoder Ready"
echo "===================================="

echo
echo "Examples:"
echo
echo "./run.sh info"
echo "./run.sh project"
echo "./run.sh brain"
echo "./run.sh search database"
echo "./run.sh explain database.py"
echo "./run.sh review database.py"
echo "./run.sh fix database.py"
echo "./run.sh refactor database.py"
echo
