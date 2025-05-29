import subprocess
import os
import shutil
from pathlib import Path
from logger import Logger

class ServerBuilder:
    def __init__(self, commit_id, tls_mode):
        self.commit_id = commit_id
        self.tls_mode = tls_mode
        self.repo_url = "https://github.com/valkey-io/valkey.git"
        self.valkey_dir = Path("../valkey") if commit_id in ["pr", "unstable"] else Path(f"../valkey_{commit_id}")

    def _run(self, command, cwd=None):
        try:
            Logger.info(f"Running: {' '.join(command)}")
            subprocess.run(command, check=True, cwd=cwd)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Command failed with error: {e}")
        except Exception as e:
            Logger.error(f"An error occurred: {e}")


    def clone_and_checkout(self):
        if self.valkey_dir.exists():
            Logger.info(f"Using existing directory: {self.valkey_dir}")
            if self.commit_id == "unstable":
                Logger.info(f"Checking out commit unstable")
                self._run(["git", "checkout", self.commit_id], cwd=self.valkey_dir)
            return

        Logger.info(f"Cloning Valkey repo into {self.valkey_dir}...")
        self._run(["git", "clone", self.repo_url, str(self.valkey_dir)])
        
        # Checkout specific commit if not using pr or unstable
        if self.commit_id not in ["pr", "unstable"]:
            Logger.info(f"Checking out commit: {self.commit_id}")
            self._run(["git", "checkout", self.commit_id], cwd=self.valkey_dir)

    def build(self, tls_mode):
        Logger.info(f"Building with TLS {'enabled' if (tls_mode == 'yes') else 'disabled'}")
        self._run(["make", "distclean"], cwd=self.valkey_dir)
        if tls_mode == "yes":
            self._run(["make", "BUILD_TLS=yes", "-j"], cwd=self.valkey_dir)
            self._run("./utils/gen-test-certs.sh", cwd=self.valkey_dir)
        else:
            self._run(["make", "-j"], cwd=self.valkey_dir)

    def checkout_and_build(self):
        self.clone_and_checkout()
        self.build(tls_mode=self.tls_mode)
        return self.valkey_dir
    
    def check_if_built(self):
        Logger.info(f"Checking if Valkey build exists at {self.valkey_dir}")
        if not self.valkey_dir.exists():
            return False
        if not (self.valkey_dir / "src" / "valkey-server").exists():
            return False
        if not (self.valkey_dir / "src" / "valkey-cli").exists():
            return False
        if not (self.valkey_dir / "src" / "valkey-benchmark").exists():
            return False
        return True
    
    def get_valkey_path(self):
        if not self.check_if_built():
            raise FileNotFoundError(f"Valkey build not found at {self.valkey_dir}")
        return str(self.valkey_dir)
