from random import random

obj_list = [
    'a banana',
    'a baseball',
    'a beach ball',
    'a blanket',
    'a boomerang',
    'a bunch of grapes',
    'a computer out the window',
    'a couch',
    'a discus',
    'a football',
    'a fridge at their neighbor',
    'a frustratingly long book',
    'a knife',
    'a loaded gun instead of shooting it',
    'a paper airplane',
    'a plate',
    'a pool ball',
    'a samurai sword',
    'a sharp stone',
    'a shot put',
    'a singular grape',
    'a spear',
    'a stuffed toad plushie',
    'a trident',
    'a water polo ball',
    'an apple',
    'an error',
    'an exception',
    'an orange',
    'away the trash',
    'away their chances at a relationship',
    'some dice',
    'some eggs',
    'some hands',
    'some poop',
    'some water balloons',
    'their last brain cell out the window',
    'their phone at the wall'
]

def get_random_object():
    return random.choose(obj_list)

if __name__ == "__main__":
    raise ImportError("objects.py must be imported, not run directly")
