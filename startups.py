#!/usr/bin/python3
# -*- coding: utf-8 -*-

import collections
import enum
import logging
import random


class Entreprise(enum.Enum):

    giraffe_beer = 5
    bowwow_games = 6
    flamingo_soft = 7
    octo_coffee = 8
    hippo_powertech = 9
    elephant_mars_travel = 10


class Action:

    def __init__(self, entreprise):
        self._entreprise = entreprise
        self._valeur = 0

    def __repr__(self):
        retour = "{}[0x{:x}({!r}".format(
            self.__class__.__name__, id(self), self._entreprise.name)
        if self._valeur != 0:
            retour += " → {}€".format(self._valeur)
        retour += ")"
        return retour

    def __str__(self):
        retour = "{}({!r}".format(
            self.__class__.__name__, self._entreprise.name)
        if self._valeur != 0:
            retour += " → {}€".format(self._valeur)
        retour += ")"
        return retour

    @property
    def entreprise(self):
        """Entreprise dont l'Action est une part du capital
        """
        return self._entreprise

    @property
    def valeur(self):
        """Argent actuellement déposé sur l'action (au marché, donc)
        """
        return self._valeur

    def rétribuer(self):
        """Augmente la valeur de l'action d'une unité
        """
        self._valeur += 1

    def purger_dividendes(self):
        """Passe la valeur à 0
        """
        self._valeur = 0


class Joueur:

    def __init__(self, nom):
        self._nom = nom
        self.main = list()
        self.actions = collections.Counter()

        self.pioche = None
        self.marché = None
        self.richesse = None
        self.points = 0
        self.majorités = set()

    @property
    def nom(self):
        """Identifiant du joueur"""
        return self._nom

    def initier_manche(self, main, pioche, marché):
        self.main = main
        self.actions.clear()
        self.pioche = pioche
        self.marché = marché
        self.richesse = 10
        self.majorités.clear()

    def jouer(self):
        raise NotImplementedError

    def est_majoritaire(self, entreprise):
        retour = entreprise in self.majorités
        return retour

    def devient_majoritaire(self, entreprise):
        logging.info("{} devient majoritaire sur {}".format(
            self.nom, entreprise.name))
        self.majorités.add(entreprise)

    def perd_majorité(self, entreprise):
        self.majorités.remove(entreprise)

    def afficher_portefeuille(self):
        lignes = list()
        for e in Entreprise:
            if self.actions[e] != 0:
                ligne = "{} x{}".format(e, self.actions[e])
                if e in self.majorités:
                    ligne += " (majoritaire)"
                lignes.append(ligne)
        retour = "\n".join(lignes)
        return retour

    def afficher_main(self):
        retour = " / ".join([str(a.entreprise) for a in self.main])
        return retour

    def _augmenter_portefeuille(self, action):
        """Le fait que nous détenions l'action devient public.

        Peut-être même deviendra-t-on majoritaire… mais je ne peux pas le
        décider seul.
        """
        logging.info("{} ajoute une action {} à son portefeuille".format(
            self.nom, action.entreprise))
        self.actions.update([action.entreprise])

    def _mettre_au_marché(self, action):
        """Reverser une action au marché
        """
        logging.info("{} reverse une action {} au marché".format(
            self.nom, action.entreprise))
        self.marché.append(action)

    def _marché_réel(self):
        """Marché limité aux entreprises pour lesquelles on n'a pas la majorité
        """
        retour = [a for a in self.marché if a.entreprise not in self.majorités]
        return retour

    def _coût_piocher(self):
        """Coût que représenterait l'action de piocher
        """
        retour = len(self._marché_réel())
        return retour

    def _piocher(self):
        retour = self.pioche.pop()
        return retour


class Humain(Joueur):
    pass


class Robot(Joueur):

    def jouer(self):
        logging.debug(self.afficher_main())

        marché = self._marché_réel()
        peut_piocher = (self.richesse >= len(marché))
        peut_prendre = (len(marché) > 0)

        # Le jeu est ainsi fait qu'on a toujours une option de jeu (tout de
        # même !)
        piocher = False
        if peut_piocher:
            if peut_prendre:
                piocher = (random.randrange(2) == 1)
            else:
                piocher = True

        if piocher:
            logging.info("{} pioche".format(self.nom))
            # On pioche (ce suspense !)
            for m in marché:
                m.rétribuer()
            self.richesse -= len(marché)
            action = self._piocher()
        else:
            # On prend une carte au marché
            action = random.sample(marché, 1)[0]
            logging.info("{} récupère une action {} au marché".format(
                self.nom, action.entreprise))
            self.marché.remove(action)
            self.richesse += action.valeur
            action.purger_dividendes()

        # …on ajoutera l'action récupérée un peu plus tard à notre main…

        # Il faut maintenant soit jouer une carte, soit en remettre une au
        # marché
        if random.randrange(2) == 1:
            # On joue une carte
            self.main.append(action)
            action = random.sample(self.main, 1)[0]
            self.main.remove(action)
            self._augmenter_portefeuille(action)
        else:
            # On restitue une carte au marché… sauf celle que l'on y a prise le
            # cas échéant
            if not piocher:
                action2 = random.sample(self.main, 1)[0]
                self.main.remove(action2)
                self._mettre_au_marché(action2)
                self.main.append(action)
            else:
                self.main.append(action)
                action2 = random.sample(self.main, 1)[0]
                self.main.remove(action2)
                self._mettre_au_marché(action2)


