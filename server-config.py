#!/usr/bin/env python3
"""
MCC Server Manager
Bloom.host Server Control & mrpack4server Deployment

Usage:
    python server-config.py          # Interactive menu
    python server-config.py status   # Check server status
    python server-config.py start    # Start server
    python server-config.py stop     # Stop server
    python server-config.py deploy   # Deploy mrpack4server + local.mrpack
"""

import paramiko
import os
import sys
import json
import urllib.request
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, FileSizeColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

# Initialize rich console
console = Console()

# Load .env file if it exists
def load_dotenv():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_dotenv()

# Fix Windows console encoding issues
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Connection details (from environment variables)
hostname = os.environ.get("SFTP_HOST", "")
port = int(os.environ.get("SFTP_PORT", "2022"))
username = os.environ.get("SFTP_USERNAME", "")
password = os.environ.get("SFTP_PASSWORD", "")

# Bloom.host Pterodactyl API settings
PTERODACTYL_API_URL = os.environ.get("PTERODACTYL_API_URL", "https://mc.bloom.host")
PTERODACTYL_API_KEY = os.environ.get("PTERODACTYL_API_KEY", "")
PTERODACTYL_SERVER_ID = os.environ.get("PTERODACTYL_SERVER_ID", "")

# Local paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MRPACK_FILE = os.path.join(SCRIPT_DIR, "local.mrpack")
MRPACK4SERVER_JAR = os.path.join(SCRIPT_DIR, "mrpack4server-0.5.0.jar")
CONFIG_DIR = os.path.join(SCRIPT_DIR, "config")


