# Mon CLAUDE.md pesait 217 Ko. Le réduire de 76 % m'a fait perdre quatre règles sans que rien ne casse

Un fichier de contexte trop lourd coûte des tokens à chaque conversation. Le découper en README résout ce problème et en crée un autre, beaucoup plus discret.

Voici la mesure brute, sur mon dépôt de travail Joomla, entre deux commits que je peux vous nommer.

| | Avant | Après | Écart |
|---|---|---|---|
| Poids | 222 864 octets | 52 392 octets | **−76,5 %** |
| Lignes | 1 262 | 520 | −58,8 % |
| Tokens estimés par session | ~60 200 | ~14 200 | **−46 000** |

Quarante-six mille tokens récupérés à chaque démarrage de conversation. C'est le chiffre qui attire l'œil, et c'est le moins intéressant des deux.

Le vrai enseignement tient en une phrase : **quand une règle disparaît pendant le découpage, rien ne casse, rien ne prévient, et personne ne s'en aperçoit.**

J'en ai perdu quatre. Je les ai toutes récupérées, uniquement parce qu'un compteur tournait à chaque étape. Cet article explique ce compteur, et pourquoi il ne fonctionne que dans une configuration bien précise.

---

## Comment arrive-t-on à un fichier de 200 Ko ?

Par accumulation, jamais par décision. Et surtout, en ayant raison à chaque étape.

Un fichier comme `CLAUDE.md`, `AGENTS.md` ou `.cursorrules` est chargé intégralement au début de chaque conversation. Il porte les règles de travail, les conventions, les pièges déjà rencontrés. Personne ne se réveille un matin en décidant de l'alourdir. Il grossit par six mécanismes, tous raisonnables pris un par un.

### 1. L'incident qui gonfle en trois temps

C'est le mécanisme principal, et le plus difficile à combattre parce que chaque ajout est justifié.

Jour 1, vous venez de passer un après-midi sur un bug. Vous écrivez la règle.

```markdown
Ne jamais lire `request.POST` avant d'avoir vérifié la signature du webhook.
```

Une ligne. Parfait.

Deux semaines plus tard, un collègue demande pourquoi. Vous ajoutez l'explication, parce que répondre une fois dans le fichier vaut mieux que répondre trois fois sur la messagerie.

Trois mois plus tard, quelqu'un propose un refactor qui casserait exactement ça. Vous ajoutez les pistes déjà écartées, pour que la discussion ne recommence pas.

```markdown
### Vérification de signature des webhooks

Ne jamais lire `request.POST` avant d'avoir vérifié la signature.

Le framework consomme le flux brut au premier accès au corps parsé, donc la
signature ne correspond plus. On a mis un après-midi à le trouver, parce que
l'erreur remontait comme un rejet côté fournisseur et pas comme un problème
d'ordre d'appel.

On a envisagé de rebufferiser la requête dans un middleware global. Rejeté,
parce que ça alourdissait toutes les requêtes du site pour un seul endpoint.
On a aussi regardé le décorateur fourni par le SDK, qui fait exactement ça
mais suppose que l'endpoint est le seul consommateur du corps.
```

Une ligne devenue quatorze. Aucune des treize ajoutées n'est fautive. La personne qui les a écrites avait raison à chaque fois.

Sauf que **la règle, elle, tient toujours en une ligne.** Les treize autres sont de la mémoire d'équipe, et la mémoire d'équipe n'a pas besoin d'être rechargée à chaque conversation.

### 2. Le catalogue qui suit la croissance du projet

Au début vous avez trois composants. Vous les décrivez en quatre lignes chacun, ce qui fait douze lignes. Personne ne verra jamais un problème là-dedans.

Dix-huit mois plus tard vous en avez vingt-deux. Le même format donnerait quatre-vingt-huit lignes, sauf que personne n'est resté à quatre lignes. Ceux qui ont eu une histoire mouvementée en ont quinze.

Voilà le vrai discriminant, et il est simple à retenir. **Un catalogue grossit avec le projet. Un ensemble de règles, non.** Le nombre de choses que vous possédez augmente sans limite. Le nombre de réflexes à avoir avant d'agir reste à peu près stable.

Si une section grossit parce que le projet grossit, elle n'a rien à faire dans un fichier chargé en permanence.