def constituer_jeu():
    retour = list()

    for e in Entreprise:
        for i in range(e.value):
            retour.append(Action(e))

    retour = random.sample(retour, len(retour) - 5)
    random.shuffle(retour)

    return retour


def afficher_portefeuilles(joueurs):
    """Affiche les portefeuilles sous forme de tableau à deux entrées
    """
    largeurs = list()
    largeurs.append(max([len(e.name) for e in Entreprise]))
    largeurs.extend([len(j.nom) for j in joueurs])

    lignes = list()
    lignes.append("")

    affs = ["{{:{}}}".format(l) for l in largeurs]
    ligne = " | ".join(map(lambda x: x[0].format(
        x[1]), zip(affs, [""] + [j.nom for j in joueurs])))
    lignes.append(ligne)

    affs = ["{{:-<{}}}".format(l) for l in largeurs]
    ligne = "-+-".join(map(lambda x: x[0].format(x[1]),
                           zip(affs, [""] * (1 + len(joueurs)))))
    lignes.append(ligne)

    affs = ["{{:^{}}}".format(l) for l in largeurs]
    for e in Entreprise:
        données = [e.name]
        for j in joueurs:
            if e in j.majorités:
                d = "*{}".format(j.actions[e])
            else:
                d = j.actions[e]
            données.append(d)
        ligne = " | ".join(
            map(lambda x: x[0].format(x[1]), zip(affs, données)))
        lignes.append(ligne)

    logging.info("\n".join(lignes))


def jouer_manche(joueurs):
    # Mise-en-place
    jeu = constituer_jeu()
    pioche = jeu[3 * len(joueurs):]
    marché = list()
    for i, j in enumerate(joueurs):
        j.initier_manche(jeu[3 * i: 3 * (i + 1)], pioche, marché)

    # Tour-par-tour
    actif = 0
    while len(pioche) > 0:
        j = joueurs[actif]

        logging.info("Tour de {}".format(j.nom))

        # Affichage des portefeuilles
        afficher_portefeuilles(joueurs)

        # Tour à proprement parler
        j.jouer()

        # Vérification des majorités
        for e in Entreprise:
            n = [j.actions[e] for j in joueurs]
            m = max(n)
            if n.count(m) == 1 and n[actif] == m:
                for k in joueurs:
                    if k.est_majoritaire(e):
                        k.perd_majorité(e)
                j.devient_majoritaire(e)

        # Fin du tour
        actif += 1
        if actif == len(joueurs):
            actif = 0

    # Ajout des mains aux portefeuilles
    logging.info("Pioche épuisée → intégration des mains aux portefeuilles")
    for j in joueurs:
        j.actions.update([a.entreprise for a in j.main])
        j.main.clear()
    logging.info(afficher_portefeuilles(joueurs))

    # Paiement des dividendes
    for e in Entreprise:
        logging.info("Paiement pour {}".format(e.name))
        n = [j.actions[e] for j in joueurs]
        m = max(n)
        if n.count(m) != 1:
            logging.info("Pas de majorité → aucun paiement")
        else:
            vainqueur = joueurs[n.index(m)]
            total = 0
            for j in joueurs:
                if j is not vainqueur and e in j.actions:
                    logging.info("{} paie {}".format(j.nom, m - j.actions[e]))
                    j.richesse -= m - j.actions[e]
                    total += m - j.actions[e]
            total *= 3
            logging.info("{} reçoit {}".format(vainqueur.nom, total))
            vainqueur.richesse += total

    # Attribution des points de victoire
    joueurs.sort(key=lambda j: j.richesse, reverse=True)
    for j in joueurs:
        logging.info("{} termine à {}€".format(j.nom, j.richesse))
    joueurs[0].points += 2
    joueurs[1].points += 1
    joueurs[-1].points -= 1


def lancer_partie(nb_joueurs, humain, nb_manches):
    # Création des joueurs
    joueurs = list()
    for i in range(nb_joueurs):
        if humain == i + 1:
            joueurs.append(Humain("humain"))
        else:
            joueurs.append(Robot("Robot n°{}".format(i)))

    # Manches
    for i in range(nb_manches):
        jouer_manche(joueurs)

    # Affichage du vainqueur
    joueurs.sort(key=lambda j: j.points, reverse=True)
    for j in joueurs:
        logging.info("{} termine à {} points".format(j.nom, j.points))


if __name__ == "__main__":
    random.seed(1977)
    logging.basicConfig(level=logging.DEBUG)

    lancer_partie(4, 0, 1)
