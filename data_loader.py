import os
from pathlib import Path
import h5py
import numpy as np
import ipywidgets as widgets
from IPython.display import display
from IPython import get_ipython

def get_nexus_path(visit_number, year):
    """Construct the full path to the nexus directory for a given visit number"""
    base_path = '/dls/k11/data/'
    return str(Path(base_path) / year / visit_number / 'nexus')

def is_tomography_scan(filepath):
    """Check if the NXS file contains tomography data"""
    try:
        with h5py.File(filepath, 'r') as f:
            return 'entry/imaging/data' in f
    except Exception:
        return False

class NXSDataLoader:
    def __init__(self, visit_number, year):
        self.filepath = None
        """Initialize the data loader widget for a specific visit."""
        self.nexus_path = get_nexus_path(visit_number, year)
        self.current_data = None
        self.image_key = None
        self.proj_indices = None
        
        # Create file browsing widgets
        self.path_label = widgets.HTML(
            value=f'<b>Nexus Path:</b> {self.nexus_path}',
            layout={'width': '800px'}
        )
        
        self.file_select = widgets.Select(
            options=[],
            description='Files:',
            disabled=False,
            layout={'width': '600px', 'height': '200px'}
        )
        
        self.refresh_button = widgets.Button(
            description='Refresh',
            icon='refresh'
        )
        
        self.load_button = widgets.Button(
            description='Load Data',
            icon='upload',
            disabled=True
        )
        
        self.status_label = widgets.HTML(
            value='Ready to browse'
        )
        
        self.data_info = widgets.HTML(
            value='No data loaded'
        )
        
        # Set up callbacks
        self.refresh_button.on_click(self._on_refresh_click)
        self.load_button.on_click(self._on_load_click)
        self.file_select.observe(self._on_selection_change, names='value')
        
        # Initial file list update
        self._update_file_list()
        
        # Create and display layout
        self._create_layout()
    
    def _update_file_list(self):
        """Update the file list based on the current path"""
        try:
            path = Path(self.nexus_path)
            if not path.exists():
                self.status_label.value = '<span style="color: red">Nexus path does not exist!</span>'
                self.file_select.options = []
                return
            
            self.status_label.value = 'Scanning for tomography files...'
            tomo_files = []
            
            for f in sorted(path.glob('*.nxs')):
                if is_tomography_scan(str(f)):
                    tomo_files.append(f.name)
            
            if not tomo_files:
                self.status_label.value = '<span style="color: orange">No tomography files found in directory</span>'
                self.file_select.options = []
                return
            
            self.file_select.options = tomo_files
            self.status_label.value = f'Found {len(tomo_files)} tomography files'
            
        except Exception as e:
            self.status_label.value = f'<span style="color: red">Error: {str(e)}</span>'
            self.file_select.options = []
    
    def _on_selection_change(self, change):
        """Handle file selection changes"""
        self.load_button.disabled = not bool(change.new)
        self._reset_widgets()
    
    def _on_refresh_click(self, b):
        """Handle refresh button clicks"""
        self._update_file_list()

    def _reset_widgets(self):
        """Reset all widgets to their default state"""
        self.current_data = None
        self.image_key = None
        self.proj_indices = None
        self.data_info.value = 'No data loaded'
        # Clear the global data variable from IPython namespace
        ipython = get_ipython()
        if 'data' in ipython.user_ns:
            del ipython.user_ns['data']
    
    def _on_load_click(self, b):
        """Handle load button clicks"""
        try:
            self.filepath = self.get_selected_file()
            self.status_label.value = f'Loading data from {self.filepath}...'
            
            with h5py.File(self.filepath, 'r') as f:
                # Load the data and ensure it's uint16
                raw_data = f['entry/imaging/data'][:]
                self.current_data = np.asarray(raw_data, dtype=np.uint16)
                
                # Assign to IPython's global namespace
                ipython = get_ipython()
                ipython.push({'data': self.current_data})
                
                self.image_key = f['/entry/instrument/imaging/image_key'][:]
                
                # Get indices of projection images (key == 0)
                self.proj_indices = np.where(self.image_key == 0)[0]
                
                # Update info display
                n_proj = len(self.proj_indices)
                n_flat = np.sum(self.image_key == 1)
                n_dark = np.sum(self.image_key == 2)
                shape_str = ' × '.join(str(dim) for dim in self.current_data.shape)
                size_gb = self.current_data.nbytes / (1024**3)
                
                info_text = f"""
                <b>Data loaded:</b><br>
                Shape: {shape_str}<br>
                Data type: {self.current_data.dtype}<br>
                Size in memory: {size_gb:.2f} GB<br>
                Number of projections: {n_proj}<br>
                Number of flat fields: {n_flat}<br>
                Number of dark fields: {n_dark}<br>
                <b>Note:</b> Data has been loaded into global variable 'data'
                """
                self.data_info.value = info_text
                self.status_label.value = 'Data loaded successfully'
                
        except Exception as e:
            self.status_label.value = f'<span style="color: red">Error loading data: {str(e)}</span>'
            self._reset_widgets()
    
    def _create_layout(self):
        """Create the widget layout"""
        file_box = widgets.VBox([
            self.path_label,
            self.refresh_button,
            widgets.HBox([self.file_select, widgets.VBox([self.load_button])]),
            self.status_label,
            self.data_info
        ])
        
        display(file_box)
    
    def get_selected_file(self):
        """Return the full path of the selected file"""
        if self.file_select.value:
            return str(Path(self.nexus_path) / self.file_select.value)
        return None
    
    def get_data(self):
        """Return the currently loaded data array"""
        return self.current_data
        
    def get_projection_indices(self):
        """Return the indices of projection images"""
        return self.proj_indices
    
    def get_image_key(self):
        """Return the image key array"""
        return self.image_key
