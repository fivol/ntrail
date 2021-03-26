
if __name__ == '__main__':

    scope = (0, 2, 10, 13, 16, 18, 20)

    mask = 0
    for item in scope:
        mask += 1 << item

    print("Маска", mask)
