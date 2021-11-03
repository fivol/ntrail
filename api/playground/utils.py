def show_icon(url):
    a = io.imread(url)
    plt.figure(figsize=(1, 1))
    plt.axis('off')
    plt.imshow(a)
    plt.show()