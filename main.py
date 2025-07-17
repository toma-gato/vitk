import os
import sys
import argparse
import itk
import locale

from contextlib import contextmanager

from src.registration import register_images, data_path
from src.segmentation import segment_tumor, segment_brain
from src.analysis import compute_volume_difference, compute_intensity_statistics, compute_dice_coefficient
from src.visualization import visualize_with_vtk, visualize_volume_vtk, visualize_two_tumors_vtk

@contextmanager
def force_c_locale():
    """Force temporairement la locale numérique en 'C' (utile pour ITK)"""
    current = locale.setlocale(locale.LC_NUMERIC)
    try:
        locale.setlocale(locale.LC_NUMERIC, "C")
        yield
    finally:
        locale.setlocale(locale.LC_NUMERIC, current)

def safe_itk_write(image, path):
    """Écrit un fichier ITK tout en forçant la locale C"""
    with force_c_locale():
        itk.imwrite(image, path)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

fixed_path = data_path("case6_gre1.nrrd")
moving_path = data_path("case6_gre2.nrrd")
registered_path = data_path("registered.nrrd")
fixed_brain_mask_path = data_path("fixed_brain_mask.nrrd")
fixed_tumor_mask_path = data_path("fixed_tumor_mask.nrrd")
registered_brain_mask_path = data_path("registered_brain_mask.nrrd")
registered_tumor_mask_path = data_path("registered_tumor_mask.nrrd")

def step_register(viz=False):
    print("RECALAGE...")
    if not os.path.exists(fixed_path) or not os.path.exists(moving_path):
        print("Erreur: Images sources manquantes.")
        return
    registered_image = register_images(fixed_path, moving_path)
    safe_itk_write(registered_image, registered_path)

    if viz:
        visualize_volume_vtk(registered_image, "Registered Image")

def step_segment(viz=False, hardcode=None):
    print("SEGMENTATION...")
    if hardcode is None :
        print("La segmentation est semi-automatique. Cliquer sur la tumeur dans l'interface.")

    fixed_brain_mask = segment_brain(fixed_path)
    safe_itk_write(fixed_brain_mask, fixed_brain_mask_path)
    fixed_tumor_mask, seed = segment_tumor(fixed_path, hardcode)
    safe_itk_write(fixed_tumor_mask, fixed_tumor_mask_path)
    registered_brain_mask = segment_brain(registered_path)
    safe_itk_write(registered_brain_mask, registered_brain_mask_path)
    registered_tumor_mask, _ = segment_tumor(registered_path, seed)
    safe_itk_write(registered_tumor_mask, registered_tumor_mask_path)

    if viz:
        visualize_with_vtk(registered_brain_mask, registered_tumor_mask)

def step_analysis():
    print("ANALYSE...")
    fixed_tumor_mask = itk.imread(fixed_tumor_mask_path)
    registered_tumor_mask = itk.imread(registered_tumor_mask_path)

    vol_diff, vol1, vol2 = compute_volume_difference(fixed_tumor_mask, registered_tumor_mask)
    dice = compute_dice_coefficient(fixed_tumor_mask, registered_tumor_mask)
    stats1, stats2 = compute_intensity_statistics(fixed_path, registered_path, fixed_tumor_mask, registered_tumor_mask)

    print()
    print(f"Volume tumeur 1 : {vol1:.2f} mm³")
    print(f"Volume tumeur 2 : {vol2:.2f} mm³")
    print(f"Différence : {vol_diff:.2f} mm³")
    print(f"Dice : {dice:.3f}")
    print(f"Moyennes d'intensité : T1={stats1['mean']:.2f} ± {stats1['std']:.2f}, "
          f"T2={stats2['mean']:.2f} ± {stats2['std']:.2f}")
    print(f"Différence moyenne d'intensité : {stats2['mean'] - stats1['mean']:.2f}")
    print()

def step_visualization():
    print("VISUALISATION...")
    fixed_tumor_mask = itk.imread(fixed_tumor_mask_path)
    registered_tumor_mask = itk.imread(registered_tumor_mask_path)
    registered_brain_mask = itk.imread(registered_brain_mask_path)
    visualize_two_tumors_vtk(fixed_tumor_mask, registered_tumor_mask, registered_brain_mask)

def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline d'analyse de tumeur")
    parser.add_argument("--step", choices=["register", "segment", "analyze", "viz"], help="Étape à exécuter")
    parser.add_argument("--all", action="store_true", help="Tout exécuter")
    parser.add_argument("--viz", action="store_true", help="Activer la visualisation à chaque étape")
    parser.add_argument("--hardcodeseed", action="store_true", help="Utilise une valeur hardcode pour la seed de la tumeur")
    return parser.parse_args()

def main():
    args = parse_args()

    if not args.all and not args.step:
        args.all = True
        args.hardcodeseed = True

    seed = None
    if args.hardcodeseed :
        seed = (53, 63, 83)

    if args.all:
        step_register(viz=args.viz)
        step_segment(viz=args.viz, hardcode=seed)
        step_analysis()
        step_visualization()
    elif args.step == "register":
        step_register(viz=args.viz)
    elif args.step == "segment":
        step_segment(viz=args.viz, hardcode=seed)
    elif args.step == "analyze":
        step_analysis()
    elif args.step == "viz":
        step_visualization()
    else:
        print("Spécifier --step ou --all. Utilise --help pour les options.")

if __name__ == "__main__":
    main()