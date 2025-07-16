# Étude Longitudinale de l'Évolution d'une Tumeur Cérébrale

## Objectif

Ce projet a été développé en Python avec les bibliothèques ITK et VTK. Il permet un traitement semi-automatisé en ligne de commande ou via une interface interactive. Il réalise le suivi semi-automatisé des changements d'une tumeur à partir de deux scans IRM effectués sur un même patient à des dates différentes. L'analyse inclut le recalage des volumes, la segmentation des tumeurs et la quantification des changements.

## Structure du Projet

```
tumor_evolution/
│
├── Data/
│   ├── case6_gre1.nrrd                # Premier scan (image fixe)
│   ├── case6_gre2.nrrd                # Second scan (image mobile)
│   ├── registered.nrrd                # Image recalée (générée)
│   ├── fixed_brain_mask.nrrd          # Masque du cerveau du premier scan (générée)
│   ├── fixed_tumor_mask.nrrd          # Masque de la tumeur du premier scan (générée)
│   ├── registered_brain_mask.nrrd     # Masque du cerveau du second scan (générée)
│   └── registered_tumor_mask.nrrd     # Masque de la tumeur du second scan (généré)
│
├── src/
│   ├── registration.py         # Recalage des images
│   ├── segmentation.py         # Segmentation des tumeurs
│   ├── analysis.py             # Analyse des différences
│   └── visualization.py        # Visualisation des résultats
│
├── main.py                     # Point d'entrée principal
├── README.md                   # Documentation
└── requirements.txt            # Dépendances
```

## Installation

### Dépendances requises

```bash
pip install itk
pip install vtk
pip install numpy
pip install matplotlib
```

### Installation automatique des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Exécution complète

```bash
python main.py
```

Le script s'exécute automatiquement sans interaction utilisateur et produit :
- Le recalage des deux images
- La segmentation des tumeurs
- L'analyse quantitative des changements
- La visualisation des résultats

### Exécution étape par étape

- Recalage : --step register
- Segmentation : --step segment
- Analyse : --step analyze
- Visualisation finale : --step viz

Par exemple :

```bash
python main.py --step segment --viz
```

### Visualisation interactive

Lors de la visualisation finale, les touches suivantes sont disponibles :

   - 1 : Afficher/Masquer la tumeur du premier scan (jaune)

   - 2 : Afficher/Masquer la tumeur du second scan (bleu)

   - b : Afficher/Masquer le cerveau (gris)

## Méthodes Implémentées

### 1. Recalage d'Images (`registration.py`)

**Algorithme choisi** : Registration rigide

**Composants** :
- **Transformation** : `VersorRigid3DTransform` (6 paramètres : 3 rotations + 3 translations)
- **Métrique** : `MattesMutualInformationImageToImageMetricv4`
- **Optimiseur** : `RegularStepGradientDescentOptimizerv4`
- **Initialisation** : `CenteredTransformInitializer` avec centrage géométrique

**Paramètres optimisés** :
- Learning rate : 0.2
- Nombre d'itérations : 300
- Scales : [1000, 1000, 1000, 1, 1, 1] (équilibrage rotation/translation)

**Justification** : Le recalage rigide est approprié pour les images cérébrales où les déformations sont principalement dues au repositionnement du patient.

### 2. Segmentation des Tumeurs (`segmentation.py`)

**Méthode principale** : Croissance de région, morphologie et composantes connexes

**Pipeline** :
1. **Sélection interactive du point seed** : L’utilisateur clique sur un voxel appartenant à la tumeur via une interface avec slider de coupe.
2. **Croissance de région 3D** : Inclusion des voxels dont l’intensité est comprise entre 0.8×seed et 1.2×seed.
3. **Seuillage binaire** : Génère un masque binaire à partir de la région extraite.
4. **Ouverture morphologique** : Élimine le bruit tout en conservant la forme de la tumeur.
5. **Étiquetage des composantes connexes** : Identification des régions disjointes.
6. **Filtrage par taille** : Seules les composantes de taille suffisante sont conservées (≥ 100 voxels).

**Méthode complémentaire** : Segmentation du cerveau (segment_brain)
1. **Seuillage Otsu**
2. **Fermeture morphologique**
3. **Extraction de la plus grande composante connexe**

**Justification** : La croissance de région est efficace tumeurs ou dans les cas avec peu de contraste. La sélection manuelle du seed améliore la précision.

### 3. Analyse des Changements (`analysis.py`)

**Métriques calculées** :

1. **Différence de volume** :
   - Volume absolu (mm³) de chaque tumeur
   - Différence absolue et relative
   - Indique croissance ou régression

2. **Coefficient de Dice** :
   - Mesure de similarité spatiale entre 0 et 1
   - Évalue la concordance géométrique des segmentations

3. **Statistiques d'intensité** :
   - Moyenne, écart-type, médiane, min, max
   - Comparaison des propriétés tissulaires

**Formules** :
- Volume = Nombre_voxels × Espacement_x × Espacement_y × Espacement_z
- Dice = 2 × |A ∩ B| / (|A| + |B|)

### 4. Visualisation (`visualization.py`)

**Visualisation 2D (matplotlib)** :
- Interface interactive pour choisir un point seed pour la croissance de région
- Slider de coupe axiale pour naviguer dans les plans IRM

**Visualisation 3D (VTK)** :
- Rendu volumique avec vtkSmartVolumeMapper
- Isosurfaces pour :
   - Masque cérébral (gris translucide)
   - Tumeur ancienne (jaune)
   - Tumeur actuelle (bleu)

- Contrôles clavier en temps réel :
   - 1 : Afficher / masquer la tumeur ancienne
   - 2 : Afficher / masquer la tumeur actuelle
   - b : Afficher / masquer le cerveau

**Justification** : L’interface 2D permet une sélection intuitive du seed pour la segmentation. La visualisation 3D avec rendu interactif améliore la compréhension spatiale de l’évolution tumorale.

## Résultats Attendus

### Sorties quantitatives typiques

```
Volume tumeur 1 : 5454.00 mm³
Volume tumeur 2 : 6399.00 mm³
Différence : 945.00 mm³
Dice : 0.794
Moyennes d'intensité : T1=700.56 ± 67.29, T2=674.74 ± 59.59
Différence moyenne d'intensité : -25.81
```


## Difficultés Rencontrées

### 1. Segmentation automatique
- **Difficulté** : Segmentation complètement automatique très peu robuste
- **Solution** : Interface utilisateur pour une méthode semi-automatique

### 2. Gestion des types ITK
- **Difficulté** : Compatibilité entre types d'images
- **Solution** : Conversion systématique avec `CastImageFilter`


## Crédits

**Développeurs** :
- Galateau Thomas
- Sue Nathan
- Lépinay Jules-Victor

**Bibliothèques utilisées** :
- ITK (Insight Segmentation and Registration Toolkit)
- VTK (Visualization Toolkit)
- NumPy
- Matplotlib
