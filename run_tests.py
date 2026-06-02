"""
Script de ejemplo para ejecutar tests
"""
import subprocess
import sys


def run_all_tests():
    """Ejecutar todos los tests con cobertura"""
    print("🧪 Ejecutando suite completa de tests...")
    result = subprocess.run([
        "pytest",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ])
    return result.returncode


def run_integration_tests():
    """Ejecutar solo tests de integración"""
    print("🔗 Ejecutando tests de integración...")
    result = subprocess.run([
        "pytest",
        "tests/integration/",
        "-v"
    ])
    return result.returncode


def run_concurrency_tests():
    """Ejecutar solo tests de concurrencia"""
    print("⚡ Ejecutando tests de concurrencia...")
    result = subprocess.run([
        "pytest",
        "tests/concurrency/",
        "-v"
    ])
    return result.returncode


def run_quick_tests():
    """Ejecutar tests rápidos (sin cobertura)"""
    print("⚡ Ejecutando tests rápidos...")
    result = subprocess.run([
        "pytest",
        "-v",
        "--tb=short"
    ])
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            exit_code = run_all_tests()
        elif command == "integration":
            exit_code = run_integration_tests()
        elif command == "concurrency":
            exit_code = run_concurrency_tests()
        elif command == "quick":
            exit_code = run_quick_tests()
        else:
            print(f"❌ Comando desconocido: {command}")
            print("Comandos disponibles: all, integration, concurrency, quick")
            exit_code = 1
    else:
        print("📋 Uso: python run_tests.py [all|integration|concurrency|quick]")
        print("")
        print("Comandos:")
        print("  all          - Ejecutar todos los tests con cobertura")
        print("  integration  - Ejecutar solo tests de integración")
        print("  concurrency  - Ejecutar solo tests de concurrencia")
        print("  quick        - Ejecutar tests rápidos sin cobertura")
        exit_code = 0
    
    sys.exit(exit_code)