### 3. Le journal collé en tête

Il commence par une date. Puis une phrase, pour dire ce qui a changé. Puis une deuxième, parce que la première était trop vague.

On voit régulièrement, dans des fichiers de contexte, un « Last updated » devenu **une seule ligne de plusieurs milliers de caractères**, où deux ans d'historique ont été concaténés entre parenthèses. Personne ne l'a décidé. Chacun a simplement ajouté sa parenthèse à la suite.

Ce contenu a une vraie valeur. Il n'en a aucune au démarrage de chaque conversation.

### 4. La documentation défensive

On écrit pour un lecteur imaginaire qui ne sait rien. Alors on explique ce qu'est une migration, à quoi sert une file de tâches, pourquoi on met les secrets dans une variable d'environnement.

Le lecteur réel est un modèle qui connaît déjà le framework mieux que vous ne le documenterez jamais. Ce qu'il ignore, c'est ce qui est **spécifique à votre projet**. Tout le reste occupe de la place sans rien apporter.

Test rapide sur un paragraphe : s'il serait vrai à l'identique sur n'importe quel autre projet du même stack, il est de trop.

### 5. La duplication qu'on ne voit pas

Passé une certaine taille, plus personne ne sait ce que le fichier contient déjà. Alors on rajoute la règle une deuxième fois, dans une autre section, avec une autre formulation.

Ce n'est pas de la négligence, c'est mécanique. Au-delà de quelques centaines de lignes, relire avant d'écrire coûte plus cher que réécrire.

### 6. Le collage de sortie brute

Un extrait de terminal, un fichier de configuration complet, une trace d'erreur de quarante lignes. C'est très rapide à coller et très lourd à porter. Le rapport entre le poids et l'information utile est catastrophique.

### L'arithmétique, sans rien exagérer

Prenez un projet actif, deux incidents documentés par semaine, dix à quinze lignes chacun une fois qu'ils ont gonflé selon le mécanisme numéro 1.

Sur dix-huit mois, ça fait environ cent cinquante incidents et **entre 1 500 et 2 000 lignes**. Ajoutez un catalogue qui suit la croissance, un journal en tête, et la documentation défensive des débuts.

Vous obtenez un fichier de plusieurs centaines de kilo-octets sans qu'aucune décision individuelle n'ait été mauvaise. C'est exactement pour ça que le problème passe inaperçu : il n'y a personne à blâmer et aucun moment où ça a dérapé.

### Comment savoir où ça se cache chez vous

Ne jugez pas au poids seul. Une grosse section peut être parfaitement légitime.

Le signal utile est le rapport entre le poids d'une section et le nombre de règles qu'elle contient. C'est ce que la commande `measure` affiche en dernière colonne (l'outil s'affiche en anglais : `size` = poids, `rules` = règles, `B/rule` = octets par règle).

```
                                           size   rules     B/rule
Composants                               80.8 KB      63       1313
Skills                                   39.9 KB      18       2268
Journal des versions                     10.4 KB       2       5320  <-- a story
```

Une section à quelques centaines d'octets par règle est dense, elle se défend. Une section à plusieurs milliers est une histoire avec une règle dedans, et c'est elle qu'il faut sortir en premier.

Le même fichier après extraction, sur les mêmes sections :

| Section | Avant | Après | Densité |
|---|---|---|---|
| Composants | 1 313 o/règle | 612 | 2,1 fois plus dense |
| Skills | 2 268 o/règle | 461 | 4,9 fois plus dense |
| Serveurs MCP | 1 510 o/règle | 483 | 3,1 fois plus dense |
| Journal | 5 320 o/règle | 878 | 6,1 fois plus dense |

Le fichier n'a pas seulement maigri. Chaque kilo-octet restant porte trois à cinq fois plus de règles qu'avant.

Une remarque honnête pour finir sur ce point. L'outil signale toujours une section à 4 543 octets par règle dans mon propre fichier, et je l'ai laissée. C'est l'arborescence du dépôt, qui sert à naviguer et pas à décider. Le ratio est un indicateur, pas un juge.

## Quel est le mode de panne exact ?

Une règle supprimée ne provoque aucune erreur. Elle cesse simplement de s'appliquer.

