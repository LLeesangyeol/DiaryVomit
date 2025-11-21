import matplotlib.pyplot as plt
import matplotlib.image as img
import os
base_path = os.path.abspath('.')
path = os.path.join(base_path, 'src\\images', 'da.jpg')
image = img.imread(path)
plt.imshow(image)
plt.show()