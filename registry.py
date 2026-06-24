FEATURES = {}   # name -> (description, callable)


def register(name, desc):
    def decorator(fn):
        FEATURES[name] = (desc, fn)
        return fn
    return decorator
