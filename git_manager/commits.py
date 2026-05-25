"""Git operations for Unagi vault."""
from pathlib import Path
from typing import Optional
from datetime import datetime
import git
from git import Repo, Actor
from config import get_settings


class GitError(Exception):
    """Raised when git operations fail."""
    pass


class GitManager:
    """Manages git operations for the vault."""
    
    def __init__(self):
        """Initialize the git manager with settings."""
        self.settings = get_settings()
        self.repo: Optional[Repo] = None
        
        if self.settings.git_enabled:
            self._init_repo()
    
    def _init_repo(self):
        """Initialize or open the git repository."""
        try:
            vault_path = Path(self.settings.vault_root)
            
            # Check if it's already a git repo
            if (vault_path / ".git").exists():
                self.repo = Repo(vault_path)
            else:
                # Not a git repo yet - will be initialized on first commit
                self.repo = None
                
        except Exception as e:
            raise GitError(f"Failed to initialize git repo: {str(e)}")
    
    def ensure_repo_initialized(self) -> bool:
        """Ensure the vault is a git repository.
        
        Returns:
            True if repo was initialized, False if already existed
            
        Raises:
            GitError: If initialization fails
        """
        try:
            vault_path = Path(self.settings.vault_root)
            
            if (vault_path / ".git").exists():
                return False
            
            # Ensure vault directory exists
            vault_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize new repo with explicit path
            self.repo = Repo.init(str(vault_path))
            
            # Create .gitignore for Obsidian
            gitignore_path = vault_path / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("# Obsidian\n.obsidian/\n")
            
            # Make initial commit
            self.repo.index.add([".gitignore"])
            author = Actor(
                self.settings.git_author_name,
                self.settings.git_author_email
            )
            self.repo.index.commit(
                "[unagi] init: Initialize Unagi vault repository",
                author=author
            )
            
            # Add remote if configured
            if self.settings.git_remote_url:
                try:
                    # Build authenticated URL if token is provided
                    remote_url = self.settings.git_remote_url
                    if self.settings.git_remote_token and 'github.com' in remote_url:
                        remote_url = remote_url.replace('https://', f'https://{self.settings.git_remote_token}@')
                    self.repo.create_remote('origin', remote_url)
                except Exception:
                    # Remote might already exist
                    pass
            
            return True
            
        except Exception as e:
            raise GitError(f"Failed to initialize git repository: {str(e)}")
    
    def commit_file(
        self,
        file_path: Path,
        action: str,
        date: datetime,
        summary: str
    ) -> bool:
        """Commit a file change to git.
        
        Args:
            file_path: Path to the file to commit
            action: Action type ('create' or 'update')
            date: Date of the log entry
            summary: Summary of changes (e.g., "Cal: 1250 | P: 118g")
            
        Returns:
            True if commit successful
            
        Raises:
            GitError: If commit fails
        """
        if not self.settings.git_enabled:
            return False
        
        try:
            # Ensure repo is initialized
            if self.repo is None:
                self.ensure_repo_initialized()
                self._init_repo()
            
            # Get relative path from repo root
            vault_path = Path(self.settings.vault_root)
            rel_path = file_path.relative_to(vault_path)
            
            # Stage the file
            self.repo.index.add([str(rel_path)])
            
            # Create commit message
            date_str = date.strftime("%Y-%m-%d")
            commit_msg = f"[unagi] {action}: {date_str} — {summary}"
            
            # Create author
            author = Actor(
                self.settings.git_author_name,
                self.settings.git_author_email
            )
            
            # Commit
            self.repo.index.commit(commit_msg, author=author)
            
            # Push if auto-push is enabled
            if self.settings.git_auto_push and self.settings.git_remote_url:
                self.push()
            
            return True
            
        except Exception as e:
            raise GitError(f"Failed to commit file: {str(e)}")
    
    def push(self) -> bool:
        """Push commits to remote.
        
        Returns:
            True if push successful
            
        Raises:
            GitError: If push fails
        """
        if not self.settings.git_enabled or not self.settings.git_remote_url:
            return False
        
        try:
            if self.repo is None:
                return False
            
            # Build authenticated URL if token is provided
            remote_url = self.settings.git_remote_url
            if self.settings.git_remote_token and 'github.com' in remote_url:
                # Inject token into URL: https://TOKEN@github.com/user/repo.git
                remote_url = remote_url.replace('https://', f'https://{self.settings.git_remote_token}@')
            
            # Get or create remote with authenticated URL
            try:
                remote = self.repo.remote('origin')
                # Update URL if it changed
                if remote.url != remote_url:
                    remote.set_url(remote_url)
            except ValueError:
                # Remote doesn't exist, create it
                remote = self.repo.create_remote('origin', remote_url)
            
            # Push to remote
            remote.push(self.settings.git_branch)
            return True
            
        except Exception as e:
            # Don't raise error for push failures - just log warning
            print(f"Warning: Failed to push to remote: {str(e)}")
            return False
    
    def get_status(self) -> str:
        """Get git status summary.
        
        Returns:
            Status string
        """
        if not self.settings.git_enabled or self.repo is None:
            return "Git disabled"
        
        try:
            # Check if there are uncommitted changes
            if self.repo.is_dirty():
                return "Uncommitted changes"
            
            # Check if we're ahead of remote
            try:
                remote = self.repo.remote('origin')
                remote.fetch()
                
                local_commit = self.repo.head.commit
                remote_commit = self.repo.commit(f'origin/{self.settings.git_branch}')
                
                if local_commit != remote_commit:
                    return "Ahead of remote"
            except Exception:
                pass
            
            return "Up to date"
            
        except Exception:
            return "Unknown"
    
    def get_last_commit_message(self) -> Optional[str]:
        """Get the last commit message.
        
        Returns:
            Last commit message, or None if no commits
        """
        if not self.settings.git_enabled or self.repo is None:
            return None
        
        try:
            return self.repo.head.commit.message.strip()
        except Exception:
            return None


# Global git manager instance
_git_manager: Optional[GitManager] = None


def get_git_manager(reload: bool = False) -> GitManager:
    """Get the global git manager instance.
    
    Args:
        reload: If True, create a new manager instance
        
    Returns:
        GitManager instance
    """
    global _git_manager
    if _git_manager is None or reload:
        _git_manager = GitManager()
    return _git_manager

# Made with Bob
