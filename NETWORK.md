# Echanges Client/Node, fonctionnement

Toutes les données envoyées sont préfixées, en clair, de "XX:", XX indiquant la taille en octets des données
Ce préfixe est toujours présent quelque soient les données, chiffrées ou non. Il ne sera pas indiqué dans la suite de ce document mais il est bien présent.

Le node préfixe ses réponses de OK ou de ERR en fonction du succès de la commande envoyées par le client.
Une ligne préfixée par (E) indique que l'échange se fait chiffré en AES (algo GCM) avec la clé de session négociée lors de l'ouverture de connexion.

## Initialisation de la connexion
Un client souhaite se connecter à un node. Dès qu'il reçoit une nouvelle connexion, les échanges suivants commencent :

Node : OK WELCOME Bannière de connexion

Node : OK SERVER-KEY Clé publique du serveur (base64)

Node : OK SERVER-AUTH signature encodée en base64 du timestamp actuel sans son dernier chiffre (offre une tolérance de -+ 10sec)

Client : SESSION-KEY clé de session (chiffrement AES 128 bits) générée aléatoirement et chiffrée avec la clé publique du serveur

Node : OK SESSION-OK Session key exchange successful

(E) Client : CLIENT-KEY Clé publique du client

(E) Client : CLIENT-AUTH signature encodée en base64 du timestamp actuel sans son dernier chiffre (offre une tolérance de -+ 10sec)

(E) Node : OK AUTH-OK Successfully authenticated, welcome <hash de la clé publique du client, càd identité du client>

La connexion est à ce stade établie et à l'exception des keepalives spécifiés ci-dessous, TOUS les échanges Node-Client sont chiffrés en AES avec la clé de session.

## Keepalives
Le node considère qu'un client a timeout si il n'envoie pas de données pendant une durée supérieure à 12 secondes.

Pour que le client puisse signaler qu'il est toujours présent même lorsqu'il n'envoie pas de données, il envoie "keepalive" toutes les 8 secondes :

Client : keepalive

Cet échange n'est PAS chiffré, même si la clé de session a déjà été générée. 
A noter que le client peut théoriquement envoyer n'importe quelle donnée, cela va reset le timer de 12 secondes sur le serveur.
Cependant, le Node est codé pour ne rien faire si le client envoie "keepalive" sans chiffrement, ce qui permet de ne pas trigger d'erreur.

## Erreur côté node : commande client inconnue
Lorsque le client envoie une commande inconnue du node, il renvoie la chose suivante :

(E) Node : ERR Unknown command

## Commandes client :
Voici les commandes à disposition du client :

"hello TEXT" : fait renvoyer le texte spécifié par le serveur. Utilisé comme "ping" à des fins de test

(E) Node : OK Hello user ! You said TEXT

"whoami" : fait renvoyer par le Node l'identité du client. Utilisé à des fins de test :

(E) Node : OK You are IDENTITÉ CLIENT

"quit" n'est pas une commande implémentée sur le serveur, elle fait simplement quitter le client. Le serveur reçoit les TCP FIN et met fin à la connexion.
