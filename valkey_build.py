import subprocess
import os
import shutil
from pathlib import Path
from logger import Logger

class ServerBuilder:
    def __init__(self, commit_id, tls_mode, valkey_path):
        self.commit_id = commit_id
        self.tls_mode = tls_mode
        self.repo_url = "https://github.com/valkey-io/valkey.git"
        self.valkey_dir = Path(valkey_path)

    def _run(self, command, cwd=None):
        try:
            Logger.info(f"Running: {' '.join(command)}")
            subprocess.run(command, check=True, cwd=cwd)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with error: {e}")
        except Exception as e:
            Logger.error(f"An error occurred: {e}")


    def clone_and_checkout(self):
        if not self.valkey_dir.exists():
            Logger.info(f"Cloning Valkey repo into {self.valkey_dir}...")
            self._run(["git", "clone", self.repo_url, str(self.valkey_dir)])
            
        if self.commit_id == "HEAD":
            return
        
        # Checkout specific commit
        Logger.info(f"Checking out commit: {self.commit_id}")
        self._run(["git", "checkout", self.commit_id], cwd=self.valkey_dir)

    def build(self):
        self.clone_and_checkout()
        Logger.info(f"Building with TLS {'enabled' if (self.tls_mode == 'yes') else 'disabled'}")
        self._run(["make", "distclean"], cwd=self.valkey_dir)
        if self.tls_mode == "yes":
            self._run(["make", "BUILD_TLS=yes", "-j"], cwd=self.valkey_dir)
            self._run("./utils/gen-test-certs.sh", cwd=self.valkey_dir)
        else:
            self._run(["make", "-j"], cwd=self.valkey_dir)
        return self.valkey_dir
