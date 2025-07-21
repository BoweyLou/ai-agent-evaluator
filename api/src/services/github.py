import httpx
from typing import List, Dict, Any
from pathlib import Path
import base64
import json
from ..core.config import settings


class GitHubService:
    """GitHub integration for managing evaluation branches"""
    
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO
        self.base_url = "https://api.github.com"
        
        if not self.token or not self.repo:
            raise ValueError("GitHub token and repository must be configured")
    
    async def prepare_evaluation_branches(self, eval_id: str, task_id: str, agents: List[str]):
        """Create GitHub branches for each agent in an evaluation"""
        
        async with httpx.AsyncClient() as client:
            # Get main branch SHA
            main_sha = await self._get_main_branch_sha(client)
            
            # Create evaluation base branch
            base_branch = f"{settings.GITHUB_BRANCH_PREFIX}-{eval_id}"
            await self._create_branch(client, base_branch, main_sha)
            
            # Copy task baseline files to the branch
            await self._setup_task_workspace(client, base_branch, task_id)
            
            # Create agent-specific branches
            for agent in agents:
                agent_branch = f"{base_branch}-{agent}"
                branch_sha = await self._get_branch_sha(client, base_branch)
                await self._create_branch(client, agent_branch, branch_sha)
                
                # Create agent instructions file
                await self._create_agent_instructions(client, agent_branch, eval_id, task_id, agent)
    
    async def get_branch_files(self, branch_name: str) -> Dict[str, str]:
        """Get all files from a specific branch"""
        
        async with httpx.AsyncClient() as client:
            files = {}
            
            # Get branch contents
            url = f"{self.base_url}/repos/{self.repo}/contents"
            headers = {"Authorization": f"token {self.token}"}
            
            response = await client.get(f"{url}?ref={branch_name}", headers=headers)
            
            if response.status_code == 200:
                contents = response.json()
                
                for item in contents:
                    if item["type"] == "file":
                        # Get file content
                        file_response = await client.get(item["download_url"])
                        if file_response.status_code == 200:
                            files[item["name"]] = file_response.text
            
            return files
    
    async def reset_evaluation_branches(self, eval_id: str, agents: List[str]):
        """Reset evaluation branches by deleting them"""
        
        async with httpx.AsyncClient() as client:
            # Delete agent branches
            for agent in agents:
                branch_name = f"{settings.GITHUB_BRANCH_PREFIX}-{eval_id}-{agent}"
                await self._delete_branch(client, branch_name)
            
            # Delete base evaluation branch
            base_branch = f"{settings.GITHUB_BRANCH_PREFIX}-{eval_id}"
            await self._delete_branch(client, base_branch)
    
    async def _get_main_branch_sha(self, client: httpx.AsyncClient) -> str:
        """Get the SHA of the main branch"""
        url = f"{self.base_url}/repos/{self.repo}/git/refs/heads/main"
        headers = {"Authorization": f"token {self.token}"}
        
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["object"]["sha"]
        else:
            raise Exception(f"Failed to get main branch SHA: {response.text}")
    
    async def _get_branch_sha(self, client: httpx.AsyncClient, branch_name: str) -> str:
        """Get the SHA of a specific branch"""
        url = f"{self.base_url}/repos/{self.repo}/git/refs/heads/{branch_name}"
        headers = {"Authorization": f"token {self.token}"}
        
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["object"]["sha"]
        else:
            raise Exception(f"Failed to get branch SHA for {branch_name}: {response.text}")
    
    async def _create_branch(self, client: httpx.AsyncClient, branch_name: str, sha: str):
        """Create a new branch"""
        url = f"{self.base_url}/repos/{self.repo}/git/refs"
        headers = {"Authorization": f"token {self.token}"}
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        
        response = await client.post(url, headers=headers, json=data)
        if response.status_code not in [200, 201]:
            # Branch might already exist, which is okay
            if "already exists" not in response.text:
                raise Exception(f"Failed to create branch {branch_name}: {response.text}")
    
    async def _delete_branch(self, client: httpx.AsyncClient, branch_name: str):
        """Delete a branch"""
        url = f"{self.base_url}/repos/{self.repo}/git/refs/heads/{branch_name}"
        headers = {"Authorization": f"token {self.token}"}
        
        response = await client.delete(url, headers=headers)
        # 404 is okay (branch doesn't exist)
        if response.status_code not in [200, 204, 404]:
            print(f"Warning: Failed to delete branch {branch_name}: {response.text}")
    
    async def _setup_task_workspace(self, client: httpx.AsyncClient, branch_name: str, task_id: str):
        """Copy task baseline files to the workspace"""
        
        task_dir = Path(settings.TASKS_DIR) / task_id / "baseline"
        if not task_dir.exists():
            return
        
        # Create workspace directory structure
        workspace_files = []
        
        for file_path in task_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(task_dir)
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Encode content for GitHub API
                encoded_content = base64.b64encode(content).decode('utf-8')
                
                workspace_files.append({
                    "path": f"workspace/{relative_path}",
                    "content": encoded_content,
                    "encoding": "base64"
                })
        
        # Create files in the branch
        for file_info in workspace_files:
            await self._create_file(client, branch_name, file_info["path"], file_info["content"])
    
    async def _create_agent_instructions(
        self, 
        client: httpx.AsyncClient, 
        branch_name: str, 
        eval_id: str, 
        task_id: str, 
        agent: str
    ):
        """Create agent-specific instructions file"""
        
        # Load task config to get agent prompt
        task_config_path = Path(settings.TASKS_DIR) / task_id / "config.yaml"
        if task_config_path.exists():
            import yaml
            with open(task_config_path) as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        task_info = config.get("task", {})
        agent_prompt = config.get("agents", {}).get(agent, "Complete the task as described.")
        
        instructions = f"""# {agent.title()} Evaluation Instructions

## Evaluation ID: {eval_id}
## Task: {task_info.get('name', task_id)}

### Description
{task_info.get('description', 'No description available')}

### Your Task
{agent_prompt}

### Instructions
1. Navigate to the `workspace/` directory
2. Complete the task according to the prompt above
3. Commit your changes with a descriptive message
4. Push your changes to this branch
5. Mark the task as complete in the evaluation interface

### Files to Work With
All baseline files are in the `workspace/` directory. Modify these files as needed to complete the task.

### Commit Your Work
```bash
git add workspace/
git commit -m "feat: {agent} solution for {task_id}"
git push origin {branch_name}
```

Good luck!
"""
        
        # Encode and create the file
        encoded_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        await self._create_file(client, branch_name, "INSTRUCTIONS.md", encoded_content)
    
    async def _create_file(self, client: httpx.AsyncClient, branch_name: str, file_path: str, content: str):
        """Create a file in the specified branch"""
        url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
        headers = {"Authorization": f"token {self.token}"}
        
        data = {
            "message": f"Add {file_path}",
            "content": content,
            "branch": branch_name
        }
        
        response = await client.put(url, headers=headers, json=data)
        if response.status_code not in [200, 201]:
            print(f"Warning: Failed to create file {file_path}: {response.text}")


# Mock implementation for testing without GitHub
class MockGitHubService(GitHubService):
    """Mock GitHub service for testing"""
    
    def __init__(self):
        pass  # Skip token validation
    
    async def prepare_evaluation_branches(self, eval_id: str, task_id: str, agents: List[str]):
        print(f"Mock: Prepared branches for {eval_id} with agents: {agents}")
    
    async def get_branch_files(self, branch_name: str) -> Dict[str, str]:
        # Return mock files for testing
        return {
            "index.html": "<html><body>Mock content</body></html>",
            "style.css": "body { color: blue; }"
        }
    
    async def reset_evaluation_branches(self, eval_id: str, agents: List[str]):
        print(f"Mock: Reset branches for {eval_id}")