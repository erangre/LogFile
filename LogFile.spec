# -*- mode: python -*-

block_cipher = None


a = Analysis(['LogFile.py'],
             pathex=['C:\\GitHub\\LogFile'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['epics'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='LogFile',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='icons\\google_notebook.ico')
