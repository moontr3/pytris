
class InvalidColor(Exception):
    pass

def is_valid(color: tuple) -> bool:
    if len(color) == 3:

        for i in color:
            if i < 0 or i > 255 and type(i) != int:
                return False
        
        return True
    
    return False


def invert(color: tuple) -> tuple:
    if not is_valid(color):
        raise InvalidColor
    
    new_color = []

    for i in color:
        new_color.append(255-i)
    
    return tuple(new_color)

def grayscale(color, return_single_value=False) -> tuple:
    if not is_valid(color):
        raise InvalidColor
    
    grayscaled_color = sum(color)//len(color)
    
    if return_single_value:
        return grayscaled_color

    return (grayscaled_color, grayscaled_color, grayscaled_color)
    
def transition(from_color, to_color, key) -> tuple:
    if (not is_valid(from_color)) or (not is_valid(to_color)) or key < 0 or key > 1:
        raise InvalidColor
    
    difference = (from_color[0]-to_color[0], from_color[1]-to_color[1], from_color[2]-to_color[2])
    return (from_color[0]-difference[0]*key, from_color[1]-difference[1]*key, from_color[2]-difference[2]*key)