Comparez avec du code. Si vous supprimez une fonction utilisée ailleurs, l'application plante, le test rougit, vous corrigez dans la minute. Le signal est immédiat et bruyant.

Une règle de comportement n'a aucun de ces mécanismes. Vous la retirez du fichier, tout continue de fonctionner, les réponses restent plausibles. Trois semaines plus tard, le modèle prend une décision que vous auriez refusée, et vous ne reliez jamais cette décision à la ligne que vous avez déplacée un mardi soir.

C'est une panne silencieuse à effet différé. La pire catégorie qui soit, parce qu'elle ne laisse pas de trace à laquelle remonter.

## Comment transformer un tri subjectif en test ?

En choisissant un critère qu'on peut compter.

Voici celui que j'ai retenu : **une ligne reste dans le fichier de contexte si elle porte un impératif de comportement. Sinon elle part vers un README.**

Les marqueurs sont lexicaux et volontairement simples : `obligatoire`, `toujours`, `jamais`, `avant de`, `en cas de conflit`, `par défaut`, `ne pas`, `doit`, `il faut`, plus leurs équivalents anglais.

Ce critère n'est pas juste. Il attrape des lignes qui auraient pu partir, il en rate qui auraient dû rester. Ce n'est pas ce qu'on lui demande.

On lui demande d'être **comptable**. Je compte les lignes impératives avant une extraction, je recompte après, et si le nombre baisse je sais exactement quoi aller relire. Un critère imparfait mais mesurable bat un jugement fin mais invérifiable, parce que le second ne se contrôle pas à trois heures du matin après la quatrième section.

Le calcul d'empreinte tient en une ligne :

```python
fingerprint = re.sub(r'[^a-z0-9]', '', ligne.lower())[:60]
```

On ne garde que les soixante premiers caractères alphanumériques. La ponctuation, la casse et les accents disparaissent. Une ligne où vous déplacez un gras ou ajoutez une virgule reste reconnue. Une ligne supprimée ressort. C'est exactement le compromis voulu, parce qu'on cherche les disparitions et pas les retouches.

## Quelle est la procédure complète ?

Cinq étapes, dont une qui se répète.

**1. Mesurer.** Poids, lignes, tokens estimés, et surtout le poids de chaque section prise séparément. On attaque par la plus lourde.

```bash
python lm-context-diet.py measure CLAUDE.md
```

**2. Poser une baseline.** Le script enregistre l'empreinte de chaque ligne impérative dans un fichier JSON.

**3. Extraire une section. Une seule.** L'historique et les détails partent dans le README de l'élément concerné. Il reste une ligne d'index dans le fichier de contexte.

Et une contrainte qui n'a rien d'évident : **déplacez la phrase de règle telle quelle, ne la réécrivez pas dans la même passe.** J'ai fait l'erreur en préparant le jeu d'exemple de cet article. Une extraction où j'avais reformulé les règles en même temps que je les déplaçais rend 9 disparues et 9 nouvelles, donc rien d'exploitable. La même extraction avec les phrases recopiées à l'identique rend 5 disparues, toutes classables en quelques secondes.

Dans les deux cas, toutes les règles avaient survécu. Dans le premier, le contrôle ne pouvait plus le prouver. Si une règle doit être reformulée, faites-en une passe séparée, avec sa propre baseline.

**4. Recompter tout de suite.** Le script liste nommément les empreintes disparues et sort en code retour 1. Pour chaque ligne listée, il faut trancher : historique parti légitimement, ou règle à restaurer.

**5. Reboucler.** Nouvelle baseline, section suivante.

À la fin, un dernier contrôle sur les liens. Un lien d'index cassé rend le README inatteignable, donc la règle muette. C'est le même mode de panne par un autre chemin.

## Qu'est-ce que le compteur a réellement attrapé ?

Une règle qui existait encore, et qui ne servait plus.

Après l'extraction du bloc consacré à mes serveurs MCP, le compteur est passé de 81 à 78. Trois lignes manquaient. En les relisant, j'en ai trouvé une qui n'aurait jamais dû partir :

> **Toujours utiliser les classes natives Joomla (`Table\Category`, `Table\Content`, `Table\Menu`) via un script CLI. Jamais de SQL brut** pour créer menus, catégories ou articles.

