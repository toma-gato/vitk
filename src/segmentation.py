import itk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def segment_brain(image_path):
    PixelType = itk.F
    ImageType = itk.Image[PixelType, 3]
    MaskPixelType = itk.UC
    MaskType = itk.Image[MaskPixelType, 3]

    reader = itk.ImageFileReader[ImageType].New()
    reader.SetFileName(image_path) 
    reader.Update()


    otsu = itk.OtsuThresholdImageFilter[ImageType, MaskType].New()
    otsu.SetInput(reader.GetOutput())
    otsu.SetOutsideValue(0)
    otsu.SetInsideValue(1)
    otsu.SetNumberOfHistogramBins(200)
    
    StructuringElementType = itk.FlatStructuringElement[3]
    structuring_element = StructuringElementType.Ball(1)
    
    morpho = itk.BinaryMorphologicalClosingImageFilter[MaskType, MaskType, StructuringElementType].New()
    morpho.SetInput(otsu.GetOutput())
    morpho.SetKernel(structuring_element)
    morpho.SetForegroundValue(1)
    
    connected_components = itk.ConnectedComponentImageFilter[MaskType, itk.Image[itk.UL, 3]].New()
    connected_components.SetInput(morpho.GetOutput())

    cast = itk.CastImageFilter[itk.Image[itk.UL, 3], MaskType].New()
    cast.SetInput(connected_components.GetOutput())
    cast.Update()
    
    relabel = itk.RelabelComponentImageFilter[MaskType, MaskType].New()
    relabel.SetInput(cast.GetOutput())
    relabel.SortByObjectSizeOn()
    
    threshold = itk.BinaryThresholdImageFilter[MaskType, MaskType].New()
    threshold.SetInput(relabel.GetOutput())
    threshold.SetLowerThreshold(1)
    threshold.SetUpperThreshold(1)
    threshold.SetOutsideValue(0)
    threshold.SetInsideValue(1)
    threshold.Update()
    
    return threshold.GetOutput()


def segment_tumor(image_path, seed=None, lower_factor=0.8, upper_factor=1.2, min_tumor_size=100):
    PixelType = itk.F
    ImageType = itk.Image[PixelType, 3]
    LabelType = itk.UC
    LabelImageType = itk.Image[LabelType, 3]

    reader = itk.ImageFileReader[ImageType].New(FileName=image_path)
    reader.Update()
    image = reader.GetOutput()
    image_array = itk.GetArrayFromImage(image)

    if seed is None:
        fig, ax = plt.subplots(figsize=(8, 6))
        plt.subplots_adjust(bottom=0.25)
        current_slice = image_array.shape[0] // 2
        img_disp = ax.imshow(image_array[current_slice], cmap='gray')
        ax.set_title(f"Coupe axiale {current_slice}")
        ax_slider = plt.axes([0.25, 0.1, 0.65, 0.03])
        slider = Slider(ax_slider, 'Slice', 0, image_array.shape[0]-1,
                        valinit=current_slice, valstep=1)

        def update(val):
            sl = int(slider.val)
            img_disp.set_data(image_array[sl])
            ax.set_title(f"Coupe axiale {sl}")
            fig.canvas.draw_idle()
        slider.on_changed(update)

        seed_point = None
        def onclick(event):
            nonlocal seed_point
            if event.inaxes == ax:
                x, y = int(round(event.xdata)), int(round(event.ydata))
                z = int(slider.val)
                seed_point = (z, y, x)
                ax.scatter(x, y, c='r', marker='+', s=100)
                fig.canvas.draw_idle()
        fig.canvas.mpl_connect('button_press_event', onclick)

        plt.text(0.5, 0.02,
                "Cliquez sur la tumeur puis fermez la fenêtre",
                transform=fig.transFigure, ha='center')
        plt.show()
    else:
        seed_point = seed

    if seed_point is None:
        raise RuntimeError("Sélectionner un seed point avant de fermer la fenêtre.")

    brain_only_img = image
    seed_val = image_array[seed_point]
    lower = int(max(0, seed_val * lower_factor))
    upper = int(seed_val * upper_factor)

    reg = itk.ConnectedThresholdImageFilter[ImageType, ImageType].New()
    reg.SetInput(brain_only_img)
    reg.SetLower(lower)
    reg.SetUpper(upper)
    reg.SetReplaceValue(1)
    
    idx = itk.Index[3]()
    idx[0], idx[1], idx[2] = seed_point[2], seed_point[1], seed_point[0]
    reg.AddSeed(idx)
    
    reg.Update()
    tumor_raw_float = reg.GetOutput()
    
    tumor_raw = itk.BinaryThresholdImageFilter[ImageType, LabelImageType].New()
    tumor_raw.SetInput(tumor_raw_float)
    tumor_raw.SetLowerThreshold(1)
    tumor_raw.SetUpperThreshold(1)
    tumor_raw.SetInsideValue(1)
    tumor_raw.SetOutsideValue(0)
    tumor_raw.Update()
    tumor_raw_img = tumor_raw.GetOutput()
    
    tumor_array = itk.GetArrayFromImage(tumor_raw_img)
    
    if tumor_array.sum() == 0:
        print("Erreur: Aucun pixel segmenté même après adaptation!")
        return tumor_raw_img
    
    opening = itk.BinaryMorphologicalOpeningImageFilter[LabelImageType, LabelImageType, itk.FlatStructuringElement[3]].New()
    opening.SetInput(tumor_raw_img)
    opening.SetKernel(itk.FlatStructuringElement[3].Ball(1))
    opening.SetForegroundValue(1)
    opening.Update()
    opened = opening.GetOutput()

    opened_array = itk.GetArrayFromImage(opened)
    if opened_array.sum() == 0:
        print("Erreur: Opening a tout supprimé!")
        return opened

    cc = itk.ConnectedComponentImageFilter[LabelImageType, itk.Image[itk.UL, 3]].New()
    cc.SetInput(opened)
    cc.Update()

    relabel = itk.RelabelComponentImageFilter[itk.Image[itk.UL, 3], LabelImageType].New()
    relabel.SetInput(cc.GetOutput())
    relabel.SetMinimumObjectSize(min_tumor_size)
    relabel.Update()

    final_tumor = itk.BinaryThresholdImageFilter[LabelImageType, LabelImageType].New()
    final_tumor.SetInput(relabel.GetOutput())
    final_tumor.SetLowerThreshold(1)
    final_tumor.SetUpperThreshold(itk.NumericTraits[LabelType].max())
    final_tumor.SetInsideValue(1)
    final_tumor.SetOutsideValue(0)
    final_tumor.Update()
    
    return final_tumor.GetOutput(), seed_point