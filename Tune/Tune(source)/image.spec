# -*- mode: python -*-

block_cipher = None


a = Analysis(['image.py'],
             pathex=['C:\\Users\\Sheldon\\Documents\\GitHub\\Beacon18\\Tune(source)'],
             binaries=[],
             datas=[('C:\\Users\\Sheldon\\Documents\\GitHub\\Beacon18\\Tune(source)\\image','image')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['gtk', 'PyQt4', 'PyQt5', 'wx'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Tune',
          debug=False,
          strip=False,
          upx=False,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='Tune')