Cette règle protège d'un bug précis. La table `#__menu` de Joomla est un arbre en nested set, avec des bornes `lft` et `rgt` qui doivent être recalculées à chaque insertion. Un `INSERT` direct ne les recalcule pas. Le menu se corrompt sans erreur SQL, et le symptôme apparaît plus tard, ailleurs, sous une forme méconnaissable.

Le détail qui fait toute la valeur du contrôle : **cette règle existait toujours** dans un fichier de gotchas, à l'autre bout du dépôt. Elle était parfaitement rédigée. Elle n'était simplement plus sur le chemin de chargement automatique, donc elle ne se déclenchait plus au bon moment.

J'insiste, parce que c'est le piège principal. **Chercher si le texte existe encore quelque part ne prouve rien.** La seule question qui compte est de savoir s'il est encore atteint.

Trois autres règles ont été remontées après l'extraction du bloc des skills, dans les mêmes conditions. Total : quatre règles récupérées, zéro perdue.

## Pourquoi comparer le début et la fin ne marche pas ?

Parce que le signal se noie dans le bruit. Voici la mesure, faite avec l'outil livré, sur les commits réels de ce dégraissage.

| Portée du contrôle | Lignes disparues à arbitrer | Exploitable ? |
|---|---|---|
| Une section | 3 | Oui, se relit en une minute |
| Un commit groupant deux sections | 78 | Non |
| Tout le dégraissage d'un coup | 120 | Non |

Trois lignes, vous les lisez et vous tranchez. Cent vingt lignes, vous ne les lisez pas, et la vraie règle perdue reste cachée parmi cent dix-neuf déplacements parfaitement légitimes.

Cette découverte m'a surpris pendant la préparation de cet article. Je croyais avoir appliqué un test global. En vérifiant, j'ai constaté que j'avais mesuré à chaque étape, et que c'est la seule raison pour laquelle ça a fonctionné.

Même un commit est déjà trop gros. Mon commit qui regroupait deux sections rend 78 disparitions, donc inutilisable. Le script émet maintenant un avertissement au-delà de douze : quand il se déclenche, ce n'est pas un résultat, c'est le signal qu'il faut découper plus finement.

## Que garde-t-on, que déplace-t-on ?

| Reste dans le fichier de contexte | Part vers un README |
|---|---|
| Règles d'orchestration : quel outil, quand, dans quel ordre | Historique : pourquoi on l'a construit, avec quels retours |
| Arbitrages : qui prime en cas de conflit | Catalogues : la liste de ce qui existe |
| Contraintes techniques dures : ce qui casse si on le déplace | Pièges propres à un seul élément |
| Valeurs par défaut, appliquées sans qu'on les demande | Journaux datés, notes de version |
| Réflexes de sécurité et de confidentialité | Détails d'implémentation, paramètres |

Un test visuel très simple permet de savoir si vous vous y prenez bien. Regardez l'évolution section par section :

| Section | Avant | Après | Écart |
|---|---|---|---|
| Composants | 80,8 Ko | 19,1 Ko | −76,3 % |
| Skills | 39,9 Ko | 5,4 Ko | −86,4 % |
| Outils | 45,0 Ko | 2,8 Ko | −93,8 % |
| Serveurs MCP | 17,7 Ko | 4,7 Ko | −73,3 % |
| Journal des versions | 10,4 Ko | 1,7 Ko | −83,5 % |
| **Règles absolues** | 6,3 Ko | **6,7 Ko** | **+7,6 %** |
| **Sécurité** | 1,3 Ko | **1,7 Ko** | **+31,1 %** |

Les cinq premières s'effondrent. Les deux dernières grossissent, parce que c'est là que j'ai remonté les règles récupérées.

**Un dégraissage réussi ne réduit pas uniformément.** Il vide les catalogues et laisse les règles intactes ou plus denses. Si toutes vos sections maigrissent au même rythme, vous êtes en train de perdre des règles.

## Pourquoi un README bien écrit peut rester lettre morte ?

Parce qu'un README n'est pas chargé automatiquement. Il est atteint parce qu'un lien le rend visible au bon moment.

Et ce qui déclenche la lecture, ce n'est pas le lien. C'est le texte autour du lien.

Version inatteignable :

```markdown
Voir [`MCP/README.md`](MCP/README.md) pour les détails.
```

