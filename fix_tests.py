"""Fix test files to use new SanskritMeshCompiler API."""
import os

os.chdir(r'c:\Users\com\Desktop\sanskrit')

# Fix test_core_layers.py
content = open('tests/test_core_layers.py').read()
content = content.replace(
    'from sanskrit_mesh.core.layers.entropy import EntropyLayer ; HyperCompiler = SanskritMeshCompiler',
    'from sanskrit_mesh import SanskritMeshCompiler'
)
content = content.replace('HyperCompiler(level=', 'SanskritMeshCompiler(level=')
open('tests/test_core_layers.py', 'w').write(content)

# Fix test_ir_contract.py
content = open('tests/test_ir_contract.py').read()
content = content.replace('from sanskrit_mesh import SanskritMeshCompiler', 'from sanskrit_mesh import SanskritMeshCompiler')
# Remove wrap_ir / unwrap_ir kwargs
content = content.replace(', wrap_ir=True, version="2.0.0"', '')
content = content.replace(', unwrap_ir=True', '')
open('tests/test_ir_contract.py', 'w').write(content)

# Fix test_v2.py
content = open('tests/test_v2.py').read()
content = content.replace('from sanskrit_mesh import SanskritMeshCompiler ; HyperCompiler, SanskritMeshCompiler', 'from sanskrit_mesh import SanskritMeshCompiler')
# The test_v2.py only imports at line 3, then uses hc_fixed = SanskritMeshCompiler directly
# But there may be extra ; statements
open('tests/test_v2.py', 'w').write(content)

# Fix benchmark.py  
content = open('tests/benchmark.py').read()
content = content.replace('from sanskrit_mesh.core.compiler import HyperCompiler', 'from sanskrit_mesh import SanskritMeshCompiler ; HyperCompiler = SanskritMeshCompiler')
open('tests/benchmark.py', 'w').write(content)

print('Done')