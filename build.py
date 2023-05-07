import PyInstaller.__main__
from shutil import rmtree  
from os import remove, path

if __name__ == '__main__':
    PyInstaller.__main__.run([
        'rummy.py',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--icon',
        path.join('images', 'rummy.ico'),
        '--add-data',
        'images;images',
        '--distpath',
        ''
    ])
    rmtree('build')
    remove('rummy.spec')