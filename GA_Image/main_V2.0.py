import random
import numpy as np
import time


# imBMP (image bitmap) class qui represente une image d'un fichier bitmap
# (oui le bitmap c'est pas opti, mais comme ça je peux directement prendre les bytes en memoire)

class imBMP:

    # name: le path vers l'image
    # core: c'est la partie qui represente les données des pixels
    # start: l'indice a partire du quel commence les données des pixels
    # end: l'indice a partire du quel finit les données des pixels
    # header: les données de l'entête du fichier
    # tailer: les données de fin du fichier
    #
    # note--les  liste de données contiennent des int entre 0 et 255 (1o)
    def __init__(self, path):
        self.name = path
        self.core = []
        self.start = 0
        self.end = 0
        self.header = []
        self.tail = []

    # prend un autre object imBMP en arg
    # return tous les indices où les valeurs des bytes sont differents entre les deux fichiers
    # en pratique cela permet de determiner toutes les propriétées du fichier et de les attribuer a l'object appelant
    # !!!!!!! A APPELER IMPERATIVEMENT AVANT DE COMMENCE L'ALGO
    def dif(self, other_file):
        file1 = open(self.name, "rb")
        file2 = open(other_file.name, "rb")
        i = 0
        difs = []
        while 1:
            r1, r2 = file1.read(1), file2.read(1)
            if len(r1) == 0 or len(r2) == 0:
                break
            if r2 != r1:
                difs.append(i)
            i += 1
        file1.close()
        file2.close()
        self.start = difs[0]
        self.end = difs[-1] + 1
        self.setCore()
        self.header = list(self.getHeader()[0])
        self.tail = list(self.getTailer()[0])
        return difs

    # en connaissant start, return un bytes like object du header et un tableau contenant les valeurs hex du header
    def getHeader(self):
        file = open(self.name, "rb")
        headerByte = file.read(self.start)
        headerReadable = [hex(i)[2:].rjust(2, '0').upper() for i in list(headerByte)]
        return headerByte, headerReadable

    # pareil que getHeader() mais pour la fin de fichier
    def getTailer(self):
        file = open(self.name, "rb")
        file.seek(self.end, 0)
        tailByte = file.read()
        tailReadable = [hex(i)[2:].rjust(2, '0').upper() for i in list(tailByte)]
        return tailByte, tailReadable

    # remplie le param core (les données pixels) de l'object
    def setCore(self):
        file = open(self.name, "rb")
        file.seek(self.start, 0)
        self.core = list(file.read(self.end - self.start))
        return self.core


# class qui represente un "candidat" pour le processus de l'algo genetique
class candidat:

    # size: la taille de l'image*3 (3 bytes par pixels)
    # core: les données actuelle du candidat (au debut géneré en random)
    # score1 et score2: une memoire de la fonction d'evaluation pour la premiere moitie et seconde moitie du core respectivement
    # (la separation en deux parties est utile pour la fusion des deux candidats)
    def __init__(self, size):
        self.size = size
        self.core = []
        self.score = 0
        for i in range(size):
            self.core.append(random.randint(0, 255))

    # fonction de notation, imgRef est un imgBMP cible et update automatiquement les scores
    def notation(self, imgRef):

        for i in range(self.size):
            self.score += (self.core[i] - imgRef.core[i]) ** 2
        return self.score

    # mix deux candidats et met le resultat dans le candidat appelant
    def mix(self, base1, mem):
        for i in mem:
            self.core[i] = base1.core[i]
        self.score = base1.score
        return mem

    # random chance de muter, la mutation va changer d'un random dans [-span, span] et update automatiquement les scores
    def mutate(self, core, chance, span):
        mem = random.sample(range(self.size), k=np.random.binomial(self.size, chance))
        for i in mem:
            self.score -= (self.core[i] - core[i]) ** 2
            r = random.randint(-1 * span, span)
            self.core[i] += r
            self.core[i] = 0 if self.core[i] < 0 else (255 if self.core[i] > 255 else self.core[i])
            self.score += (self.core[i] - core[i]) ** 2
        return mem


# creer un fichier composer du header h, du core c et de la fin t
def creatFile(name, h, c, t):
    file = open(name, "wb")
    file.write(bytes(h))
    file.write(bytes(c))
    file.write(bytes(t))
    file.close()


# prend une liste de 6 candidats et va mixer les 3 meileurs pour remplacer les 3 pires +(mutation sur les nouveaux)
def fusion(core, set, mem):
    set.sort(key=lambda x: x.score)

    set[1].mix(set[0], mem)

    mem = set[1].mutate(core, 0.00007, 40)

    return mem

start=time.time()

# source: l'image source
# content border: une image de meme taille mais avec le coin haut droite et le coin bas gauche de couleur differents de l'image source
# (j'avais prevenu que c'etait un peu schlag, va faloir sortir paint)
# il faut bien que les images soit des .bmp
source = imBMP("Image/Juan/Source.bmp")
contentBorder = imBMP("Image/Juan/SourceC.bmp")

# appel a dif, permet d'initialiser toutes les données de l'image source
source.dif(contentBorder)


# creation des 6 candidats
classRoom = []
for i in range(2):
    classRoom.append(candidat(source.end - source.start))
    print(classRoom[i].notation(source))
print()
classRoom.sort(key=lambda x: x.score)
classRoom[1].core = classRoom[0].core.copy()


# boucle infini
#changeListMemory est une memoir des indices changés entre deux iterations, ça permet de "copier" le meilleur des
#deux sans avoir besoin de faire une copie complète
i = 0
changeListMemory = []
while 1:
    # ntation et fusion des candidats
    changeListMemory = fusion(source.core, classRoom, changeListMemory)

    # print et creer un fichier toutes les kème boucles
    k = 1000
    if i % k == 0:
        creatFile("Image/Juan/gen" + str(i) + ".bmp", source.header, classRoom[0].core, source.tail)
        print(i, int(classRoom[0].score / classRoom[0].size))
        # que une image finale de k-lité:
        testKli = int(classRoom[0].score / classRoom[0].size)
        if testKli <= 100:
            #     creatFile("Image/BigChungus/gen" + str(i) + ".bmp", source.header, classRoom[0].core, source.tail)
            break
    i += 1
print(time.time()-start)
