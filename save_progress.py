import pickle
import pygame


def save_data(data, filename="savefile.pkl"):
    """Saves any Python object, handling lists of objects and simple types."""
    with open(filename, "wb") as f:
        if isinstance(data, list) and all(hasattr(obj, "__dict__") for obj in data):
            # Convert objects to dictionaries, excluding pygame.Surface
            cleaned_data = []
            for obj in data:
                obj_dict = {
                    key: value for key, value in obj.__dict__.items()
                    if not isinstance(value, pygame.Surface)  # Exclude images
                }
                cleaned_data.append(obj_dict)
            pickle.dump(cleaned_data, f)
        else:
            # Save normally if it's a basic data type
            pickle.dump(data, f)


def load_data(filename, cls=None):
    """Loads saved data, reconstructing class instances if needed."""
    with open(filename, "rb") as f:
        data = pickle.load(f)

    # If it's a list of dictionaries and a class is provided, reconstruct objects
    if isinstance(data, list) and cls and all(isinstance(item, dict) for item in data):
        objects = []
        for item in data:
            image_path = item.get("image_path")  # Get saved image path
            projectile_image = item.get("projectile_image")  # Get projectile image path

            obj = cls(**item)  # Create a new instance of the class

            # Reload images if paths exist
            if image_path:
                obj.image = pygame.image.load(image_path).convert_alpha()
                obj.original_image = pygame.image.load(image_path).convert_alpha()

            objects.append(obj)
        return objects

    return data  # Return raw data if it's not a list of objects
