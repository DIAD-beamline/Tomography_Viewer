def viewer(
        image,
        slice_number: int = None,
        axis: int = 0,
        continuous_update: bool = True,
        zoom_factor: float = 1.0,
        zoom_spline_order: int = 0,
        colormap: str = None,
        display_min: float = None,
        display_max: float = None,
):
    """Shows an image with intensity range sliders and mouse position/value picker.
    
    Parameters
    ----------
    image : image
        Image shown on the left (behind the curtain)
    slice_number : int, optional
        Slice-position in case we are looking at an image stack
    axis : int, optional
        This parameter is obsolete. If you want to show any other axis than the first, 
        you need to transpose the image before, e.g. using np.swapaxes().
    continuous_update : bool, optional
        Update the image while dragging the mouse, default: False
    zoom_factor: float, optional
        Allows showing the image larger (> 1) or smaller (<1)
    zoom_spline_order: int, optional
        Spline order used for interpolation (default=0, nearest-neighbor)
    colormap: str, optional
        Matplotlib colormap name or "pure_green", "pure_magenta", ...
    display_min: float, optional
        Lower bound of properly shown intensities
    display_max: float, optional
        Upper bound of properly shown intensities

    Returns
    -------
    An ipywidget with an image display, intensity sliders, and position/value label.
    """
    import ipywidgets
    from ipyevents import Event
    from ._image_widget import ImageWidget, _img_to_rgb
    from ._utilities import _no_resize
    import numpy as np

    if 'cupy.ndarray' in str(type(image)):
        image = image.get()

    slice_slider = None

    if slice_number is None:
        slice_number = int(image.shape[axis] / 2)

    # Setup slice slider
    slice_slider = ipywidgets.IntSlider(
        value=slice_number,
        min=0,
        max=image.shape[axis] - 1,
        continuous_update=continuous_update,
        description="Slice"
    )
    if len(image.shape) < 3 or (len(image.shape) == 3 and image.shape[-1] == 3):
        slice_slider.layout.display = 'none'

    # Setup intensity range sliders
    if display_min is None:
        display_min = np.min(image)
    if display_max is None:
        display_max = np.max(image)

    min_slider = ipywidgets.IntSlider(
        value=display_min,
        min=display_min,
        max=display_max,
        continuous_update=continuous_update,
        description="Minimum"
    )

    max_slider = ipywidgets.IntSlider(
        value=display_max,
        min=display_min,
        max=display_max,
        continuous_update=continuous_update,
        description="Maximum"
    )

    # Add position/value label
    position_label = ipywidgets.Label("Position: [] Value: ")

    def transform_image():
        if len(image.shape) < 3 or (len(image.shape) == 3 and image.shape[-1] == 3):
            image_slice = _img_to_rgb(image.copy(), colormap=colormap, 
                                    display_min=min_slider.value, 
                                    display_max=max_slider.value)
        else:
            image_slice = _img_to_rgb(np.take(image, slice_slider.value, axis=axis),
                                    colormap=colormap, 
                                    display_min=min_slider.value,
                                    display_max=max_slider.value)
        return image_slice

    # Create image widget
    view = ImageWidget(transform_image(), zoom_factor=zoom_factor,
                      zoom_spline_order=zoom_spline_order)

    # Set up mouse event handling
    event_handler = Event(source=view, watched_events=['mousemove'])

    def get_current_slice():
        if len(image.shape) < 3 or (len(image.shape) == 3 and image.shape[-1] == 3):
            return image
        else:
            return np.take(image, slice_slider.value, axis=axis)

    def update_position_label(event):
        relative_x = event['relativeX'] / zoom_factor
        relative_y = event['relativeY'] / zoom_factor
        x = int(relative_x)
        y = int(relative_y)
        
        current_slice = get_current_slice()
        if 0 <= y < current_slice.shape[0] and 0 <= x < current_slice.shape[1]:
            intensity = current_slice[y, x]
            if len(image.shape) < 3:
                position_label.value = f"Position: [{y}, {x}] Value: {intensity}"
            else:
                position_label.value = f"Position: [{y}, {x}] Value: {intensity}"

    event_handler.on_dom_event(update_position_label)

    # Update image when sliders change
    def configuration_updated(event=None):
        view.data = transform_image()

    configuration_updated(None)

    # Connect user interface with events
    slice_slider.observe(configuration_updated)
    min_slider.observe(configuration_updated)
    max_slider.observe(configuration_updated)

    # Create layout
    result = _no_resize(ipywidgets.VBox([
        _no_resize(view),
        slice_slider,
        min_slider,
        max_slider,
        position_label
    ]))
    
    result.update = configuration_updated
    return result