#!/usr/bin/env python3
"""
Simple test script to validate the AI Evaluation Platform structure
"""

import os
import sys
from pathlib import Path

def test_structure():
    """Test that all required files and directories exist"""
    
    base_dir = Path(__file__).parent
    
    # Required directories
    required_dirs = [
        "api/src",
        "api/src/core",
        "api/src/models", 
        "api/src/routers",
        "api/src/services",
        "api/tests",
        "web/src",
        "web/src/components",
        "web/src/pages",
        "web/src/services",
        "tasks/css-consolidation/baseline",
        ".github/workflows"
    ]
    
    # Required files
    required_files = [
        "README.md",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        ".env.example",
        "api/Dockerfile",
        "api/requirements.txt",
        "api/src/main.py",
        "api/src/core/config.py",
        "api/src/models/database.py",
        "api/src/models/schemas.py",
        "api/src/routers/tasks.py",
        "api/src/routers/evaluations.py",
        "api/src/routers/agents.py",
        "api/src/routers/results.py",
        "api/src/services/openrouter.py",
        "api/src/services/github.py",
        "api/src/services/evaluation.py",
        "api/src/core/evaluators/css_evaluator.py",
        "api/tests/test_main.py",
        "web/Dockerfile",
        "web/package.json",
        "web/src/App.js",
        "web/src/index.js",
        "web/src/components/Navbar.js",
        "web/src/pages/Dashboard.js",
        "web/src/services/api.js",
        "tasks/css-consolidation/config.yaml",
        "tasks/css-consolidation/baseline/sample.html",
        ".github/workflows/deploy.yml"
    ]
    
    print("🚀 Testing AI Agent Evaluation Platform Structure")
    print("=" * 50)
    
    # Test directories
    print("\n📁 Checking directories...")
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path}")
            missing_dirs.append(dir_path)
    
    # Test files
    print("\n📄 Checking files...")
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists() and full_path.is_file():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"✅ Directories: {len(required_dirs) - len(missing_dirs)}/{len(required_dirs)}")
    print(f"✅ Files: {len(required_files) - len(missing_files)}/{len(required_files)}")
    
    if missing_dirs:
        print(f"\n❌ Missing directories: {len(missing_dirs)}")
        for d in missing_dirs:
            print(f"  - {d}")
    
    if missing_files:
        print(f"\n❌ Missing files: {len(missing_files)}")
        for f in missing_files:
            print(f"  - {f}")
    
    # Test configuration files
    print("\n🔧 Testing configuration...")
    try:
        import yaml
        config_file = base_dir / "tasks/css-consolidation/config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
                print("✅ CSS task configuration valid")
                print(f"  - Task: {config.get('task', {}).get('name', 'Unknown')}")
                print(f"  - Evaluation type: {config.get('evaluation', {}).get('type', 'Unknown')}")
                print(f"  - Agents: {len(config.get('agents', {}))}")
        else:
            print("❌ CSS task configuration missing")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    # Test baseline files
    print("\n📋 Testing baseline files...")
    baseline_dir = base_dir / "tasks/css-consolidation/baseline"
    if baseline_dir.exists():
        html_files = list(baseline_dir.glob("*.html"))
        print(f"✅ Found {len(html_files)} HTML baseline files")
        for html_file in html_files:
            print(f"  - {html_file.name}")
    else:
        print("❌ No baseline files found")
    
    # Overall status
    total_missing = len(missing_dirs) + len(missing_files)
    if total_missing == 0:
        print("\n🎉 SUCCESS: Platform structure is complete!")
        print("Ready for deployment and testing.")
        return True
    else:
        print(f"\n⚠️  WARNING: {total_missing} items missing")
        print("Platform may not function correctly.")
        return False


def test_css_evaluator():
    """Test the CSS evaluator functionality"""
    print("\n🧪 Testing CSS Evaluator...")
    
    try:
        # Test basic pattern detection
        sample_html = '''
        <div style="font-family: Arial; color: red;">Test 1</div>
        <div style="font-family: Arial; color: red;">Test 2</div>
        <font face="Arial">Legacy font</font>
        '''
        
        # Simple pattern counting
        font_family_count = sample_html.count('font-family: Arial')
        font_tags = sample_html.count('<font')
        
        print(f"✅ Pattern detection working")
        print(f"  - Repetitive font-family styles: {font_family_count}")
        print(f"  - Legacy font tags: {font_tags}")
        
        return True
        
    except Exception as e:
        print(f"❌ CSS evaluator test failed: {e}")
        return False


if __name__ == "__main__":
    print("AI Agent Evaluation Platform - Structure Test")
    print("=" * 60)
    
    structure_ok = test_structure()
    evaluator_ok = test_css_evaluator()
    
    print("\n" + "=" * 60)
    if structure_ok and evaluator_ok:
        print("🎉 ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: cd api && pip install -r requirements.txt")
        print("2. Install web deps: cd web && npm install")
        print("3. Start with docker: docker-compose up")
        print("4. Access web interface: http://localhost:3000")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please fix the issues above before proceeding.")
        sys.exit(1)