class RichProgressTracker:
    """Tracks upload progress using Rich"""
    def __init__(self, total_files=1, total_size=0):
        self.total_files = total_files
        self.total_size = total_size
        self.current_file = 0
        self.files_succeeded = 0
        self.files_failed = 0
        self.total_bytes_transferred = 0
        self.previous_file_transferred = 0

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="right"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            "•",
            FileSizeColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=console,
            expand=True
        )

        self.overall_task_id = None
        self.current_file_task_id = None

    def __enter__(self):
        self.progress.__enter__()
        if self.total_files > 1:
            self.overall_task_id = self.progress.add_task(
                f"[cyan]Overall Progress ({self.files_succeeded + self.files_failed}/{self.total_files} files)",
                total=self.total_size
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.__exit__(exc_type, exc_val, exc_tb)

    def start_file(self, filename, file_size):
        self.current_file += 1
        self.previous_file_transferred = 0

        display_name = filename
        if len(display_name) > 60:
            display_name = "..." + display_name[-57:]

        if self.current_file_task_id is not None:
            self.progress.remove_task(self.current_file_task_id)

        self.current_file_task_id = self.progress.add_task(
            f"[green]{display_name}",
            total=file_size
        )

    def update(self, transferred, total):
        if self.current_file_task_id is not None:
            self.progress.update(self.current_file_task_id, completed=transferred)

        if self.overall_task_id is not None:
            delta = transferred - self.previous_file_transferred
            if delta > 0:
                self.total_bytes_transferred += delta
                self.previous_file_transferred = transferred
                self.progress.update(
                    self.overall_task_id,
                    completed=min(self.total_bytes_transferred, self.total_size),
                    description=f"[cyan]Overall Progress ({self.files_succeeded + self.files_failed}/{self.total_files} files)"
                )

    def file_complete(self, success=True):
        if success:
            self.files_succeeded += 1
            if self.current_file_task_id is not None:
                # Access task by ID using internal dict (not list index)
                task = self.progress._tasks.get(self.current_file_task_id)
                if task and task.completed < task.total:
                    remaining = task.total - task.completed
                    self.total_bytes_transferred += remaining
                if task:
                    self.progress.update(self.current_file_task_id, completed=task.total)
                self.progress.remove_task(self.current_file_task_id)
                self.current_file_task_id = None

            if self.overall_task_id is not None:
                self.progress.update(
                    self.overall_task_id,
                    completed=min(self.total_bytes_transferred, self.total_size),
                    description=f"[cyan]Overall Progress ({self.files_succeeded + self.files_failed}/{self.total_files} files)"
                )
        else:
            self.files_failed += 1
            if self.current_file_task_id is not None:
                # Update overall progress to account for skipped file size
                task = self.progress._tasks.get(self.current_file_task_id)
                if task:
                    self.total_bytes_transferred += task.total  # Count as "done" for progress
                self.progress.remove_task(self.current_file_task_id)
                self.current_file_task_id = None

            # Update overall progress bar even on failure
            if self.overall_task_id is not None:
                self.progress.update(
                    self.overall_task_id,
                    completed=min(self.total_bytes_transferred, self.total_size),
                    description=f"[cyan]Overall Progress ({self.files_succeeded + self.files_failed}/{self.total_files} files)"
                )


def progress_callback(tracker):
    """Create a callback function for paramiko"""
    def callback(transferred, total):
        tracker.update(transferred, total)
    return callback


def check_credentials():
    """Check if credentials are configured"""
    if not hostname or not username or not password:
        console.print("[red]Error: SFTP credentials not configured![/red]")
        console.print("[yellow]Please create a .env file with:[/yellow]")
        console.print("  SFTP_HOST=your-server.bloom.host")
        console.print("  SFTP_PORT=2022")
        console.print("  SFTP_USERNAME=your-username")
        console.print("  SFTP_PASSWORD=your-password")
        console.print("  PTERODACTYL_API_KEY=your-api-key")
        console.print("  PTERODACTYL_SERVER_ID=your-server-id")
        return False
    return True


def upload_file(local_path, remote_path):
    """Upload a single file to the server"""
    if not os.path.exists(local_path):
        console.print(f"[red]Error: File not found: {local_path}[/red]")
        return False

    if not check_credentials():
        return False

    console.print(f"[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        console.print("[green]Connected![/green]")

        sftp = ssh.open_sftp()

        file_size = os.path.getsize(local_path)
        filename = os.path.basename(local_path)
        console.print(f"\n[bold]Uploading {filename} ({file_size / (1024*1024):.1f} MB)...[/bold]\n")

        with RichProgressTracker(total_files=1, total_size=file_size) as tracker:
            tracker.start_file(filename, file_size)

            try:
                callback = progress_callback(tracker)
                sftp.put(local_path, remote_path, callback=callback)
                tracker.file_complete(success=True)
                console.print(f"\n[green]✓ Upload complete![/green]")
            except Exception as e:
                tracker.file_complete(success=False)
                console.print(f"\n[red]✗ Upload failed: {e}[/red]")
                return False

        sftp.close()
        ssh.close()
        return True

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        return False


def upload_directory(local_dir, remote_dir):
    """Upload a directory recursively"""
    if not os.path.exists(local_dir):
        console.print(f"[red]Error: Directory not found: {local_dir}[/red]")
        return False

    if not check_credentials():
        return False

    console.print(f"[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        console.print("[green]Connected![/green]")

        sftp = ssh.open_sftp()

        # Count files and total size
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_count += 1
                total_size += os.path.getsize(file_path)

        console.print(f"\n[bold]Uploading {file_count} files ({total_size / (1024*1024):.1f} MB)...[/bold]\n")

        with RichProgressTracker(total_files=file_count, total_size=total_size) as tracker:
            def upload_recursive(local_path, remote_path):
                for item in os.listdir(local_path):
                    local_item = os.path.join(local_path, item)
                    remote_item = remote_path + "/" + item

                    if os.path.isfile(local_item):
                        try:
                            file_size = os.path.getsize(local_item)
                            rel_path = os.path.relpath(local_item, local_dir)
                            tracker.start_file(rel_path, file_size)
                            callback = progress_callback(tracker)
                            sftp.put(local_item, remote_item, callback=callback)
                            tracker.file_complete(success=True)
                        except Exception as e:
                            tracker.file_complete(success=False)
                            console.print(f"[red]Error uploading {item}: {e}[/red]")
                    elif os.path.isdir(local_item):
                        try:
                            sftp.mkdir(remote_item)
                        except IOError:
                            pass  # Directory exists
                        upload_recursive(local_item, remote_item)

            # Ensure remote directory exists
            try:
                sftp.mkdir(remote_dir)
            except IOError:
                pass

            upload_recursive(local_dir, remote_dir)

        console.print(f"\n[green]✓ Upload complete![/green]")

        sftp.close()
        ssh.close()
        return True

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        return False


# =============================================================================
# Pterodactyl Server Control
# =============================================================================

def pterodactyl_request(endpoint, method="GET", data=None):
    """Make a request to the Pterodactyl API"""
    if not PTERODACTYL_SERVER_ID or not PTERODACTYL_API_KEY:
        console.print("[red]Error: Pterodactyl API credentials not configured![/red]")
        return None

    url = f"{PTERODACTYL_API_URL}/api/client/servers/{PTERODACTYL_SERVER_ID}{endpoint}"

    headers = {
        "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 204:
                return {"success": True}
            return json.loads(response.read().decode('utf-8'))

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        console.print(f"[red]API Error {e.code}: {e.reason}[/red]")
        if error_body:
            console.print(f"[dim]{error_body}[/dim]")
        return None
    except urllib.error.URLError as e:
        console.print(f"[red]Connection Error: {e.reason}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def get_server_status():
    """Get current server status"""
    result = pterodactyl_request("/resources")
    if result and "attributes" in result:
        return result["attributes"]["current_state"]
    return None


def send_power_action(action):
    """Send a power action (start, stop, restart, kill)"""
    result = pterodactyl_request("/power", method="POST", data={"signal": action})
    return result is not None


def server_start():
    """Start the server"""
    console.print("[cyan]Starting server...[/cyan]")
    if send_power_action("start"):
        console.print("[green]✓ Start signal sent[/green]")
        return True
    return False


def server_stop():
    """Stop the server"""
    console.print("[cyan]Stopping server...[/cyan]")
    if send_power_action("stop"):
        console.print("[green]✓ Stop signal sent[/green]")
        return True
    return False


def server_restart():
    """Restart the server"""
    console.print("[cyan]Restarting server...[/cyan]")
    if send_power_action("restart"):
        console.print("[green]✓ Restart signal sent[/green]")
        return True
    return False


def server_status():
    """Display current server status"""
    console.print("[cyan]Checking server status...[/cyan]")
    status = get_server_status()
    if status:
        status_colors = {
            "running": "green",
            "starting": "yellow",
            "stopping": "yellow",
            "offline": "red"
        }
        color = status_colors.get(status, "white")
        console.print(f"[bold]Server Status:[/bold] [{color}]{status.upper()}[/{color}]")
        return status
    else:
        console.print("[red]Could not retrieve server status[/red]")
        return None


def send_console_command(command):
    """Send a command to the server console"""
    url = f"{PTERODACTYL_API_URL}/api/client/servers/{PTERODACTYL_SERVER_ID}/command"

    headers = {
        "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        data_bytes = json.dumps({"command": command}).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=30) as response:
            return True

    except urllib.error.HTTPError as e:
        if e.code == 502:
            console.print("[yellow]Server may still be starting (502 error)[/yellow]")
        else:
            console.print(f"[red]API Error {e.code}: {e.reason}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


# =============================================================================
# World Regeneration Functions
# =============================================================================

# Biome presets for single-biome worlds
BIOME_PRESETS = {
    "plains": {
        "name": "Plains (Default)",
        "level_type": "minecraft:flat",
        "generator_settings": '{"biome":"minecraft:plains","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"features":true,"lakes":false,"structure_overrides":[]}'
    },
    "forest": {
        "name": "Forest",
        "level_type": "minecraft:flat",
        "generator_settings": '{"biome":"minecraft:forest","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"features":true,"lakes":true,"structure_overrides":[]}'
    },
    "desert": {
        "name": "Desert",
        "level_type": "minecraft:flat",
        "generator_settings": '{"biome":"minecraft:desert","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:sandstone","height":2},{"block":"minecraft:sand","height":1}],"features":true,"lakes":false,"structure_overrides":[]}'
    },
    "snowy": {
        "name": "Snowy Plains",
        "level_type": "minecraft:flat",
        "generator_settings": '{"biome":"minecraft:snowy_plains","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"features":true,"lakes":true,"structure_overrides":[]}'
    },
    "cherry": {
        "name": "Cherry Grove",
        "level_type": "minecraft:flat",
        "generator_settings": '{"biome":"minecraft:cherry_grove","layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:dirt","height":2},{"block":"minecraft:grass_block","height":1}],"features":true,"lakes":false,"structure_overrides":[]}'
    },
    "normal": {
        "name": "Normal World (Random Seed)",
        "level_type": "minecraft:normal",
        "generator_settings": ""
    },
    "amplified": {
        "name": "Amplified Terrain",
        "level_type": "minecraft:amplified",
        "generator_settings": ""
    },
    "large_biomes": {
        "name": "Large Biomes",
        "level_type": "minecraft:large_biomes",
        "generator_settings": ""
    }
}


def delete_world_folders():
    """Delete world folders on the server via SFTP"""
    if not check_credentials():
        return False

    console.print(f"[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        console.print("[green]Connected![/green]")

        sftp = ssh.open_sftp()

        # World folders to delete (Fabric stores dimensions inside world/)
        world_folders = ["world"]
        deleted = []

        for folder in world_folders:
            try:
                # Check if folder exists
                sftp.stat(f"/{folder}")
                console.print(f"[yellow]Deleting /{folder}...[/yellow]")

                # Recursively delete folder
                delete_recursive(sftp, f"/{folder}")
                deleted.append(folder)
                console.print(f"[green]✓ Deleted /{folder}[/green]")
            except IOError:
                console.print(f"[dim]/{folder} does not exist, skipping[/dim]")

        sftp.close()
        ssh.close()

        if deleted:
            console.print(f"\n[green]✓ Deleted {len(deleted)} world folder(s)[/green]")
        else:
            console.print("\n[yellow]No world folders found to delete[/yellow]")

        return True

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def delete_recursive(sftp, path):
    """Recursively delete a directory via SFTP"""
    try:
        files = sftp.listdir_attr(path)
        for f in files:
            filepath = f"{path}/{f.filename}"
            if f.st_mode & 0o40000:  # Is directory
                delete_recursive(sftp, filepath)
            else:
                sftp.remove(filepath)
        sftp.rmdir(path)
    except IOError as e:
        console.print(f"[red]Error deleting {path}: {e}[/red]")


def get_server_properties():
    """Download and parse server.properties"""
    if not check_credentials():
        return None

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        sftp = ssh.open_sftp()

        with sftp.open("/server.properties", "r") as f:
            content = f.read().decode('utf-8')

        sftp.close()
        ssh.close()

        # Parse properties
        props = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                props[key.strip()] = value.strip()

        return props

    except Exception as e:
        console.print(f"[red]Error reading server.properties: {e}[/red]")
        return None


def update_server_properties(updates):
    """Update server.properties with new values"""
    if not check_credentials():
        return False

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        sftp = ssh.open_sftp()

        # Read current file
        with sftp.open("/server.properties", "r") as f:
            lines = f.read().decode('utf-8').split('\n')

        # Update values
        updated_keys = set()
        new_lines = []

        for line in lines:
            if line.strip() and not line.strip().startswith('#') and '=' in line:
                key = line.split('=', 1)[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Add any new keys that weren't in the file
        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")

        # Write back
        with sftp.open("/server.properties", "w") as f:
            f.write('\n'.join(new_lines).encode('utf-8'))

        sftp.close()
        ssh.close()

        console.print("[green]✓ Updated server.properties[/green]")
        return True

    except Exception as e:
        console.print(f"[red]Error updating server.properties: {e}[/red]")
        return False


def regenerate_world(preset_key=None, custom_seed=None, auto_confirm=False):
    """Regenerate the world with specified settings"""
    from rich.prompt import Prompt, Confirm
    import time

    console.print(Panel(
        "[bold]World Regeneration[/bold]\n\n"
        "[red]WARNING: This will DELETE the current world![/red]\n"
        "All builds, player data, and progress will be lost.",
        title="[yellow]⚠ Danger Zone[/yellow]",
        border_style="red"
    ))

    # Check server status first
    status = get_server_status()
    if status == "running" or status == "starting":
        console.print(f"\n[red]Server is currently {status}![/red]")
        if not auto_confirm and not Confirm.ask("Stop the server first?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return False
        server_stop()
        console.print("[cyan]Waiting for server to stop...[/cyan]")
        for i in range(15):
            time.sleep(2)
            status = get_server_status()
            if status == "offline":
                break
        if status != "offline":
            console.print("[yellow]Server didn't stop gracefully, sending kill signal...[/yellow]")
            send_power_action("kill")
            for _ in range(10):
                time.sleep(2)
                status = get_server_status()
                if status == "offline":
                    break
        if status != "offline":
            console.print("[red]Server still not offline. Please stop manually.[/red]")
            return False

    # Select preset if not provided
    if preset_key is None:
        console.print("\n[bold]Available World Types:[/bold]\n")
        table = Table(show_header=True, box=box.ROUNDED)
        table.add_column("Key", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Type", style="yellow")

        for key, preset in BIOME_PRESETS.items():
            table.add_row(key, preset["name"], preset["level_type"].replace("minecraft:", ""))

        console.print(table)
        console.print()

        preset_key = Prompt.ask(
            "Select world type",
            choices=list(BIOME_PRESETS.keys()),
            default="normal"
        )

    preset = BIOME_PRESETS.get(preset_key)
    if not preset:
        console.print(f"[red]Unknown preset: {preset_key}[/red]")
        return False

    # Custom seed?
    if custom_seed is None and not auto_confirm:
        seed_input = Prompt.ask("Enter seed (leave blank for random)", default="")
        custom_seed = seed_input if seed_input else ""
    elif custom_seed is None:
        custom_seed = ""

    # Final confirmation
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  World Type: [cyan]{preset['name']}[/cyan]")
    console.print(f"  Level Type: [yellow]{preset['level_type']}[/yellow]")
    console.print(f"  Seed: [green]{custom_seed if custom_seed else '(random)'}[/green]")

    if not auto_confirm and not Confirm.ask("\n[red]DELETE current world and regenerate?[/red]"):
        console.print("[yellow]Cancelled.[/yellow]")
        return False

    # Delete world folders
    console.print("\n[bold]Step 1/3: Deleting world folders...[/bold]")
    if not delete_world_folders():
        console.print("[red]Failed to delete world folders[/red]")
        return False

    # Update server.properties
    console.print("\n[bold]Step 2/3: Updating server.properties...[/bold]")
    updates = {
        "level-type": preset["level_type"],
        "level-seed": custom_seed,
    }
    if preset["generator_settings"]:
        updates["generator-settings"] = preset["generator_settings"]
    else:
        updates["generator-settings"] = ""

    if not update_server_properties(updates):
        console.print("[red]Failed to update server.properties[/red]")
        return False

    console.print("\n[bold]Step 3/3: Starting server...[/bold]")
    server_start()

    console.print("\n" + "="*50)
    console.print("[bold green]✓ World regeneration initiated![/bold green]")
    console.print("[yellow]The server will generate a new world on startup.[/yellow]")
    console.print("="*50)

    return True


# =============================================================================
# Deployment Functions
# =============================================================================

def deploy_mrpack4server():
    """Deploy mrpack4server.jar and local.mrpack to the server"""
    console.print(Panel(
        "[bold]Deploying MCC to Bloom.host[/bold]\n\n"
        "This will upload:\n"
        f"  • mrpack4server-0.5.0.jar\n"
        f"  • local.mrpack\n\n"
        "[yellow]The server will auto-install mods on first start.[/yellow]",
        title="[cyan]mrpack4server Deployment[/cyan]",
        border_style="cyan"
    ))

    # Check files exist
    if not os.path.exists(MRPACK4SERVER_JAR):
        console.print(f"[red]Error: {MRPACK4SERVER_JAR} not found![/red]")
        console.print("[yellow]Download from: https://github.com/Patbox/mrpack4server/releases[/yellow]")
        return False

    if not os.path.exists(MRPACK_FILE):
        console.print(f"[red]Error: {MRPACK_FILE} not found![/red]")
        console.print("[yellow]Run: copy MCC-0.9.8.mrpack local.mrpack[/yellow]")
        return False

    console.print("\n[bold]Step 1/2: Uploading mrpack4server.jar[/bold]")
    if not upload_file(MRPACK4SERVER_JAR, "/mrpack4server-0.5.0.jar"):
        return False

    console.print("\n[bold]Step 2/2: Uploading local.mrpack[/bold]")
    if not upload_file(MRPACK_FILE, "/local.mrpack"):
        return False

    console.print("\n" + "="*50)
    console.print("[bold green]✓ Deployment complete![/bold green]")
    console.print("\n[yellow]Next steps in Bloom.host panel:[/yellow]")
    console.print("  1. Go to Startup tab")
    console.print("  2. Set Java Version to Java 21")
    console.print("  3. Set Server Jar to: mrpack4server-0.5.0.jar")
    console.print("  4. Start the server")
    console.print("="*50)

    return True


def update_modpack_info(version):
    """Update modpack-info.json on server to point to a GitHub release"""
    import hashlib

    mrpack_file = os.path.join(SCRIPT_DIR, f"MCC-{version}.mrpack")

    if not os.path.exists(mrpack_file):
        console.print(f"[red]Error: {mrpack_file} not found![/red]")
        console.print("[yellow]Run: ./packwiz.exe modrinth export[/yellow]")
        return False

    if not check_credentials():
        return False

    # Calculate hash and size
    console.print(f"[cyan]Calculating hash for {os.path.basename(mrpack_file)}...[/cyan]")
    file_size = os.path.getsize(mrpack_file)

    sha512 = hashlib.sha512()
    with open(mrpack_file, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha512.update(chunk)
    file_hash = sha512.hexdigest()

    # Build the config
    github_url = f"https://github.com/mindfulent/MCC/releases/download/v{version}/MCC-{version}.mrpack"

    new_config = {
        "project_id": "mcc",
        "version_id": version,
        "display_name": "MCC",
        "display_version": version,
        "url": github_url,
        "size": file_size,
        "sha512": file_hash,
        "whitelisted_domains": ["github.com", "objects.githubusercontent.com"],
        "non_overwritable_paths": [
            "world", "world_nether", "world_the_end",
            "server.properties", "ops.json", "whitelist.json",
            "banned-players.json", "banned-ips.json"
        ]
    }

    # Upload to server
    console.print(f"[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        sftp = ssh.open_sftp()

        with sftp.open("/modpack-info.json", "w") as f:
            f.write(json.dumps(new_config, indent=2).encode())

        sftp.close()
        ssh.close()

        console.print(Panel(
            f"[bold green]Updated modpack-info.json to v{version}[/bold green]\n\n"
            f"URL: {github_url}\n"
            f"Size: {file_size / (1024*1024):.2f} MB\n"
            f"SHA512: {file_hash[:32]}...",
            title="[cyan]Modpack Info Updated[/cyan]",
            border_style="green"
        ))

        console.print("\n[yellow]Next steps:[/yellow]")
        console.print("  1. Ensure GitHub release v{} exists with the .mrpack attached".format(version))
        console.print("  2. Run: python server-config.py restart")

        return True

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def deploy_configs():
    """Upload config directory to server"""
    console.print("[bold]Uploading config directory...[/bold]")

    if not os.path.exists(CONFIG_DIR):
        console.print(f"[yellow]No config directory found at {CONFIG_DIR}[/yellow]")
        return False

    return upload_directory(CONFIG_DIR, "/config")


def list_remote_files():
    """List files on the remote server root"""
    if not check_credentials():
        return

    console.print(f"[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        console.print("[green]Connected![/green]\n")

        sftp = ssh.open_sftp()

        files = sftp.listdir_attr("/")

        table = Table(title="Server Root Directory", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Type", style="yellow")

        for f in sorted(files, key=lambda x: x.filename):
            size = f"{f.st_size / (1024*1024):.1f} MB" if f.st_size > 1024*1024 else f"{f.st_size / 1024:.1f} KB" if f.st_size > 1024 else f"{f.st_size} B"
            file_type = "DIR" if f.st_mode & 0o40000 else "FILE"
            table.add_row(f.filename, size, file_type)

        console.print(table)

        sftp.close()
        ssh.close()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# =============================================================================
# Interactive Menu
# =============================================================================

def interactive_menu():
    """Show an interactive menu"""
    from rich.prompt import Prompt

    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]MCC Server Manager[/bold cyan]\n"
            "[dim]Bloom.host Deployment & Control[/dim]",
            border_style="cyan"
        ))

        # Show server status
        console.print()
        server_status()
        console.print()

        # Menu options
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Action", style="white")

        table.add_row("1", "Deploy mrpack4server + modpack")
        table.add_row("2", "Upload configs only")
        table.add_row("3", "List server files")
        table.add_row("", "")
        table.add_row("4", "Start Server")
        table.add_row("5", "Stop Server")
        table.add_row("6", "Restart Server")
        table.add_row("7", "Send Console Command")
        table.add_row("", "")
        table.add_row("b", "[cyan]Backup Menu →[/cyan]")
        table.add_row("", "")
        table.add_row("8", "[red]Regenerate World[/red]")
        table.add_row("", "")
        table.add_row("", "[dim]── Local Server ──[/dim]")
        table.add_row("9", "Download Production World")
        table.add_row("10", "Switch Local to Production Mode")
        table.add_row("11", "Switch Local to Test Mode")
        table.add_row("", "")
        table.add_row("q", "Quit")

        console.print(table)
        console.print()

        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "b", "q"], default="q")

        if choice == "1":
            deploy_mrpack4server()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "2":
            deploy_configs()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "3":
            list_remote_files()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "4":
            server_start()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "5":
            server_stop()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "6":
            server_restart()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "7":
            cmd = Prompt.ask("Enter command")
            if cmd:
                if send_console_command(cmd):
                    console.print("[green]✓ Command sent[/green]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "b":
            backup_menu()

        elif choice == "8":
            regenerate_world()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "9":
            download_world()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "10":
            switch_local_production_mode()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "11":
            switch_local_test_mode()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "q":
            console.print("[dim]Goodbye![/dim]")
            break


def backup_menu():
    """Show backup management submenu"""
    from rich.prompt import Prompt

    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Backup Management[/bold cyan]\n"
            "[dim]Advanced Backups Control[/dim]",
            border_style="cyan"
        ))

        console.print()

        # Menu options
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Key", style="bold yellow")
        table.add_column("Action", style="white")

        table.add_row("1", "List Backups")
        table.add_row("2", "Create Backup")
        table.add_row("3", "Create Snapshot (immune to purge)")
        table.add_row("4", "[yellow]Restore from Backup[/yellow]")
        table.add_row("", "")
        table.add_row("b", "← Back to Main Menu")

        console.print(table)
        console.print()

        choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "b"], default="b")

        if choice == "1":
            backup_list()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "2":
            comment = Prompt.ask("Backup comment (optional)", default="")
            backup_create(comment)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "3":
            comment = Prompt.ask("Snapshot comment (optional)", default="")
            backup_snapshot(comment)
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "4":
            backup_restore()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

        elif choice == "b":
            break


# =============================================================================
# Backup Management Functions
# =============================================================================

def get_sftp_connection():
    """Create and return an SFTP connection"""
    if not check_credentials():
        return None, None

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port=port, username=username, password=password)
    sftp = ssh.open_sftp()
    return ssh, sftp


def backup_list():
    """List all available backups"""
    console.print("[cyan]Fetching backup list...[/cyan]\n")

    ssh, sftp = get_sftp_connection()
    if not sftp:
        return None

    backups = []

    try:
        # Check differential backups
        try:
            for item in sftp.listdir_attr('/backups/world/differential'):
                if item.filename.endswith('.zip'):
                    backup_type = "full" if "-full.zip" in item.filename else "partial"
                    backups.append({
                        'name': item.filename,
                        'path': f'/backups/world/differential/{item.filename}',
                        'size': item.st_size,
                        'type': f'differential-{backup_type}',
                        'mtime': item.st_mtime
                    })
        except IOError:
            pass

        # Check zip backups
        try:
            for item in sftp.listdir_attr('/backups/world/zips'):
                if item.filename.endswith('.zip'):
                    backups.append({
                        'name': item.filename,
                        'path': f'/backups/world/zips/{item.filename}',
                        'size': item.st_size,
                        'type': 'zip',
                        'mtime': item.st_mtime
                    })
        except IOError:
            pass

        # Check snapshots (manual backups immune to auto-delete)
        try:
            for item in sftp.listdir_attr('/backups/world/snapshots'):
                if item.filename.endswith('.zip'):
                    backups.append({
                        'name': item.filename,
                        'path': f'/backups/world/snapshots/{item.filename}',
                        'size': item.st_size,
                        'type': 'snapshot',
                        'mtime': item.st_mtime
                    })
        except IOError:
            pass

        sftp.close()
        ssh.close()

        if not backups:
            console.print("[yellow]No backups found.[/yellow]")
            return []

        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x['mtime'], reverse=True)

        # Display table
        table = Table(title="Available Backups", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Date", style="white")

        for i, backup in enumerate(backups, 1):
            size = backup['size']
            if size > 1024*1024*1024:
                size_str = f"{size/(1024*1024*1024):.2f} GB"
            elif size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f} MB"
            else:
                size_str = f"{size/1024:.1f} KB"

            date_str = datetime.fromtimestamp(backup['mtime']).strftime('%Y-%m-%d %H:%M')
            table.add_row(str(i), backup['name'], backup['type'], size_str, date_str)

        console.print(table)
        return backups

    except Exception as e:
        console.print(f"[red]Error listing backups: {e}[/red]")
        sftp.close()
        ssh.close()
        return None


def backup_create(comment=""):
    """Trigger a manual backup via server command"""
    status = get_server_status()
    if status != "running":
        console.print(f"[red]Server is not running (status: {status})[/red]")
        console.print("[yellow]Start the server first to create a backup.[/yellow]")
        return False

    cmd = f"backup start {comment}".strip()
    console.print(f"[cyan]Sending: {cmd}[/cyan]")

    if send_console_command(cmd):
        console.print("[green]✓ Backup command sent[/green]")
        console.print("[dim]Check server console for progress.[/dim]")
        return True
    return False


def backup_snapshot(comment=""):
    """Create a snapshot backup (immune to auto-purging)"""
    status = get_server_status()
    if status != "running":
        console.print(f"[red]Server is not running (status: {status})[/red]")
        return False

    cmd = f"backup snapshot {comment}".strip()
    console.print(f"[cyan]Sending: {cmd}[/cyan]")

    if send_console_command(cmd):
        console.print("[green]✓ Snapshot command sent[/green]")
        console.print("[dim]Snapshots are immune to automatic purging.[/dim]")
        return True
    return False


def backup_restore(backup_index=None, auto_confirm=False):
    """Restore from a backup"""
    import tempfile
    import zipfile
    import time

    # List backups first
    backups = backup_list()
    if not backups:
        return False

    # Select backup
    if backup_index is None:
        from rich.prompt import Prompt
        console.print()
        selection = Prompt.ask("Select backup number to restore", default="1")
        try:
            backup_index = int(selection)
        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return False

    if backup_index < 1 or backup_index > len(backups):
        console.print(f"[red]Invalid backup number. Choose 1-{len(backups)}[/red]")
        return False

    selected = backups[backup_index - 1]

    # For partial differential, find the chain
    restore_chain = [selected]
    if selected['type'] == 'differential-partial':
        # Need to find the most recent full backup before this one
        full_backups = [b for b in backups if b['type'] == 'differential-full' and b['mtime'] < selected['mtime']]
        if not full_backups:
            console.print("[red]Error: No full backup found before this partial![/red]")
            console.print("[yellow]Cannot restore a partial backup without its base full backup.[/yellow]")
            return False
        # Get the most recent full backup before this partial
        full_backup = max(full_backups, key=lambda x: x['mtime'])
        restore_chain = [full_backup, selected]
        console.print(f"\n[yellow]This is a partial backup. Will restore chain:[/yellow]")
        console.print(f"  1. {full_backup['name']} (full)")
        console.print(f"  2. {selected['name']} (partial)")

    # Calculate total download size
    total_size = sum(b['size'] for b in restore_chain)
    size_str = f"{total_size/(1024*1024*1024):.2f} GB" if total_size > 1024*1024*1024 else f"{total_size/(1024*1024):.1f} MB"

    console.print(Panel(
        f"[bold]Restore: {selected['name']}[/bold]\n\n"
        f"Download size: [cyan]{size_str}[/cyan]\n"
        f"Backups in chain: [cyan]{len(restore_chain)}[/cyan]\n\n"
        "[red]WARNING: This will replace the current world![/red]",
        title="[yellow]⚠ Backup Restore[/yellow]",
        border_style="yellow"
    ))

    if not auto_confirm:
        from rich.prompt import Confirm
        if not Confirm.ask("\nProceed with restore?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return False

    # Step 1: Stop server
    console.print("\n[bold]Step 1/5: Stopping server...[/bold]")
    status = get_server_status()
    if status == "running" or status == "starting":
        server_stop()
        console.print("[cyan]Waiting for server to stop...[/cyan]")
        for i in range(30):
            time.sleep(2)
            status = get_server_status()
            if status == "offline":
                break
        if status != "offline":
            console.print("[yellow]Server didn't stop gracefully, sending kill signal...[/yellow]")
            send_power_action("kill")
            time.sleep(5)

    console.print("[green]✓ Server stopped[/green]")

    # Step 2: Download backups
    console.print("\n[bold]Step 2/5: Downloading backup(s)...[/bold]")

    ssh, sftp = get_sftp_connection()
    if not sftp:
        return False

    temp_dir = tempfile.mkdtemp(prefix="mc_restore_")
    downloaded_files = []

    try:
        for backup in restore_chain:
            local_path = os.path.join(temp_dir, backup['name'])
            console.print(f"[cyan]Downloading {backup['name']}...[/cyan]")

            with RichProgressTracker(total_files=1, total_size=backup['size']) as tracker:
                tracker.start_file(backup['name'], backup['size'])
                sftp.get(backup['path'], local_path, callback=progress_callback(tracker))
                tracker.file_complete(success=True)

            downloaded_files.append(local_path)
            console.print(f"[green]✓ Downloaded {backup['name']}[/green]")

        # Step 3: Extract backups
        console.print("\n[bold]Step 3/5: Extracting backup(s)...[/bold]")
        extract_dir = os.path.join(temp_dir, "world")
        os.makedirs(extract_dir, exist_ok=True)

        for zip_path in downloaded_files:
            console.print(f"[cyan]Extracting {os.path.basename(zip_path)}...[/cyan]")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            console.print(f"[green]✓ Extracted[/green]")

        # Step 4: Delete remote world folder
        console.print("\n[bold]Step 4/5: Clearing remote world folder...[/bold]")
        delete_world_folders()

        # Recreate world folder
        try:
            sftp.mkdir("/world")
        except IOError:
            pass

        # Step 5: Upload restored files
        console.print("\n[bold]Step 5/5: Uploading restored world...[/bold]")

        # Count files for progress
        file_count = 0
        total_upload_size = 0
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_count += 1
                total_upload_size += os.path.getsize(file_path)

        console.print(f"[cyan]Uploading {file_count} files ({total_upload_size/(1024*1024):.1f} MB)...[/cyan]")

        with RichProgressTracker(total_files=file_count, total_size=total_upload_size) as tracker:
            def upload_recursive(local_path, remote_path):
                for item in os.listdir(local_path):
                    local_item = os.path.join(local_path, item)
                    remote_item = remote_path + "/" + item

                    if os.path.isfile(local_item):
                        try:
                            file_size = os.path.getsize(local_item)
                            rel_path = os.path.relpath(local_item, extract_dir)
                            tracker.start_file(rel_path, file_size)
                            sftp.put(local_item, remote_item, callback=progress_callback(tracker))
                            tracker.file_complete(success=True)
                        except Exception as e:
                            tracker.file_complete(success=False)
                            console.print(f"[red]Error uploading {item}: {e}[/red]")
                    elif os.path.isdir(local_item):
                        try:
                            sftp.mkdir(remote_item)
                        except IOError:
                            pass
                        upload_recursive(local_item, remote_item)

            upload_recursive(extract_dir, "/world")

        console.print("[green]✓ World restored[/green]")

        sftp.close()
        ssh.close()

        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Start server
        console.print("\n[bold]Starting server...[/bold]")
        server_start()

        console.print("\n" + "="*50)
        console.print("[bold green]✓ Backup restore complete![/bold green]")
        console.print(f"[cyan]Restored from: {selected['name']}[/cyan]")
        console.print("="*50)

        return True

    except Exception as e:
        console.print(f"[red]Error during restore: {e}[/red]")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        sftp.close()
        ssh.close()
        return False


# =============================================================================
# Local Server Mode Functions
# =============================================================================

def get_local_server_dir():
    """Get the LocalServer directory path"""
    return os.path.abspath(os.path.join(SCRIPT_DIR, "..", "LocalServer"))


def switch_local_production_mode():
    """Switch local server to production mode"""
    import shutil

    local_dir = get_local_server_dir()

    console.print(Panel(
        "[bold]Production Mode Setup[/bold]\n\n"
        "This mode replicates production settings:\n"
        "  • Normal world generation (not superflat)\n"
        "  • Mobs enabled\n"
        "  • Configs synced from MCC\n"
        "  • Production-like server.properties",
        title="[cyan]Local Server Mode[/cyan]",
        border_style="cyan"
    ))

    # Check paths exist
    props_production = os.path.join(local_dir, "server.properties.production")
    if not os.path.exists(props_production):
        console.print(f"[red]Error: {props_production} not found![/red]")
        return False

    # Step 1: Switch server.properties
    console.print("\n[bold]Step 1/3: Switching to production server.properties...[/bold]")
    props_file = os.path.join(local_dir, "server.properties")
    shutil.copy(props_production, props_file)
    console.print("[green]✓ server.properties updated[/green]")

    # Step 2: Sync configs from MCC
    console.print("\n[bold]Step 2/3: Syncing configs from MCC...[/bold]")
    mcc_config = os.path.join(SCRIPT_DIR, "config")
    local_config = os.path.join(local_dir, "config")

    if os.path.exists(mcc_config):
        os.makedirs(local_config, exist_ok=True)
        config_count = 0
        for item in os.listdir(mcc_config):
            src = os.path.join(mcc_config, item)
            dst = os.path.join(local_config, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            config_count += 1
        console.print(f"[green]✓ Synced {config_count} config items[/green]")
    else:
        console.print("[yellow]⚠ MCC config folder not found, skipping sync[/yellow]")

    # Step 3: World status
    console.print("\n[bold]Step 3/3: World setup...[/bold]")
    world_production = os.path.join(local_dir, "world-production")
    if os.path.exists(world_production):
        console.print("[green]✓ Using existing world-production folder[/green]")
        console.print("[dim]  To reset, delete world-production folder manually[/dim]")
    else:
        console.print("[yellow]⚠ world-production will be generated on first start[/yellow]")
        console.print("[dim]  Or run 'download-world' to sync from production[/dim]")

    # Summary
    console.print("\n" + "="*50)
    console.print("[bold green]✓ Production Mode Ready[/bold green]")
    console.print("\n[bold]Settings applied:[/bold]")
    console.print("  • server.properties: production mode")
    console.print("  • Configs: synced from MCC")
    console.print("  • World: world-production (normal generation)")
    console.print("\n[dim]To start: cd ../LocalServer && start.bat[/dim]")
    console.print("="*50)

    return True


def switch_local_test_mode():
    """Switch local server to test mode"""
    import shutil

    local_dir = get_local_server_dir()

    console.print(Panel(
        "[bold]Test Mode Setup[/bold]\n\n"
        "Switching back to test settings:\n"
        "  • Superflat world\n"
        "  • Peaceful difficulty\n"
        "  • No mobs",
        title="[cyan]Local Server Mode[/cyan]",
        border_style="cyan"
    ))

    # Check paths exist
    props_test = os.path.join(local_dir, "server.properties.test")
    if not os.path.exists(props_test):
        console.print(f"[red]Error: {props_test} not found![/red]")
        return False

    # Switch server.properties
    console.print("\n[bold]Switching to test server.properties...[/bold]")
    props_file = os.path.join(local_dir, "server.properties")
    shutil.copy(props_test, props_file)
    console.print("[green]✓ server.properties updated[/green]")

    # Summary
    console.print("\n" + "="*50)
    console.print("[bold green]✓ Test Mode Ready[/bold green]")
    console.print("\n[bold]Settings applied:[/bold]")
    console.print("  • server.properties: test mode (superflat, peaceful)")
    console.print("  • World: world-test")
    console.print("\n[dim]To start: cd ../LocalServer && start.bat[/dim]")
    console.print("="*50)

    return True


# =============================================================================
# World Download Functions
# =============================================================================

def get_remote_directory_info(sftp, path):
    """
    Calculate total size and file count of a remote directory recursively.
    Returns (file_count, total_size) or (0, 0) if path doesn't exist.
    """
    total_size = 0
    file_count = 0

    def scan_recursive(remote_path):
        nonlocal total_size, file_count
        try:
            for item in sftp.listdir_attr(remote_path):
                item_path = f"{remote_path}/{item.filename}"
                if item.st_mode & 0o40000:  # Directory
                    scan_recursive(item_path)
                else:
                    total_size += item.st_size
                    file_count += 1
        except IOError:
            pass

    try:
        sftp.stat(path)
        scan_recursive(path)
    except IOError:
        pass

    return file_count, total_size


def download_directory_recursive(sftp, remote_path, local_path, tracker, base_path=None):
    """Download a remote directory recursively to local path with progress tracking."""
    if base_path is None:
        base_path = local_path

    os.makedirs(local_path, exist_ok=True)

    try:
        for item in sftp.listdir_attr(remote_path):
            remote_item = f"{remote_path}/{item.filename}"
            local_item = os.path.join(local_path, item.filename)

            if item.st_mode & 0o40000:  # Directory
                download_directory_recursive(sftp, remote_item, local_item, tracker, base_path)
            else:
                try:
                    rel_path = os.path.relpath(local_item, base_path)
                    tracker.start_file(rel_path, item.st_size)
                    sftp.get(remote_item, local_item, callback=progress_callback(tracker))
                    tracker.file_complete(success=True)
                except Exception as e:
                    tracker.file_complete(success=False)
                    console.print(f"[red]Error downloading {item.filename}: {e}[/red]")
    except IOError as e:
        console.print(f"[red]Error accessing {remote_path}: {e}[/red]")


def backup_local_world(world_dirs):
    """
    Backup existing local world directories before overwriting.
    Creates a timestamped backup folder.
    Returns the backup directory path or None if no backup was needed.
    """
    import shutil

    # Check if any directories exist
    existing_dirs = [d for d in world_dirs if os.path.exists(d)]
    if not existing_dirs:
        return None

    # Create timestamped backup folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_base = os.path.join(os.path.dirname(existing_dirs[0]), f"world-backup-{timestamp}")
    os.makedirs(backup_base, exist_ok=True)

    for world_dir in existing_dirs:
        dir_name = os.path.basename(world_dir)
        backup_dest = os.path.join(backup_base, dir_name)
        console.print(f"[cyan]Backing up {dir_name}...[/cyan]")
        shutil.copytree(world_dir, backup_dest)
        console.print(f"[green]✓ Backed up {dir_name}[/green]")

    return backup_base


def download_world(destination_dir=None, backup_existing=True, auto_confirm=False):
    """
    Download world data from production server to local directory.

    Args:
        destination_dir: Base path for download (default: ../LocalServer/)
        backup_existing: Whether to backup existing local world first
        auto_confirm: Skip confirmation prompts
    """
    from rich.prompt import Confirm

    # Determine destination directory
    if destination_dir is None:
        destination_dir = os.path.join(SCRIPT_DIR, "..", "LocalServer")
    destination_dir = os.path.abspath(destination_dir)

    # World folders mapping: (remote_path, local_folder_name)
    WORLD_FOLDERS = [
        ("/world", "world-production"),
        ("/world_nether", "world-production_nether"),
        ("/world_the_end", "world-production_the_end"),
    ]

    console.print(Panel(
        "[bold]Download Production World[/bold]\n\n"
        "This will download world data from the production server\n"
        "to your local test environment.",
        title="[cyan]World Sync[/cyan]",
        border_style="cyan"
    ))

    if not check_credentials():
        return False

    # Connect and scan remote folders
    console.print(f"\n[cyan]Connecting to {hostname}:{port}...[/cyan]")

    ssh, sftp = get_sftp_connection()
    if not sftp:
        return False

    console.print("[green]Connected![/green]")
    console.print("\n[cyan]Scanning remote world folders...[/cyan]")

    # Gather info about each world folder
    folder_info = []
    total_files = 0
    total_size = 0

    for remote_path, local_name in WORLD_FOLDERS:
        file_count, size = get_remote_directory_info(sftp, remote_path)
        if file_count > 0:
            folder_info.append({
                'remote': remote_path,
                'local': local_name,
                'files': file_count,
                'size': size
            })
            total_files += file_count
            total_size += size
        else:
            console.print(f"[dim]  {remote_path} (not found, skipping)[/dim]")

    if not folder_info:
        console.print("[red]No world folders found on remote server![/red]")
        sftp.close()
        ssh.close()
        return False

    # Display summary
    size_str = f"{total_size/(1024*1024*1024):.2f} GB" if total_size > 1024*1024*1024 else f"{total_size/(1024*1024):.1f} MB"

    table = Table(title="Remote World Folders", box=box.ROUNDED)
    table.add_column("Folder", style="cyan")
    table.add_column("Files", style="white", justify="right")
    table.add_column("Size", style="green", justify="right")

    for info in folder_info:
        folder_size = f"{info['size']/(1024*1024*1024):.2f} GB" if info['size'] > 1024*1024*1024 else f"{info['size']/(1024*1024):.1f} MB"
        table.add_row(info['remote'], str(info['files']), folder_size)

    table.add_row("", "", "", style="dim")
    table.add_row("[bold]Total[/bold]", f"[bold]{total_files}[/bold]", f"[bold]{size_str}[/bold]")

    console.print()
    console.print(table)
    console.print(f"\n[bold]Destination:[/bold] {destination_dir}")

    # Check for local server running
    session_lock = os.path.join(destination_dir, "world-production", "session.lock")
    if os.path.exists(session_lock):
        console.print("\n[yellow]⚠ Warning: Local server may be running (session.lock exists)[/yellow]")
        if not auto_confirm and not Confirm.ask("Continue anyway?"):
            console.print("[yellow]Cancelled.[/yellow]")
            sftp.close()
            ssh.close()
            return False

    # Confirm download
    if not auto_confirm:
        console.print()
        if not Confirm.ask(f"Download {size_str} from production server?"):
            console.print("[yellow]Cancelled.[/yellow]")
            sftp.close()
            ssh.close()
            return False

    # Backup existing local world
    if backup_existing:
        local_world_dirs = [os.path.join(destination_dir, info['local']) for info in folder_info]
        existing_dirs = [d for d in local_world_dirs if os.path.exists(d)]
        if existing_dirs:
            console.print("\n[bold]Backing up existing world...[/bold]")
            backup_path = backup_local_world(local_world_dirs)
            if backup_path:
                console.print(f"[green]✓ Backup saved to: {os.path.basename(backup_path)}/[/green]")

    # Download each folder
    console.print("\n[bold]Downloading world data...[/bold]\n")

    with RichProgressTracker(total_files=total_files, total_size=total_size) as tracker:
        for info in folder_info:
            local_path = os.path.join(destination_dir, info['local'])

            # Clear existing directory if it exists
            if os.path.exists(local_path):
                import shutil
                shutil.rmtree(local_path)

            console.print(f"[cyan]Downloading {info['remote']}...[/cyan]")
            download_directory_recursive(sftp, info['remote'], local_path, tracker)

    sftp.close()
    ssh.close()

    # Summary
    console.print("\n" + "="*50)
    console.print("[bold green]✓ World download complete![/bold green]")
    console.print(f"\n[cyan]Downloaded {total_files} files ({size_str})[/cyan]")
    console.print(f"\n[bold]Files saved to:[/bold]")
    for info in folder_info:
        console.print(f"  {destination_dir}\\{info['local']}\\")
    console.print("\n[dim]To use this world, set level-name=world-production in server.properties[/dim]")
    console.print("="*50)

    return True


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "deploy":
            deploy_mrpack4server()
        elif command == "configs":
            deploy_configs()
        elif command == "list":
            list_remote_files()
        elif command == "start":
            server_start()
        elif command == "stop":
            server_stop()
        elif command == "restart":
            server_restart()
        elif command == "status":
            server_status()
        elif command == "cmd" and len(sys.argv) > 2:
            cmd = " ".join(sys.argv[2:])
            console.print(f"[cyan]Sending: {cmd}[/cyan]")
            if send_console_command(cmd):
                console.print("[green]✓ Command sent[/green]")
        elif command == "regenerate":
            # Optional: python server-config.py regenerate <preset> [seed] [-y]
            # Parse args (preset, seed, -y flag)
            args = sys.argv[2:]
            auto_yes = "-y" in args or "--yes" in args
            args = [a for a in args if a not in ("-y", "--yes")]
            preset = args[0] if len(args) > 0 else None
            seed = args[1] if len(args) > 1 else None
            regenerate_world(preset_key=preset, custom_seed=seed, auto_confirm=auto_yes)
        elif command == "presets":
            # List available presets
            console.print("\n[bold]Available World Presets:[/bold]\n")
            table = Table(show_header=True, box=box.ROUNDED)
            table.add_column("Key", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Type", style="yellow")
            for key, preset in BIOME_PRESETS.items():
                table.add_row(key, preset["name"], preset["level_type"].replace("minecraft:", ""))
            console.print(table)
        elif command == "update-pack" and len(sys.argv) > 2:
            version = sys.argv[2]
            update_modpack_info(version)
        elif command == "download-world":
            # Parse args: download-world [destination] [--no-backup] [-y]
            args = sys.argv[2:]
            auto_yes = "-y" in args or "--yes" in args
            no_backup = "--no-backup" in args
            args = [a for a in args if a not in ("-y", "--yes", "--no-backup")]
            destination = args[0] if args else None
            download_world(destination_dir=destination, backup_existing=not no_backup, auto_confirm=auto_yes)
        elif command == "local-production":
            switch_local_production_mode()
        elif command == "local-test":
            switch_local_test_mode()
        elif command == "backup":
            # Backup subcommands
            if len(sys.argv) < 3:
                console.print("[yellow]Backup commands:[/yellow]")
                console.print("  python server-config.py backup list              # List all backups")
                console.print("  python server-config.py backup create [comment]  # Create manual backup")
                console.print("  python server-config.py backup snapshot [comment] # Create snapshot (immune to purge)")
                console.print("  python server-config.py backup restore [number]  # Restore from backup")
            else:
                subcmd = sys.argv[2]
                if subcmd == "list":
                    backup_list()
                elif subcmd == "create":
                    comment = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
                    backup_create(comment)
                elif subcmd == "snapshot":
                    comment = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
                    backup_snapshot(comment)
                elif subcmd == "restore":
                    backup_index = None
                    auto_confirm = "-y" in sys.argv or "--yes" in sys.argv
                    args = [a for a in sys.argv[3:] if a not in ("-y", "--yes")]
                    if args:
                        try:
                            backup_index = int(args[0])
                        except ValueError:
                            console.print(f"[red]Invalid backup number: {args[0]}[/red]")
                            sys.exit(1)
                    backup_restore(backup_index, auto_confirm)
                else:
                    console.print(f"[red]Unknown backup command: {subcmd}[/red]")
        else:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  python server-config.py              # Interactive menu")
            console.print("  python server-config.py status       # Server status")
            console.print("  python server-config.py start        # Start server")
            console.print("  python server-config.py stop         # Stop server")
            console.print("  python server-config.py restart      # Restart server")
            console.print("  python server-config.py cmd <cmd>    # Send console command")
            console.print("")
            console.print("[yellow]Deployment:[/yellow]")
            console.print("  python server-config.py update-pack <version>  # Update modpack-info.json")
            console.print("  python server-config.py deploy       # Upload mrpack4server + local.mrpack")
            console.print("  python server-config.py configs      # Upload config directory")
            console.print("  python server-config.py list         # List server files")
            console.print("")
            console.print("[yellow]Backup Management:[/yellow]")
            console.print("  python server-config.py backup list              # List all backups")
            console.print("  python server-config.py backup create [comment]  # Create manual backup")
            console.print("  python server-config.py backup snapshot [comment] # Create snapshot (immune to purge)")
            console.print("  python server-config.py backup restore [number]  # Restore from backup")
            console.print("")
            console.print("[yellow]World Management:[/yellow]")
            console.print("  python server-config.py regenerate [preset] [seed] [-y]  # Regenerate world")
            console.print("  python server-config.py presets      # List world presets")
            console.print("")
            console.print("[yellow]Local Server:[/yellow]")
            console.print("  python server-config.py download-world [path] [--no-backup] [-y]  # Download production world")
            console.print("  python server-config.py local-production  # Switch local to production mode")
            console.print("  python server-config.py local-test        # Switch local to test mode")
    else:
        interactive_menu()
