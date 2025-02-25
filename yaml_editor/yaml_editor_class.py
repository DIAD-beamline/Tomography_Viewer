import ipywidgets as widgets
from ipyfilechooser import FileChooser
from IPython.display import display, Markdown, clear_output
import yaml
import subprocess
import copy
import os

class YAML_Editor:
    def __init__(self, yaml_default_path="/"):
        self.HtTomo_base_yaml_path = None
        self.save_path = None
        self.initial_data = None
        self.current_data = None
        self.yaml_default_path = yaml_default_path
        self.file_chooser = FileChooser(self.yaml_default_path)
        self.file_chooser.title = 'YAML file editor:'
        self.path_label = widgets.Label(value="yaml file:")
        self.save_file_chooser = FileChooser(self.file_chooser.default_path)
        self.save_file_chooser.title = 'Save To:'
        self.save_file_chooser.show_only_dirs = False
        self.display_area = widgets.VBox()
        self.reset_button = widgets.Button(description='Reset All', layout=widgets.Layout(width='100px', margin='10px 0px 0px 0px'))
        self.save_button = widgets.Button(description='Save', layout=widgets.Layout(width='100px', margin='10px 0px 0px 10px'))
        self.horizontal_line = widgets.HTML(value="<hr style='width: 500px; margin-left: 0;'>")
        self.buttons_box = widgets.HBox([self.reset_button])
        self.figure = widgets.VBox([self.file_chooser, self.display_area, self.buttons_box, self.horizontal_line, self.save_file_chooser, self.save_button])
        self.buttons = []

        self.file_chooser.register_callback(self.save_file_path)
        #self.save_file_chooser.register_callback()#self.save_current_data)
        self.reset_button.on_click(lambda b: self.reset_all())
        self.save_button.on_click(lambda b: self.save_current_data())

    def save_file_path(self, chooser):
        if chooser.selected:
            self.HtTomo_base_yaml_path = chooser.selected
            with open(self.HtTomo_base_yaml_path, 'r') as file:
                self.initial_data = yaml.safe_load(file)
                self.current_data = copy.deepcopy(self.initial_data)
            print(f"Selected file path: {self.HtTomo_base_yaml_path}")
            self.reset_all()

    def update_current_data(self, path, new_value):
        path_components = path.split('.')
        current_level = self.current_data

        for component in path_components[:-1]:
            try:
                index = int(component) - 1
                if isinstance(current_level, list):
                    current_level = current_level[index]
                else:
                    keys = list(current_level.keys())
                    current_level = current_level[keys[index]]
            except (ValueError, TypeError):
                current_level = current_level[component]

        last_component = path_components[-1]
        try:
            index = int(last_component) - 1
            if isinstance(current_level, list):
                current_level[index] = new_value
            else:
                keys = list(current_level.keys())
                current_level[keys[index]] = new_value
        except (ValueError, TypeError):
            current_level[last_component] = new_value

    def remove_entry(self, path, button):
        path_components = path.split('.')
        current_level = self.current_data

        for component in path_components[:-1]:
            try:
                index = int(component) - 1
                if isinstance(current_level, list):
                    current_level = current_level[index]
                else:
                    keys = list(current_level.keys())
                    current_level = current_level[keys[index]]
            except (ValueError, TypeError):
                current_level = current_level[component]

        last_component = path_components[-1]
        try:
            index = int(last_component) - 1
            if isinstance(current_level, list):
                current_level.pop(index)
            else:
                keys = list(current_level.keys())
                del current_level[keys[index]]
        except (ValueError, TypeError):
            del current_level[last_component]

        self.buttons.remove(button)
        self.display_area.children = [child for child in self.display_area.children if button not in child.children]

        if not self.current_data:
            self.display_area.children = []

        self.display_widgets()

    def reset_all(self):
        self.current_data = copy.deepcopy(self.initial_data)
        self.display_area.children = []  # Clear the display area
        self.buttons = []  # Reset the buttons list
        print("Resetting all widgets and display area.")
        self.display_widgets()  # Redisplay the widgets from scratch

    def save_current_data(self, chooser=None):
        if chooser and chooser.selected:
            self.save_path = chooser.selected
        elif self.save_file_chooser.selected:
            self.save_path = self.save_file_chooser.selected
        else:
            print("No file selected for saving.")
            return

        with open(self.save_path, 'w') as file:
            yaml.dump(self.current_data, file)
        print(f"Current data saved to {save_path}")

    def open_save_file_chooser(self, button):
        if self.HtTomo_base_yaml_path:
            base_path, ext = os.path.splitext(self.HtTomo_base_yaml_path)
            default_save_path = f"{base_path}_edit{ext}"
            self.save_file_chooser.default_filename = os.path.basename(default_save_path)
        display(self.save_file_chooser)

    def is_terminal(self, value):
        return not isinstance(value, (dict, list))

    def calculate_max_label_width(self, entry, indent=0):
        max_length = 0
        for key, value in entry.items():
            number_space = "-" if indent == 0 else ". " * indent
            display_key = f"{number_space} {key}"
            max_length = max(max_length, len(display_key))
            if isinstance(value, dict):
                max_length = max(max_length, self.calculate_max_label_width(value, indent + 1))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        max_length = max(max_length, self.calculate_max_label_width(item, indent + 1))
        return max_length

    def display_widgets(self):
        dropdown_layout = widgets.Layout(width='400px')  # Set a fixed width for the dropdown menu
        remove_button_width = '100px'  # Set a fixed width for the remove button

        # Clear the display area before adding new widgets
        self.display_area.children = []

        if isinstance(self.current_data, list):
            max_label_width = max(self.calculate_max_label_width(entry) for entry in self.current_data)
            for entry_index, entry in enumerate(self.current_data, 1):
                entry_widgets = self.create_widgets(entry, prefix=f"{entry_index}.", max_label_width=max_label_width)

                remove_button = widgets.Button(
                    description='Remove',
                    layout=widgets.Layout(width=remove_button_width, margin='5px 0px 5px 0px')
                )
                remove_button.on_click(lambda b, path=f"{entry_index}", button=remove_button: self.remove_entry(path, button))
                self.buttons.append(remove_button)

                dropdown = widgets.Accordion(children=[widgets.VBox(entry_widgets)], layout=dropdown_layout)

                # Use the value of the first key as the title
                first_key = list(entry.keys())[0]
                title = str(entry[first_key])
                dropdown.set_title(0, title)

                self.display_area.children += (
                    widgets.HBox([remove_button, dropdown], layout=widgets.Layout(margin='0px 0px 10px 0px')),
                )
        elif isinstance(self.current_data, dict):
            max_label_width = self.calculate_max_label_width(self.current_data)
            entry_widgets = self.create_widgets(self.current_data, max_label_width=max_label_width)
            remove_button = widgets.Button(
                description='Remove',
                layout=widgets.Layout(width=remove_button_width, margin='5px 0px 5px 0px')
            )
            remove_button.on_click(lambda b, path="Configuration", button=remove_button: self.remove_entry(path, button))
            self.buttons.append(remove_button)

            dropdown = widgets.Accordion(children=[widgets.VBox(entry_widgets)], layout=dropdown_layout)
            dropdown.set_title(0, "Configuration")

            self.display_area.children += (
                widgets.HBox([remove_button, dropdown], layout=widgets.Layout(margin='0px 0px 10px 0px')),
            )

        # Set the width of the reset and save buttons to match the remove button width
        self.reset_button.layout.width = remove_button_width
        self.save_button.layout.width = remove_button_width

    def create_widgets(self, entry, indent=0, prefix="", max_label_width=0):
        widgets_list = []
        label_layout = widgets.Layout(min_width=f'{max_label_width + 10}px', margin='0px 5px 0px 0px')  # Set a minimum width and right margin for labels
        widget_layout = widgets.Layout(width='auto')  # Flexible width for entry widgets

        for i, (key, value) in enumerate(entry.items(), 1):
            number_space = "-" if indent == 0 else ". " * indent
            display_key = f"{number_space} {key}"
            widget_path = f"{prefix}{key}"

            if self.is_terminal(value):
                if isinstance(value, bool):
                    entry_widget = widgets.Dropdown(
                        options=[True, False],
                        value=value,
                        description='',
                        layout=widget_layout
                    )
                    entry_widget.observe(lambda change, path=widget_path: self.update_current_data(path, change['new']), names='value')
                elif isinstance(value, (int, float)):
                    entry_widget = widgets.Text(
                        value=str(value),
                        description='',
                        layout=widget_layout
                    )
                    entry_widget.observe(
                        lambda change, path=widget_path, orig_type=type(value):
                        self.update_current_data(path, orig_type(change['new'])),
                        names='value'
                    )
                elif isinstance(value, str) and '/' in value:
                    entry_widget = widgets.Text(
                        value=value,
                        description='',
                        layout=widget_layout
                    )
                    entry_widget.observe(lambda change, path=widget_path: self.update_current_data(path, change['new']), names='value')
                else:
                    entry_widget = widgets.Label(value=str(value), layout=widget_layout)

                widgets_list.append(
                    widgets.HBox([
                        widgets.Label(value=display_key + ":", layout=label_layout),
                        entry_widget
                    ], layout=widgets.Layout(margin='0px 0px 0px 0px'))
                )
            else:
                widgets_list.append(widgets.Label(value=display_key + ":", layout=label_layout))
                if isinstance(value, dict):
                    sub_widgets = self.create_widgets(value, indent + 1, f"{prefix}{key}.", max_label_width)
                    widgets_list.extend(sub_widgets)
                elif isinstance(value, list):
                    for j, item in enumerate(value, 1):
                        if isinstance(item, dict):
                            sub_widgets = self.create_widgets(item, indent + 1, f"{prefix}{key}.{j}.", max_label_width)
                            widgets_list.extend(sub_widgets)
                        else:
                            widgets_list.append(
                                widgets.HBox([
                                    widgets.Label(value=f"{number_space} - {item}", layout=label_layout)
                                ])
                            )
        return widgets_list

    def Editor(self):
        display(self.figure)
        self.display_widgets()
