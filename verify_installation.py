#!/usr/bin/env python3
"""
Installation verification script for QuailTrail
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 10):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected. QuailTrail requires Python 3.10+")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
    return True

def check_quail_import():
    """Check if QuailTrail can be imported"""
    print("\n📦 Checking QuailTrail import...")
    
    try:
        import quail
        print(f"✅ QuailTrail imported successfully (version: {getattr(quail, '__version__', 'unknown')})")
        return True
    except ImportError as e:
        print(f"❌ Failed to import QuailTrail: {e}")
        return False

def check_cli_availability():
    """Check if QuailTrail CLI is available"""
    print("\n🔧 Checking CLI availability...")
    
    try:
        # Test both entry points
        result1 = subprocess.run(['quail', '--help'], capture_output=True, text=True, timeout=10)
        if result1.returncode == 0:
            print("✅ 'quail' command available")
            cli_available = True
        else:
            print("❌ 'quail' command not available")
            cli_available = False
            
        result2 = subprocess.run(['python', '-m', 'quail', '--help'], capture_output=True, text=True, timeout=10)
        if result2.returncode == 0:
            print("✅ 'python -m quail' command available")
            return cli_available or True
        else:
            print("❌ 'python -m quail' command not available")
            return cli_available
            
    except subprocess.TimeoutExpired:
        print("❌ CLI command timed out")
        return False
    except FileNotFoundError:
        print("❌ CLI command not found in PATH")
        return False

def check_core_modules():
    """Check if core QuailTrail modules can be imported"""
    print("\n🧩 Checking core modules...")
    
    modules = [
        ('quail.core', 'Core engine'),
        ('quail.cli', 'CLI interface'),
        ('quail.orm', 'ORM decorators'),
        ('quail.graph', 'Dependency graph'),
    ]
    
    all_good = True
    for module_name, description in modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {description} ({module_name})")
        except ImportError as e:
            print(f"❌ {description} ({module_name}): {e}")
            all_good = False
    
    return all_good

def check_optional_dependencies():
    """Check optional dependencies"""
    print("\n🔗 Checking optional dependencies...")
    
    optional_deps = [
        ('sqlalchemy', 'Database support'),
        ('mongoengine', 'MongoDB support'),
        ('pandas', 'Analytics support'),
        ('psycopg2', 'PostgreSQL support'),
    ]
    
    for module_name, description in optional_deps:
        try:
            importlib.import_module(module_name)
            print(f"✅ {description} ({module_name})")
        except ImportError:
            print(f"⚠️  {description} ({module_name}) - Optional, not installed")

def run_simple_test():
    """Run a simple QuailTrail functionality test"""
    print("\n🧪 Running simple functionality test...")
    
    try:
        from quail.core import qtask, qcheck
        
        @qtask(id="test_task")
        def test_task(ctx):
            return {"test": "success"}
        
        @qcheck(id="test_check", requires=["test_task"])
        def test_check(ctx):
            from quail.core import CheckResult
            return CheckResult(
                id="test_check",
                status="pass",
                description="Simple test check"
            )
        
        print("✅ Task and check decorators working")
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all installation verification checks"""
    print("🔍 QuailTrail Installation Verification")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_quail_import,
        check_cli_availability,
        check_core_modules,
        run_simple_test,
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    # Optional dependencies check (doesn't affect overall result)
    check_optional_dependencies()
    
    print("\n" + "=" * 50)
    print("📊 Installation Verification Results:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} core checks passed!")
        print("\n🎉 QuailTrail is properly installed and ready to use!")
        print("\nNext steps:")
        print("  • Run 'quail --help' to see CLI options")
        print("  • Use 'quail nest <project_name>' to create a new project")
        print("  • Check documentation at: https://github.com/lbundalian/quail")
        return 0
    else:
        print(f"❌ {total - passed} of {total} checks failed")
        print("\n💡 Try:")
        print("  • Reinstalling: pip uninstall quailtrail && pip install -e .")
        print("  • Installing with dependencies: pip install -e '.[all]'")
        print("  • Checking Python version compatibility (3.10+ required)")
        return 1

if __name__ == "__main__":
    sys.exit(main())