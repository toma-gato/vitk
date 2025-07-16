import itk
import os
import numpy as np

def data_path(data_file):
    return os.path.join(os.path.dirname(__file__), "../Data/", data_file)

def register_images(fixed_path, moving_path):
    PixelType = itk.ctype("float")
    
    fixed_image = itk.imread(fixed_path, PixelType)
    moving_image = itk.imread(moving_path, PixelType)
    
    FixedImageType = type(fixed_image)
    MovingImageType = type(moving_image)
    
    TransformType = itk.VersorRigid3DTransform[itk.D]
    initial_transform = TransformType.New()
    
    InitializerType = itk.CenteredTransformInitializer[TransformType, FixedImageType, MovingImageType]
    initializer = InitializerType.New()
    initializer.SetTransform(initial_transform)
    initializer.SetFixedImage(fixed_image)
    initializer.SetMovingImage(moving_image)
    initializer.GeometryOn()
    initializer.InitializeTransform()
    
    MetricType = itk.MattesMutualInformationImageToImageMetricv4[FixedImageType, MovingImageType]
    metric = MetricType.New()
    metric.SetNumberOfHistogramBins(50)
    metric.SetUseMovingImageGradientFilter(False)
    metric.SetUseFixedImageGradientFilter(False)
    
    OptimizerType = itk.RegularStepGradientDescentOptimizerv4[itk.D]
    optimizer = OptimizerType.New()
    optimizer.SetLearningRate(0.2)
    optimizer.SetMinimumStepLength(0.001)
    optimizer.SetNumberOfIterations(300)
    optimizer.SetRelaxationFactor(0.5)
    
    optimizer_scales = itk.OptimizerParameters[itk.D](initial_transform.GetNumberOfParameters())
    optimizer_scales[0] = 1000.0  # versor x
    optimizer_scales[1] = 1000.0  # versor y  
    optimizer_scales[2] = 1000.0  # versor z
    optimizer_scales[3] = 1.0     # translation x
    optimizer_scales[4] = 1.0     # translation y
    optimizer_scales[5] = 1.0     # translation z
    optimizer.SetScales(optimizer_scales)
    
    RegistrationType = itk.ImageRegistrationMethodv4[FixedImageType, MovingImageType]
    registration = RegistrationType.New()
    
    registration.SetFixedImage(fixed_image)
    registration.SetMovingImage(moving_image)
    registration.SetMetric(metric)
    registration.SetOptimizer(optimizer)
    registration.SetInitialTransform(initial_transform)
    
    registration.SetSmoothingSigmasPerLevel([0])
    registration.SetShrinkFactorsPerLevel([1])
    registration.SetNumberOfLevels(1)
    registration.Update()
    
    transform = registration.GetTransform()
    
    ResampleFilterType = itk.ResampleImageFilter[MovingImageType, FixedImageType]
    resampler = ResampleFilterType.New()
    resampler.SetTransform(transform)
    resampler.SetInput(moving_image)
    resampler.SetReferenceImage(fixed_image)
    resampler.SetUseReferenceImage(True)
    resampler.SetDefaultPixelValue(0)
    
    InterpolatorType = itk.LinearInterpolateImageFunction[MovingImageType, itk.D]
    interpolator = InterpolatorType.New()
    resampler.SetInterpolator(interpolator)
    
    resampler.Update()
    registered_image = resampler.GetOutput()
        
    return registered_image