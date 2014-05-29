# Modified from Console.py to make it searching DLLs in sub-folder
import os
import sys
import zipimport

sys.frozen = True
sys.path = sys.path[:2]
# Changes
sys.path.append(os.path.join(DIR_NAME, 'lib'))
sys.path.append(os.path.join(DIR_NAME, 'lib/library.zip'))

m = __import__("__main__")
importer = zipimport.zipimporter(INITSCRIPT_ZIP_FILE_NAME)
if INITSCRIPT_ZIP_FILE_NAME != SHARED_ZIP_FILE_NAME:
    moduleName = m.__name__
else:
    name, ext = os.path.splitext(os.path.basename(os.path.normcase(FILE_NAME)))
    moduleName = "%s__main__" % name
code = importer.get_code(moduleName)
exec(code, m.__dict__)

versionInfo = sys.version_info[:3]
if versionInfo >= (2, 5, 0) and versionInfo <= (2, 6, 4):
    module = sys.modules.get("threading")
    if module is not None:
        module._shutdown()

