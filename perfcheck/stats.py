def compute_confidence(std, median):
    if median == 0:
        return 0

    noise = std / median

    if noise < 0.05:
        return 0.9
    elif noise < 0.1:
        return 0.8
    elif noise < 0.2:
        return 0.6
    else:
        return 0.4

