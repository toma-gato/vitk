import itk
import numpy as np

def compute_volume_difference(mask1, mask2):
    if isinstance(mask1, str):
        mask1 = itk.imread(mask1, itk.ctype("unsigned char"))
    if isinstance(mask2, str):
        mask2 = itk.imread(mask2, itk.ctype("unsigned char"))
    
    arr1 = itk.GetArrayFromImage(mask1)
    arr2 = itk.GetArrayFromImage(mask2)
    
    count1 = np.count_nonzero(arr1)
    count2 = np.count_nonzero(arr2)
    
    spacing = mask1.GetSpacing()
    voxel_volume = spacing[0] * spacing[1] * spacing[2]
    
    vol1 = count1 * voxel_volume
    vol2 = count2 * voxel_volume
    
    return vol2 - vol1, vol1, vol2

def compute_intensity_statistics(image1, image2, mask1, mask2):
    if isinstance(image1, str):
        image1 = itk.imread(image1, itk.ctype("float"))
    if isinstance(image2, str):
        image2 = itk.imread(image2, itk.ctype("float"))
    if isinstance(mask1, str):
        mask1 = itk.imread(mask1, itk.ctype("unsigned char"))
    if isinstance(mask2, str):
        mask2 = itk.imread(mask2, itk.ctype("unsigned char"))
    
    img1_arr = itk.GetArrayFromImage(image1)
    img2_arr = itk.GetArrayFromImage(image2)
    mask1_arr = itk.GetArrayFromImage(mask1)
    mask2_arr = itk.GetArrayFromImage(mask2)
    
    intensities1 = img1_arr[mask1_arr > 0]
    intensities2 = img2_arr[mask2_arr > 0]
    
    stats1 = {
        'mean': np.mean(intensities1),
        'std': np.std(intensities1),
        'median': np.median(intensities1),
        'min': np.min(intensities1),
        'max': np.max(intensities1)
    }
    
    stats2 = {
        'mean': np.mean(intensities2),
        'std': np.std(intensities2),
        'median': np.median(intensities2),
        'min': np.min(intensities2),
        'max': np.max(intensities2)
    }
    
    return stats1, stats2

def compute_dice_coefficient(mask1, mask2):
    if isinstance(mask1, str):
        mask1 = itk.imread(mask1, itk.ctype("unsigned char"))
    if isinstance(mask2, str):
        mask2 = itk.imread(mask2, itk.ctype("unsigned char"))
    
    arr1 = itk.GetArrayFromImage(mask1)
    arr2 = itk.GetArrayFromImage(mask2)
    
    intersection = np.logical_and(arr1, arr2)
    dice = 2.0 * intersection.sum() / (arr1.sum() + arr2.sum())
    
    return dice