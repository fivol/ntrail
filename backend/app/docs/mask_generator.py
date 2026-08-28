
if __name__ == '__main__':

    scope = (1, 3, 2, 13, 16, 18, 20)

    mask = 0
    for item in scope:
        mask += 1 << item

    print("Маска", mask)
