from batchclip import batchclip
import os, sys, pathlib

#python .\projetoclip.py D:\MA\Trabalhos\2022\Analuce\Esmeraldas
#python .\projetoclip.py D:\MA\Trabalhos\2022\Analuce\Esmeraldas CAR

def main():
	projeto = sys.argv[1]
	basedir = pathlib.Path(projeto).absolute().joinpath('SIG')
	IDEdir = pathlib.Path(r'D:\MA\Trabalhos\BASE-SIG\IDE-SISEMA-struct').absolute()

	if len(sys.argv) == 2:
		subfolders = ['UCs','Interesse','Teste','ZEE','hidro-completos','hidro-SoOsNomeados','Inventario-MG-split']
		createdirs(basedir, subfolders)
		for each in subfolders:
			batchclip(str(basedir) + '\\' + 'CLIP.shp',[str(IDEdir) +'\\'+each],str(basedir)+'\\'+each)

	if len(sys.argv) > 2:
		for t in range(2, len(sys.argv)):
			print(sys.argv[t])
			if sys.argv[t] == 'CAR':
				createdirs(basedir, ['CAR', 'CAR_split'])
				batchclip(str(basedir) + '\\' + 'CLIP.shp', [str(basedir) + '\\' + 'CAR'], str(basedir) + '\\' + 'CAR_split')
			if sys.argv[t] == 'UC':
				createdirs(basedir, ['UCs'])
				batchclip(str(basedir) + '\\' + 'CLIP.shp', [str(IDEdir) +'\\'+ 'UCs'], str(basedir) + '\\' + 'UCs')

def createdirs(basedir, subfolders):
	try:
		os.mkdir(basedir)
	except: pass
	for each in subfolders:
		dir = basedir.joinpath(each)
		try:
			os.mkdir(dir)
		except: pass

if __name__ == "__main__":
	main()