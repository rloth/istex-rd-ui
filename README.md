WEBUI pour les programmes istex-rd
==================================
**Une appli web a lancer en local pour visualiser les résultats des traitements istex-rd**

Pour l'instant, c'est juste une interface html pour les évaluations de la résolution bib-findout.

Mise en place et lancement
--------------------------
La première fois, il faut installer le framework flask (publication web pour python):


```
pip3 install --user flask
```

Ensuite, chaque fois qu'on veut travailler par l'interface on la lance par


```
python3 run_ui.py
```

Le serveur devient alors accessible depuis un navigateur sur l'adresse `http://localhost:5000`.


Evaluation des résultats de test_findout
-----------------------------------------
### Principe

Pour chaque refbib de chaque document, on a lancé une série de requêtes visant à retrouver la refbib dans la base istex (pour plus d'infos, cf. `refbibs-stack/bib-findout-api`)

L'interface affiche un formulaire d'évaluation des résultats obtenus par ces requêtes. Le formulaire affiche la refbib d'origine, la requête lancée et le résultat, avec une case à cocher (est-ce que c'est bien la bonne refbib ?).

### Préalable à faire une fois
Éditer le champ `fixture_dir` dans le fichier `ui.config` pour que l'interface sache où prendre les données d'évaluation.

Idem pour le champ `eval_results_dir` pour qu'il sache où sauvegarder les résultats des formulaires.

Exemple:

```
[evaluation_findout]

fixture_dir=/chemin/vers/les/données/mes_50.resolution.d
eval_results_dir=/home/loth/gitz/refbibs-stack/bib-findout-api/mes_50.évalués.d
```

Après modification de `ui.config` on relance `run_ui.py` et on accède par navigateur à la liste des documents et aux formulaires d'évaluation pour chaque document.
