import itk
import vtk
import numpy as np

def visualize_volume_vtk(itk_image, title="Volume"):
    vtk_image = itk.vtk_image_from_image(itk_image);

    volume_mapper = vtk.vtkSmartVolumeMapper()
    volume_mapper.SetInputData(vtk_image)

    opacity_transfer_function = vtk.vtkPiecewiseFunction()
    opacity_transfer_function.AddPoint(0, 0.0)
    opacity_transfer_function.AddPoint(100, 0.2)
    opacity_transfer_function.AddPoint(255, 0.6)

    color_transfer_function = vtk.vtkColorTransferFunction()
    color_transfer_function.AddRGBPoint(0, 0.0, 0.0, 0.0)
    color_transfer_function.AddRGBPoint(255, 1.0, 1.0, 1.0)

    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_transfer_function)
    volume_property.SetScalarOpacity(opacity_transfer_function)
    volume_property.ShadeOn()
    volume_property.SetInterpolationTypeToLinear()

    volume = vtk.vtkVolume()
    volume.SetMapper(volume_mapper)
    volume.SetProperty(volume_property)

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    renderer.AddVolume(volume)
    renderer.SetBackground(0.1, 0.1, 0.1)
    render_window.SetSize(800, 600)
    render_window.SetWindowName(title)

    interactor.Initialize()
    render_window.Render()
    interactor.Start()

def visualize_with_vtk(brain_mask, tumor_mask):
    def make_actor(vtk_img, value, color, opacity):
        iso = vtk.vtkMarchingCubes()
        iso.SetInputData(vtk_img)
        iso.SetValue(0, value)
        iso.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(iso.GetOutputPort())
        mapper.ScalarVisibilityOff()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetOpacity(opacity)
        return actor

    brain_vtk = itk.vtk_image_from_image(brain_mask)
    tumor_vtk = itk.vtk_image_from_image(tumor_mask)

    brain_actor = make_actor(brain_vtk, 0.5, (0.8, 0.8, 0.8), 0.4)
    tumor_actor = make_actor(tumor_vtk, 0.5, (1.0, 0.0, 0.0), 0.9)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.AddActor(brain_actor)
    renderer.AddActor(tumor_actor)

    ren_win = vtk.vtkRenderWindow()
    ren_win.AddRenderer(renderer)
    ren_win.SetSize(1000, 800)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(ren_win)

    renderer.ResetCamera()
    ren_win.Render()
    interactor.Initialize()
    interactor.Start()

def visualize_two_tumors_vtk(mask1, mask2, brain_mask):
    def load_vtk(mask):
        if isinstance(mask, str):
            mask = itk.imread(mask, itk.ctype("unsigned char"))
        return itk.vtk_image_from_image(mask)

    vtk1 = load_vtk(mask1)
    vtk2 = load_vtk(mask2)
    vtk_brain = load_vtk(brain_mask)

    def make_actor(vtk_img, color, opacity):
        contour = vtk.vtkMarchingCubes()
        contour.SetInputData(vtk_img)
        contour.SetValue(0, 0.5)
        contour.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(contour.GetOutputPort())
        mapper.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetOpacity(opacity)
        return actor

    actor1 = make_actor(vtk1, (1.0, 1.0, 0.0), 0.6)   # Jaune
    actor2 = make_actor(vtk2, (0.0, 0.5, 1.0), 0.6)   # Bleu
    actor_brain = make_actor(vtk_brain, (0.8, 0.8, 0.8), 0.1)  # Gris

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.1)

    window = vtk.vtkRenderWindow()
    window.AddRenderer(renderer)
    window.SetSize(800, 600)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)

    mode = ['1', '2', 'b']
    
    def show_mode():
        renderer.RemoveAllViewProps()
        if '1' in mode:
            renderer.AddActor(actor1)
        if '2' in mode:
            renderer.AddActor(actor2)
        if 'b' in mode:
            renderer.AddActor(actor_brain)
        renderer.ResetCamera()
        window.Render()

    def keypress_callback(obj, event):
        key = obj.GetKeySym()
        match key:
            case '1':
                if '1' in mode:
                    mode.remove('1')
                else:
                    mode.append('1')
                show_mode()
            case '2':
                if '2' in mode:
                    mode.remove('2')
                else:
                    mode.append('2')
                show_mode()
            case 'b':
                if 'b' in mode:
                    mode.remove('b')
                else:
                    mode.append('b')
                show_mode()

    interactor.AddObserver('KeyPressEvent', keypress_callback)

    show_mode()

    interactor.Initialize()
    interactor.Start()