Rien n'indique quand ouvrir ce fichier. Il ne sera ouvert que par quelqu'un qui cherche déjà les détails du MCP, donc jamais au moment où la règle compte.

Version atteignable :

```markdown
**📖 Ordre d'appel obligatoire, règle de publication, pièges de routage :**
[`MCP/README.md`](MCP/README.md)
```

La ligne d'index doit annoncer **de quoi la règle parle**, pas seulement où elle habite. Elle joue le rôle d'un sommaire qui déclenche la lecture, pas d'une note de bas de page.

Corollaire utile : si une règle est trop importante pour dépendre de ce déclenchement, elle ne part pas. Elle reste dans le fichier de contexte, en entier, et tant pis pour les tokens.

## Ce que ces chiffres ne prouvent pas

Ils viennent d'**un seul dépôt**, dont le fichier avait grossi anormalement pendant plus d'un an. Si le vôtre fait 15 Ko et qu'il est déjà propre, vous ne ferez pas 76 %. Vous ferez peut-être 10 %, et ce sera très bien.

L'estimation en tokens repose sur environ 3,7 octets par token, calibrée sur du markdown français accentué. C'est un ordre de grandeur pour arbitrer, pas une facturation.

Le critère de tri reste un **filtre lexical**, pas une compréhension du texte. Il attrape les règles écrites avec un verbe d'obligation. Une règle formulée sans marqueur passera au travers, et aucun comptage ne la protégera. C'est une raison de plus pour écrire ses règles avec des verbes d'obligation explicites, ce qui les rend au passage plus claires pour un humain.

## Par où commencer

Mesurez d'abord, sans rien toucher. Le seul chiffre qui décide s'il y a un problème est le poids de votre plus grosse section.

Si elle dépasse 20 Ko, elle contient presque certainement du catalogue et de l'historique qui n'ont pas besoin d'être chargés à chaque conversation. Sortez-la, une section à la fois, en comptant à chaque étape.

Et gardez en tête la seule chose qui compte vraiment dans cette opération : **votre objectif n'est pas un fichier plus petit, c'est un fichier où chaque ligne restante travaille encore.**

---

## Questions fréquentes

**Combien de tokens un CLAUDE.md de 200 Ko coûte-t-il réellement ?**
Environ 55 000 à 60 000 tokens sur du markdown français accentué, comptés à chaque nouvelle conversation avant votre première question.

**Découper son CLAUDE.md fait-il perdre des règles ?**
Oui, silencieusement, si vous ne comptez pas les lignes impératives avant et après chaque extraction. J'en ai perdu quatre sur une seule opération.

**Comment savoir qu'une règle a disparu du contexte ?**
Comptez les lignes contenant un marqueur d'obligation avant l'extraction, recomptez après, et relisez nommément les lignes manquantes.

**Pourquoi faut-il extraire une seule section à la fois ?**
Parce qu'une extraction unique produit trois lignes à arbitrer, alors qu'un lot en produit plus de cent, et personne ne relit cent lignes.

**Une règle déplacée dans un README s'applique-t-elle encore ?**
Seulement si la ligne d'index laissée dans le fichier principal annonce le sujet de la règle, sans quoi le README ne sera jamais ouvert au bon moment.

**Quelle taille viser pour un fichier de contexte ?**
Il n'existe pas de seuil universel, mais toute section dépassant 20 Ko contient presque toujours du catalogue déplaçable vers un README.

**Pourquoi un CLAUDE.md grossit-il sans que personne ne le décide ?**
Parce que chaque ajout est justifié isolément : un incident documenté prend dix à quinze lignes, et deux par semaine suffisent à produire deux mille lignes en dix-huit mois.

**Comment repérer les sections à extraire en premier ?**
Divisez le poids de chaque section par le nombre de règles qu'elle contient : au-delà de quelques milliers d'octets par règle, c'est du récit avec une règle dedans.

**Que garde-t-on obligatoirement dans le fichier principal ?**
Les règles d'orchestration, les arbitrages en cas de conflit, les contraintes techniques dures, les valeurs par défaut et les réflexes de sécurité.

**Cette méthode fonctionne-t-elle pour AGENTS.md ou .cursorrules ?**
Oui, le mécanisme ne dépend d'aucun outil particulier, seulement du fait que le fichier soit chargé intégralement à chaque session.
