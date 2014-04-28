import os
import glob
uicpath = 'pyside-uic'
os.chdir(os.path.dirname(__file__))
os.chdir('../ui')
for i in glob.glob('*.ui'):
    os.system(uicpath+' -o %s -x %s' % (i.split('.')[0]+'_ui.py', i))
              
for i in glob.glob('*.py'):
    if not i.endswith('_ui.py'): continue
    with open(i, 'r', encoding='utf-8') as f:
        new = []
        for l in f:
            # resource will be imported in ui.__init__
            if l.startswith('import icons_rc'): continue
            if l.startswith('from') and not l.startswith('from PySide'):
                l = l.replace('from ', 'from .')
            new.append(l)
        new = ''.join(new)

    with open(i, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new)